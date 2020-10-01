#from future.utils.surrogateescape import register_surrogateescape
#register_surrogateescape()

from csv import Dialect
import csv
import logging

import re

file1 = 'data/hotelleerparis2.csv'

class file1Dialect(csv.Dialect):
	delimiter      = ';'
	doublequote    = True
	lineterminator = '\r\n'
	quotechar      = '"'
	quoting        = csv.QUOTE_MINIMAL
	escapechar     = '\\'
	skipinitialspace = True

file2 = 'data/afsender2.csv'

class file2Dialect(csv.Dialect):
	delimiter      = ','
	doublequote    = True
	lineterminator = ';'
	quotechar      = '"'
	quoting        = csv.QUOTE_MINIMAL
	escapechar     = '\\'
	skipinitialspace = True

# with open(file1, newline='') as csvfile:
# 	spamreader = csv.reader(csvfile, delimiter=';')
# 	for row in spamreader:
# 		print(' | '.join(row))

_surrogates = re.compile(r"[\ufffd]")

def detect_decoding_errors_line(l, _s=_surrogates.finditer):
	"""Return decoding errors in a line of text

	Works with text lines decoded with the surrogateescape
	error handler.

	Returns a list of (pos, byte) tuples

	"""
	# DC80 - DCFF encode bad bytes 80-FF
	# return [(m.start(), bytes([ord(m.group()) - 0xDC00]))
	#         for m in _s(l)]
	return _surrogates.search(l)

class CSV:
	def __init__(self, file, dialect=None, encoding='latin-1'):
		self.lineNum = 0
		self.dialect = dialect
		self.encoding = encoding
		
		f = open(file, 'rb')
		file = f.read().decode(encoding, 'replace')

		#file = open(file, encoding=encoding).read()

		#TODO: doublequote, skipinitialspace, strict
		self.re = re.compile(r'''
			(?!$)((?:								# Start capturing here.
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

		# # + dialect.delimiter is a hack, since regex for splitting is annoying
		# self.csvIter = (x.group(1) + dialect.delimiter for x in re.finditer(self.re, f.read()))

		# skipSpace = '\s*' if dialect.skipinitialspace else ''
		# self.reSplit = re.compile(r'''
		# 	{skipSpace}((?:										# Start capturing here.
		# 	  [^{delimiter}{quotechar}]			# Either a series of non-delimiter non-quote characters.
		# 	  |										# OR
		# 	  {quotechar}(?:						# A double-quote followed by a string of characters...
		# 	    [^{quotechar}\{escapechar}]|\{escapechar}.	# That are either non-quotes or escaped...
		# 	  )*									# ...repeated any number of times.
		# 	  {quotechar}							# Followed by a closing double-quote.
		# 	)*)										# Done capturing.
		# 	(?:[{delimiter}])		# Followed by a delimiter or the end of a string.
		# 	'''.format(delimiter=dialect.delimiter, 
		# 		quotechar=dialect.quotechar, 
		# 		escapechar=dialect.escapechar, 
		# 		lineterminator=dialect.lineterminator,
		# 		skipSpace=skipSpace), re.VERBOSE)

	def __del__(self):
		logging.debug("Lines read {}".format(self.lineNum))

	def __iter__(self):
		self.header()
		return self

	def next(self):
		return self.__next__()

	def __next__(self):
		row = None
		while row == None:
			row = self.get_next_row()
# check lenght on rows
		return dict(zip(self.header(), row))

	def get_next_row(self, skip=False):
		row = next(self.csvIter).encode(self.encoding)
		print(row.__repr__())
		self.lineNum += 1

		if not skip:
			# Check bad decoding
#			res = detect_decoding_errors_line(row)
#			if res != None:
#				logging.error("Encoding error detected at line {}".format(self.lineNum))
#				return None

			#Split cells
			row = list(csv.reader([row], dialect=self.dialect))[0]
			#row = self.reSplit.findall(row)

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

		#self.headerLine = self.reSplit.findall(row)
		self.headerLine = row

	def skip(self, skip_lines):
		for _ in range(skip_lines):
			row = self.get_next_row(verify=False, skip=True)

# def test():
# 	#csv = CSV(file1, dialect=file1Dialect, encoding='UTF8')
# 	csv = CSV(file2, dialect=file2Dialect, encoding='UTF8')
# 	csv.skip(0) # skip 4 lines
# 	csv.read_header() # read line into a header
# 	#print(csv.header()) #return read header
# 	for line in csv:
# 		print(str(csv.lineNum) + ": ", line)

# 		# if csv.lineNum == 1963:
# 		# 	break

# 		continue

# import timeit
# print(timeit.timeit("test()", setup="from __main__ import test", number=1))

if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description='CSV Reader')
	parser.add_argument('file', type=str, help='Path to CSV file')
	parser.add_argument('-e', type=str, help='encoding', default='latin-1')
	parser.add_argument('-d', type=str, help='delimiter', default=',')
	parser.add_argument('-q', type=str, help='quotechar', default='"')
	parser.add_argument('-t', type=str, help='lineterminator', default='\r\n')
	parser.add_argument('-dq', type=bool, help='doublequote ', default=True)
	parser.add_argument('-ss', type=bool, help='skipinitialspace ', default=False)
	parser.add_argument('-es', type=str, help='escapechar ', default='\\')


	args = parser.parse_args()

	class dialect(Dialect):
		delimiter = args.d
		quotechar = args.q
		doublequote = args.dq
		skipinitialspace = args.ss
		lineterminator = args.t
		escapechar = args.es
		quoting = csv.QUOTE_MINIMAL

	csvObj = CSV(args.file, dialect=dialect, encoding=args.e)
	csvObj.read_header()

	print("Header: " + str(csvObj.header()))
	for l in csvObj:
		print(l)
		if csvObj.lineNum == 560:
			break
		continue
	print("Lines reader: " + str(csvObj.lineNum))

