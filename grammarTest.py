from __future__ import unicode_literals
from csv import Dialect
import csv

file1 = 'data/hotelleerparis2.csv'

class file1Dialect(csv.Dialect):
	delimiter      = ';'
	doublequote    = True
	lineterminator = '\r\n'
	quotechar      = '"'
	quoting        = csv.QUOTE_MINIMAL
	escapechar     = '\\'
	skipinitialspace = True

file1 = 'data/afsender2.csv'

class file1Dialect(csv.Dialect):
	delimiter      = ','
	doublequote    = True
	lineterminator = ';'
	quotechar      = '"'
	quoting        = csv.QUOTE_MINIMAL
	escapechar     = '\\'
	skipinitialspace = True




f = open(file1, 'rb')
file = f.read().decode('latin-1', 'replace')




from arpeggio import *
from arpeggio import RegExMatch as _

def record():                   return field, ZeroOrMore(file1Dialect.delimiter, field)
def field():                    return Optional([quoted_field, field_content])
def quoted_field():             return file1Dialect.quotechar, field_content_quoted, file1Dialect.quotechar
def field_content():            return _(r'([^{d}{t}])+'.format(d=file1Dialect.delimiter, t=file1Dialect.lineterminator))
def field_content_quoted():     return _(r'(({q}{q})|([^{q}]))+'.format(q=file1Dialect.quotechar))
def csvfile():                  return OneOrMore([record], file1Dialect.lineterminator), 


parser = ParserPython(csvfile, ws='\t ')
# parser = ParserPython(csvfile, ws='\t ', debug=True)



parse_tree = parser.parse(file)

class CSVVisitor(PTNodeVisitor):
    def visit_record(self, node, children):
        # record is a list of fields. The children nodes are fields so just
        # transform it to python list.
        return list(children)

    def visit_csvfile(self, node, children):
        # We are not interested in empty lines so we will filter them.
        return [x for x in children if x!='\n']

csv_content = visit_parse_tree(parse_tree, CSVVisitor())
for record in csv_content:
    print(record)