#!/bin/env python

import sys
import os.path

from conf import ConfigSample

class Replicate:
	
	def __init__(self, name, mapped_reads_file, results_dir, read_files=None):
		self.name = name
		self.mapped_reads_file = mapped_reads_file
		self.results_dir = results_dir
		self.num_reads = -1
		if not read_files:
			self.read_files = []
		else:
			self.read_files = read_files
		
	def num_of_reads(self):
		if not os.path.exists(self.mapped_reads_file):
			print "Cannot find mapped reads file", self.mapped_reads_file
			return 0
		if self.num_reads < 0:
			self.num_reads = sum(1 for line in open(self.mapped_reads_file))
		return self.num_reads
		
		
def calc_stats(replicates, stats_file):
	for r in replicates:
		stats_file.write('num_reads=%s=%i\n' % (r.name, r.num_of_reads()))
		stats_file.write('read_files=%s=%s\n' % (r.name, str(r.read_files)))
		
def main(stats_file, sample_config_file):
	config = ConfigSample(sample_config_file)
	replicates = []
	for i, reads in enumerate(config.REPLICATES):
		rname = 'Rep'+str(i+1)
		replicates.append(Replicate(
			name=rname,
			mapped_reads_file=os.path.join(config.TEMP_DIR, config.RUN_NAME + '_' + rname, rname+'_merged_eland.txt'),
			results_dir=os.path.join(config.RESULTS_DIR, 'Rep'+str(i+1)),
			read_files=reads))
	allname = 'RepAll'
	all_replicates = Replicate(
		name=allname,
		mapped_reads_file=os.path.join(config.TEMP_DIR, config.RUN_NAME + '_' + allname, allname + '_merged_eland.txt'),
		results_dir=os.path.join(config.RESULTS_DIR, 'All'))
	replicates.append(all_replicates)

	if os.path.exists(stats_file):
		os.remove(stats_file)	

	sf = open(stats_file, 'a')
	calc_stats(replicates, sf)
	
if __name__ == '__main__':
	if len(sys.argv) != 3:
		print "Usage:  read_stats.py <stats_file> <sample_config_file>"
		raise SystemExit(1)
		
	main(sys.argv[1], sys.argv[2])
