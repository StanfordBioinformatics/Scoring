#!/bin/env python

"""
compare_hits.py

Compares multiple hit lists against each other to determine whether they agree.
Frequently used for biological replicate scoring.

Usage:  compare_hits.py [-c combined_hits_file] -o <output_result_file> -q 
<q-value> -i <filtered_hits_file1> -i <filtered_hits_file2> 
[-i <filtered_hits_file3> ...]

Arguments:
	-c, --combined
	Calculates simple statistics on file containing the hits from the merged
	replicates
	
	-o, --output
	Output filename for the result statistics
	
	-q, --qvalue
	Q-value used as a cutoff for these hits
	
	-i, --input
	Filtered hit files (modified BED format) to compare against
	
"""

import getopt
import sys
import os
import glob
from bed import PeakSeqBEDParser

bed_parser = PeakSeqBEDParser()

TOP_OVERLAP_HITS = 0.4

class Replicate:
	
	def __init__(self, name, mapped_reads_file, results_dir, eland_files=None, hits_file=None):
		self.name = name
		self.mapped_reads_file = mapped_reads_file
		self.results_dir = results_dir
		self.hits = None
		self.hits_file = hits_file
		self.q_val = None
		self.num_reads = -1
		self.rep_vs_reps = []
		if not eland_files:
			self.eland_files = []
		else:
			self.eland_files = eland_files
		
	def num_of_reads(self):
		if not os.path.exists(self.mapped_reads_file):
			return 0
		if self.num_reads < 0:
			self.num_reads = sum(1 for line in open(self.mapped_reads_file))
		return self.num_reads
		
	def form_hits(self, hits_file, q_val):
		print self.results_dir, hits_file
		f = open(os.path.join(self.results_dir, hits_file))
		self.hits = [bed_parser.parse(line) for line in f]
		self.hits_file = hits_file
		self.q_val = q_val
		
	def output(self):
		output_str = '[%s]\n' % self.name
		if self.q_val:
			output_str += 'q_value=%f\n' % (self.q_val)
		output_str += 'mapped_reads=%i\n' % self.num_of_reads()
		output_str += 'eland_files=%s\n' % str(self.eland_files)
		output_str += 'total_hits=%i\n' % len(self.hits)
		if self.hits_file:
			output_str += 'filtered_bed=%s\n' % (os.path.join(self.results_dir, self.hits_file))
		for chr_bed_file in glob.glob(os.path.join(self.results_dir, '*_hits.bed')):
			output_str += 'chr_bed=%s\n' % (chr_bed_file)
		for chr_sgr_file in glob.glob(os.path.join(os.path.join(self.results_dir, 'sgr/'), '*.sgr')):
			output_str += 'chr_sgr=%s\n' % (chr_sgr_file)
		for r in self.rep_vs_reps:
			output_str += r.output()
		return output_str
		
class ReplicateByReplicate:
	
	def __init__(self, rep1, rep2, mapped_reads_ratio, hits_ratio, percent_overlap):
		self.rep1 = rep1
		self.rep2 = rep2
		self.mapped_reads_ratio = mapped_reads_ratio
		self.hits_ratio = hits_ratio
		self.percent_overlap = percent_overlap
		
	def output(self):
		output_str = '(%s, %s)\n' % (self.rep1.name, self.rep2.name)
		output_str += 'mapped_reads_ratio=%f\n' % self.mapped_reads_ratio
		output_str += 'hits_ratio=%f\n' % self.hits_ratio
		output_str += 'percent_overlap=%f\n' % self.percent_overlap
		return output_str
		
		
def ratio(x, y):
	if y == 0:
		return 0
	return float(x) / float(y)
	
def overlaps(hit1, hit2):
	if not hit1.chr == hit2.chr:
		return False
	elif hit1.stop < hit2.start:
		return False
	elif hit1.start > hit2.stop:
		return False
	else:
		return True
	
def calculate_overlap(hits1, hits2, percent_of_hits):
	"""Calculates the percentage of hits which overlap.
	
	Args:
		hits1:  A list of BED annotations
		hits2:  A list of BED annotations
		percent_of_hits:  A float of the top percentage of hits to compare
	Returns:
		The percentage of hits from hits1 which overlapped a hit from hits2
	"""
	min_len = min(len(hits1), len(hits2))  # Truncate hit lists to length of smaller list
	hits1_trunk = hits1[:min_len]
	hits2_trunk = hits2[:min_len]
	total_checked = int(min_len * percent_of_hits)
	total_overlap = 0
	for h1 in hits1_trunk[:total_checked]:
		for h2 in hits2_trunk:
			if overlaps(h1, h2):
				total_overlap += 1
				break
	return float(total_overlap) / float(total_checked)
				
def replicate_stats(rep1, rep2):
	mapped_reads_ratio = ratio(rep1.num_of_reads(), rep2.num_of_reads())
	hits_ratio = ratio(len(rep1.hits), len(rep2.hits))
	percent_overlap = calculate_overlap(rep1.hits, rep2.hits, TOP_OVERLAP_HITS)
	return ReplicateByReplicate(rep1, rep2, mapped_reads_ratio, hits_ratio, percent_overlap)
	
def common_thresholds(threshold_lists):
	common = threshold_lists[0]
	for tl in threshold_lists[1:]:
		for threshold in common:
			if threshold not in tl:
				common.remove(threshold)
	return common
		
def build_report(replicates, output_file):
	f = open(output_file, 'w')
	for r1 in replicates:
		for r2 in replicates:
			if r1 == r2:
				continue
			rbyr = replicate_stats(r1, r2)
			r1.rep_vs_reps.append(rbyr)
		f.write(r1.output())
	f.close()
	for r in replicates:
		r.rep_vs_reps = []


def main(output, qvalue, hit_files):
	replicates = [Replicate('%s' % h.split('/')[-1][:-4], '', '', hits_file=h) for h in hit_files]
	for r in replicates:
		r.form_hits(r.hits_file, qvalue)
	build_report(replicates, output)

if __name__ == '__main__':
	options, arguments = getopt.gnu_getopt(sys.argv[1:], 'o:q:i:', ['output', 'qvalue', 'input',])
	
	combined = None
	output = None
	qvalue = None
	hit_files = []
	for opt, arg in options:
		if opt in ('-o', '--output'):
			output = arg
		elif opt in ('-q', '--qvalue'):
			qvalue = float(arg)
		elif opt in ('-i', '--input'):
			hit_files.append(arg)
	
	if not output or not hit_files or qvalue is None:
		print "Usage:  compare_hits.py -o <output_result_file> -q <q-value> -i <filtered_hits_file1> -i <filtered_hits_file2> [-i <filtered_hits_file3> ...]"
		raise SystemExit(1)
		
	main(output, qvalue, hit_files)