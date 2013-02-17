#!/usr/bin/python

import os
import sys
import CountMap

def count_chr_size(fa_file):
	size = 0
	f = open(fa_file)
	for l in f:
		if l.startswith('>'): continue
		l = l.strip()
		size += len(l)
	f.close()
	return size
	
def get_chr_sizes(fa_directory):
	size_map = {}
	for f in os.listdir(fa_directory):
		if f.endswith('.fa'):
			chr_name = f[:-3]
			size_map[chr_name] = count_chr_size(os.path.join(fa_directory, f))
	return size_map
	
def form_mappability_file(chr_sizes, counts_dir, output_file, window_size):
	output = open(output_file, 'w')
	for chr in sorted(chr_sizes):
		print chr
		count_map_file = os.path.join(counts_dir, str(chr) + 'b.out')
		if not os.path.exists(count_map_file):
			raise Exception("Cannot find count map file %s" % count_map_file)
		count_map = CountMap.CountMap(count_map_file)
		
		count = 0
		window = -1
		for pos in range(1, chr_sizes[chr] + 1):
			try:
				if count_map.cnt(pos) == 1:
					count += 1
			except ValueError:
				continue

			if pos % window_size == 0:
				window = int(pos / window_size) -1
				if count > 0:
					output.write('\t'.join([chr, str(window), str(count)]) + '\n')
				count = 0
	output.close()
	
if __name__ == '__main__':
	if len(sys.argv) < 4 or len(sys.argv) > 5:
		print "usage %s <counts_directory> <fasta_directory> <output_file> [<window_size>]" % sys.argv[0]
		raise SystemExit(1)
		
	counts_dir = sys.argv[1]
	fasta_dir = sys.argv[2]
	output_file = sys.argv[3]
	if len(sys.argv) == 5:
		window_size = int(sys.argv[4])
	else:
		window_size = 1000000
	chr_sizes = get_chr_sizes(fasta_dir)
	print chr_sizes
	form_mappability_file(chr_sizes, counts_dir, output_file, window_size)
