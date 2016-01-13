#!/bin/env python

import ConfigParser
import os

DEFAULT_GLOBALS = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'globals.conf')  #default globals is located in script directory

if os.path.exists('globals.conf'):
	globals_file = 'globals.conf'
	print "Using local globals.conf file"
else:
	globals_file = DEFAULT_GLOBALS
cp = ConfigParser.ConfigParser()
cp.read(globals_file)
BIN_DIR = cp.get('globals', 'BIN_DIR')
SUBMISSION_BIN_DIR = cp.get('globals', 'SUBMISSION_BIN_DIR')
SPP_BINARY = cp.get('globals', 'SPP_BINARY')
SPP_BINARY_NO_DUPS = cp.get('globals', 'SPP_BINARY_NO_DUPS')
MACS_BINARY = cp.get('globals', 'MACS_BINARY')
MACS_LIBRARY = cp.get('globals', 'MACS_LIBRARY')
MACS2_BINARY = cp.get('globals', 'MACS2_BINARY')
MACS2_LIBRARY = cp.get('globals', 'MACS2_LIBRARY')
PEAKSEQ_BINARY = cp.get('globals', 'PEAKSEQ_BINARY')
PEAKSEQ_BIN_SIZE = cp.getint('globals', 'PEAKSEQ_BIN_SIZE')
ARCHIVE_DIR = cp.get('globals', 'ARCHIVE_DIR')
DOWNLOAD_BASE = cp.get('globals', 'DOWNLOAD_BASE')
SJM_NOTIFY = eval(cp.get('globals', 'SJM_NOTIFY'))
print(SJM_NOTIFY)
QUEUE = cp.get('globals', 'QUEUE')
SGE_PROJECT = cp.get('globals', 'SGE_PROJECT')
MYSQL_PASSWORD_FILE = cp.get('globals', 'MYSQL_PASSWORD_FILE')
CONTROL_DB_HOST = cp.get('globals', 'CONTROL_DB_HOST')
CONTROL_DB_USER = cp.get('globals', 'CONTROL_DB_USER')
CONTROL_DB = cp.get('globals', 'CONTROL_DB')
CONTROL_DB_PORT = int(cp.get('globals', 'CONTROL_DB_PORT'))
GLOBAL_TMP_DIR = cp.get('globals', 'TMP_DIR')
SCHED_OPTIONS = cp.get('globals', 'SCHED_OPTIONS')

class ConfigSample:
	
	def __init__(self, config_file):
		if not os.path.isfile(config_file):
			raise Exception("Cannot find file %s" % config_file)
		cp = ConfigParser.ConfigParser()
		cp.read(config_file)
		self.path = os.path.abspath(config_file)
	
		self.RESULTS_DIR = cp.get('general', 'results_dir')
		self.TEMP_DIR = cp.get('general', 'temporary_dir')
		self.RUN_NAME = cp.get('general', 'run_name')
		self.Q_VALUE_THRESHOLDS = map(float, cp.get('general', 'q_value_thresholds').split(','))
		self.GENOME = cp.get('general', 'genome')
		self.REPLICATES = []
		replicate_sections = filter(lambda x: x.startswith('replicate'), cp.sections())
		replicate_sections.sort(key=lambda x: int(x[9:]))  # sort by replicate number e.g. replicate5
		for s in replicate_sections:
			self.REPLICATES.append(cp.get(s, 'mapped_reads').split(','))
		#print("Replicate BAM files are: " + str(self.REPLICATES) + "\n")
		
		
class ConfigControl:
	def __init__(self, config_file):
		if not os.path.isfile(config_file):
			raise Exception("Cannot find file %s" % config_file)
		cp = ConfigParser.ConfigParser()
		cp.read(config_file)
		self.path = os.path.abspath(config_file)
		
		self.CONTROL_MAPPED_READS = cp.get('peakseq', 'control_mapped_reads').split(',')
		self.RESULTS_DIR = cp.get('peakseq', 'results_dir')
		self.TEMP_DIR = cp.get('peakseq', 'temporary_dir')
		self.RUN_NAME = cp.get('peakseq', 'run_name')
		self.GENOME = cp.get('peakseq', 'genome')
