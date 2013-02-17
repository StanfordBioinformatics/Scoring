#!/bin/env python

import re
import sys

sys.path.append('/srv/gs1/projects/scg/Scoring/pipeline2/')

class ReplicateStats:
	def __init__(self, name):
		self.name = name
		self.attributes = {}
		self.rep_by_reps = []
		
	def add_attribute(self, attr_name, attr_value):
		if attr_name in self.attributes:
			raise Exception("%s already an attribute for %s" % (attr_name, self.name))
		self.attributes[attr_name] = attr_value
		
		
class ReplicateByReplicateStats(ReplicateStats):
	def __init__(self, rep1_name, rep2_name):
		self.rep1_name = rep1_name
		self.rep2_name = rep2_name
		self.attributes = {}
	

class ReplicateParser:
	def __init__(self):
		pass
	
	def parse(self, file):
		replicates = []
		last_rep = None
		current = None
		attr_name = ''
		attr_value = ''
		for line in file:
			line = line.rstrip('\n')
			m = re.match('\[([_\.\w-]+)\]$', line)
			if m:
				last_rep = ReplicateStats(m.group(1))
				current = last_rep
				replicates.append(current)
				continue
			m = re.match('\(([_\.\w-]+), ([_\.\w-]+)\)$', line)
			if m:
				r = ReplicateByReplicateStats(m.group(1), m.group(2))
				last_rep.rep_by_reps.append(r)
				current = r
				continue
			try:
				(attr_name, attr_value) = line.split('=')
			except:
				print line
				continue
			if attr_name not in ['mapped_reads', 'eland_files', 'total_hits', 'q_value', 'mapped_reads_ratio', 'hits_ratio', 'percent_overlap']:
				continue
			current.add_attribute(attr_name, attr_value)
		return replicates
		
def convert_to_text(replicates, output):
	for rep in replicates:
		output.write("Replicate %s\n" % rep.name)
		for attr_name in rep.attributes:
			output.write("\t%s = %s\n" % (attr_name, rep.attributes[attr_name]))
		for rr in rep.rep_by_reps:
			output.write("\t%s vs. %s\n" % (rr.rep1_name, rr.rep2_name))
			for attr_name in rr.attributes:
				output.write("\t\t%s = %s\n" % (attr_name, rr.attributes[attr_name]))
				
if __name__ == '__main__':
	if len(sys.argv) < 3:
		print "Usage:  convert_rep_scoring_to_text.py replicate_info output_file"
		raise SystemExit(1)
	input = open(sys.argv[1])
	output = open(sys.argv[2], 'w')
	rp = ReplicateParser()
	convert_to_text(rp.parse(input), output)
	input.close()
	output.close()
