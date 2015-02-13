#!/bin/env python

'''Simple PeakSeq wrapper, simply returns if the input file isn't found, instead
of failing.'''

import sys
import os
import subprocess

if __name__ == '__main__':
	if len(sys.argv) < 8:
		print "Usage:  peakseq_wrapper.py <PeakSeq_binary> <sample_input_file> <control_input_file> <output_sgr_file> <output_hits_file> <bin_size> <mappability_file>"
		raise SystemExit(1)
		
	if not os.path.exists(sys.argv[2]):
		print "Cannot find sample eland file %s, skipping scoring."  % sys.argv[2]
		raise SystemExit(1)
		
	subprocess.call(' '.join(sys.argv[1:]), shell=True)
