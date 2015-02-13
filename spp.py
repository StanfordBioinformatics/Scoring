#!/bin/env python

import sjm
import os

import chr_maps
import idr
import conf

BIN_DIR = conf.BIN_DIR
SPP_BINARY = conf.SPP_BINARY
QUEUE = conf.QUEUE
PROJECT = conf.SGE_PROJECT

NAME = 'spp'
USE_CONTROL_LOCK = True

from peakseq import archive_results

from peakseq import check_control_inputs

from macs import check_sample_inputs

from macs import prep_control

from peakseq import prep_sample

def form_control_files(name, control):
	cmds = []
	eland_merged = os.path.join(control.temp_dir, '%s_merged_eland.txt' % control.run_name)
	control.merged_file_location = os.path.join(control.results_dir, '%s_merged.tagAlign' % control.run_name)
	
	# Merge eland files
	cmd = os.path.join(BIN_DIR, 'merge_and_filter_reads.py')
	cmd += ' %s' % eland_merged
	for mr in control.mapped_read_files:
		cmd += ' %s' % mr
	cmds.append(cmd)
	
	# Convert to tagAlign
	cmd = os.path.join(BIN_DIR, 'eland2tagAlign.py')
	cmd += ' %s' % eland_merged
	cmd += ' %s' % control.merged_file_location
	cmd += ' %s' % control.genome
	cmds.append(cmd)
	
	j = sjm.Job(control.run_name, cmds, queue=QUEUE)
	control.add_jobs(name, [j,])

from peakseq import form_sample_files

from macs import form_sample_files_nodups

from macs import form_replicate_files

from peakseq import complete_control

from peakseq import archive_control

from peakseq import archive_sample

from peakseq import calc_pbc

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
		spp_cmd = SPP_BINARY
		spp_cmd += ' -rf' # overwrite existing plot files
		spp_cmd += ' -c=%s' % r.merged_ta # sample
		spp_cmd += ' -i=%s' % control_file # control
		spp_cmd += ' -npeak=300000' # number of peaks to call
		spp_cmd += ' -odir=%s' % r.results_dir(sample) # output directory
		spp_cmd += ' -savr'
		spp_cmd += ' -savp'
		spp_cmd += ' -x=-500:50' # exclude frag lengths within this range
		spp_cmd += ' -out=%s' % os.path.join(r.results_dir(sample), 'phantomPeakStatsRep%s.tab' % r.rep_name(sample))
		print "spp1"
		print spp_cmd	
		if 'filtchr' in options:
			for filtchr in options['filtchr']:
				spp_cmd += ' -filtchr=%s' % filtchr # ignore reads from filtchr chr
		jobs.append(sjm.Job('SPP_' + sample.run_name + '_' + r.rep_name(sample), [convert_cmd, spp_cmd,], queue=QUEUE, project=PROJECT, memory='8G'))
		r.spp_results = os.path.join(r.results_dir(sample), r.rep_name(sample) + '_VS_' + control.run_name + '_merged.regionPeak.gz')
		
		# Pseudoreplicate Runs
		r.merged_ta_pr1 = os.path.join(r.temp_dir(sample), '%s_PR1.tagAlign' % r.rep_name(sample))
		convert_cmd = os.path.join(BIN_DIR, 'eland2tagAlign.py')
		convert_cmd += ' %s' % r.pr1_merged
		convert_cmd += ' %s' % r.merged_ta_pr1
		convert_cmd += ' %s' % sample.genome
		spp_cmd = SPP_BINARY
		spp_cmd += ' -rf' # overwrite existing plot files
		spp_cmd += ' -c=%s' % r.merged_ta_pr1 # sample
		spp_cmd += ' -i=%s' % control_file # control
		spp_cmd += ' -npeak=300000' # number of peaks to call
		spp_cmd += ' -odir=%s' % r.pr1_results_dir # output directory
		spp_cmd += ' -savr'
		spp_cmd += ' -savp'
		spp_cmd += ' -x=-500:50' # exclude frag lengths within this range
		spp_cmd += ' -out=%s' % os.path.join(r.results_dir(sample), 'phantomPeakStatsRep%s.tab' % r.rep_name(sample) + '_PR1')
		print spp_cmd
		if 'filtchr' in options:
			for filtchr in options['filtchr']:
				spp_cmd += ' -filtchr=%s' % filtchr # ignore reads from filtchr chr
		jobs.append(sjm.Job('SPP_' + sample.run_name + '_' + r.rep_name(sample) + '_PR1', [convert_cmd, spp_cmd,], queue=QUEUE, project=PROJECT, memory='8G'))
		r.spp_results_pr1 = os.path.join(r.pr1_results_dir, r.rep_name(sample) + '_PR1_VS_' + control.run_name + '_merged.regionPeak.gz')
		
		r.merged_ta_pr2 = os.path.join(r.temp_dir(sample), '%s_PR2.tagAlign' % r.rep_name(sample))
		convert_cmd = os.path.join(BIN_DIR, 'eland2tagAlign.py')
		convert_cmd += ' %s' % r.pr2_merged
		convert_cmd += ' %s' % r.merged_ta_pr2
		convert_cmd += ' %s' % sample.genome
		spp_cmd = SPP_BINARY
		spp_cmd += ' -rf' # overwrite existing plot files
		spp_cmd += ' -c=%s' % r.merged_ta_pr2 # sample
		spp_cmd += ' -i=%s' % control_file # control
		spp_cmd += ' -npeak=300000' # number of peaks to call
		spp_cmd += ' -odir=%s' % r.pr2_results_dir # output directory
		spp_cmd += ' -savr'
		spp_cmd += ' -savp'
		spp_cmd += ' -x=-500:50' # exclude frag lengths within this range
		spp_cmd += ' -out=%s' % os.path.join(r.results_dir(sample), 'phantomPeakStats%s.tab' % r.rep_name(sample) + '_PR2')
		if 'filtchr' in options:
			for filtchr in options['filtchr']:
				spp_cmd += ' -filtchr=%s' % filtchr # ignore reads from filtchr chr
		jobs.append(sjm.Job('SPP_' + sample.run_name + '_' + r.rep_name(sample) + '_PR2', [convert_cmd, spp_cmd,], queue=QUEUE, project=PROJECT, memory='8G'))
		r.spp_results_pr2 = os.path.join(r.pr2_results_dir, r.rep_name(sample) + '_PR2_VS_' + control.run_name + '_merged.regionPeak.gz')
	sample.add_jobs(name, jobs)
	
def merge_results(name, sample):
	jobs = []
	for r in sample.replicates + [sample.combined_replicate,]:
		r.unfiltered_results = os.path.join(r.results_dir(sample), '%s_peaks.regionPeak' % r.rep_name(sample))
		r.unfiltered_results_pr1 = os.path.join(r.pr1_results_dir, '%s_PR1_peaks.regionPeak' % r.rep_name(sample))
		r.unfiltered_results_pr2 = os.path.join(r.pr2_results_dir, '%s_PR2_peaks.regionPeak' % r.rep_name(sample))
		unpack_cmds = ['zcat %s > %s' % (r.spp_results, r.unfiltered_results), 'zcat %s > %s' % (r.spp_results_pr1, r.unfiltered_results_pr1), 'zcat %s > %s' % (r.spp_results_pr2, r.unfiltered_results_pr2),]
		jobs.append(sjm.Job('merge_results_%s' % r.rep_name(sample), unpack_cmds, queue=QUEUE, project=PROJECT))
	sample.add_jobs(name, jobs)

def replicate_scoring(name, sample):
	j = sjm.Job('replicate_scoring', ['echo replicate_scoring',], host='localhost', queue=QUEUE, project=PROJECT)
	sample.add_jobs(name, [j,])
	
def form_idr_inputs(name, sample):
	os.makedirs(os.path.join(sample.results_dir, 'idr'))
	jobs = []
	for rep in sample.replicates + [sample.combined_replicate,]:
		rep.narrowPeak = rep.unfiltered_results
		rep.narrowPeak_pr1 = rep.unfiltered_results_pr1
		rep.narrowPeak_pr2 = rep.unfiltered_results_pr2
	sample.add_jobs(name, [sjm.Job('form_idr_inputs', ['echo form_idr_inputs',], queue=QUEUE, project=PROJECT, host='localhost'),])

from peakseq import mail_results

from macs import cleanup

def idr_analysis(name, sample):
	jobs = []
	for i, rep_a in enumerate(sample.replicates):
		for j in range(i+1, len(sample.replicates)):
			rep_b = sample.replicates[j]
			idr_name = '%s_VS_%s' % (rep_a.rep_name(sample), rep_b.rep_name(sample))
			cmd = idr.idr_analysis_cmd(rep_a.narrowPeak, rep_b.narrowPeak, os.path.join(sample.idr_dir, idr_name), 'signal.value', sample.genome)
			jobs.append(sjm.Job('idr_analysis_' + idr_name, [cmd,], queue=QUEUE, project=PROJECT))
			
		# Pseudoreplicates
		idr_name = '%s_PR1_VS_%s_PR2' % (rep_a.rep_name(sample), rep_a.rep_name(sample))
		cmd = idr.idr_analysis_cmd(rep_a.narrowPeak_pr1, rep_a.narrowPeak_pr2, os.path.join(sample.idr_dir, idr_name+'_PR'), 'signal.value', sample.genome)
		jobs.append(sjm.Job('idr_analysis_' + idr_name, [cmd,], queue=QUEUE, project=PROJECT))
		
	# Pooled Pseudoreplicates
	idr_name = '%s_PR1_VS_%s_PR2' % (sample.combined_replicate.rep_name(sample), sample.combined_replicate.rep_name(sample))
	cmd = idr.idr_analysis_cmd(sample.combined_replicate.narrowPeak_pr1, sample.combined_replicate.narrowPeak_pr2, os.path.join(sample.idr_dir, idr_name), 'signal.value', sample.genome)
	jobs.append(sjm.Job('idr_analysis_'+ idr_name, [cmd,], queue=QUEUE, project=PROJECT))
	
	sample.add_jobs(name, jobs)

def idr_filter(name, sample):
	cmd = os.path.join(BIN_DIR, 'idr_filter.py')
	cmd += ' %s' % sample.run_name
	cmd += ' %s' % sample.genome
	cmd += ' %i' % len(sample.replicates)
	cmd += ' %s' % sample.idr_dir
	cmd += ' %s' % os.path.join(os.path.join(sample.results_dir, 'All'), sample.combined_replicate.unfiltered_results)
	cmd += ' %s' % sample.results_dir
	cmd += ' 7' # sort column (signal.value)
	sample.add_jobs(name, [sjm.Job('idr_filter_' + sample.run_name, [cmd,], queue=QUEUE, project=PROJECT),])
		
