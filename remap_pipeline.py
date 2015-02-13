#!/bin/env python

import sys
import os
import gzip
import bz2

import sjm

TMP_DIR = '/srv/gs1/projects/scg/Scoring/tmp/remaps'

if __name__ == '__main__':
	if len(sys.argv) < 4:
		print "Usage:  remap_pipeline.py <fastqs_file> <genome_dir> <output_dir>"
		raise SystemExit(1)
		
	if not os.path.isdir(sys.argv[3]):
		os.makedirs(sys.argv[3])
	if not os.path.isdir(sys.argv[2]):
		raise Exception("Cannot find genome directory %s" % sys.argv[2])
	if not os.path.isdir(TMP_DIR):
		os.makedirs(TMP_DIR)
		
	jobs = []
	for fn in open(sys.argv[1]):
		cmds = []
		fn = fn.rstrip('\n')
		if 'fastq' in fn or 'sequence' in fn:
			flowcell_name = os.path.basename(fn).split('.fastq')[0]
			fasta_fn = os.path.join(TMP_DIR, flowcell_name + '.fa')
			if fn.endswith('.gz'):
				cmds.append('zcat %s | /srv/gs1/projects/scg/Scoring/fastx_toolkit/bin/fastq_to_fasta > %s' % (fn, fasta_fn))
			else:
				cmds.append('cat %s | /srv/gs1/projects/scg/Scoring/fastx_toolkit/bin/fastq_to_fasta > %s' % (fn, fasta_fn))
		elif 'eland_query' in fn:
			flowcell_name = os.path.basename(fn).split('_eland_query')[0]
			if fn.endswith('.gz'):
				fasta_fn = os.path.join(TMP_DIR, flowcell_name + '.fa')
				cmds.append('zcat %s > %s' % (fn, fasta_fn))
			else:
				fasta_fn = fn
		elif fn.endswith('export.txt'):
			flowcell_name = os.path.basename(fn).split('_export')[0]
			fastq_fn = os.path.join(TMP_DIR, flowcell_name + '.fastq')
			cmds.append('/home/pcayting/submission/export2fastq %s %s' % (fn, fastq_fn))
			fasta_fn = os.path.join(TMP_DIR, flowcell_name + '.fa')
			cmds.append('cat %s | /srv/gs1/projects/scg/Scoring/fastx_toolkit/bin/fastq_to_fasta  > %s' %(fastq_fn, fasta_fn))
		else:
			raise Exception("Can't figure out file type for %s" % fn)
			
		eland_bin = '/srv/gs1/projects/scg/Scoring/pipeline/eland_wrapper.py'
		cmds.append('%s %s %s %s' % (eland_bin, fasta_fn, sys.argv[2], os.path.join(sys.argv[3], flowcell_name + '_eland_multi.txt')))
		jobs.append(sjm.Job('eland_%s' % flowcell_name, cmds, queue='seq_pipeline', memory='16G'))
		
	submission = sjm.Submission(jobs, log_directory=os.getcwd(), notify=['pcayting',])
	submission.build('remap.jobs')
