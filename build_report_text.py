#!/bin/env python

import sys

class RepStats:
	def __init__(self):
		self.rep_overlap = []
		self.total_hits = '0'

def main(run_name, sample_archive, control_archive, rep_stats_file, spp_stats_file, idr_stats_file, output_file):
	out = open(output_file, 'w')
	out.write('Scoring results for %s\n\n' % run_name)
	out.write('Full results available at:\n%s\n%s\n\n' % (control_archive, sample_archive))
	
	out.write('***Cross Correlation Analysis***\n')
	spp = open(spp_stats_file, 'r')
	for line in spp:
		fields = line.rstrip('\n').split('\t')
		out.write(fields[0][:-9] + '\n') # Rep name without .tagAlign
		out.write('\tNumber of Uniquely Mapped Reads: %s\n' % fields[1])
		out.write('\tEstimated Fragment Length: %s\n' % fields[2])
		out.write('\tCross-Correlation Value(s): %s\n' % fields[3])
		out.write('\tPhantom Peak: %s\n' % fields[4])
		out.write('\tPhantom Peak Correlation: %s\n' % fields[5])
		out.write('\tLowest Strand Shift: %s\n' % fields[6])
		out.write('\tMinimum Cross-Correlation: %s\n' % fields[7])
		out.write('\tNormalized Strand Cross-Correlation Coefficient (NSC): %s\n' % fields[8])
		out.write('\tRelative Strand Cross-Correlation Coefficient (RSC): %s\n' % fields[9])
		out.write('\tQuality Tag (-2 very low, -1 low, 0 medium, 1 high,  2 very high): %s\n\n' % fields[10])
	spp.close()
	
	out.write('*** IDR Consistency Results ***\n')
	idr = open(idr_stats_file)
	for line in idr:
		(rep, num_hits) = line.rstrip('\n').split('=')
		if rep.endswith('RepAll_PR1_VS_PR2'):
			rep = 'Pooled Self Consistency'
		elif rep.endswith('PR1_VS_PR2'):
			rep = rep[:-11] + ' Self Consistency'
		out.write('%s,  %s hits\n' % (rep, num_hits))
	idr.close()
	
	out.write('\n*** Replicate Statistics ***\n')
	rep_stats = open(rep_stats_file, 'r')
	rep_overlaps = {}
	for line in rep_stats:
		fields = line.rstrip('\n').split('=')
		if fields[0] == 'num_reads' and fields[2] != '0':
			out.write(fields[1] + ' Uniquely Mapped Reads: %s\n' % fields[2])
		if fields[0] == 'read_files' and fields[2] != '[]':
			out.write(fields[1] + ' Read Files: ')
			rfs = eval(fields[2])
			for rf in rfs:
				out.write(rf.split('/')[-1] + ' ')
			out.write('\n')
		
		if fields[0] == 'rep_overlap' or fields[0] == 'total_hits1' or fields[0] == 'total_hits2':
			rep = fields[1].split('_VS_')[0]
			q_value = fields[1].split('_')[-1]
			# Set up stats container
			if rep not in rep_overlaps:
				rep_overlaps[rep] = {q_value: RepStats()}
			elif q_value not in rep_overlaps[rep]:
				rep_overlaps[rep][q_value] = RepStats()
			# Put data in container
			if fields[0] == 'rep_overlap':
				rep_overlaps[rep][q_value].rep_overlap.append((fields[1], fields[2]))
			if fields[0] == 'total_hits1':
				rep_overlaps[rep][q_value].total_hits = fields[2]
	
	out.write('\n')
	for rep in sorted(rep_overlaps.keys()):
		out.write(rep + '\n')
		for q_value in sorted(rep_overlaps[rep].keys()):
			out.write('Q-Value: ' + q_value + '\n')
			out.write('\tTotal Hits: %s\n' % rep_overlaps[rep][q_value].total_hits)
			for ro in rep_overlaps[rep][q_value].rep_overlap:
				out.write('\t%s: %s\n' % (ro[0], ro[1]))
		out.write('\n')
				
	out.close()
	
	
	
if __name__ == '__main__':
	if not len(sys.argv) == 8:
		print "Usage: build_report_text.py <run_name> <sample_archive> <control_archive> <rep_stats_file> <spp_stats_file> <idr_stats_file> <output_file>"
		raise SystemExit(1)
		
	main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7])
	