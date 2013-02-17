#!/bin/env python

import sys

import chr_maps

def main(eland_file, ta_file, genome):
	if genome not in chr_maps.genomes:
		print "Genome %s not found.  Valid genomes are %s" % (genome, ','.join(chr_maps.genomes.keys()))
		raise Exception
	eland = open(eland_file, 'r')
	ta = open(ta_file, 'w')
	chr_map = chr_maps.genomes[genome]
	for line in eland:
		fields = line.rstrip('\n').split('\t')
		chr = chr_map[fields[6]]
		start = int(fields[7])
		stop = start + len(fields[1])
		seq = fields[1]
		if fields[2] == 'U0':
			score = 12500
		elif fields[2] == 'U1':
			score = 11453
		elif fields[2] == 'U2':
			score = 10406
		else:
			print "Cannot determine score for %s" % line
		if fields[8] == 'R':
			strand = '-'
		elif fields[8] == 'F':
			strand = '+'
		else:
			print "Cannot determine strand for %s" % line
			
		ta_fields = [chr, str(start), str(stop), seq, str(score), strand,]
		ta.write('\t'.join(ta_fields) + '\n')
		
if __name__ == '__main__':
	if not len(sys.argv) == 4:
		print "Usage:  eland2tagAlign.py [eland file] [output file] [genome]"
		raise SystemExit(1)
	main(sys.argv[1], sys.argv[2], sys.argv[3])