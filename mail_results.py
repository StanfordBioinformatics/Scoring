#!/bin/env python

import os
import sys
import subprocess
import getopt
import conf

CYGNUS_BASE = conf.DOWNLOAD_BASE

BASE_TEXT = '''Scoring completed.  

Full results available at:
'''

if __name__ == '__main__':
	addresses = []
	results = []
	results_dir = None
	output_fn = None
	name = ''
	options, files = getopt.gnu_getopt(sys.argv[1:], 'n:m:f:o:r:', ['name', 'mail', 'file', 'output', 'resultsdir'])
	for opt, arg in options:
		if opt in ('-m', '--mail'):
			addresses.append(arg)
		elif opt in ('-f', '--file'):
			results.append(arg)
		elif opt in ('-o', '--output'):
			output_fn = arg
		elif opt in ('-n', '--name'):
			name = arg
		elif opt in ('-r', '--resultsdir'):
			results_dir = arg
	if not output_fn:
		raise Exception("Must supply output name")
	output = open(output_fn, 'w')
	output.write(BASE_TEXT)
	for r in results:
		output.write(CYGNUS_BASE + r + '\n')
		
	for fn in files:
		output.write('\n*** %s ***\n' % fn)
		input = open(fn)
		for line in input:
			output.write(line)
		input.close()
	
	if results_dir is not None:
		output.write('\n*** IDR Consistency Results ***\n')
		input = open(os.path.join(results_dir, 'idr_results.txt'))
		for line in input:
			(rep, num_hits) = line.rstrip('\n').split('=')
			if rep.endswith('_All_PR1_VS_PR2'):
				rep = rep[:-15] + ' Pooled'
			elif rep.endswith('PR1_VS_PR2'):
				rep = rep[:-11] + ' Self Consistency'
			output.write('%s,  %s hits\n' % (rep, num_hits))
		input.close()
			
		output.write('\n*** Cross Correlation Analysis ***\n')
		input = open(os.path.join(results_dir, 'spp_stats.txt'))
		for line in input:
			fields = line.rstrip('\n').split('\t')
			output.write('Replicate %s\n' % fields[0])
			output.write('    Number of Uniquely Mapped Reads: %s\n' % fields[1])
			output.write('    Estimated Fragment Length:  %s\n' % fields[2])
			output.write('    Cross-Correlation Value(s):  %s\n' % fields[3])
			output.write('    Phantom Peak:  %s\n' % fields[4])
			output.write('    Phantom Peak Correlation:  %s\n' % fields[5])
			output.write('    Lowest Strand Shift:  %s\n' % fields[6])
			output.write('    Minimum Cross-Correlation:  %s\n' % fields[7])
			output.write('    Normalized Strand Cross-Correlation Coefficient (NSC):  %s\n' % fields[8])
			output.write('    Relative Strand Cross-Correlation Coefficient (RSC):  %s\n' % fields[9])
			output.write('    Quality Tag (-2 very low, -1 low, 0 medium, 1 high,  2 very high):  %s\n\n' % fields[10])
	
	output.close()
	cmd = 'mailx -s "%s Scoring Results" ' % name
	cmd += ' '.join(addresses)
	cmd += ' < %s' % output_fn
	
	subprocess.call(cmd, shell=True)
