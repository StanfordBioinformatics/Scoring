#!/bin/env python

import sys
import os
import subprocess
import time
import conf

from eland import ElandExtendedFile, ElandMultiFile, ElandFile, BwaSamFile, BowtieSamFile, ElandSamFile, IlluminaSamFile

TMP_DIR = conf.GLOBAL_TMP_DIR

def convert_bwasam(eland_output, sam_input, mismatches):
	'''Converts SAM file from BWA to Eland, filters out all but unique reads with no more than the specified number of mismatches'''
	print("Converting BWA BAM file to SAM")
	input = BwaSamFile(sam_input, 'r')
	total_passed = 0
	for i, line in enumerate(input):
		if line.num_best_hits != 1:
			continue
		elif line.num_mismatches > mismatches:
			continue
		else:
			total_passed += 1
			eland_output.write(line.convert_to_eland())
	print "bwasam: total lines", i, "total passed", total_passed
	input.close()
	
def convert_bowtiesam(eland_output, sam_input, mismatches):
	'''Converts SAM file from Bowtie to Eland, filters out all but unique reads with no more than the specified number of mismatches.'''
	input = BowtieSamFile(sam_input, 'r')
	total_passed = 0
	for i, line in enumerate(input):
		if line.num_hits != 1:
			continue
		elif line.edit_distance > mismatches:
			continue
		else:
			total_passed += 1
			eland_output.write(line.convert_to_eland())
	print "bowtiesam: total lines", i, "total passed", total_passed
	input.close()
	
def convert_illuminasam(eland_output, sam_input, mismatches):
	'''Converts SAM file from Bowtie to Eland, filters out reads with no more than the specified number of mismatches.  NOTE:  Due to limitations of Illumina format, does not filter out unique reads.  Assumes prefiltered.'''
	input = IlluminaSamFile(sam_input, 'r')
	total_passed = 0
	for i, line in enumerate(input):
		if line.mismatching_positions > mismatches:
			continue
		else:
			total_passed += 1
			eland_output.write(line.convert_to_eland())
	print "illuminasam: total lines", i, "total passed", total_passed
	input.close()
	eland_output.close()
	
def convert_elandsam(eland_output, sam_input, mismatches):
	input = ElandSamFile(sam_input, 'r')
	total_passed = 0
	for i, line in enumerate(input):
		if line.num_hits != 1:
			continue
		elif line.edit_distance > mismatches:
			continue
		else:
			total_passed += 1
			eland_output.write(line.convert_to_eland())
	print "elandsam: total lines", i, "total passed", total_passed
	input.close()
		
def convert_sam(eland_output, sam_input, mismatches):
	'''Determines SAM format and converts to eland'''
	print("Hi, sam input is: {sam_input}".format(sam_input=sam_input))
	input = open(sam_input, 'r')
	line = input.readline()
	# Look for proper headers first
	while line.startswith('@'):
		if line.startswith('@PG'):
			fields = line.split('\t')
			program_name = None
			for f in fields:
				if f.startswith('PN:'):
					program_name = f[3:]
					continue
				if f.startswith('ID:'):
					program_name = f[3:]
					continue
			if program_name == 'bwa':
				input.close()
				convert_bwasam(eland_output, sam_input, mismatches)
				return
			elif program_name == 'bowtie':
				input.close()
				convert_bowtiesam(eland_output, sam_input, mismatches)
			elif program_name == 'illumina_export2sam.pl':
				input.close()
				convert_illuminasam(eland_output, sam_input, mismatches)
				return
		line = input.readline()
	
	# If no proper headers, try to guess appropriate SAM format
	fields = line.split('\t')
	for f in fields[11:]:
		if f.startswith('X0'):
			input.close()
			convert_bwasam(eland_output, sam_input, mismatches)
			return
		if f.startswith('NM'):
			input.close()
			convert_elandsam(eland_output, sam_input, mismatches)
			return
	input.close()
	if len(fields) == 11:  # No Custom flags
		raise Exception("Cannot convert regular SAM file")
	else:
		convert_bowtiesam(eland_output, sam_input, mismatches)
		
def convert_bam(eland_output, bam_input, mismatches):
	"""
	bam2sam
	"""
	print "converting bam to sam ...",mismatches
	sam_input = os.path.join(TMP_DIR, os.path.basename(bam_input)[:-4
	] + str(time.time()) + '.sam')
	print "converting to sam: %s" % sam_input
	bam2sam_cmd = 'samtools view -h %s > %s' % (bam_input, sam_input)
	print bam2sam_cmd
	subprocess.call(bam2sam_cmd, shell=True)
	print("Converting SAM to ELAND")
	convert_sam(eland_output, sam_input, mismatches)
	print "deleting %s" % sam_input
	try:
		os.remove(sam_input)
	except OSError: #don't know why but somehow the file is pre-deleted.
		pass
			
def merge_unique_eland(output, mapped_reads_files, mismatches=2):
	print "merge_filter %s to %s" % (','.join(mapped_reads_files), output)
	eland_out = ElandFile(output, 'w')
	for i in mapped_reads_files:
		if not os.path.exists(i):
			raise Exception("File %s does not exist" % i)
		if i.endswith('.bam'):
			convert_bam(eland_out, i, mismatches)
			continue
		if i.endswith('.sam'):
			convert_sam(eland_out, i, mismatches)
			continue
		if 'multi' in i:
			print " multi eland ..."
			eland_in = ElandMultiFile(i, 'r')
		elif 'extended' in i:
			print " extended ..."
			eland_in = ElandExtendedFile(i, 'r')
		else:
			print "ElandFile ..."
			eland_in = ElandFile(i, 'r')
		total_passed = 0
		for i, line in enumerate(eland_in):
			best_hits = line.best_matches()
			if len(best_hits) == 0:
				continue
			elif len(best_hits) > 1:
				continue  # Only merge unique hits
			elif best_hits[0].number_of_mismatches() > mismatches:
				continue
			else:
				total_passed += 1
				eland_out.write(line.convert_to_eland())
			print "best_hits",best_hits	
		print "unique eland: total lines", i, "total passed", total_passed
		eland_in.close()
	eland_out.close()
	
if __name__ == '__main__':
	if len(sys.argv) < 3:
		print "Usage:  merge_and_filter_reads.py output_file reads_file [reads_file ...]"
		raise SystemExit(1)
	merge_unique_eland(sys.argv[1], sys.argv[2:])
