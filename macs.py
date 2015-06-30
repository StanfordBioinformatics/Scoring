#!/bin/env python

import sjm
import os
import glob

import chr_maps
import idr
import conf


BIN_DIR = conf.BIN_DIR #/srv/gs1/projects/scg/Scoring/pipeline2
SUBMISSION_BIN_DIR = conf.SUBMISSION_BIN_DIR
MACS_BINARY = conf.MACS_BINARY
MACS_LIBRARY = conf.MACS_LIBRARY
QUEUE = conf.QUEUE
PROJECT = conf.SGE_PROJECT

NAME = 'macs'
USE_CONTROL_LOCK = True

from peakseq import archive_results
	
def check_control_inputs(control):
	if control.genome not in chr_maps.genomes:
		raise Exception("Genome %s not found.  Valid genomes: " % (control.genome, ' '.join(chr_maps.genomes.keys())))
	if control.genome not in chr_maps.macs_genome_size:
		raise Exception("Genome %s MACS size not found.  Valid genomes: " % (control.genome, ' '.join(chr_maps.macs_genome_size.keys())))
	for mr in control.mapped_read_files:
		if not os.path.exists(mr):
			raise Exception("Cannot find mapped reads file %s" % mr)
			
def check_sample_inputs(sample,force=False):
	repStatsFile = os.path.join(sample.results_dir, 'rep_stats')
	if os.path.exists(repStatsFile):
		if not force:
			errMsg = "Error: File " + repStatsFile + " exists. Sample results non-empty. Overwriting"
			raise Exception(errMsg)
 	#if os.path.exists(sample.archive_file):
 		#raise Exception("Archive of sample results already exists as %s" % sample.archive_file)
	if sample.genome not in chr_maps.genomes:
		raise Exception("Genome %s not found. Valid genomes: " % (sample.genome, ' '.join(chr_maps.genomes.keys())))
	if sample.genome not in chr_maps.macs_genome_size:
		raise Exception("Genome %s MACS size not found.  Valid genomes: " % (sample.genome, ' '.join(chr_maps.macs_genome_size.keys())))
		
def prep_control(control):
	if not os.path.isdir(control.temp_dir):
		os.makedirs(control.temp_dir)
	if not os.path.isdir(control.results_dir):
		os.makedirs(control.results_dir)
		
from peakseq import prep_sample
		
def form_control_files(name, control):
	cmds = []
	control.merged_file_location = os.path.join(control.results_dir, '%s_merged_eland.txt' % control.run_name)
	# Merge eland files
	cmd = os.path.join(BIN_DIR, 'merge_and_filter_reads.py')
	cmd += ' %s' % control.merged_file_location

	for mr in control.mapped_read_files:
		cmd += ' %s' % mr
		print "mr 1 " + cmd
	cmds.append(cmd)
	
	j = sjm.Job(control.run_name, cmds, modules=["samtools/1.2"], queue=QUEUE, project=PROJECT,sched_options="-m e") #QUEUE=seq_pipeline
	control.add_jobs(name, [j,])
		
from peakseq import form_sample_files

def form_sample_files_nodups(name, sample):
	jobs = []
	for rep in sample.replicates:
		jobs.append(sjm.Job(rep.rep_name(sample) + '_merge', form_replicate_files(rep, sample, rmdups=True),modules=["samtools/1.2"], queue=QUEUE, project=PROJECT, memory='16G',sched_options="-m e"))
	jobs.append(sjm.Job(sample.run_name + '_All_merge', form_replicate_files(sample.combined_replicate, sample, rmdups=True),modules=["samtools/1.2"], queue=QUEUE, project=PROJECT, memory='16G',sched_options="-m e"))
	sample.add_jobs(name, jobs)
	
def form_replicate_files(rep, sample, rmdups=False):
	cmds = []
	# Make directories
	if not os.path.exists(rep.temp_dir(sample)):
		os.makedirs(rep.temp_dir(sample))
	if not os.path.exists(rep.results_dir(sample)):
		os.makedirs(rep.results_dir(sample))
	# Merge and filter
	rep.merged_file_location = os.path.join(rep.temp_dir(sample), rep.rep_name(sample) + '_merged_eland.txt')
	cmd = os.path.join(BIN_DIR, 'merge_and_filter_reads.py')
	cmd += ' %s' % rep.merged_file_location
	for f in rep.mapped_read_files:
		cmd += ' %s' % f
	cmds.append(cmd)
	# Remove Duplicates
	if rmdups:
		orig_merged = rep.merged_file_location
		rep.merged_file_location = os.path.join(rep.temp_dir(sample), rep.rep_name(sample) + '_rmdup_merged_eland.txt')
		cmd = os.path.join(BIN_DIR, 'filter_dup_reads_eland.py')
		cmd += ' %s' % orig_merged
		cmd += ' %s' % rep.merged_file_location
		print "no_dups",cmd
		cmds.append(cmd)
	
	# Make Pseudoreplicates
	rep.pr1_name = rep.rep_name(sample) + '_PR1'
	rep.pr1_results_dir = os.path.join(sample.results_dir, rep.pr1_name)
	if not os.path.exists(rep.pr1_results_dir):
		os.makedirs(rep.pr1_results_dir)
	rep.pr1_merged = os.path.join(rep.temp_dir(sample), rep.pr1_name + '_merged_eland.txt')
	rep.pr2_name = rep.rep_name(sample) + '_PR2'
	rep.pr2_results_dir = os.path.join(sample.results_dir, rep.pr2_name)
	if not os.path.exists(rep.pr2_results_dir):
		os.makedirs(rep.pr2_results_dir)
	rep.pr2_merged = os.path.join(rep.temp_dir(sample), rep.pr2_name + '_merged_eland.txt')
	cmd = os.path.join(BIN_DIR, 'shuffle_mapped_reads.py')
	cmd += ' %s %s %s' % (rep.merged_file_location, rep.pr1_merged, rep.pr2_merged)
	cmds.append(cmd)
	return cmds
	

from peakseq import complete_control

from peakseq import archive_control

from peakseq import archive_sample

from peakseq import calc_pbc

def run_peakcaller(name, control, sample, options=None):
	if not options:
		options = {}
	jobs = []
	sppFile = os.path.join(sample.results_dir, 'spp_stats.txt')

	for r in sample.replicates + [sample.combined_replicate,]:
		# Regular Run
		cmds = ['cd %s' % r.results_dir(sample), 'export PYTHONPATH=%s:$PYTHONPATH' % MACS_LIBRARY,]
		macs_cmd = MACS_BINARY
		macs_cmd += ' -t %s' % r.merged_file_location # sample
		macs_cmd += ' -c %s' % control.merged_file_location # control
		macs_cmd += ' -n %s' % r.rep_name(sample) # name
		macs_cmd += ' -g %s' % chr_maps.macs_genome_size[sample.genome] # mappable genome size
		macs_cmd += ' -w' # create wiggle file
		macs_cmd += ' -p 1e-2' # Generous p-value cutoff for req for IDR
		macs_wrapper_cmd = os.path.join(BIN_DIR, 'macs_wrapper.py') 
		macs_wrapper_cmd += ' ' + sppFile
		macs_wrapper_cmd += ' ' + r.rep_name(sample) + '.tagAlign'
		macs_wrapper_cmd += ' ' + macs_cmd
		cmds.append(macs_wrapper_cmd)
		jobs.append(sjm.Job('MACS_' + r.rep_name(sample), cmds, queue=QUEUE, project=PROJECT, memory='16G',sched_options="-m e"))
		
		# Pseudoreplicate Runs
		cmds = ['cd %s' % r.pr1_results_dir, 'export PYTHONPATH=%s:$PYTHONPATH' % MACS_LIBRARY,]
		macs_cmd = MACS_BINARY
		macs_cmd += ' -t %s' % r.pr1_merged
		macs_cmd += ' -c %s' % control.merged_file_location
		macs_cmd += ' -n %s_PR1' % r.rep_name(sample)
		macs_cmd += ' -g %s' % chr_maps.macs_genome_size[sample.genome]
		macs_cmd += ' -w'
		macs_cmd += ' -p 1e-2' # Generous p-value cutoff for req for IDR
		macs_wrapper_cmd = os.path.join(BIN_DIR, 'macs_wrapper.py') 
		macs_wrapper_cmd += ' ' + os.path.join(sample.results_dir, 'spp_stats.txt')
		macs_wrapper_cmd += ' ' + r.rep_name(sample) + '.tagAlign'
		macs_wrapper_cmd += ' ' + macs_cmd
		cmds.append(macs_wrapper_cmd)
		jobs.append(sjm.Job('MACS_' + r.rep_name(sample) + '_PR1', cmds, queue=QUEUE, project=PROJECT, memory='16G',sched_options="-m e"))
		
		cmds = ['cd %s' % r.pr2_results_dir, 'export PYTHONPATH=%s:$PYTHONPATH' % MACS_LIBRARY,]
		macs_cmd = MACS_BINARY
		macs_cmd += ' -t %s' % r.pr2_merged
		macs_cmd += ' -c %s' % control.merged_file_location
		macs_cmd += ' -n %s_PR2' % r.rep_name(sample)
		macs_cmd += ' -g %s' % chr_maps.macs_genome_size[sample.genome]
		macs_cmd += ' -w'
		macs_cmd += ' -p 1e-2' # Generous p-value cutoff for req for IDR
		macs_wrapper_cmd = os.path.join(BIN_DIR, 'macs_wrapper.py') 
		macs_wrapper_cmd += ' ' + os.path.join(sample.results_dir, 'spp_stats.txt')
		macs_wrapper_cmd += ' ' + r.rep_name(sample) + '.tagAlign'
		macs_wrapper_cmd += ' ' + macs_cmd
		cmds.append(macs_wrapper_cmd)
		jobs.append(sjm.Job('MACS_' + r.rep_name(sample) + '_PR2', cmds, queue=QUEUE, project=PROJECT, memory='16G',sched_options="-m e"))
	sample.add_jobs(name, jobs)
			
def merge_results(name, sample):
	for r in sample.replicates + [sample.combined_replicate,]:
		r.unfiltered_results = os.path.join(r.results_dir(sample), '%s_peaks.bed' % r.rep_name(sample))
		r.unfiltered_results_pr1 = os.path.join(r.pr1_results_dir, '%s_PR1_peaks.bed' % r.rep_name(sample))
		r.unfiltered_results_pr2 = os.path.join(r.pr2_results_dir, '%s_PR2_peaks.bed' % r.rep_name(sample))
	j = sjm.Job('merge_results', ['echo merge_results', ], queue=QUEUE, project=PROJECT, host='localhost',sched_options="-m e")
	sample.add_jobs(name, [j,])
			
from peakseq import replicate_scoring			

def form_idr_inputs(name, sample):
	idrDir = os.path.join(sample.results_dir, 'idr')
	if not os.path.exists(idrDir):
		os.makedirs(idrDir)
	jobs = []
	for rep in sample.replicates + [sample.combined_replicate,]:
		cmds = []
		rep.narrowPeak = os.path.join(rep.results_dir(sample), rep.rep_name(sample) + '.regionPeak')
		cmd = os.path.join(SUBMISSION_BIN_DIR, 'macs2npk.sh')
		cmd += ' %s %s' % (os.path.join(rep.results_dir(sample), rep.rep_name(sample) + '_peaks.xls'), rep.results_dir(sample))
		np_job = sjm.Job(rep.rep_name(sample) + '_hits2narrowPeak', cmd, queue=QUEUE, project=PROJECT,sched_options="-m e")
		jobs.append(np_job)
		cmd = 'head -n 300000 %s > %s.temp' % (rep.narrowPeak, rep.narrowPeak)
		cmds.append(cmd)
		cmd = 'mv %s.temp %s' % (rep.narrowPeak, rep.narrowPeak)
		cmds.append(cmd)
		jobs.append(sjm.Job(rep.rep_name(sample) + '_narrowPeak_filter', cmds, queue=QUEUE, project=PROJECT,sched_options="-m e",dependencies=[np_job,]))
		
		# Pseudoreplicates
		cmds = []
		rep.narrowPeak_pr1 = os.path.join(rep.results_dir(sample), rep.rep_name(sample) + '_PR1.regionPeak')
		cmd = os.path.join(SUBMISSION_BIN_DIR, 'macs2npk.sh')
		pr1_results_dir = os.path.join(sample.results_dir, rep.rep_name(sample) + '_PR1')
		cmd += ' %s %s' % (os.path.join(pr1_results_dir, rep.rep_name(sample) + '_PR1_peaks.xls'), rep.results_dir(sample))
		np_job = sjm.Job(rep.rep_name(sample) + '_PR1_hits2narrowPeak', cmd, queue=QUEUE, project=PROJECT,sched_options="-m e")
		jobs.append(np_job)
		cmd = 'head -n 300000 %s > %s.temp && mv %s.temp %s' % (rep.narrowPeak_pr1, rep.narrowPeak_pr1, rep.narrowPeak_pr1, rep.narrowPeak_pr1)
		cmds.append(cmd)
		jobs.append(sjm.Job(rep.rep_name(sample) + '_PR1_narrowPeak_filter', cmds, queue=QUEUE, project=PROJECT,sched_options="-m e",dependencies=[np_job,]))
		
		cmds = []
		rep.narrowPeak_pr2 = os.path.join(rep.results_dir(sample), rep.rep_name(sample) + '_PR2.regionPeak')
		cmd = os.path.join(SUBMISSION_BIN_DIR, 'macs2npk.sh')
		pr2_results_dir = os.path.join(sample.results_dir, rep.rep_name(sample) + '_PR2')
		cmd += ' %s %s' % (os.path.join(pr2_results_dir, rep.rep_name(sample) + '_PR2_peaks.xls'), rep.results_dir(sample))
		np_job = sjm.Job(rep.rep_name(sample) + '_PR2_hits2narrowPeak', cmd, queue=QUEUE, project=PROJECT,sched_options="-m e")
		jobs.append(np_job)
		cmd = 'head -n 300000 %s > %s.temp && mv %s.temp %s' % (rep.narrowPeak_pr2, rep.narrowPeak_pr2, rep.narrowPeak_pr2, rep.narrowPeak_pr2)
		cmds.append(cmd)
		jobs.append(sjm.Job(rep.rep_name(sample) + '_PR2_narrowPeak_filter', cmds, queue=QUEUE, project=PROJECT,sched_options="-m e",dependencies=[np_job,]))
	
	sample.add_jobs(name, jobs)
	
from peakseq import mail_results

def cleanup(sample, control):
	cmds = []
	if sample:
		temp_dirs = []
		for r in sample.replicates:
			temp_dirs.append(r.temp_dir(sample))
		if sample.combined_replicate.mapped_read_files:
			temp_dirs.append(sample.combined_replicate.temp_dir(sample))
		for td in temp_dirs:
			if td and os.path.exists(td):
				cmds.append('rm -rf %s' % td)
	return sjm.Job('cleanup', cmds, queue=QUEUE, project=PROJECT,sched_options="-m e", dependencies=sample.all_jobs() + control.all_jobs())
	
def idr_analysis(name, sample):
	jobs = []
	for i, rep_a in enumerate(sample.replicates):
		for j in range(i+1, len(sample.replicates)):
			rep_b = sample.replicates[j]
			idr_name = '%s_VS_%s' % (rep_a.rep_name(sample), rep_b.rep_name(sample))
			cmd = idr.idr_analysis_cmd(rep_a.narrowPeak, rep_b.narrowPeak, os.path.join(sample.idr_dir, idr_name), 'p.value', sample.genome)
			jobs.append(sjm.Job('idr_analysis_' + idr_name, [cmd,], queue=QUEUE, project=PROJECT,sched_options="-m e"))
			
		# Pseudoreplicates
		idr_name = '%s_PR1_VS_%s_PR2' % (rep_a.rep_name(sample), rep_a.rep_name(sample))
		cmd = idr.idr_analysis_cmd(rep_a.narrowPeak_pr1, rep_a.narrowPeak_pr2, os.path.join(sample.idr_dir, idr_name+'_PR'), 'p.value', sample.genome)
		jobs.append(sjm.Job('idr_analysis_' + idr_name, [cmd,], queue=QUEUE, project=PROJECT,sched_options="-m e"))
		
	# Pooled Pseudoreplicates
	idr_name = '%s_PR1_VS_%s_PR2' % (sample.combined_replicate.rep_name(sample), sample.combined_replicate.rep_name(sample))
	cmd = idr.idr_analysis_cmd(sample.combined_replicate.narrowPeak_pr1, sample.combined_replicate.narrowPeak_pr2, os.path.join(sample.idr_dir, idr_name), 'p.value', sample.genome)
	jobs.append(sjm.Job('idr_analysis_'+ idr_name, [cmd,], queue=QUEUE, project=PROJECT,sched_options="-m e"))
	
	sample.add_jobs(name, jobs)


def idr_filter(name, sample):
	cmd = os.path.join(BIN_DIR, 'idr_filter.py')
	cmd += ' %s' % sample.run_name
	cmd += ' %s' % sample.genome
	cmd += ' %i' % len(sample.replicates)
	cmd += ' %s' % sample.idr_dir
	cmd += ' %s' % os.path.join(os.path.join(sample.results_dir, 'All'), sample.combined_replicate.unfiltered_results)
	cmd += ' %s' % sample.results_dir
	cmd += ' 8' # sort column (p.value)
	sample.add_jobs(name, [sjm.Job('idr_filter_' + sample.run_name, [cmd,], queue=QUEUE, project=PROJECT,sched_options="-m e"),])
