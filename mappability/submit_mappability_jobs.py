#!/usr/bin/python

import sys
import os

import sge
		

script_dir = '/srv/gs1/projects/scg/Scoring/pipeline/mappability'

def fa_bases(fa_dir):
	fas = []
	for f in os.listdir(fa_dir):
		if f.endswith('.fa'):
			fas.append(f[:-3])
	return fas
	

if __name__ == '__main__':
	if not len(sys.argv) == 3:
		print 'usage %s <fa directory> <kmer_len>' % sys.argv[0]  # Standard kmer_len is 30
		raise SystemExit(1)
	fa_dir = sys.argv[1]
	merlen = sys.argv[2]
	os.chdir(fa_dir)
	
	chrs = fa_bases(fa_dir)
	# Step 1:  Convert each fa file to hash
	cmd = os.path.join(script_dir, 'chr2hash') + ' %s.fa'
	chr2hash_jobs = [sge.Job('chr2_hash_%s' % chr, cmd % chr, queue='seq_pipeline', cwd=True) for chr in chrs]

		
	# Step 2:  Find counts for crossproduct of chromosomes
	cmd = os.path.join(script_dir, 'oligoFindPLFFile') + ' %s.fa %s.fa %s 0 0 1 1 > %sx%s.out'
	oligo_jobs = [sge.Job('oligoFindPLFFile_%sx%s' % (chrA, chrB), cmd % (chrA, chrB, merlen, chrA, chrB), queue='seq_pipeline', cwd=True) for chrA in chrs for chrB in chrs]
	for o in oligo_jobs:
		for j in chr2hash_jobs:
			o.addDependency(j)
			
	# Step 3:  Merge Counts
	cmd = os.path.join(script_dir, 'mergeOligoCounts') + ' %s > %sb.out'
	merge_jobs = []
	for chrA in chrs:
		merge_jobs.append(sge.Job('mergeOligoCounts_%s' % chrA, cmd % (' '.join(['%sx%s.out' % (chrB, chrA) for chrB in chrs]), chrA), queue='seq_pipeline', cwd=True))
	for m in merge_jobs:
		for j in oligo_jobs:
			pass
			#m.addDependency(m)
					
	#sge.build_submission(fa_dir, chr2hash_jobs + oligo_jobs)
	sge.build_submission(fa_dir, merge_jobs)
		
	