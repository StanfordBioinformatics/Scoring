#!/bin/env python

import sjm
import os

import chr_maps
import idr
import conf

from spp import *

BIN_DIR = conf.BIN_DIR
SPP_NODUPS_BINARY = conf.SPP_BINARY_NO_DUPS
QUEUE = conf.QUEUE
PROJECT = conf.SGE_PROJECT

NAME = 'spp_nodups'
USE_CONTROL_LOCK = True

def run_peakcaller(name, control, sample, options=None):
	if not options:
		options = {}
	jobs = []
	control_file = os.path.join(control.results_dir, '%s_merged.tagAlign' % control.run_name)
	for r in sample.replicates + [sample.combined_replicate,]:
		# Regular Run
		r.merged_ta = os.path.join(r.temp_dir(sample), '%s.tagAlign' % r.rep_name(sample))
		convert_cmd = os.path.join(BIN_DIR, 'eland2tagAlign.py')
		convert_cmd += ' %s' % r.merged_file_location
		convert_cmd += ' %s' % r.merged_ta
		convert_cmd += ' %s' % sample.genome
		spp_cmd = SPP_NODUPS_BINARY
		spp_cmd += ' -rf' # overwrite existing plot files
		spp_cmd += ' -c=%s' % r.merged_ta # sample
		spp_cmd += ' -i=%s' % control_file # control
		spp_cmd += ' -npeak=300000' # number of peaks to call
		spp_cmd += ' -odir=%s' % r.results_dir(sample) # output directory
		spp_cmd += ' -savr'
		spp_cmd += ' -savp'
		spp_cmd += ' -x=-500:50' # exclude frag lengths within this range
		spp_cmd += ' -out=%s' % os.path.join(r.results_dir(sample), 'phantomPeakStatsReps.tab')
		if 'filtchr' in options:
			for filtchr in options['filtchr']:
				spp_cmd += ' -filtchr=%s' % filtchr # ignore reads from filtchr chr
		jobs.append(sjm.Job('SPP_' + sample.run_name + '_' + r.rep_name(sample), [convert_cmd, spp_cmd,], queue=QUEUE, project=PROJECT, memory='8G',sched_options="-m e"))
		r.spp_results = os.path.join(r.results_dir(sample), r.rep_name(sample) + '_VS_' + control.run_name + '_merged.regionPeak.gz')
		
		# Pseudoreplicate Runs
		r.merged_ta_pr1 = os.path.join(r.temp_dir(sample), '%s_PR1.tagAlign' % r.rep_name(sample))
		convert_cmd = os.path.join(BIN_DIR, 'eland2tagAlign.py')
		convert_cmd += ' %s' % r.pr1_merged
		convert_cmd += ' %s' % r.merged_ta_pr1
		convert_cmd += ' %s' % sample.genome
		spp_cmd = SPP_NODUPS_BINARY
		spp_cmd += ' -rf' # overwrite existing plot files
		spp_cmd += ' -c=%s' % r.merged_ta_pr1 # sample
		spp_cmd += ' -i=%s' % control_file # control
		spp_cmd += ' -npeak=300000' # number of peaks to call
		spp_cmd += ' -odir=%s' % r.pr1_results_dir # output directory
		spp_cmd += ' -savr'
		spp_cmd += ' -savp'
		spp_cmd += ' -x=-500:50' # exclude frag lengths within this range
		spp_cmd += ' -out=%s' % os.path.join(r.results_dir(sample), 'phantomPeakStatsReps.tab')
		if 'filtchr' in options:
			for filtchr in options['filtchr']:
				spp_cmd += ' -filtchr=%s' % filtchr # ignore reads from filtchr chr
		jobs.append(sjm.Job('SPP_' + sample.run_name + '_' + r.rep_name(sample) + '_PR1', [convert_cmd, spp_cmd,], queue=QUEUE, project=PROJECT, memory='8G',sched_options="-m e"))
		r.spp_results_pr1 = os.path.join(r.pr1_results_dir, r.rep_name(sample) + '_PR1_VS_' + control.run_name + '_merged.regionPeak.gz')
		
		r.merged_ta_pr2 = os.path.join(r.temp_dir(sample), '%s_PR2.tagAlign' % r.rep_name(sample))
		convert_cmd = os.path.join(BIN_DIR, 'eland2tagAlign.py')
		convert_cmd += ' %s' % r.pr2_merged
		convert_cmd += ' %s' % r.merged_ta_pr2
		convert_cmd += ' %s' % sample.genome
		spp_cmd = SPP_NODUPS_BINARY
		spp_cmd += ' -rf' # overwrite existing plot files
		spp_cmd += ' -c=%s' % r.merged_ta_pr2 # sample
		spp_cmd += ' -i=%s' % control_file # control
		spp_cmd += ' -npeak=300000' # number of peaks to call
		spp_cmd += ' -odir=%s' % r.pr2_results_dir # output directory
		spp_cmd += ' -savr'
		spp_cmd += ' -savp'
		spp_cmd += ' -x=-500:50' # exclude frag lengths within this range
		spp_cmd += ' -out=%s' % os.path.join(r.results_dir(sample), 'phantomPeakStatsReps.tab')
		if 'filtchr' in options:
			for filtchr in options['filtchr']:
				spp_cmd += ' -filtchr=%s' % filtchr # ignore reads from filtchr chr
		jobs.append(sjm.Job('SPP_' + sample.run_name + '_' + r.rep_name(sample) + '_PR2', [convert_cmd, spp_cmd,], queue=QUEUE, project=PROJECT, memory='8G',sched_options="-m e"))
		r.spp_results_pr2 = os.path.join(r.pr2_results_dir, r.rep_name(sample) + '_PR2_VS_' + control.run_name + '_merged.regionPeak.gz')
	sample.add_jobs(name, jobs)
