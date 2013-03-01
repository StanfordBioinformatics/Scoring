#!/usr/bin/python

import sys
import os.path
import subprocess
from chr_maps import IDR_THRESHOLDS

def replicate_pairs(num_reps):
	rep_pairs = []
	for i in range(1, num_reps+1):
		for j in range(i+1, num_reps+1):
			rep_pairs.append((i, j))
	return rep_pairs
	
def num_hits(idr_hit_list, idr_threshold):
	f = open(idr_hit_list, 'r')
	num_hits = 0
	for line in f:
		fields = line.split()
		try:
			idr_value = float(fields[9])
		except:
			continue
		if idr_value <= idr_threshold:
			num_hits += 1
	f.close()
	return num_hits
	
def hit_cmd(unfiltered_pooled_hits, num_hits, output_file):
	sorted_hits = unfiltered_pooled_hits + '.sorted'
	if not os.path.exists(sorted_hits):
		subprocess.call('sort -k5nr,5nr %s > %s' % (unfiltered_pooled_hits, sorted_hits), shell=True)
	subprocess.call('head -n %i %s > %s' % (num_hits, sorted_hits, output_file), shell=True)

def main(sample_name, genome, num_reps, idr_dir, unfiltered_pooled_hits, output_dir):
	idr_results = open(os.path.join(output_dir, 'idr_results.txt'), 'w')
	
	if num_reps > 1:
		# Number of hits for individual replicates
		rep_hits = []
		for rep_a, rep_b in replicate_pairs(num_reps):
			idr_file = os.path.join(idr_dir, 'Rep%i_VS_Rep%i-overlapped-peaks.txt' % (rep_a, rep_b))
			h = num_hits(idr_file, IDR_THRESHOLDS[genome][0])
			rep_hits.append(h)
			idr_results.write('Rep%i_VS_Rep%i=%i\n' % (rep_a, rep_b, h))
		
	# Number of self-consistency hits
	for i in range(1, num_reps+1):
		idr_file = os.path.join(idr_dir, 'Rep%i_PR1_VS_Rep%i_PR2_PR-overlapped-peaks.txt' % (i, i))
		h = num_hits(idr_file, IDR_THRESHOLDS[genome][1])
		idr_results.write('Rep%i_PR1_VS_PR2=%i\n' % (i, h))
		
	# Number of pooled replicate self-consistency hits
	idr_file = os.path.join(idr_dir, 'RepAll_PR1_VS_RepAll_PR2-overlapped-peaks.txt')
	num_peaks_pooled = num_hits(idr_file, IDR_THRESHOLDS[genome][2])
	idr_results.write('RepAll_PR1_VS_PR2=%i\n' %  num_peaks_pooled)

	# Create hit files
	if num_reps > 1:
		max_rep_hits = max(rep_hits)
	else:
		max_rep_hits = 0
	cons_file = os.path.join(output_dir, '%s_conservative_narrowPeak.bed' % sample_name)
	hit_cmd(unfiltered_pooled_hits, max_rep_hits, cons_file)
	opt_file = os.path.join(output_dir, '%s_optimal_narrowPeak.bed' % sample_name)
	hit_cmd(unfiltered_pooled_hits, max(num_peaks_pooled, max_rep_hits), opt_file)
	
	
	
	
if __name__=='__main__':
	if not len(sys.argv) == 7:
		print "Usage:  idr_filter.py <sample name> <genome> <number of replicates> <idr directory> <unfiltered pooled hits file> <output directory>"
		raise SystemExit(1)
	
	main(sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5], sys.argv[6])