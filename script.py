import mcsv

from mcsv import (
    PEGParserFactory,
    CSVVisitor
)

#TODO where to put good to have dirty scripts.
f = open(file1, 'rb')
file = f.read().decode('latin-1', 'replace')

parser = PEGParserFactory.gen_parser()
parse_tree = parser.parse(file)
csv_content = visit_parse_tree(parse_tree, CSVVisitor()) #TODO visit_parse_tree is nowhere to be foind
for record in csv_content:
    print(record)