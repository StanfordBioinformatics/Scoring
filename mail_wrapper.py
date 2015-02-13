#!/bin/env python

import sys
import subprocess

def main(subject, input, emails):
	cmd = 'mailx -s "%s" ' % subject
	cmd += ' '.join(emails)
	cmd += ' < %s' % input

	print cmd
	subprocess.check_call(cmd, shell=True)
	
if __name__ == '__main__':
	if not len(sys.argv) >= 4:
		print "Usage: mail_wrapper.py <subject> <input_file> <email> [<email> ...]"
		raise SystemExit(1)
	main(sys.argv[1], sys.argv[2], sys.argv[3:])
