#!/bin/env python

import sjm
import os
import glob

import chr_maps
import idr
import conf


BIN_DIR = conf.BIN_DIR
SUBMISSION_BIN_DIR = conf.SUBMISSION_BIN_DIR
MACS_BINARY = conf.MACS2_BINARY
MACS_LIBRARY = conf.MACS2_LIBRARY
QUEUE = conf.QUEUE
PROJECT = conf.SGE_PROJECT

NAME = 'macs2'
USE_CONTROL_LOCK = False

from peakseq import archive_results

from macs import check_control_inputs		

from macs import check_sample_inputs

from macs import prep_control

from peakseq import prep_sample

from macs import form_control_files

from peakseq import form_sample_files

from macs import form_replicate_files

from peakseq import complete_control

from peakseq import archive_control

from peakseq import archive_sample

from peakseq import calc_pbc

def run_peakcaller(name, control, sample, options=None):
	if not options:
		options = {}
	jobs = []
	for r in sample.replicates + [sample.combined_replicate,]:
		# Regular Run
		cmds = ['cd %s' % r.results_dir(sample), 'export PYTHONPATH=%s:$PYTHONPATH' % MACS_LIBRARY,]
		macs_cmd = MACS_BINARY
		macs_cmd += ' callpeak'
		macs_cmd += ' -t %s' % r.merged_file_location # sample
		macs_cmd += ' -c %s' % control.merged_file_location # control
		macs_cmd += ' -f ELAND'
		macs_cmd += ' -n %s' % r.rep_name(sample) # name
		macs_cmd += ' -g %s' % chr_maps.macs_genome_size[sample.genome] # mappable genome size
		macs_cmd += ' -B' # create bedGraph file (wig not supported)
		macs_cmd += ' -p 0.1' # Generous p-value cutoff for req for IDR
		macs_cmd += ' --to-large'
		macs_wrapper_cmd = os.path.join(BIN_DIR, 'macs_wrapper.py') 
		macs_wrapper_cmd += ' ' + os.path.join(sample.results_dir, 'spp_stats.txt')
		macs_wrapper_cmd += ' ' + r.rep_name(sample) + '.tagAlign'
		macs_wrapper_cmd += ' ' + macs_cmd
		cmds.append(macs_wrapper_cmd)
		jobs.append(sjm.Job('MACS_' + r.rep_name(sample), cmds, queue=QUEUE, project=PROJECT, memory='16G'))
		
		# Pseudoreplicate Runs
		cmds = ['cd %s' % r.pr1_results_dir, 'export PYTHONPATH=%s:$PYTHONPATH' % MACS_LIBRARY,]
		macs_cmd = MACS_BINARY
		macs_cmd += ' callpeak'
		macs_cmd += ' -t %s' % r.pr1_merged
		macs_cmd += ' -c %s' % control.merged_file_location
		macs_cmd += ' -f ELAND'
		macs_cmd += ' -n %s_PR1' % r.rep_name(sample)
		macs_cmd += ' -g %s' % chr_maps.macs_genome_size[sample.genome]
		macs_cmd += ' -p 0.1' # Generous p-value cutoff for req for IDR
		macs_cmd += ' --to-large'
		macs_wrapper_cmd = os.path.join(BIN_DIR, 'macs_wrapper.py') 
		macs_wrapper_cmd += ' ' + os.path.join(sample.results_dir, 'spp_stats.txt')
		macs_wrapper_cmd += ' ' + r.rep_name(sample) + '.tagAlign'
		macs_wrapper_cmd += ' ' + macs_cmd
		cmds.append(macs_wrapper_cmd)
		jobs.append(sjm.Job('MACS_' + r.rep_name(sample) + '_PR1', cmds, queue=QUEUE, project=PROJECT, memory='16G'))
		
		cmds = ['cd %s' % r.pr2_results_dir, 'export PYTHONPATH=%s:$PYTHONPATH' % MACS_LIBRARY,]
		macs_cmd = MACS_BINARY
		macs_cmd += ' callpeak'
		macs_cmd += ' -t %s' % r.pr2_merged
		macs_cmd += ' -c %s' % control.merged_file_location
		macs_cmd += ' -f ELAND'
		macs_cmd += ' -n %s_PR2' % r.rep_name(sample)
		macs_cmd += ' -g %s' % chr_maps.macs_genome_size[sample.genome]
		macs_cmd += ' -p 1e-2' # Generous p-value cutoff for req for IDR
		macs_cmd += ' --to-large'
		macs_wrapper_cmd = os.path.join(BIN_DIR, 'macs_wrapper.py') 
		macs_wrapper_cmd += ' ' + os.path.join(sample.results_dir, 'spp_stats.txt')
		macs_wrapper_cmd += ' ' + r.rep_name(sample) + '.tagAlign'
		macs_wrapper_cmd += ' ' + macs_cmd
		cmds.append(macs_wrapper_cmd)
		jobs.append(sjm.Job('MACS_' + r.rep_name(sample) + '_PR2', cmds, queue=QUEUE, project=PROJECT, memory='16G'))
	sample.add_jobs(name, jobs)
			
def merge_results(name, sample):
	for r in sample.replicates + [sample.combined_replicate,]:
		r.unfiltered_results = os.path.join(r.results_dir(sample), '%s_peaks.encodePeak' % r.rep_name(sample))
		r.unfiltered_results_pr1 = os.path.join(r.pr1_results_dir, '%s_PR1_peaks.encodePeak' % r.rep_name(sample))
		r.unfiltered_results_pr2 = os.path.join(r.pr2_results_dir, '%s_PR2_peaks.encodePeak' % r.rep_name(sample))
	j = sjm.Job('merge_results', ['echo merge_results', ], queue=QUEUE, project=PROJECT, host='localhost')
	sample.add_jobs(name, [j,])
			
from peakseq import replicate_scoring			

def form_idr_inputs(name, sample):
	os.makedirs(os.path.join(sample.results_dir, 'idr'))
	jobs = []
	for rep in sample.replicates + [sample.combined_replicate,]:
		cmds = []
		rep.narrowPeak = rep.unfiltered_results + '.filtered'
		cmd = 'sort -k8nr %s | head -n 300000 > %s.temp && mv %s.temp %s' % (rep.unfiltered_results, rep.narrowPeak, rep.narrowPeak, rep.narrowPeak)
		cmds.append(cmd)
		jobs.append(sjm.Job(rep.rep_name(sample) + '_narrowPeak_filter', cmds, queue=QUEUE, project=PROJECT))
		
		# Pseudoreplicates
		cmds = []
		rep.narrowPeak_pr1 = rep.unfiltered_results_pr1 + '.filtered'
		cmd = 'sort -k8nr %s | head -n 300000 > %s.temp && mv %s.temp %s' % (rep.unfiltered_results_pr1, rep.narrowPeak_pr1, rep.narrowPeak_pr1, rep.narrowPeak_pr1)
		cmds.append(cmd)
		jobs.append(sjm.Job(rep.rep_name(sample) + '_PR1_narrowPeak_filter', cmds, queue=QUEUE, project=PROJECT))
		
		cmds = []
		rep.narrowPeak_pr2 = rep.unfiltered_results_pr2 + '.filtered'
		cmd = 'sort -k8nr %s | head -n 300000 > %s.temp && mv %s.temp %s' % (rep.unfiltered_results_pr2, rep.narrowPeak_pr2, rep.narrowPeak_pr2, rep.narrowPeak_pr2)
		cmds.append(cmd)
		jobs.append(sjm.Job(rep.rep_name(sample) + '_PR2_narrowPeak_filter', cmds, queue=QUEUE, project=PROJECT))
	
	sample.add_jobs(name, jobs)
	
from peakseq import mail_results

from macs import cleanup

from macs import idr_analysis	

from macs import idr_filter
