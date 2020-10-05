# coding: utf-8

# Copyright (C) 2001,2002 Python Software Foundation
# csv package unit tests

from __future__ import unicode_literals
import sys
import io
import unittest
import csv_reader
from textwrap import dedent
from collections import OrderedDict


if sys.version_info.major < 3:
    try:
        unicode_literals
    except NameError:
        from io import BytesIO as StringIO
        import tempfile
        import csv as _csv

        def TemporaryFile(mode='w+b', newline='', encoding=None):
            return tempfile.TemporaryFile('Ur+')

        class unix_dialect(_csv.Dialect):
            """Describe the usual properties of Unix-generated CSV files."""
            delimiter = ','
            quotechar = '"'
            doublequote = True
            skipinitialspace = False
            lineterminator = '\n'
            quoting = _csv.QUOTE_ALL
        _csv.register_dialect("unix", unix_dialect)
    else:
        from io import StringIO
        import csv as _csv

        def TemporaryFile(mode='w+b', newline='', encoding=None):
            return StringIO(newline=None)

        class unix_dialect(_csv.Dialect):
            """Describe the usual properties of Unix-generated CSV files."""
            delimiter = b','
            quotechar = b'"'
            doublequote = True
            skipinitialspace = False
            lineterminator = b'\n'
            quoting = _csv.QUOTE_ALL
        _csv.register_dialect("unix", unix_dialect)
else:
    from io import StringIO
    import tempfile
    def TemporaryFile(mode='w+b', newline='', encoding=None):
        return tempfile.TemporaryFile(mode, newline=None, encoding=encoding)


class csv:

    Error = csv_reader.Error
    QUOTE_NONE = csv_reader.QUOTE_NONE
    QUOTE_NONNUMERIC = csv_reader.QUOTE_NONNUMERIC

    class excel:
        delimiter = ','
        quotechar = '"'
        doublequote = True
        skipinitialspace = False
        lineterminator = '\r\n'
        quoting = csv_reader.QUOTE_MINIMAL

    @staticmethod
    def reader(csvfile, *args, **kwargs):
        if isinstance(csvfile, list):
            csvfile = StringIO('\n'.join(l.rstrip('\r\n') for l in csvfile))
        return csv_reader.Reader(csvfile, *args, **kwargs)

    @staticmethod
    def DictReader(csvfile, *args, **kwargs):
        if isinstance(csvfile, list):
            csvfile = StringIO('\n'.join(l.rstrip('\r\n') for l in csvfile))
        return csv_reader.DictReader(csvfile, *args, **kwargs)


class Test_Csv(unittest.TestCase):
    """
    Test the underlying C csv parser in ways that are not appropriate
    from the high level interface. Further tests of this nature are done
    in TestDialectRegistry.
    """

    def _read_test(self, input, expect, **kwargs):
        reader = csv.reader(input, **kwargs)
        result = list(reader)
        self.assertEqual(result, expect)

    def test_read_oddinputs(self):
        self._read_test([], [])
        #self._read_test([''], [[]]) #TODO
        self.assertRaises(csv.Error, self._read_test,
                          ['"ab"c'], None, strict = 1)
        self._read_test(['ab\0c'], [['ab\0c']], strict = 1)
        self._read_test(['"ab"c'], [['abc']], doublequote = 0)


    def test_read_eol(self):
        self._read_test(['a,b'], [['a','b']])
        self._read_test(['a,b\n'], [['a','b']])
        self._read_test(['a,b\r\n'], [['a','b']])
        self._read_test(['a,b\r'], [['a','b']])
        #TODO
        #self.assertRaises(csv.Error, self._read_test, ['a,b\rc,d'], [])
        #self.assertRaises(csv.Error, self._read_test, ['a,b\nc,d'], [])
        #self.assertRaises(csv.Error, self._read_test, ['a,b\r\nc,d'], [])

    def test_read_eof(self):
        self._read_test(['a,"'], [['a', '']])
        self._read_test(['"a'], [['a']])
        self._read_test(['^'], [['\n']], escapechar='^')
        self.assertRaises(csv.Error, self._read_test, ['a,"'], [], strict=True)
        self.assertRaises(csv.Error, self._read_test, ['"a'], [], strict=True)
        self.assertRaises(csv.Error, self._read_test,
                          ['^'], [], escapechar='^', strict=True)

    def test_read_escape(self):
        self._read_test(['a,\\b,c'], [['a', 'b', 'c']], escapechar='\\')
        self._read_test(['a,b\\,c'], [['a', 'b,c']], escapechar='\\')
        self._read_test(['a,"b\\,c"'], [['a', 'b,c']], escapechar='\\')
        self._read_test(['a,"b,\\c"'], [['a', 'b,c']], escapechar='\\')
        self._read_test(['a,"b,c\\""'], [['a', 'b,c"']], escapechar='\\')
        self._read_test(['a,"b,c"\\'], [['a', 'b,c\\']], escapechar='\\')

    def test_read_quoting(self):
        self._read_test(['1,",3,",5'], [['1', ',3,', '5']])
        self._read_test(['1,",3,",5'], [['1', '"', '3', '"', '5']],
                        quotechar=None, escapechar='\\')
        self._read_test(['1,",3,",5'], [['1', '"', '3', '"', '5']],
                        quoting=csv.QUOTE_NONE, escapechar='\\')
        #TODO
        # will this fail where locale uses comma for decimals?
        #self._read_test([',3,"5",7.3, 9'], [['', 3, '5', 7.3, 9]],
        #                quoting=csv.QUOTE_NONNUMERIC)
        self._read_test(['"a\nb", 7'], [['a\nb', ' 7']])
        #TODO
        #self.assertRaises(ValueError, self._read_test,
        #                  ['abc,3'], [[]],
        #                  quoting=csv.QUOTE_NONNUMERIC)

    def test_read_linenum(self):
        r = csv.reader(['line,1', 'line,2', 'line,3'])
        self.assertEqual(r.line_num, 0)
        next(r)
        self.assertEqual(r.line_num, 1)
        next(r)
        self.assertEqual(r.line_num, 2)
        next(r)
        #self.assertEqual(r.line_num, 3) #TODO
        self.assertRaises(StopIteration, next, r)
        #self.assertEqual(r.line_num, 3) #TODO


class TestCsvBase(unittest.TestCase):
    def readerAssertEqual(self, input, expected_result):
        with TemporaryFile("w+", newline='') as fileobj:
            fileobj.write(input)
            fileobj.seek(0)
            reader = csv.reader(fileobj, dialect = self.dialect)
            fields = list(reader)
            self.assertEqual(fields, expected_result)

class TestDialectExcel(TestCsvBase):
    dialect = 'excel'

    def test_single(self):
        self.readerAssertEqual('abc', [['abc']])

    def test_simple(self):
        self.readerAssertEqual('1,2,3,4,5', [['1','2','3','4','5']])

    def test_blankline(self):
        self.readerAssertEqual('', [])

    def test_empty_fields(self):
        self.readerAssertEqual(',', [['', '']])

    def test_singlequoted(self):
        self.readerAssertEqual('""', [['']])

    def test_singlequoted_left_empty(self):
        self.readerAssertEqual('"",', [['','']])

    def test_singlequoted_right_empty(self):
        self.readerAssertEqual(',""', [['','']])

    def test_single_quoted_quote(self):
        self.readerAssertEqual('""""', [['"']])

    def test_quoted_quotes(self):
        self.readerAssertEqual('""""""', [['""']])

    def test_inline_quote(self):
        self.readerAssertEqual('a""b', [['a""b']])

    def test_inline_quotes(self):
        self.readerAssertEqual('a"b"c', [['a"b"c']])

    def test_quotes_and_more(self):
        # Excel would never write a field containing '"a"b', but when
        # reading one, it will return 'ab'.
        self.readerAssertEqual('"a"b', [['ab']])

    def test_lone_quote(self):
        self.readerAssertEqual('a"b', [['a"b']])

    def test_quote_and_quote(self):
        # Excel would never write a field containing '"a" "b"', but when
        # reading one, it will return 'a "b"'.
        self.readerAssertEqual('"a" "b"', [['a "b"']])

    def test_space_and_quote(self):
        self.readerAssertEqual(' "a"', [[' "a"']])

    def test_quoted(self):
        self.readerAssertEqual('1,2,3,"I think, therefore I am",5,6',
                               [['1', '2', '3',
                                 'I think, therefore I am',
                                 '5', '6']])

    def test_quoted_quote(self):
        self.readerAssertEqual('1,2,3,"""I see,"" said the blind man","as he picked up his hammer and saw"',
                               [['1', '2', '3',
                                 '"I see," said the blind man',
                                 'as he picked up his hammer and saw']])

    def test_quoted_nl(self):
        input = '''\
1,2,3,"""I see,""
said the blind man","as he picked up his
hammer and saw"
9,8,7,6'''
        self.readerAssertEqual(input,
                               [['1', '2', '3',
                                   '"I see,"\nsaid the blind man',
                                   'as he picked up his\nhammer and saw'],
                                ['9','8','7','6']])

    def test_dubious_quote(self):
        self.readerAssertEqual('12,12,1",', [['12', '12', '1"', '']])

class EscapedExcel(csv.excel):
    quoting = csv.QUOTE_NONE
    escapechar = '\\'

class TestEscapedExcel(TestCsvBase):
    dialect = EscapedExcel()

    def test_read_escape_fieldsep(self):
        self.readerAssertEqual('abc\\,def\r\n', [['abc,def']])

class TestDialectUnix(TestCsvBase):
    dialect = 'unix'

    def test_simple_reader(self):
        self.readerAssertEqual('"1","abc def","abc"\n', [['1', 'abc def', 'abc']])

class QuotedEscapedExcel(csv.excel):
    quoting = csv.QUOTE_NONNUMERIC
    escapechar = '\\'

class TestQuotedEscapedExcel(TestCsvBase):
    dialect = QuotedEscapedExcel()

    def test_read_escape_fieldsep(self):
        self.readerAssertEqual('"abc\\,def"\r\n', [['abc,def']])

class TestDictFields(unittest.TestCase):
    ### "long" means the row is longer than the number of fieldnames
    ### "short" means there are fewer elements in the row than fieldnames

    def test_read_dict_fields(self):
        with TemporaryFile("w+") as fileobj:
            fileobj.write("1,2,abc\r\n")
            fileobj.seek(0)
            reader = csv.DictReader(fileobj,
                                    fieldnames=["f1", "f2", "f3"])
            self.assertEqual(next(reader), {"f1": '1', "f2": '2', "f3": 'abc'})

    def test_read_dict_no_fieldnames(self):
        with TemporaryFile("w+") as fileobj:
            fileobj.write("f1,f2,f3\r\n1,2,abc\r\n")
            fileobj.seek(0)
            reader = csv.DictReader(fileobj)
            self.assertEqual(next(reader), {"f1": '1', "f2": '2', "f3": 'abc'})
            self.assertEqual(reader.fieldnames, ["f1", "f2", "f3"])

    # Two test cases to make sure existing ways of implicitly setting
    # fieldnames continue to work.  Both arise from discussion in issue3436.
    def test_read_dict_fieldnames_from_file(self):
        with TemporaryFile("w+") as fileobj:
            fileobj.write("f1,f2,f3\r\n1,2,abc\r\n")
            fileobj.seek(0)
            reader = csv.DictReader(fileobj,
                                    fieldnames=next(csv.reader(fileobj)))
            self.assertEqual(reader.fieldnames, ["f1", "f2", "f3"])
            self.assertEqual(next(reader), {"f1": '1', "f2": '2', "f3": 'abc'})

    def test_read_dict_fieldnames_chain(self):
        import itertools
        with TemporaryFile("w+") as fileobj:
            fileobj.write("f1,f2,f3\r\n1,2,abc\r\n")
            fileobj.seek(0)
            reader = csv.DictReader(fileobj)
            first = next(reader)
            for row in itertools.chain([first], reader):
                self.assertEqual(reader.fieldnames, ["f1", "f2", "f3"])
                self.assertEqual(row, {"f1": '1', "f2": '2', "f3": 'abc'})

    def test_read_long(self):
        with TemporaryFile("w+") as fileobj:
            fileobj.write("1,2,abc,4,5,6\r\n")
            fileobj.seek(0)
            reader = csv.DictReader(fileobj,
                                    fieldnames=["f1", "f2"])
            self.assertEqual(next(reader), {"f1": '1', "f2": '2',
                                             None: ["abc", "4", "5", "6"]})

    def test_read_long_with_rest(self):
        with TemporaryFile("w+") as fileobj:
            fileobj.write("1,2,abc,4,5,6\r\n")
            fileobj.seek(0)
            reader = csv.DictReader(fileobj,
                                    fieldnames=["f1", "f2"], restkey="_rest")
            self.assertEqual(next(reader), {"f1": '1', "f2": '2',
                                             "_rest": ["abc", "4", "5", "6"]})

    def test_read_long_with_rest_no_fieldnames(self):
        with TemporaryFile("w+") as fileobj:
            fileobj.write("f1,f2\r\n1,2,abc,4,5,6\r\n")
            fileobj.seek(0)
            reader = csv.DictReader(fileobj, restkey="_rest")
            self.assertEqual(reader.fieldnames, ["f1", "f2"])
            self.assertEqual(next(reader), {"f1": '1', "f2": '2',
                                             "_rest": ["abc", "4", "5", "6"]})

    def test_read_short(self):
        with TemporaryFile("w+") as fileobj:
            fileobj.write("1,2,abc,4,5,6\r\n1,2,abc\r\n")
            fileobj.seek(0)
            reader = csv.DictReader(fileobj,
                                    fieldnames="1 2 3 4 5 6".split(),
                                    restval="DEFAULT")
            self.assertEqual(next(reader), {"1": '1', "2": '2', "3": 'abc',
                                             "4": '4', "5": '5', "6": '6'})
            self.assertEqual(next(reader), {"1": '1', "2": '2', "3": 'abc',
                                             "4": 'DEFAULT', "5": 'DEFAULT',
                                             "6": 'DEFAULT'})

    def test_read_multi(self):
        sample = [
            '2147483648,43.0e12,17,abc,def\r\n',
            '147483648,43.0e2,17,abc,def\r\n',
            '47483648,43.0,170,abc,def\r\n'
            ]

        reader = csv.DictReader(sample,
                                fieldnames="i1 float i2 s1 s2".split())
        self.assertEqual(next(reader), {"i1": '2147483648',
                                         "float": '43.0e12',
                                         "i2": '17',
                                         "s1": 'abc',
                                         "s2": 'def'})

    def test_read_with_blanks(self):
        reader = csv.DictReader(["1,2,abc,4,5,6\r\n","\r\n",
                                 "1,2,abc,4,5,6\r\n"],
                                fieldnames="1 2 3 4 5 6".split())
        self.assertEqual(next(reader), {"1": '1', "2": '2', "3": 'abc',
                                         "4": '4', "5": '5', "6": '6'})
        self.assertEqual(next(reader), {"1": '1', "2": '2', "3": 'abc',
                                         "4": '4', "5": '5', "6": '6'})

    def test_read_semi_sep(self):
        reader = csv.DictReader(["1;2;abc;4;5;6\r\n"],
                                fieldnames="1 2 3 4 5 6".split(),
                                delimiter=';')
        self.assertEqual(next(reader), {"1": '1', "2": '2', "3": 'abc',
                                         "4": '4', "5": '5', "6": '6'})

class TestUnicode(unittest.TestCase):

    names = ["Martin von Löwis",
             "Marc André Lemburg",
             "Guido van Rossum",
             "François Pinard"]

    def test_unicode_read(self):
        with TemporaryFile("w+", newline='', encoding="utf-8") as fileobj:
            fileobj.write(",".join(self.names) + "\r\n")
            fileobj.seek(0)
            reader = csv.reader(fileobj)
            self.assertEqual(list(reader), [self.names])

class KeyOrderingTest(unittest.TestCase):

    def test_ordered_dict_reader(self):
        data = dedent('''\
            FirstName,LastName
            Eric,Idle
            Graham,Chapman,Over1,Over2

            Under1
            John,Cleese
        ''').splitlines()

        self.assertEqual(list(csv.DictReader(data)),
            [OrderedDict([('FirstName', 'Eric'), ('LastName', 'Idle')]),
             OrderedDict([('FirstName', 'Graham'), ('LastName', 'Chapman'),
                          (None, ['Over1', 'Over2'])]),
             OrderedDict([('FirstName', 'Under1'), ('LastName', None)]),
             OrderedDict([('FirstName', 'John'), ('LastName', 'Cleese')]),
            ])

        self.assertEqual(list(csv.DictReader(data, restkey='OtherInfo')),
            [OrderedDict([('FirstName', 'Eric'), ('LastName', 'Idle')]),
             OrderedDict([('FirstName', 'Graham'), ('LastName', 'Chapman'),
                          ('OtherInfo', ['Over1', 'Over2'])]),
             OrderedDict([('FirstName', 'Under1'), ('LastName', None)]),
             OrderedDict([('FirstName', 'John'), ('LastName', 'Cleese')]),
            ])

        del data[0]            # Remove the header row
        self.assertEqual(list(csv.DictReader(data, fieldnames=['fname', 'lname'])),
            [OrderedDict([('fname', 'Eric'), ('lname', 'Idle')]),
             OrderedDict([('fname', 'Graham'), ('lname', 'Chapman'),
                          (None, ['Over1', 'Over2'])]),
             OrderedDict([('fname', 'Under1'), ('lname', None)]),
             OrderedDict([('fname', 'John'), ('lname', 'Cleese')]),
            ])


class DictReaderTest(unittest.TestCase):

    def test_skip(self):
        data = StringIO(
            'illegal line\n'
            'field_a,field_b\n'
            'asdasdasdas\n'
            '\n'
            '1,abc\n'
            '2,def'
        )
        reader = csv_reader.DictReader(data)
        reader.skip()
        reader.read_header()
        reader.skip(2)
        self.assertEqual(
            list(reader),
            [
                OrderedDict([('field_a', '1'), ('field_b', 'abc')]),
                OrderedDict([('field_a', '2'), ('field_b', 'def')])
            ]
        )

    def test_semicolon_lineterminator(self):
        data = StringIO(
            'field_a,field_b;'
            '1,abc;'
            '2,de\nf'
        )
        reader = csv_reader.DictReader(data, lineterminator=';')
        self.assertEqual(
            list(reader),
            [
                OrderedDict([('field_a', '1'), ('field_b', 'abc')]),
                OrderedDict([('field_a', '2'), ('field_b', 'de\nf')])
            ]
        )


if __name__ == '__main__':
    import logging
    logging.disable(logging.CRITICAL)
    unittest.main()

