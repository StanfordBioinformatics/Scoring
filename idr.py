#!/bin/env python

import os
import sjm
import conf
from chr_maps import IDR_BIN_DIR

BIN_DIR = conf.BIN_DIR
SUBMISSION_BIN_DIR = conf.SUBMISSION_BIN_DIR
QUEUE = conf.QUEUE
PROJECT = conf.SGE_PROJECT
R_BINARY = conf.R_BINARY
SPP_BINARY = conf.SPP_BINARY
SPP_BINARY_NO_DUPS = conf.SPP_BINARY_NO_DUPS
	
def idr_analysis_cmd(hit1, hit2, output, ranking_measure, genome):
	cmd = R_BINARY + ' '
	cmd += os.path.join(IDR_BIN_DIR[genome], 'batch-consistency-analysis.r')
	cmd += ' %s' % hit1
	cmd += ' %s' % hit2
	cmd += ' -1 %s' % output
	cmd += ' 0 F'
	cmd += ' %s' % ranking_measure
	return cmd
		
# def idr_filter(name, sample):
# 	cmd = '/srv/gs1/projects/scg/Scoring/dev_pipeline2/idr_filter_macs2.py'
# 	#cmd = os.path.join(BIN_DIR, 'idr_filter.py')
# 	cmd += ' %s' % sample.run_name
# 	cmd += ' %s' % sample.genome
# 	cmd += ' %i' % len(sample.replicates)
# 	cmd += ' %s' % sample.idr_dir
# 	cmd += ' %s' % os.path.join(os.path.join(sample.results_dir, 'All'), sample.combined_replicate.unfiltered_results)
# 	cmd += ' %s' % sample.results_dir
# 	sample.add_jobs(name, [sjm.Job('idr_filter_' + sample.run_name, [cmd,], queue=QUEUE, project=PROJECT),])
	
def cross_correlation_analysis(name, sample, no_duplicates=False, options=None):
	if not options:
		options = {}
	cmds = []
        ctr=1
        for rep in sample.replicates:
		#print rep.merged_file_location
                print rep
		# Convert merged and filtered eland file to tagAlign
		rep.tagAlign = os.path.join(rep.temp_dir(sample), '%s.tagAlign' % rep.rep_name(sample))
		cmd = os.path.join(SUBMISSION_BIN_DIR, 'convert2tagAlign.py')
		cmd += ' %s' %	 rep.merged_file_location
	        cmd += ' %s' % rep.tagAlign
		cmd += ' %s' % sample.genome
		cmds.append(cmd)
	        print 'SPP Cmd 1 ', cmd	
		# Run SPP
		if no_duplicates:
			cmd = SPP_BINARY_NO_DUPS
		else:
			cmd = SPP_BINARY
		cmd += ' -rf' # overwrite plot files if exists
		cmd += ' -c=%s' % rep.tagAlign
		cmd += ' -savp='
                cmd += sample.results_dir 
		cmd +='/rep' + str(ctr) + '.pdf' 
		print '/rep' + str(ctr) + '.pdf'
		cmd += ' -x=-50:40' # manually exclude fragment lengths [-50,40]
		cmd += ' -out=%s' % sample.spp_stats
		if 'filtchr' in options:
			for filtchr in options['filtchr']:
				cmd += ' -filtchr=%s' % filtchr # ignore reads from filtchr chr
		
		print 'SPP Cmd: ', cmd 
		ctr += 1
		cmds.append(cmd)
		
	sample.add_jobs(name, [sjm.Job('x_correlation_' + sample.run_name, cmds, queue=QUEUE, project=PROJECT, memory='8G',sched_options="-m e"),])
	
