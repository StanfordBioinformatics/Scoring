#!/usr/bin/env python

from argparse import ArgumentParser
import os

description = ""
parser = ArgumentParser(description=description)
parser.add_argument('-e','--eland-file',required=True)
parser.add_argument('-o','--outfile',required=True,help="The output tag align file.")

args = parser.parse_args()
elandFile = args.eland_file
outfile = args.outfile

fh = open(elandFile,'r')
fout = open(outfile,'w')

for line in fh:
	line = line.strip("\n")
	if not line:
		continue
	line = line.split("\t")
	readName = line[0]
	sequence = line[1]
	typeOfMatch = line[2]
	numExactMatch = line[3]
	numOneMismatch = line[4]
	numTwoMismatch = line[5]
	chrom = line[6]
	start = line[7] #one-base (http://wanglab.ucsd.edu/star/pipeline.php?s=pre_intro)
	matchDirection = line[8] #either R or F

	fout.write(os.path.splitext(chrom)[0] + "\t")
	zeroBasePosition = int(start) - 1
	fout.write(str(zeroBasePosition) + "\t")
	endPosition = zeroBasePosition + len(sequence)
	fout.write(str(endPosition) + "\t")
	fout.write(sequence + "\t")	
	
	#calculate score
	score = 0
	if numExactMatch == "1":
		score = 1000
	elif numOneMismatch != "0":
		score = 250
	elif numTwoMismatch != "0":
		score = 63
	fout.write(str(score) + "\t")

	if matchDirection == "F":
		fout.write("+")
	else:
		fout.write("-")
	fout.write("\n")
fout.close()
