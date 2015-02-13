#!/bin/env python

import sys
import os
import subprocess

def main(x_correlation_file, rep_name, macs_cmd):
	frag_length = get_frag_length(x_correlation_file, rep_name)
	macs_cmd = ' '.join(macs_cmd)
	if frag_length > 10:
		macs_cmd += ' --nomodel --shiftsize=%i' % (frag_length/2)
	ferr = open("macs_cmd_stderr.txt","w")
	try:
		subprocess.check_call(macs_cmd, shell=True,stderr=ferr)
	except subprocess.CalledProcessError as e:
		msg = "Error with return code {retcode} while running command {cmd}:".format(retcode=e.returncode,cmd=e.cmd)
		msg += open(ferr.name,'r').read()
		sys.stderr.write(msg)
		raise
	finally:
		os.remove(ferr.name)
		
	
def get_frag_length(x_correlation_file, rep_name):
	f = open(x_correlation_file, 'r')
	sum_frag_lengths = 0
	num_frag_lengths = 0
	for line in f:
		fields = line.rstrip('\n').split('\t')
		frag_length = int(fields[2].split(',')[0])
		if frag_length <= 0:
			frag_length = sum([int(x) for x in fields[2].split(',')]) / len(fields[2].split(','))
		if rep_name == fields[0]:
			return frag_length
		sum_frag_lengths += frag_length
		num_frag_lengths += 1
	return sum_frag_lengths / num_frag_lengths
	
if __name__ == '__main__':
	if len(sys.argv) < 3:
		print "Usage:  macs_wrapper.py <X Correlation File> <Replicate Name> <MACS command>"
		raise SystemExit(1)
	main(sys.argv[1], sys.argv[2], sys.argv[3:])
		
