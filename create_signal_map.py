#!/bin/env python

import os
import sys
import re

from eland import ElandExtendedFile, ElandFile
from sgr import SGR

WINDOW = 200

def create_sgr(output_dir, eland_file_path, chr):
	eland = ElandFile(eland_file_path, 'r')
	output = open(os.path.join(output_dir, chr + ".sgr"), 'w')
	signals = {}
	for hit in eland:
		read_length = len(hit.sequence)
		if hit.strand == 'F':
			start = int(hit.coordinate)
			stop = int(hit.coordinate) + WINDOW
		elif hit.strand == 'R':
			start = max(int(hit.coordinate) + read_length - WINDOW, 1)
			stop = int(hit.coordinate) + read_length
		
		if start in signals:
			signals[start] += 1
		else:
			signals[start] = 1
		if stop in signals:
			signals[stop] += -1
		else:
			signals[stop] = -1
			
	sorted_keys = signals.keys()
	sorted_keys.sort()
	height = 0
	for coord in sorted_keys:
		height += signals[coord]
		s = SGR(chr, coord, height)
		output.write(str(s) + "\n")
	eland.close()
	output.close()
	
if __name__ == "__main__":
	if len(sys.argv) < 3:
		print "Usage:  create_signal_map.py output_dir input_dir"
		raise SystemExit(1)
	output_dir = sys.argv[1]
	if not os.path.isdir(output_dir):
		os.makedirs(output_dir)
	input_dir = sys.argv[2]
	
	eland_re = re.compile('(\w+)_eland\.txt')
	for file in os.listdir(input_dir):
		m = eland_re.match(file)
		if not m:
			continue
		print "Creating SGR for %s " % file
		create_sgr(output_dir, os.path.join(input_dir, file), m.group(1))