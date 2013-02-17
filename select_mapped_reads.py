#!/bin/env python

import random
import sys
STRIDE_LENGTH = 1000000.0



def main(stride, output_file, eland_file, max_reads=None):
	fq = open(eland_file, 'r')
	total_reads = sum(1 for read in fq)
	print total_reads
	if not max_reads:
		max_reads = total_reads
	
	for i, num_reads in enumerate(range(stride, max_reads, stride)):
		print "Selecting %i reads" % num_reads
		output = open(output_file % (float(stride*(i+1)) / STRIDE_LENGTH), 'w')
		fq.seek(0)
		threshold = float(num_reads) / float(total_reads)
		count = 0
		for read in fq:
			if random.random() <= threshold:
				if not read:
					print count
				output.write(read)
				count += 1
		print "Selected %i reads" % count
		output.close()
	fq.close()
	
if __name__ == '__main__':
	if len(sys.argv) < 4 or len(sys.argv) > 5:
		print "Usage:  select_reads.py <stride in millions> <output file template> <eland multi file> [<max_reads>]"
		print "Example:  select_reads.py 2.5 output_%g.fastq input.fastq 50000000"
		raise SystemExit(1)
	if len(sys.argv) == 4:
		main(int(float(sys.argv[1])*STRIDE_LENGTH), sys.argv[2], sys.argv[3])
	else:
		main(int(float(sys.argv[1])*STRIDE_LENGTH), sys.argv[2], sys.argv[3], int(sys.argv[4]))
