#!/bin/env python

import os
import sys
import subprocess

if __name__ == '__main__':
	if not len(sys.argv) >= 3:
		print "Usage:  archive_results.py <results_directory> <archive_file>"
		raise SystemExit(64)
	results_dir = sys.argv[1].rstrip('/')
	archive_file = sys.argv[2]
	force = False
	if len(sys.argv) >= 4:
		force = sys.argv[3]
	if os.path.exists(archive_file):
		if not force:
			raise Exception("%s already exists." % archive_file)

	os.chdir(os.path.join(results_dir, os.pardir))
	cmd = "tar czf %s %s" % (archive_file, os.path.basename(results_dir))
	subprocess.call(cmd, shell=True)
