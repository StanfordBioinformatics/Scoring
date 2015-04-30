
from argparse import ArgumentParser
import os
import subprocess

def getFastqPath(archive,bam,fqExt):
	"""
	Function : Given an archive path to sequencing and analysis results, and a BAM file, tries to find the path to the FASTQ file used to generate the BAM, using several assumptions.
	Args     : archive - str. Archive directory path.
						 bam - str. Bam file name (w/o directory path)
						 fqExt - str. File exension used for the FASTQ file (i.e. 'fastq', or 'fq').
	Returns  : str, or None.
	"""
	fastqBasename = bam.rstrip(".gz")
	fastqBasename = fastqBasename.rstrip(".bam") + "." + fqExt
	fastqPath = os.path.join(archive,fastqBasename)
	if os.path.exists(fastqPath):
		return fastqPath

	fastqPathGz = fastqPath + ".gz"
	if os.path.exists(fastqPathGz):
		return fastqPathGz

	fastqPath = os.path.join(archive,lane,fastqBasename)
	if os.path.exists(fastqPath):
		return fastqPath

	fastqPathGz = fastqPath + ".gz"
	if os.path.exists(fastqPathGz):
		return fastqPathGz
	else:
		return None

description = "Runs the kwality tool with the bwa aln conf file at /srv/gs1/software/gbsc/kwality/1.0/instances/bwa-aln-se.json to generate single-end BAM files.  This script is used to create BAMS for read files that should have a corresponding BAM file, but don't."
parser = ArgumentParser(description=description)
parser.add_argument('-i','--infile',help="Tab-delimited input file.")
parser.add_argument('--archive-path-fieldnum',default=1,type=int,help="The 0-base index of the field that provides the archive path directory.")
parser.add_argument('--lane-fieldnum',default=2,type=int,help="The 0-base index of the field that provides the lane number in the format L\d.")
parser.add_argument('--bam-fieldnum',default=3,type=int,help="The 0-base index of the field that provides the BAM file name that should exist. Note that from this BAM file name, the corresponding FASTQ file name will be calculated and checked for existance.")
parser.add_argument('--run',action="store_true",help="Presence of this option means to run the resulting sjm file.")

args = parser.parse_args()

fh = open(args.infile,'r')
for line in fh:
	line = line.strip("\n")
	if not line:
		continue
	line = line.split("\t")
	ap = line[args.archive_path_fieldnum]
	lane = line[args.lane_fieldnum]
	bam = line[args.bam_fieldnum]
	fastqPath = getFastqPath(ap,bam,"fastq")
	if not fastqPath:
		fastqPath = getFastqPath(ap,bam,"fq")
	if not fastqPath:
		warning = "Warning: Cannot locate FASTQ file used to generate bam file '{bam}' in archive '{archive}'.".format(bam=bam,archive=ap)
		print(warning)
		#sys.stderr.write(warning)
		continue
	outdir = os.path.join(ap,lane)
	cmd = "kwality.py -c /srv/gs1/software/gbsc/kwality/1.0/instances/bwa-aln-se.json --outdir={outdir} -s makeBams.sjm".format(outdir=outdir)
	if args.run:
		cmd += " {}".format("--run")
	cmd += " fastq={}".format(fastqPath)
	subprocess.call(cmd,shell=True)
fh.close()
