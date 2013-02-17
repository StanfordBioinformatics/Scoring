#!/bin/env python

"""
pipeline.py

Runs PeakSeq scoring pipeline for ChipSeq data.

Usage:  pipeline.py [-f] [-p] [-h] [-s] [-a] [-m <email address>] [-l <directory>] [-n <run_name>] [-c <peakcaller>] <control_config_file> [<sample_config_file>]

Arguments:
	-c, --peakcaller <peakcaller>
	specify the peakcaller to be used.  Current options are peakseq, macs, 
	macs2, spp. Defaults to macs2.
	
	-a, --no_archive
	does not archive the control and sample results.  
	
	-f, --force
	forces running of pipeline, even if results already exist
	
	-p, --print
	prints the job commands, but does not dispatch them to the cluster
	
	-d, --no_duplicates
	runs cross correlation analysis assuming duplicated reads have
	already been filtered out of the mapped reads.  Uncommon, so
	defaults to false.
	
	-h, --help
	displays this usage information and exits
	
	-l <directory>, --log <directory>
	log directory, current working directory if not specified
	
	-n <run_name>, --name <run_name>
	name for the pipeline run
	
	-m <email_address>, --mail <email_address>
	email address to send summary and result location
	
	-s, --snap
	make a call to the SNAP LIMS after completion
	
	--filtchr <chromosome>
	SPP option to ignore a chromosome during analysis.  Used to fix bug that 
	chrs with low read counts causes SPP to fail. 
	
	--rmdups
	Filter out all duplicate reads in sample read files before peakcalling.  Use
	when PCR amplification errors are present.  (i.e., PBC value is low)
	
	<control_config_file>
	(required) configuration file for the experiment's control
	
	<sample_config_file>
	configuration file for the sample replicates in the experiment.  Optional, 
	but in most cases this is specified.

"""

import getopt
import sys
import os

import sjm
import control_scoring
import idr
from conf import ConfigControl, ConfigSample
import conf


BIN_DIR = conf.BIN_DIR
ARCHIVE_DIR = conf.ARCHIVE_DIR
DOWNLOAD_BASE = conf.DOWNLOAD_BASE
SJM_NOTIFY = conf.SJM_NOTIFY
QUEUE = conf.QUEUE
PROJECT = conf.SGE_PROJECT
SNAP_RUN = False

class ScoringJobs:
	def add_jobs(self, jobs_name, jobs):
		if not jobs_name in self.jobs:
			self.jobs[jobs_name] = jobs
		else:
			self.jobs[jobs_name] += jobs
	
	def all_jobs(self):
		all_jobs = []
		for jn, js in self.jobs.iteritems():
			all_jobs += js
		return all_jobs
				

class Control(ScoringJobs):
	def __init__(self, run_name, results_dir, temp_dir, genome, mapped_read_files, conf, peakcaller):
		self.run_name = run_name
		self.results_dir = results_dir
		self.temp_dir = temp_dir
		self.genome = genome
		self.mapped_read_files = mapped_read_files
		self.conf = conf
		self.archive_file = os.path.join(ARCHIVE_DIR, run_name + peakcaller + '.tar.gz')
		self.archive_file_download = DOWNLOAD_BASE + run_name + peakcaller + '.tar.gz'
		self.sgr_dir = os.path.join(results_dir, 'sgr')
		self.jobs = {}
		self.peakcaller = peakcaller
		self.merged_file_location = os.path.join(self.results_dir, self.run_name + '_merged_eland.txt')
		
	def __str__(self):
		return self.run_name
		
class Sample(ScoringJobs):
	def __init__(self, run_name, results_dir, temp_dir, genome, replicates, conf):
		self.run_name = run_name
		self.results_dir = results_dir
		self.temp_dir = temp_dir
		self.genome = genome
		self.replicates = replicates
		self.conf = conf
		self.archive_file = os.path.join(ARCHIVE_DIR, run_name + '.tar.gz')
		self.archive_file_download = DOWNLOAD_BASE + run_name + '.tar.gz'
		self.idr_dir = os.path.join(results_dir, 'idr')
		self.spp_stats = os.path.join(results_dir, 'spp_stats.txt')
		self.jobs = {}
		self.combined_replicate = CombinedReplicate([])
		for r in self.replicates:
			self.combined_replicate.mapped_read_files += r.mapped_read_files
			
	def __str__(self):
		return self.run_name
		
class SampleReplicate:
	def __init__(self, rep_num, mapped_read_files):
		self.rep_num = rep_num
		self.mapped_read_files = mapped_read_files
		self.hit_files = {}
		
	def rep_name(self, sample):
		return 'Rep%i' % self.rep_num
		
	def results_dir(self, sample):
		return os.path.join(sample.results_dir, 'Rep%i' % self.rep_num)
		
	def sgr_dir(self, sample):
		return os.path.join(self.results_dir(sample), 'sgr')
		
	def temp_dir(self, sample):
		return os.path.join(sample.temp_dir, sample.run_name + '_' + self.rep_name(sample))
		
	def __str__(self):
		return "Rep%i" % self.rep_num
		
class CombinedReplicate(SampleReplicate):
	def __init__(self, mapped_read_files):
		self.mapped_read_files = mapped_read_files
		self.hit_files = {}
		
	def rep_name(self, sample):
		return 'RepAll'
		
	def results_dir(self, sample):
		return os.path.join(sample.results_dir, 'RepAll')
		
	def __str__(self):
		return "RepAll"

def add_dependencies(primary_jobs, dependent_jobs):
	for dj in dependent_jobs:
		for pj in primary_jobs:
			dj.add_dependency(pj)		
		
def main(peakcaller, run_name, control_conf, sample_conf=None, force=False, print_cmds=False, log_dir=None, no_duplicates=False, archive_results=True, emails=None, peakcaller_options=None, xcorrelation_options=None, remove_duplicates=False):
	control_conf = ConfigControl(control_conf)
	if sample_conf:
		sample_conf = ConfigSample(sample_conf)
	if not emails:
		emails = []
	if not log_dir:
		log_dir = os.getcwd()
	if not peakcaller_options:
		peakcaller_options = {}
	if not xcorrelation_options:
		xcorrelation_options = {}
		
	jobs = []	
	
	control = Control(control_conf.RUN_NAME, control_conf.RESULTS_DIR, control_conf.TEMP_DIR, control_conf.GENOME, control_conf.CONTROL_MAPPED_READS, control_conf, peakcaller.NAME)
	if not control_scoring.check_for_control(control_conf.RESULTS_DIR, control.peakcaller, peakcaller.USE_CONTROL_LOCK):
		try:
			peakcaller.check_control_inputs(control)
			peakcaller.form_control_files('form_control_files', control)
			peakcaller.complete_control('complete_control', control)
			add_dependencies(control.jobs['form_control_files'], control.jobs['complete_control'])
			if archive_results:
				peakcaller.archive_control('archive_control', control)
				add_dependencies(control.jobs['form_control_files'], control.jobs['archive_control'])
			jobs += control.all_jobs()
		except Exception, e:
			import traceback
 			print "error detected, removing control lock"
 			traceback.print_exc()
 			control_scoring.remove_lock(control.results_dir, control.peakcaller, peakcaller.USE_CONTROL_LOCK)
 			raise e
	else:
		print "Control %s already scored, skipping." % control.run_name
	
	sample = None
	if sample_conf:
		sample = Sample(sample_conf.RUN_NAME, sample_conf.RESULTS_DIR, sample_conf.TEMP_DIR, sample_conf.GENOME, [SampleReplicate(i+1, x) for i, x in enumerate(sample_conf.REPLICATES)], sample_conf)
		peakcaller.check_sample_inputs(sample)
		if remove_duplicates:
			peakcaller.form_sample_files_nodups('form_sample_files', sample)
		else:
			peakcaller.form_sample_files('form_sample_files', sample)
		peakcaller.calc_pbc('calc_pbc', control, sample)
		peakcaller.run_peakcaller('peakcaller', control, sample, peakcaller_options)
		add_dependencies(sample.jobs['form_sample_files'], sample.jobs['calc_pbc'])
		add_dependencies(sample.jobs['form_sample_files'], sample.jobs['peakcaller'])
		if control.jobs:
			add_dependencies(control.jobs['form_control_files'], sample.jobs['peakcaller'])
		peakcaller.merge_results('merge_results', sample)
		add_dependencies(sample.jobs['peakcaller'], sample.jobs['merge_results'])
		if archive_results:
			peakcaller.archive_sample('archive_sample', sample, control)
			add_dependencies(sample.jobs['merge_results'], sample.jobs['archive_sample'])
		
		
		# IDR Analysis
		peakcaller.form_idr_inputs('idr_format_inputs', sample)
		add_dependencies(sample.jobs['merge_results'], sample.jobs['idr_format_inputs'])
		if len(sample.replicates) > 1:
			peakcaller.replicate_scoring('replicate_scoring', sample)
			add_dependencies(sample.jobs['merge_results'], sample.jobs['replicate_scoring'])
			if archive_results:
				add_dependencies(sample.jobs['replicate_scoring'], sample.jobs['archive_sample'])
			add_dependencies(sample.jobs['idr_format_inputs'], sample.jobs['replicate_scoring'])
		peakcaller.idr_analysis('idr_analysis', sample)
		add_dependencies(sample.jobs['idr_format_inputs'], sample.jobs['idr_analysis'])
 		peakcaller.idr_filter('idr_filter', sample)
 		add_dependencies(sample.jobs['idr_analysis'], sample.jobs['idr_filter'])
 		if archive_results:
 			add_dependencies(sample.jobs['idr_filter'], sample.jobs['archive_sample'])
		
		# Cross-Correlation Analysis
		idr.cross_correlation_analysis('cross_correlation_analysis', sample, no_duplicates=no_duplicates, options=xcorrelation_options)
		add_dependencies(sample.jobs['form_sample_files'], sample.jobs['cross_correlation_analysis'])
		if archive_results:
			add_dependencies(sample.jobs['cross_correlation_analysis'], sample.jobs['archive_sample'])
		add_dependencies(sample.jobs['cross_correlation_analysis'], sample.jobs['peakcaller'])
			
		jobs += sample.all_jobs()

	if emails:
		jobs.append(peakcaller.mail_results(sample, control, run_name, emails))
	jobs.append(peakcaller.cleanup(sample, control))
	
	if SNAP_RUN and sample_conf:
		snap_job = sjm.Job("SNAP", "bash /srv/gs1/apps/snap_support/production/current/peakseq_report_parser_wrapper.sh production %s >& ~alwon/peakseq_report_out " % sample_conf.path,  queue=QUEUE, project=PROJECT, host='localhost', dependencies=sample.all_jobs())
		jobs.append(snap_job)
				
	if control.jobs:
		peakcaller.prep_control(control)
	if sample.jobs:
		peakcaller.prep_sample(sample)
	submission = sjm.Submission(jobs, log_directory=log_dir, notify=SJM_NOTIFY)
	if print_cmds:
		submission.build(run_name + '.jobs') 
		raise SystemExit(0)
	if log_dir:
		submission.run(os.path.join(log_dir, run_name + '.jobs'))
	else:
		submission.run(run_name + '.jobs')
	
	
if __name__ == '__main__':
	options, arguments = getopt.gnu_getopt(sys.argv[1:], 'fdaphl:n:m:c:', ['force', 'no_duplicates', 'no_archive', 'print', 'help', 'log', 'mail', 'peakcaller', 'snap', 'filtchr=', 'rmdups',])
	force = False
	print_cmds = False
	log_dir = None
	no_duplicates = False
	archive_results = True
	emails = []
	run_name = 'Pipeline'
	peakcaller = 'macs2'
	peakcaller_options = {}
	xcorrelation_options = {}
	remove_duplicates = False
	for opt, arg in options:
		if opt in ('-f', '--force'):
			force = True
		elif opt in ('-d', '--no_duplicates'):
			no_duplicates = True
		elif opt in ('-p', '--print'):
			print_cmds = True
		elif opt in ('-h', '--help'):
			print __doc__
			raise SystemExit(0)
		elif opt in ('-l', '--log'):
			log_dir = arg
		elif opt in ('-n', '--name'):
			run_name = arg
		elif opt in ('-m', '--mail'):
			emails.append(arg)
		elif opt in ('-c', '--peakcaller'):
			peakcaller = arg
		elif opt in ('-s', '--snap'):
			SNAP_RUN = True
		elif opt in ('-a', '--no_archive'):
			archive_results = False
		elif opt in ('--rmdups'):
			remove_duplicates = True
		elif opt in ('--filtchr'):
			if 'filtchr' in peakcaller_options:
				peakcaller_options['filtchr'].append(arg)
				xcorrelation_options['filtchr'].append(arg)
			else:
				peakcaller_options['filtchr'] = [arg,]
				xcorrelation_options['filtchr'] = [arg,]
	if len(arguments) < 1:
		print "Usage:  pipeline.py [-f] [-d] [-a] [-p] [-h] [-c <peakcaller>] [-l <directory>] [-n <run_name>] [-m <email_address>] <control_config_file> [<sample_config_file> ...]"
		raise SystemExit(1)	
	control_conf = arguments[0]
	if len(arguments) > 1:
		sample_conf = arguments[1]
	else:
		sample_conf = None
	if peakcaller == 'peakseq':
		import peakseq
		peakcaller_module = peakseq
	elif peakcaller == 'macs':
		import macs
		peakcaller_module = macs
	elif peakcaller == 'macs2':
		import macs2
		peakcaller_module = macs2
	elif peakcaller == 'spp':
		import spp
		peakcaller_module = spp
	elif peakcaller == 'spp_nodups':
		import spp_nodups
		peakcaller_module = spp_nodups
	else:
		print "Invalid Peakcaller selected.  Options are 'peakseq', 'macs', 'macs2',  'spp' or 'spp_nodups'"
		raise SystemExit(1)	
	
	main(peakcaller_module, run_name, control_conf, sample_conf=sample_conf, force=force, print_cmds=print_cmds, log_dir=log_dir, no_duplicates=no_duplicates, archive_results=archive_results, emails=emails, peakcaller_options=peakcaller_options, xcorrelation_options=xcorrelation_options, remove_duplicates=remove_duplicates)
