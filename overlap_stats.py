#!/bin/env python

import sys
import math

from bed import PeakSeqBEDParser, NarrowPeakBEDParser

def main(hits_file1, hits_file2, stats_file, q_value, percent_of_hits=.4, name=None):
	"""Calculates the percentage of hits which overlap.
	
	Args:
		hits_file1:  A file of BED annotations
		hits_file2:  A file of BED annotations
		stats_file:  A file which will be appended with the overlap stats
		q_value:  Float of the q-value to use as a cutoff.  Use -1.0 for no filtering.
		percent_of_hits:  A float of the top percentage of hits to compare
	"""	
	hf1 = open(hits_file1, 'r')
	hf2 = open(hits_file2, 'r')
	sf = open(stats_file, 'a')
	if not name:
		name = hits_file1 + '_VS_' + hits_file2
	
	
	hits1 = []
	if hits_file1.endswith('.regionPeak') or hits_file1.endswith('.narrowPeak') or hits_file1.endswith('.narrowPeak.bed') or hits_file1.endswith('.regionPeak.bed'):
		bed_parser = NarrowPeakBEDParser()
	else:
		bed_parser = PeakSeqBEDParser()
	for line in hf1:
		h = bed_parser.parse(line)
		if q_value != -1.0 and h.q_value < q_value:
			continue
		hits1.append(h)
	if hits_file2.endswith('.regionPeak') or hits_file2.endswith('.narrowPeak') or hits_file2.endswith('.narrowPeak.bed') or hits_file2.endswith('.regionPeak.bed'):
		bed_parser = NarrowPeakBEDParser()
	else:
		bed_parser = PeakSeqBEDParser()
	hits2 = []
	for line in hf2:
		h = bed_parser.parse(line)
		if q_value != -1.0 and h.q_value < q_value:
			continue
		hits2.append(h)
	
	if not hits1:
		print "Warning: %s has no hits" % hits_file1
	if not hits2:
		print "Warning: %s has no hits" % hits_file2
		
	sf.write('total_hits1=%s=%i\n' % (name, len(hits1)))
	sf.write('total_hits2=%s=%i\n' % (name, len(hits2)))
	
	total_checked = max(min(int(float(len(hits1) * percent_of_hits)), int(float(len(hits2)) * percent_of_hits)), 1)
	total_overlap = 0
	hits1.sort(key=lambda x: x.p_value)
	hits1.reverse()
	for h1 in  hits1[:total_checked]:
		for h2 in hits2:
			if overlaps(h1, h2):
				total_overlap += 1
				break
	print len(hits1), len(hits2), total_checked, total_overlap
	sf.write('rep_overlap=%s=%f\n' % (name, float(total_overlap) / float(total_checked)))
	
def overlaps(hit1, hit2):
	if not hit1.chr == hit2.chr:
		return False
	elif hit1.stop < hit2.start:
		return False
	elif hit1.start > hit2.stop:
		return False
	else:
		return True
		
if __name__ == '__main__':
	if len(sys.argv) < 5 or len(sys.argv) > 7:
		print "Usage:  overlap_stats.py <BED file> <BED file> <stats file>  <q_value_cutoff (use -1 for no cutoff)> [<name>] [<percent_top_overlap>=.4]"
		raise SystemExit(1)
		
	hits_file1 = sys.argv[1]
	hits_file2 = sys.argv[2]
	stats_file = sys.argv[3]
	q_value = -math.log(float(sys.argv[4]))  # Using -log10 scale
	if len(sys.argv) >= 6:
		name = sys.argv[5]
	else:
		name = None
	if len(sys.argv) == 7:
		percent_overlap = float(sys.argv[6])
	else:
		percent_overlap = .4
		
	main(hits_file1, hits_file2, stats_file, q_value, percent_overlap, name)
