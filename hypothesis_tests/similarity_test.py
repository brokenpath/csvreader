import unittest


import io
from io import (StringIO, SEEK_SET)
import csv
from hypothesis import given
import hypothesis.strategies as st
import mcsv
from mcsv.csv_reader import (
    PEGParserFactory,
    DictReader,
    Dialect
)

class SameResult(unittest.TestCase):
    def __init__(self, methodName):
        super().__init__(methodName)
        self.dialect_peg = Dialect(
                delimiter      = ';',
                doublequote    = True,
                lineterminator = '\\r\\n',
                quotechar      = '"',
                quoting        = csv.QUOTE_MINIMAL,
                escapechar     = '\\',
                skipinitialspace = True
            )
        self.dialect = Dialect(
                delimiter      = ';',
                doublequote    = True,
                lineterminator = '\r\n',
                quotechar      = '"',
                quoting        = csv.QUOTE_MINIMAL,
                escapechar     = '\\',
                skipinitialspace = True
            )

        self.header = "field1" + self.dialect.delimiter + "field2" 
        
    
    @given(st.text())
    def test_random_string(self, s):
        input = StringIO(self.header+self.dialect.lineterminator + s)
        peg_parser = PEGParserFactory(input,self.dialect_peg)
        peg_parser.read_header()
        peg_result = [l for l in peg_parser]
        input.seek(SEEK_SET)
        dict_parser = DictReader(input,dialect=self.dialect)
        dict_parser.read_header()
        dict_result = [l for l in dict_parser]
        self.assertEqual(peg_result,dict_result) 

