#!/bin/env python

import math
import sys
import os
import glob

from conf import ConfigSample
from bed import PeakSeqBEDParser

bed_parser = PeakSeqBEDParser()

TOP_OVERLAP_HITS = 0.4

class Replicate:
	
	def __init__(self, name, mapped_reads_file, results_dir, eland_files=None):
		self.name = name
		self.mapped_reads_file = mapped_reads_file
		self.results_dir = results_dir
		self.hits = None
		self.hits_file = None
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
		f = open(os.path.join(self.results_dir, hits_file))
		self.hits = [bed_parser.parse(line) for line in f]
		if not self.hits:
			raise Exception("Hits file %s empty" % hits_file)
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
	total_checked = max(int(min_len * percent_of_hits), 1)
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
		
def build_report(combined, replicates, output_file):
	f = open(output_file, 'w')
	f.write(combined.output())
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
		
if __name__ == '__main__':
	if len(sys.argv) < 3:
		print "Usage:  replicate_scoring.py output_file sample_config_file [top_overlap_hits]"
		raise SystemExit(1)
	
	if len(sys.argv) == 4:
		TOP_OVERLAP_HITS = float(sys.argv[3])
	
	config = ConfigSample(sys.argv[2])
	replicates = [Replicate('Rep%i' % (i+1), os.path.join(config.TEMP_DIR, config.RUN_NAME + '_%i' % (i+1), '%s_merged_eland.txt' % (config.RUN_NAME + '_%i' % (i+1))), os.path.join(config.RESULTS_DIR, 'Rep%i' % (i+1)), eland_files=reads) for i, reads in enumerate(config.REPLICATES)]
	all_replicates = Replicate('RepAll', os.path.join(config.TEMP_DIR, config.RUN_NAME + '_All', '%s_merged_eland.txt' % (config.RUN_NAME + '_All')), os.path.join(config.RESULTS_DIR, 'RepAll'))
	
	for q_val in config.Q_VALUE_THRESHOLDS:
		for r in replicates + [all_replicates,]:
			r.form_hits('%s_%f_hits_filtered.bed' % (r.name, q_val), q_val)
		build_report(all_replicates, replicates, sys.argv[1] + '.%f' % q_val)
