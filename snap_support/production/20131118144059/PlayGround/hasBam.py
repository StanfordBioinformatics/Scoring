
import os
import glob
from argparse import ArgumentParser

description = "Given an input file with bam file names, determines whether they exist or not. I originally wrote this to support SNAP runs. Often, the request has BAM files that don't exist, and need to be created."
parser = ArgumentParser(description=description)
parser.add_argument('-i','--infile',required=True,help="Tab-delimited input file with the archive path in field 0, the lane number in field 1, and the bam file in lane 2.")

args = parser.parse_args()

fh = open(args.infile,'r')
for line in fh:
	line = line.strip()
	if not line:
		continue	
	line = line.split("\t")
	path = line[1]
	lane = line[2]
	bam = line[3]
	path = os.path.join(path,lane,bam)
	if os.path.exists(path):
		print ("done")
	else:
		print("not started")
fh.close()
	
	
