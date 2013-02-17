#!/bin/env python

'''Adjusts large peaks (>2000 bp) to be no greater than 2000 bp in length.
Used to fix MACS calling of large broad peaks which causes issues in IDR.

also Anshul's crazy adjustments.

'''

import sys
import subprocess


def main(narrowpeak_input, narrowpeak_output):
#	narrowpeak_input_sorted = narrowpeak_input + '.sorted'
#	subprocess.call('sort %s -k8nr,8nr -k7nr,7nr > %s' % (narrowpeak_input, narrowpeak_input_sorted), shell=True)
#	total_hits = int(subprocess.check_output('wc -l %s' % narrowpeak_input_sorted, shell=True).split(' ')[0])
#	np_in = open(narrowpeak_input_sorted, 'r')
	np_out = open(narrowpeak_output, 'w')
        np_in = open(narrowpeak_input, 'r')
	
	for i, line in enumerate(np_in):
		fields = line.rstrip('\n').split('\t')
		chromStart = int(fields[1])
		chromEnd = int(fields[2])
		peak = int(fields[9])
		if chromEnd - chromStart > 1000:
			peak_point = chromStart + peak
			chromStart = max(chromStart, peak_point - 500)
			chromEnd = min(chromEnd, peak_point + 500)
			peak = peak_point - chromStart
		fields[1] = str(chromStart)
		fields[2] = str(chromEnd)
		fields[9] = str(peak)
#		fields[6] = str(range(1, total_hits + 1)[-i-1])
		np_out.write('\t'.join(fields) + '\n')
		
	np_in.close()
	np_out.close()
	
if __name__ == '__main__':
	if not len(sys.argv) == 3:
		print "Usage:  adjustPeakLength.py <narrowPeak input> <narrowPeak output>"
		raise SystemExit(1)
	main(sys.argv[1], sys.argv[2])
	
