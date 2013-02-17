#!/bin/env python

import sys
import os

from eland import ElandFile
from chr_maps import get_chr_mapping

def divide_eland_by_chr(eland_file, genome, output_dir=""):
	chr_files = {}
	chr_map = get_chr_mapping(genome)
	i = ElandFile(eland_file, 'r')
	for line in i:
		if line.chr_name not in chr_map:
			#print "%s not a valid chromosome name, skipping." % line.chr_name
			continue
		o = open_chr_file(line.chr_name, chr_files, genome, chr_map, output_dir)
		o.write(line)
	i.close()
	for f in chr_files.values():
		f.close()
		
def open_chr_file(chr_name, chr_files, genome, chr_map, output_dir=""):
	if chr_name in chr_files:
		return chr_files[chr_name]
	else:
		f = ElandFile(
			os.path.join(output_dir, '%s_eland.txt' % (chr_map[chr_name])), 'w')
		chr_files[chr_name] = f
		return f
		
if __name__ == '__main__':
	if len(sys.argv) < 3:
		print "Usage:  divide_eland.py eland_file genome [output_dir]"
		raise SystemExit(1)
	output_dir = ""
	if len(sys.argv) == 4:
		output_dir = sys.argv[3]
		if not os.path.isdir(output_dir):
			os.makedirs(output_dir)
	divide_eland_by_chr(sys.argv[1], sys.argv[2], output_dir)
