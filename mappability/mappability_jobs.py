#!/usr/bin/python

import sjm
import sys
import os


SCRIPT_DIR = '/srv/gs1/projects/scg/Scoring/pipeline/mappability'

def fa_bases(fa_dir):
	fas = []
	for f in os.listdir(fa_dir):
		if f.endswith('.fa'):
			fas.append(f[:-3])
	return fas
	
if __name__ == '__main__':
	if len(sys.argv) < 3:
		print 'usage mappability_jobs.py <fa directory> <output_file> [<kmer_len>] [<window_size>]'
		raise SystemExit(0)
		
	fa_dir = sys.argv[1]
	output_file = sys.argv[2]
	if len(sys.argv) > 3:
		kmer_len = int(sys.argv[3])
	else:
		kmer_len = 30
	if len(sys.argv) > 4:
		window_size = int(sys.argv[4])
	else:
		window_size = 1000000
	
	chrs = fa_bases(fa_dir)
	jobs = []
	
	# Step 1:  Convert each fa file to hash
	chrhash_cmd = os.path.join(SCRIPT_DIR, 'chr2hash') + ' %s.fa'
	dir_cmd = 'cd %s' % fa_dir
	chr2hash_jobs = [sjm.Job('chr2_hash_%s' % chr, [dir_cmd, chrhash_cmd % chr], queue='seq_pipeline') for chr in chrs]
	
	# Step 2:  Find counts for crossproduct of chromosomes
	cross_cmd = os.path.join(SCRIPT_DIR, 'oligoFindPLFFile') + ' %s.fa %s.fa %i 0 0 1 1 > %sx%s.out'
	oligo_jobs = [sjm.Job('oligoFindPlFFILE_%sx%s' % (chrA, chrB), [dir_cmd, cross_cmd % (chrA, chrB, kmer_len, chrA, chrB)], queue='seq_pipeline') for chrA in chrs for chrB in chrs]
	for o in oligo_jobs:
		for j in chr2hash_jobs:
			o.add_dependency(j)
			
	# Step 3:  Merge Counts
	merge_cmd = os.path.join(SCRIPT_DIR, 'mergeOligoCounts') + ' %s > %sb.out'
	merge_jobs = []
	for chrA in chrs:
		merge_jobs.append(sjm.Job('mergeOligoCounts_%s' % chrA, [dir_cmd, merge_cmd % (
		' '.join(['%sx%s.out' % (chrB, chrA) for chrB in chrs]), chrA)], queue='seq_pipeline'))
	for m in merge_jobs:
		for j in oligo_jobs:
			m.add_dependency(j)
			
	# Step 4:  Form mappability file
	form_map_cmd = os.path.join(SCRIPT_DIR, 'form_mappability_file.py')
	form_map_cmd += ' %s %s %s %i' % (fa_dir, fa_dir, output_file, window_size)
	form_map_job = sjm.Job('form_mappability_file', form_map_cmd, queue='seq_pipeline', dependencies=merge_jobs, memory='20G')
	
	# Build Submission
	submission = sjm.Submission(chr2hash_jobs + oligo_jobs + merge_jobs + [form_map_job,], log_directory=os.getcwd(), notify=['pcayting',])
	submission.build('mappability.jobs')
