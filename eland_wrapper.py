#!/bin/env python

'''Determines read length of FASTA file in order to call correct eland'''

import os
import sys
import subprocess

ELAND_BIN_DIR = '/share/apps/illumina/GAPipeline-1.4.0/bin/'

def read_length(filename):
	f = open(filename, 'r')
	for line in f:
		if line.startswith('>'):
			continue
		print line
		read_len = len(line.rstrip('\n'))
		f.close()
		if read_len > 32:
			return 32
		return read_len

if __name__ == '__main__':
	if not len(sys.argv) == 4:
		print "Usage:  eland_wrapper.py <reads_fasta> <genome_dir> <output_file>"
		raise SystemExit(1)
	
	reads_fn = sys.argv[1]
	genome_dir = sys.argv[2]
	output_fn = sys.argv[3]
	
	eland_bin = os.path.join(ELAND_BIN_DIR, 'eland_%i' % read_length(reads_fn))
	
	subprocess.call("%s %s %s %s --multi=10" % (eland_bin, reads_fn, genome_dir, output_fn), shell=True)
	