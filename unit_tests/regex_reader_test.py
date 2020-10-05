# coding: utf-8

# Copyright (C) 2001,2002 Python Software Foundation
# csv package unit tests

from __future__ import unicode_literals
import sys
import io
import unittest

import mcsv
from mcsv.csv_reader import (
    RegexReader,
    Dialect
)



class RegexReaderTest(unittest.TestCase):
    def validate_hotelleer():
        dialect = Dialect(
            delimiter      = ';',
            doublequote    = True,
            lineterminator = '\r\n',
            quotechar      = '"',
            quoting        = csv.QUOTE_MINIMAL,
            escapechar     = '\\',
            skipinitialspace = True
        )

        file1 = 'data/hotelleerparis2.csv'

        self.assertEqual(False,True)


    def validate_afsender():
        dialect = Dialect(
            delimiter      = ',',
            doublequote    = True,
            lineterminator = ';',
            quotechar      = '"',
            quoting        = csv.QUOTE_MINIMAL,
            escapechar     = '\\',
            skipinitialspace = True)
        file1 = 'data/afsender2.csv'

        self.assertEqual(False,True)