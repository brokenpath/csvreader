

#TODO seems to be unused?

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



#TODO : diff console part, maybe smaller is better ..
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

	csvObj = RegexReader(args.file, dialect=dialect, encoding=args.e)
	csvObj.read_header()

	print("Header: " + str(csvObj.header()))
	for l in csvObj:
		print(l)
		# if csvObj.lineNum == 560:
		# 	break
		continue
	print("Lines reader: " + str(csvObj.lineNum))

