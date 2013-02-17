#!/bin/env python

import random
import sys

def main(eland_file, output_file1, output_file2):
	eland = open(eland_file, 'r')
	out1 = open(output_file1, 'w')
	out2 = open(output_file2, 'w')
	threshold = 0.5
	for read in eland:
		if random.random() <= threshold:
			if not read:
				continue
			out1.write(read)
		else:
			if not read:
				continue
			out2.write(read)
	out1.close()
	out2.close()
	eland.close()
	
if __name__ == '__main__':
	if len(sys.argv) != 4:
		print "Usage: shuffle_mapped_reads.py <eland file> <output file1> <output file2>"
		raise SystemExit(1)
	main(sys.argv[1], sys.argv[2], sys.argv[3])