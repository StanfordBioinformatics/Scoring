#!/bin/env python

import sys
import os
import glob

import chr_maps
from bed import PeakSeqBEDParser
from sgr_map import SGRMap


def filter_peakseq(input_directory, sgr_directory, genome, output_file, q_value_threshold=None):
	if genome not in chr_maps.genomes:
		raise Exception("Genome %s not found.  Valid genomes:  %s" % (genome, str(chr_maps.genomes.keys())))
	chr_map = chr_maps.genomes[genome]
	# Load SGRMap
	signal_map = SGRMap()
	hits = []
	hits_by_chr = {}
	parser = PeakSeqBEDParser()
	output = open(output_file, 'w')
	for fn in glob.glob(os.path.join(input_directory, '*_hits.bed')):
		f = open(fn, 'r')
		for line in f:
			hit = parser.parse(line)
			if hit.chr in hits_by_chr:
				hits_by_chr[hit.chr].append(hit)
			else:
				hits_by_chr[hit.chr] = [hit,]
		f.close()
	for chr in hits_by_chr:
		print "Determining localmaxes for %s" % chr
		sgr_file = os.path.join(sgr_directory, chr_map[chr + '.fa'] + '.sgr')
		if not os.path.exists(sgr_file):
			raise Exception("Cannot find sgr file %s" % sgr_file)
		for i, localmax in enumerate(signal_map.localmaxes(sgr_file, chr, hits_by_chr[chr])):
			hit = hits_by_chr[chr][i]
			hit.localmax = localmax.coordinate
			hits.append(hit)
		hits_by_chr[chr] = None
	hits.sort()  # sort on p_value
	total_hits = float(len(hits))
	print total_hits
	for i, hit in enumerate(hits):
		hit.q_value = (hit.p_value * total_hits) / float(i+1)  # BH correction
		if q_value_threshold:
			if hit.q_value <= q_value_threshold:
				output.write(str(hit) + '\n')
		else:
			output.write(str(hit) + '\n')
	output.close()
	
	
if __name__ == '__main__':
	if len(sys.argv) < 5:
		print "Usage:  filter_hits.py hits_directory sgr_directory genome output_file [q_value_threshold]"
		raise SystemExit(1)
	if len(sys.argv) == 6:
		q_value_threshold = float(sys.argv[5])
	else:
		q_value_threshold = None
		
	filter_peakseq(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], q_value_threshold)
	
	
