#!/bin/env python

import sjm
import os
import sys

import chr_maps
import idr
import conf

BIN_DIR = conf.BIN_DIR
SUBMISSION_BIN_DIR = conf.SUBMISSION_BIN_DIR
QUEUE = conf.QUEUE
PROJECT = conf.SGE_PROJECT
PEAKSEQ_BINARY = conf.PEAKSEQ_BINARY 
BIN_SIZE = conf.PEAKSEQ_BIN_SIZE

NAME = 'peakseq'
USE_CONTROL_LOCK = True

def archive_results(name, results_dir, archive_file,force=False):
 	if os.path.exists(archive_file):
		if not force:
	 		raise Exception("Archive file %s already exists" % archive_file)
	archive_cmd = '%s %s %s %s' % (os.path.join(BIN_DIR, 'archive_results.py'), results_dir, archive_file,force)
	return sjm.Job('Archive_%s' % name, archive_cmd, queue=QUEUE, project=PROJECT,sched_options="-m e")

def check_control_inputs(control,force):
	"""
	Function : Checks for existance of
						 1) genome, and 
						 2) mapped reads files.
						 Both must exist, or else an Exception is raised.
						 Checks whether control.archive_file exists. If as and the force argument is False, then an Exception is raised
						 because the archive will not be overwritten unless force is True.
	"""
	if control.genome not in chr_maps.genomes:
		raise Exception("Genome %s not found. Valid genomes: %s" % (control.genome, ' '.join(chr_maps.genomes.keys())))
	for mr in control.mapped_read_files:
		if not os.path.exists(mr):
			raise Exception("Cannot find mapped reads file %s" % mr)
	if os.path.exists(control.archive_file):
		if not force:
			raise Exception("Archive of control results already exists as %s" % control.archive_file)
		
def check_sample_inputs(sample,force):
	if os.path.exists(os.path.join(sample.results_dir, 'rep_stats')):
		if not force:
			raise Exception("Sample results non-empty.")
	if os.path.exists(sample.archive_file):
		if not force:
			raise Exception("Archive of sample results already exists as %s" % sample.archive_file)
	if not sample.genome in chr_maps.peakseq_mappability_file:
		raise Exception("PeakSeq mappability file not defined in chr_maps.py")
	if not os.path.exists(chr_maps.peakseq_mappability_file[sample.genome]):
		raise Exception("Cannot find sample mappability file %s" % chr_maps.peakseq_mappability_file[sample.genome])
	if sample.genome not in chr_maps.genomes:
		raise Exception("Genome %s not found. Valid genomes: " % (sample_conf.GENOME, ' '.join(chr_maps.genomes.keys())))
		
def prep_control(control):
	if not os.path.isdir(control.results_dir):
		os.makedirs(control.results_dir)
	if not os.path.isdir(control.temp_dir):
		os.makedirs(control.temp_dir)
	if not os.path.isdir(control.sgr_dir):
		os.makedirs(control.sgr_dir)
		
def prep_sample(sample):
	if not os.path.isdir(sample.results_dir):
		os.makedirs(sample.results_dir)
	if not os.path.isdir(sample.temp_dir):
		os.makedirs(sample.temp_dir)
		
def form_control_files(name, control):
	print " ******* form control files ****** "
	cmds = []
	control.merged_file_location = os.path.join(control.temp_dir, '%s_merged_eland.txt' % control.run_name)
        print " merged conrol files ", control.merged_file_location	
	# Merge eland files
	cmd = os.path.join(BIN_DIR, 'merge_and_filter_reads.py')

	cmd += ' %s' % control.merged_file_location

	print " merged conrol files ", cmd
	#sys.exit()
	for mr in control.mapped_read_files:
		cmd += ' %s' % mr
	cmds.append(cmd)
	
	# Divide merged file by chr
	cmd = os.path.join(BIN_DIR, 'divide_eland.py')
	cmd += " %s %s %s" % (control.merged_file_location, control.genome, control.results_dir)
	cmds.append(cmd)
	
	# Create Signal Map
	cmd = os.path.join(BIN_DIR, 'create_signal_map.py')
	cmd += ' %s %s' % (control.sgr_dir, control.results_dir)
	cmds.append(cmd)
	control.add_jobs(name, [sjm.Job(control.run_name, cmds, queue=QUEUE, project=PROJECT,sched_options="-m e"),])
	
def form_sample_files(name, sample):
	jobs = []
	print " peakseq: form sample files ***"
	for rep in sample.replicates:
		jobs.append(sjm.Job(rep.rep_name(sample) + '_merge', form_replicate_files(rep, sample), queue=QUEUE, project=PROJECT,sched_options="-m e"))
	
	jobs.append(sjm.Job(sample.run_name + '_All_merge', form_replicate_files(sample.combined_replicate, sample),modules=["samtools/1.2"], queue=QUEUE, project=PROJECT,sched_options="-m e"))
	sample.add_jobs(name, jobs)
				
def form_replicate_files(rep, sample):
	cmds = []
	# Make directories
	if not os.path.exists(rep.temp_dir(sample)):
		os.makedirs(rep.temp_dir(sample))
	if not os.path.exists(rep.results_dir(sample)):
		os.makedirs(rep.results_dir(sample))
	if not os.path.exists(rep.sgr_dir(sample)):
		os.makedirs(rep.sgr_dir(sample))

	#print "dirs 1: ", rep.temp_dir(sample), " 2: ", rep.results_dir(sample), " 3: ", rep.sgr_dir(sample)
	# Merge and filter
	rep.merged_file_location = os.path.join(rep.temp_dir(sample), rep.rep_name(sample) + '_merged_eland.txt')
	cmd = os.path.join(BIN_DIR, 'merge_and_filter_reads.py')
	cmd += ' %s' % rep.merged_file_location
	for f in rep.mapped_read_files:
		print "In peakseq.py, replicate mapped read file is: %s\n" % f
		cmd += ' %s' % f
		print "cmd:  ",cmd
	cmds.append(cmd)

	# Divide by chr
	cmd = os.path.join(BIN_DIR, 'divide_eland.py')
	cmd += ' %s %s %s' % (rep.merged_file_location, sample.genome, rep.temp_dir(sample))
	cmds.append(cmd)
	print "cmd div by chr ",cmd

	# Make Pseudoreplicates
	rep.pr1_name = rep.rep_name(sample) + '_PR1'
	rep.pr1_results_dir = os.path.join(sample.results_dir, rep.pr1_name)
	if not os.path.exists(rep.pr1_results_dir):
		os.makedirs(rep.pr1_results_dir)
	rep.pr1_sgr_dir = os.path.join(rep.pr1_results_dir, 'sgr')
	if not os.path.exists(rep.pr1_sgr_dir):
		os.makedirs(rep.pr1_sgr_dir)
	rep.pr1_merged = os.path.join(rep.temp_dir(sample), rep.pr1_name + '_merged_eland.txt')
	rep.pr2_name = rep.rep_name(sample) + '_PR2'
	rep.pr2_results_dir = os.path.join(sample.results_dir, rep.pr2_name)
	if not os.path.exists(rep.pr2_results_dir):
		os.makedirs(rep.pr2_results_dir)
	rep.pr2_sgr_dir = os.path.join(rep.pr2_results_dir, 'sgr')
	if not os.path.exists(rep.pr2_sgr_dir):
		os.makedirs(rep.pr2_sgr_dir)
	rep.pr2_merged = os.path.join(rep.temp_dir(sample), rep.pr2_name + '_merged_eland.txt')
	cmd = os.path.join(BIN_DIR, 'shuffle_mapped_reads.py')
	cmd += ' %s %s %s' % (rep.merged_file_location, rep.pr1_merged, rep.pr2_merged)
	cmds.append(cmd)

	cmd = os.path.join(BIN_DIR, 'divide_eland.py')
	cmd += ' %s %s %s' % (rep.pr1_merged, sample.genome, rep.temp_dir(sample))
	cmds.append(cmd)

	cmd = os.path.join(BIN_DIR, 'divide_eland.py')
	cmd += ' %s %s %s' % (rep.pr2_merged, sample.genome, rep.temp_dir(sample))
	cmds.append(cmd)

	return cmds
	
def complete_control(name, control):
	if USE_CONTROL_LOCK:
		cmd = 'python '
		cmd += os.path.join(BIN_DIR, 'complete_control_scoring.py')
		cmd += ' %s' % control.results_dir
		cmd += ' %s' % control.peakcaller
		print "complete control", cmd
		control.add_jobs(name, [sjm.Job('complete_control', [cmd,], queue=QUEUE, project=PROJECT, host='localhost',sched_options="-m e"),])
			
def archive_control(name, control,force):
	control.add_jobs(name, [archive_results(control.run_name, control.results_dir, control.archive_file,force=force),])
	
def archive_sample(name, sample, control,force):
	# Put archive file locations in stats file for SNAP
	f = open(os.path.join(sample.results_dir, 'rep_stats'), 'a')
	f.write('sample_tar_complete=%s\n' % sample.archive_file)
	f.write('control_tar_complete=%s\n' % control.archive_file)
	f.close()
	
	sample.add_jobs(name, [archive_results(sample.run_name, sample.results_dir, sample.archive_file,force=force),])
	
def calc_pbc(name, control, sample):
	pbc_stats_file = os.path.join(sample.results_dir, 'pbc_stats.txt')
	if os.path.exists(pbc_stats_file):
		os.remove(pbc_stats_file)
	cmds = []
	for r in sample.replicates:
		cmd = "python " + os.path.join(BIN_DIR, 'calc_pbc.py')
		cmd += ' %s' % r.merged_file_location
		cmd += ' %s' % pbc_stats_file
		cmd += ' %s' % r.rep_name(sample)
		
		cmds.append(cmd)
	sample.add_jobs(name, [sjm.Job('calc_pbc', cmds, queue=QUEUE, project=PROJECT, memory='10G',sched_options="-m e"),])
	
def run_peakcaller(name, control, sample, options=None):
	if not options:
		options = {}
	mappability_file = chr_maps.peakseq_mappability_file[sample.genome]
	for r in sample.replicates + [sample.combined_replicate,]:
		for chr in chr_maps.genomes[sample.genome]:
			# Regular Run
			chr = chr[:-3] # remove .fa
			input = os.path.join(r.temp_dir(sample), '%s_eland.txt' % chr)
			cmd = PEAKSEQ_BINARY + " %s %s %s %s %s %s" % (
				os.path.join(r.temp_dir(sample), '%s_eland.txt' % chr), #input
				os.path.join(control.results_dir, '%s_eland.txt' % chr), #control
				os.path.join(r.sgr_dir(sample), '%s.sgr' % chr),
				os.path.join(r.results_dir(sample), '%s_hits.bed' % chr),
				BIN_SIZE,
				mappability_file,)
			cmd = os.path.join(BIN_DIR, 'peakseq_wrapper.py') + ' ' + cmd
			sample.add_jobs(name, [sjm.Job(r.rep_name(sample) + '_%s' % chr, [cmd,], queue=QUEUE, project=PROJECT,sched_options="-m e"),])
			
			# Pseudoreplicate Runs
			input = os.path.join(r.temp_dir(sample), '%s_eland.txt' % chr)
			cmd = PEAKSEQ_BINARY + " %s %s %s %s %s %s" % (
				os.path.join(r.temp_dir(sample), '%s_eland.txt' % chr), #input
				os.path.join(control.results_dir, '%s_eland.txt' % chr), #control
				os.path.join(r.pr1_sgr_dir, '%s.sgr' % chr),
				os.path.join(r.pr1_results_dir, '%s_hits.bed' % chr),
				BIN_SIZE,
				mappability_file,)
			cmd = os.path.join(BIN_DIR, 'peakseq_wrapper.py') + ' ' + cmd
			sample.add_jobs(name, [sjm.Job(r.rep_name(sample) + '_PR1_%s' % chr, [cmd,], queue=QUEUE, project=PROJECT,sched_options="-m e"),])
			
			input = os.path.join(r.temp_dir(sample), '%s_eland.txt' % chr)
			cmd = PEAKSEQ_BINARY + " %s %s %s %s %s %s" % (
				os.path.join(r.temp_dir(sample), '%s_eland.txt' % chr), #input
				os.path.join(control.results_dir, '%s_eland.txt' % chr), #control
				os.path.join(r.pr2_sgr_dir, '%s.sgr' % chr),
				os.path.join(r.pr2_results_dir, '%s_hits.bed' % chr),
				BIN_SIZE,
				mappability_file,)
			cmd = os.path.join(BIN_DIR, 'peakseq_wrapper.py') + ' ' + cmd
			sample.add_jobs(name, [sjm.Job(r.rep_name(sample) + '_PR2_%s' % chr, [cmd,], queue=QUEUE, project=PROJECT,sched_options="-m e"),])
	
def merge_results(name, sample):
	for r in sample.replicates + [sample.combined_replicate,]:
		for q_val in sample.conf.Q_VALUE_THRESHOLDS + [0,]:
			if q_val:
				output = os.path.join(r.results_dir(sample), '%s_%f_hits_filtered.bed' % (r.rep_name(sample), q_val))
			else:
				output = os.path.join(r.results_dir(sample), '%s_hits_filtered.bed' % r.rep_name(sample))
				r.unfiltered_results = output
			cmd = filter_hits_cmd(r.results_dir(sample), r.sgr_dir(sample), sample.genome, output, q_val)
			sample.add_jobs(name, [sjm.Job('merge_' + r.rep_name(sample) + '%g' % (q_val), [cmd,], queue=QUEUE, project=PROJECT,sched_options="-m e"),])
	
		# Merge Pseudoreplicate Hits
		output = os.path.join(r.results_dir(sample), '%s_hits.bed' % (r.rep_name(sample) + '_PR1'))
		r.unfiltered_results_pr1 = output
		cmd = filter_hits_cmd(r.pr1_results_dir, r.pr1_sgr_dir, sample.genome, output)
		sample.add_jobs(name, [sjm.Job('merge_' + r.rep_name(sample) + '_PR1', [cmd,], queue=QUEUE, project=PROJECT,sched_options="-m e"),])
		output = os.path.join(r.results_dir(sample), '%s_hits.bed' % (r.rep_name(sample) + '_PR2'))
		r.unfiltered_results_pr2 = output
		cmd = filter_hits_cmd(r.pr1_results_dir, r.pr1_sgr_dir, sample.genome, output)
		sample.add_jobs(name, [sjm.Job('merge_' + r.rep_name(sample) + '_PR2', [cmd,], queue=QUEUE, project=PROJECT,sched_options="-m e"),])
				
def filter_hits_cmd(results_dir, sgr_dir, genome, output, q_val=None):
	cmd = os.path.join(BIN_DIR, 'filter_hits.py')
	cmd += ' %s' % results_dir
	cmd += ' %s' % sgr_dir
	cmd += ' %s' % genome
	cmd += ' %s' % output
	if q_val:
		cmd += ' %f' % q_val
	return cmd

def replicate_scoring(name, sample):
	cmds = []
	# Mapped Read Statistics
	cmd = os.path.join(BIN_DIR, 'read_stats.py')
	cmd += ' %s' % os.path.join(sample.results_dir, 'rep_stats')
	cmd += ' ' + sample.conf.path
	cmds.append(cmd)
	
	# Replicate Overlap Statistics
	for q in sample.conf.Q_VALUE_THRESHOLDS:
		for r1 in sample.replicates:
			for r2 in sample.replicates:
				if r1 == r2:
					continue
				cmd = os.path.join(BIN_DIR, 'overlap_stats.py')
				cmd += ' ' + r1.narrowPeak
				cmd += ' ' + r2.narrowPeak
				cmd += ' ' + os.path.join(sample.results_dir, 'rep_stats')
				cmd += ' %f' % q
				cmd += ' %s_VS_%s_%f' % (r1.rep_name(sample), r2.rep_name(sample), q)
				cmds.append(cmd)
				
	j = sjm.Job('replicate_stats', cmds, queue=QUEUE, project=PROJECT,sched_options="-m e")
	sample.add_jobs(name, [j,])
	
def form_idr_inputs(name, sample):
	os.makedirs(os.path.join(sample.results_dir, 'idr'))
	jobs = []
	for rep in sample.replicates + [sample.combined_replicate,]:
		rep.narrowPeak = os.path.join(rep.results_dir(sample), rep.rep_name(sample) + '_unfiltered_narrowPeak.bed')
		cmd = os.path.join(SUBMISSION_BIN_DIR, 'normalhits2narrowPeak')
		cmd += ' %s > %s' % (rep.unfiltered_results, rep.narrowPeak)
		jobs.append(sjm.Job(rep.rep_name(sample) + '_hits2narrowPeak', [cmd,], queue=QUEUE, project=PROJECT,sched_options="-m e"))
		
		# Pseudoreplicates
		rep.narrowPeak_pr1 = os.path.join(rep.results_dir(sample), rep.rep_name(sample) + '_PR1_unfiltered_narrowPeak.bed')
		cmd = os.path.join(SUBMISSION_BIN_DIR, 'normalhits2narrowPeak')
		cmd += ' %s > %s' % (rep.unfiltered_results_pr1, rep.narrowPeak_pr1)
		jobs.append(sjm.Job(rep.rep_name(sample) + '_PR1_hits2narrowPeak', [cmd,], queue=QUEUE, project=PROJECT,sched_options="-m e"))
		
		rep.narrowPeak_pr2 = os.path.join(rep.results_dir(sample), rep.rep_name(sample) + '_PR2_unfiltered_narrowPeak.bed')
		cmd = os.path.join(SUBMISSION_BIN_DIR, 'normalhits2narrowPeak')
		cmd += ' %s > %s' % (rep.unfiltered_results_pr2, rep.narrowPeak_pr2)
		jobs.append(sjm.Job(rep.rep_name(sample) + '_PR2_hits2narrowPeak', [cmd,], queue=QUEUE, project=PROJECT,sched_options="-m e"))
	
	sample.add_jobs(name, jobs)

def mail_results(sample, control, run_name, emails):
	cmds = []
	cmd = os.path.join(BIN_DIR, 'build_report_text.py')
	cmd += ' %s' % sample.run_name
	cmd += ' %s' % sample.archive_file_download
	cmd += ' %s' % control.archive_file_download
	cmd += ' %s' % os.path.join(sample.results_dir, 'rep_stats')
	cmd += ' %s' % os.path.join(sample.results_dir, 'spp_stats.txt')
	cmd += ' %s' % os.path.join(sample.results_dir, 'idr_results.txt')
	cmd += ' %s' % os.path.join(sample.results_dir, 'pbc_stats.txt')
	cmd += ' %s' % os.path.join(sample.results_dir, 'full_report.txt')
	
	cmds.append(cmd)
	
	cmd = os.path.join(BIN_DIR, 'mail_wrapper.py')
	cmd += ' "%s Scoring Results"' % sample.run_name
	cmd += ' %s' % os.path.join(sample.results_dir, 'full_report.txt')
	for email in emails:
		cmd += ' %s' % email
	cmds.append(cmd)
	
	return sjm.Job('mail_results', cmds, queue=QUEUE, project=PROJECT, host='localhost',sched_options="-m e",dependencies=sample.all_jobs() + control.all_jobs())
	
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
	if control and control.jobs:
		if os.path.exists(control.merged_file_location):
			cmds.append('rm %s' % control.merged_file_location)
	return sjm.Job('cleanup', cmds, queue=QUEUE, project=PROJECT,sched_options="-m e",dependencies=sample.all_jobs() + control.all_jobs())
		
def idr_analysis(name, sample):
	jobs = []
	for i, rep_a in enumerate(sample.replicates):
		for j in range(i+1, len(sample.replicates)):
			rep_b = sample.replicates[j]
			idr_name = '%s_VS_%s' % (rep_a.rep_name(sample), rep_b.rep_name(sample))
			cmd = idr.idr_analysis_cmd(rep_a.narrowPeak, rep_b.narrowPeak, os.path.join(sample.idr_dir, idr_name), 'q.value', sample.genome)
			jobs.append(sjm.Job('idr_analysis_' + idr_name, [cmd,], queue=QUEUE, project=PROJECT,sched_options="-m e"))
			
		# Pseudoreplicates
		idr_name = '%s_PR1_VS_%s_PR2' % (rep_a.rep_name(sample), rep_a.rep_name(sample))
		cmd = idr.idr_analysis_cmd(rep_a.narrowPeak_pr1, rep_a.narrowPeak_pr2, os.path.join(sample.idr_dir, idr_name+'_PR'), 'q.value', sample.genome)
		jobs.append(sjm.Job('idr_analysis_' + idr_name, [cmd,], queue=QUEUE, project=PROJECT,sched_options="-m e"))
		
	# Pooled Pseudoreplicates
	idr_name = '%s_PR1_VS_%s_PR2' % (sample.combined_replicate.rep_name(sample), sample.combined_replicate.rep_name(sample))
	cmd = idr.idr_analysis_cmd(sample.combined_replicate.narrowPeak_pr1, sample.combined_replicate.narrowPeak_pr2, os.path.join(sample.idr_dir, idr_name), 'q.value', sample.genome)
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
	cmd += ' 5' # sort column (p.value)
	sample.add_jobs(name, [sjm.Job('idr_filter_' + sample.run_name, [cmd,], queue=QUEUE, project=PROJECT,sched_options="-m e"),])
