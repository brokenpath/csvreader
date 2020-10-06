from __future__ import print_function
from collections import OrderedDict
import csv
from csv import (
    QUOTE_ALL,
    QUOTE_MINIMAL,
    QUOTE_NONNUMERIC,
    QUOTE_NONE
)
import logging

logger = logging.getLogger(__name__)


try:
    basestring
except NameError:
    # For python 3 compatibility
    basestring = str


class Error(Exception): pass


class Dialect:
    """Describe a CSV dialect.

    The fields means the same as for the standard csv.Dialect.
    """

    def __init__(self, delimiter=',', quotechar='"', escapechar=None,
            doublequote=True, skipinitialspace=False, lineterminator='\n',
            quoting=QUOTE_MINIMAL, strict=False):
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.escapechar = escapechar
        self.doublequote = doublequote
        self.skipinitialspace = skipinitialspace
        self.lineterminator = lineterminator
        self.quoting = quoting
        self.strict = strict


def get_dialect(dialect, **fmtparams):
    if isinstance(dialect, basestring):
        dialect = csv.get_dialect(dialect)

    # Unlike the standard csv module, this module does not have its own
    # universal newline handling, but instead expects the provided file objects
    # to be opened in universal newline mode. We therefore convert all newline
    # line terminators to '\n'.
    lineterminator = fmtparams.get('lineterminator', dialect.lineterminator)
    if lineterminator in {'\r', '\r\n'}:
        lineterminator = '\n'

    #XXX csv.Dialect does for some reason not expose strict. We set strict=False
    # by default, but this will of course be wrong if the original dialect had
    # strict=True.
    strict = False
    if hasattr(dialect, 'strict'):
        strict = dialect.strict

    return Dialect(
        delimiter=fmtparams.get('delimiter', dialect.delimiter),
        quotechar=fmtparams.get('quotechar', dialect.quotechar),
        escapechar=fmtparams.get('escapechar', dialect.escapechar),
        doublequote=fmtparams.get('doublequote', dialect.doublequote),
        skipinitialspace=fmtparams.get('skipinitialspace', dialect.skipinitialspace),
        lineterminator=lineterminator,
        quoting=fmtparams.get('quoting', dialect.quoting),
        strict=fmtparams.get('strict', strict)
    )


class ReaderState:
    END_OF_FIELD = 0
    END_OF_RECORD = 1


class Reader:
    """Reads CSV file.

    Identical to the standard csv.reader, except:

    * Does not support QUOTE_NONUMERIC.

    * Does not have its own universal newline handling, but instead expects the
    provided file objects to be opened in universal newline mode.

    * Does support non-newline lineterminator.

    * Does support '\0' in fields.

    * The method skip is added.
    """

    def __init__(self, csvfile, dialect=Dialect(), **fmtparams):
        self._csvfile = csvfile
        self.dialect = get_dialect(dialect, **fmtparams)
        self.line_num = 0

    def skip(self, num_lines=1):
        """Skip lines without parsing them."""
        for _ in range(num_lines):
            if not self._csvfile.readline():
                break
            self.line_num += 1

    def _error(self, message):
        if self.dialect.strict:
            logger.error('Error on line %s: %s', self.line_num, message)
            raise Error(message)

    def _next_char(self):
        c = self._csvfile.read(1)
        if c == '\n':
            self.line_num += 1
        return c

    def _read_escaped_char(self):
        c = self._next_char()
        if not c:
            self._error('End of file reached while reading escaped character')
            return '\n'
        return c

    def _read_field(self, first_char):
        delimiter = self.dialect.delimiter
        lineterminator = self.dialect.lineterminator
        escapechar = self.dialect.escapechar
        field = ''
        c = first_char
        while True:
            if c == delimiter:
                return field, ReaderState.END_OF_FIELD
            elif c == lineterminator or not c:
                return field, ReaderState.END_OF_RECORD
            elif c == escapechar:
                field += self._read_escaped_char()
            else:
                field += c
            c = self._next_char()

    def _read_quoted_field(self):
        field = ''
        while True:
            c = self._next_char()
            if c == self.dialect.quotechar:
                c = self._next_char()
                if self.dialect.doublequote and c == self.dialect.quotechar:
                    field += c
                else:
                    break
            elif c == self.dialect.escapechar:
                field += self._read_escaped_char()
            elif not c:
                self._error('End of file reached while reading quoted field')
                return field, ReaderState.END_OF_RECORD
            else:
                field += c
        if c == self.dialect.delimiter:
            return field, ReaderState.END_OF_FIELD
        elif c == self.dialect.lineterminator or not c:
            return field, ReaderState.END_OF_RECORD
        else:
            self._error('Found trailing data after quoted field')
            #XXX If c is escapedchar, the following will include it verbatim and
            # not escape the next character. This seems wrong, but is what the
            # standard csv module does.
            field += c
            rest, state = self._read_field(self._next_char())
            return field + rest, state

    def __iter__(self):
        return self

    def __next__(self):
        c = self._next_char()
        if not c:
            logger.debug('Finished reading csv file, read %s lines', self.line_num)
            raise StopIteration
        if c == self.dialect.lineterminator:
            return []
        record = []
        while True:
            if self.dialect.skipinitialspace:
                while c == ' ':
                    c = self._next_char()
            if self.dialect.quoting != QUOTE_NONE and c == self.dialect.quotechar:
                field, state = self._read_quoted_field()
            else:
                field, state = self._read_field(c)
            record.append(field)
            if state == ReaderState.END_OF_RECORD:
                return record
            c = self._next_char()

    next = __next__



class RegexReader:
	def __init__(self, file, dialect=None, encoding='latin-1'):
		self.lineNum = 0
		self.dialect = dialect
		self.encoding = encoding
		
		f = open(file, 'rb') #mv filepointer out
		file = f.read().decode(encoding, 'replace')

		#TODO: doublequote, skipinitialspace, strict
		self.re = re.compile(r'''
			(?=\S)((?:								# Start capturing here.
			  [^{lineterminator}{quotechar}]		# Either a series of non-lineterminator non-quote characters.
			  |										# OR
			  {quotechar}(?:						# A double-quote followed by a string of characters...
				[^{quotechar}\{escapechar}]|\{escapechar}.	# That are either non-quotes or escaped...
			  )*									# ...repeated any number of times.
			  {quotechar}							# Followed by a closing double-quote.
			)*)										# Done capturing.
			(?:[{lineterminator}]|$)				# Followed by a lineterminator or the end of a string.
			'''.format(lineterminator=dialect.lineterminator, quotechar=dialect.quotechar, escapechar=dialect.escapechar), re.VERBOSE)

		self.csvIter = (x.group(1) for x in self.re.finditer(file))

	def __del__(self):
		return

	def __iter__(self):
		self.header()
		return self

	def next(self):
		return self.__next__()

	def __next__(self):
		row = None
		while row == None:
			row = self.get_next_row()
		return dict(zip(self.header(), row))

	def get_next_row(self, skip=False):
		row = next(self.csvIter).encode(self.encoding)
		self.lineNum += 1

		if not skip:
			#Split cells
			row = list(csv.reader([row], dialect=self.dialect))[0]
			# Check empty cells
			for cell in row:
				if len(cell) == 0:
					logging.warning("Empty cell at line {}".format(self.lineNum))

		return row

	def header(self):
		try:
			return self.headerLine
		except AttributeError as error:
			raise Exception("Header not defined")

	def read_header(self):
		row = self.get_next_row()
		if row == None:
			raise Exception("Bad header")

		self.headerLine = row

	def skip(self, skip_lines):
		for _ in range(skip_lines):
			row = self.get_next_row(verify=False, skip=True)



class DictReader:
    """Reads records of CSV file to dict objects.

    Identical to the standard csv.DictReader, except:
    
    * It uses the Reader class from this module to read the CSV file, instead of
    the csv.reader class from the standard library. All the differences between
    Reader and csv.reader thus aplies here as well.

    * The methods skip and read_header are added.
    """

    def __init__(self, csvfile, fieldnames=None, restkey=None, restval=None,
            dialect="excel", *args, **kwargs):
        self._fieldnames = fieldnames   # list of keys for the dict
        self.restkey = restkey          # key to catch long rows
        self.restval = restval          # default value for short rows
        self.reader = Reader(csvfile, dialect, *args, **kwargs)
        self.dialect = dialect
        self.line_num = 0

    @property
    def fieldnames(self):
        if self._fieldnames is None:
            self.read_header()
        return self._fieldnames

    @fieldnames.setter
    def fieldnames(self, value):
        self._fieldnames = value

    def read_header(self):
        """Read field names from header."""
        try:
            self._fieldnames = next(self.reader)
        except StopIteration:
            logger.error('End of file reached when attempting to read header')
            pass
        self.line_num = self.reader.line_num
        return self._fieldnames

    def skip(self, num_lines=1):
        """Skip lines without parsing them."""
        self.reader.skip(num_lines)
        self.line_num = self.reader.line_num

    def __iter__(self):
        return self

    def __next__(self):
        if self.line_num == 0:
            # Used only for its side effect.
            self.fieldnames
        row = next(self.reader)
        self.line_num = self.reader.line_num

        # unlike the basic reader, we prefer not to return blanks,
        # because we will typically wind up with a dict full of None
        # values
        while row == []:
            row = next(self.reader)
        d = OrderedDict(zip(self.fieldnames, row))
        lf = len(self.fieldnames)
        lr = len(row)
        if lf < lr:
            d[self.restkey] = row[lf:]
        elif lf > lr:
            for key in self.fieldnames[lr:]:
                d[key] = self.restval
        return d

    next = __next__



from lark import Lark, Transformer

class PEGParserFactory:
    # TODO : will pop if dialect contains unescaped \ chars examples \n
    def __init__(self, file, dialect=None, encoding='latin-1'):
        self.lineNum = 0
        self.dialect = dialect
        self.encoding = encoding
        
        f = open(file, 'rb') #mv filepointer out
        file = f.read().decode(encoding, 'replace')

        #TODO: doublequote, skipinitialspace, strict
        grammar = """
        start: record ("{t}" record)* 
        record: field ("{d}" field)*
        field: (quoted_field | FIELD_CONTENT)*
        quoted_field.1: QUOTECHAR FIELD_CONTENT_QUOTED? QUOTECHAR
        FIELD_CONTENT: /([^{d}{t}{q}])+/
        FIELD_CONTENT_QUOTED: /[^{q}]+/
        QUOTECHAR: /{q}/
        """.format(t=dialect.lineterminator, d=dialect.delimiter, q=dialect.quotechar)

        class csvTransformer(Transformer):
            def quoted_field(self, s):
                return ''.join(s)

            def field(self, s):
                return ''.join(s)

            record = list
            start = list

        p = Lark(grammar, parser="lalr", transformer=csvTransformer())

        self.csvIter = iter(p.parse(file))

    def __del__(self):
        return

    def __iter__(self):
        self.header()
        return self

    def next(self):
        return self.__next__()

    def __next__(self):
        row = None
        while row == None:
            row = self.get_next_row()
        return dict(zip(self.header(), row))

    def get_next_row(self, skip=False):
        row = next(self.csvIter)
        self.lineNum += 1

        return row

    def header(self):
        try:
            return self.headerLine
        except AttributeError as error:
            raise Exception("Header not defined")

    def read_header(self):
        row = self.get_next_row()
        if row == None:
            raise Exception("Bad header")

        self.headerLine = row

    def skip(self, skip_lines):
        for _ in range(skip_lines):
            row = self.get_next_row(verify=False, skip=True)



def main():
    import io
    import argparse

    parser = argparse.ArgumentParser(description='CSV reader')
    parser.add_argument('file_name', metavar='FILE')
    parser.add_argument('--encoding', default='utf-8')
    parser.add_argument('--delimiter', default=',')
    parser.add_argument('--quotechar', default='"')
    parser.add_argument('--escapechar', default=None)
    parser.add_argument('--doublequote', action='store_true')
    parser.add_argument('--no-doublequote', dest='doublequote', action='store_false')
    parser.set_defaults(doublequote=True)
    parser.add_argument('--skipinitialspace', action='store_true')
    parser.add_argument('--no-skipinitialspace', dest='skipinitialspace', action='store_false')
    parser.set_defaults(skipinitialspace=False)
    parser.add_argument('--lineterminator', default='\n')
    parser.add_argument('--quoting', action='store_true')
    parser.add_argument('--no-quoting', dest='quoting', action='store_false')
    parser.set_defaults(quoting=True)
    parser.add_argument('--strict', action='store_true')
    parser.add_argument('--no-strict', dest='strict', action='store_false')
    parser.set_defaults(strict=False)
    parser.add_argument('--loglevel', default='WARNING')
    arguments = parser.parse_args()

    logging.basicConfig(level=logging.getLevelName(arguments.loglevel))

    dialect = Dialect(
        delimiter=arguments.delimiter,
        quotechar=arguments.quotechar,
        escapechar=arguments.escapechar,
        doublequote=arguments.doublequote,
        skipinitialspace=arguments.skipinitialspace,
        lineterminator=arguments.lineterminator,
        quoting=QUOTE_MINIMAL if arguments.quoting else QUOTE_NONE,
        strict=arguments.strict
    )

    with io.open(arguments.file_name, encoding=arguments.encoding) as stream:
        reader = DictReader(stream, dialect=dialect)
        header = reader.read_header()
        print('Header:', ' '.join(header))
        for i, record in enumerate(reader):
            if i % 100000 == 0 and i > 0:
                logger.debug('Read %s records', i)
        print('Lines read:', reader.line_num)
        print('Records read:', i + 1)


if __name__ == '__main__':
    main()

