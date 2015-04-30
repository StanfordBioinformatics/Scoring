import shutil
import argparse
import re
import os
from SequencingRuns import runPaths

def getRunDirPath(runName):
	try:
		path = runPaths.getPubPath(runName)
	except OSError:
		path = runPaths.getArchivePath(runName)
	return path


controlPrefixPath = "/srv/gsfs0/projects/gbsc/SNAP_Scoring/production/controls/human"
sampPrefixPath =    "/srv/gsfs0/projects/gbsc/SNAP_Scoring/production/replicates/human"

genome = "hg19_male"
mappability_file = "/srv/gs1/apps/snap_support/production/current/hg19_male.txt"
q_value_thresholds = "0.1,0.05,0.01,0.001"
bin_size = 10000
peakseq_binary = "/srv/gs1/projects/scg/Scoring/Peak-Seq_v1.02/Peak-Seq_v1.02"

description = "Generates the sample config file and the control config file for each scoring request in the input file, which contains once request per line. For each request, creates the run folder if it doesn't exist already, as well as the run folder subdirectories called 'inputs', 'results', and 'tmp'. The equivalent happens for the control name. There must be at least one sample and one control replicate (BAM file), and they must be in the first sample and first control field, respectively, of the input file. For any BAM files that are given but can't be found, it will be logged in the BAM log file (-b). For scoring requests that are successfully prepared, they will be logged to the ready-to-score file (-s)."
parser = argparse.ArgumentParser(description=description)
parser.add_argument('-i','--infile',required=True,help="The input file with parameter settings. The run name is in the first field")
parser.add_argument('--header',action="store_true",help="Presence of this option indicates that there is a single field-header line as the first line in --infile.")
parser.add_argument('-b',required=True,help="The output file for runs that need bam files. Opened in append mode.")
parser.add_argument('-s',required=True,help="The output file to send runs ready for scoring. Opened in append mode.")
parser.add_argument('-v','--verbose',action="store_true",help="Turn on verbosity")

args = parser.parse_args()
verbose = args.verbose
dico = {}
bout = open(args.b,'a')
sout = open(args.s,'a')
fh = open(args.infile,'r')
if args.header:
	fh.readline()
for line in fh:
	line = line.strip("\n")
	if not line: 
		continue
	line = line.split("\t")
	line = [x.strip() for x in line]
	if verbose:
		print(line)
	runName = line[0]
	runPath = os.path.join(sampPrefixPath,runName)
	print()
	print("Processing run {}".format(runName))
	print("runPath is {}".format(runPath))
	if not os.path.exists(runPath):
		os.mkdir(runPath)
	sampInputsDir = os.path.join(runPath,"inputs")
	if not os.path.exists(sampInputsDir):
		os.mkdir(sampInputsDir)
	sampResultsDir = os.path.join(runPath,"results")
#	if not os.path.exists(sampResultsDir):
#		os.mkdir(sampResultsDir)
	sampTempDir = os.path.join(runPath,"tmp")
	if not os.path.exists(sampTempDir):
		os.mkdir(sampTempDir)
	sampRep1 = line[3]
	sampRep1_runName = runPaths.getRunNameFlf(sampRep1)
	rundir = getRunDirPath(sampRep1_runName)
	sampRep1 = runPaths.getBamFile(rundir,sampRep1,bout)
	if not sampRep1:
		continue #bam doesn't exist (logged to bout)
	sampRep2 = line[4]
	if sampRep2:
		sampRep2_runName = runPaths.getRunNameFlf(sampRep2)
		rundir = getRunDirPath(sampRep2_runName)
		sampRep2 = runPaths.getBamFile(rundir,sampRep2,bout)
		if not sampRep2:
			continue #bam doesn't exist (logged to bout)
	controlName = line[5]
	controlDir = os.path.join(controlPrefixPath,controlName)
	print("controlPath is {}".format(controlDir))
	if not os.path.exists(controlDir):
		os.mkdir(controlDir)
	controlInputsDir = os.path.join(controlDir,"inputs")
	if not os.path.exists(controlInputsDir):
		os.mkdir(controlInputsDir)
	controlResultsDir = os.path.join(controlDir,"results")
#	if not os.path.exists(controlResultsDir):
#		os.mkdir(controlResultsDir)
	controlTempDir = os.path.join(controlDir,"tmp")
	if not os.path.exists(controlTempDir):
		os.mkdir(controlTempDir)
	controlRep1 = line[6]
	controlRep1_runName = runPaths.getRunNameFlf(controlRep1)
	rundir = getRunDirPath(controlRep1_runName)
	controlRep1 = runPaths.getBamFile(rundir,controlRep1,bout)
	if not controlRep1:
		continue #bam doesn't exist (logged to bout)
	controls = controlRep1
	controlRep2 = ""
	try:
		controlRep2 = line[7]
	except IndexError:
		pass
	if controlRep2:
		controlRep2_runName = runPaths.getRunNameFlf(controlRep2)
		rundir = getRunDirPath(controlRep2_runName)
		controlRep2 = runPaths.getBamFile(rundir,controlRep2,bout)

		if not controlRep2:
			continue #bam doesn't exist (logged to bout)
		controls += "," + controlRep2
	controlConfFile = os.path.join(controlInputsDir,"control.conf")
	sampleConfFile = os.path.join(sampInputsDir,"sample.conf")
	sfout = open(sampleConfFile,'w')

	sfout.write("[general]\n")
	sfout.write("run_name = {}\n".format(runName))
	sfout.write("control_results_dir = {}\n".format(controlResultsDir))
	sfout.write("results_dir = {}\n".format(sampResultsDir))
	sfout.write("genome = {}\n".format(genome))
	sfout.write("mappability_file = {}\n".format(mappability_file))
	sfout.write("q_value_thresholds = {}\n".format(q_value_thresholds))
	sfout.write("temporary_dir = {}\n".format(sampTempDir))
	sfout.write("bin_size = {}\n".format(bin_size))
	sfout.write("peakseq_binary = {}\n".format(peakseq_binary))
	sfout.write("\n")
	sfout.write("[replicate1]\n")
	sfout.write("mapped_reads = {}\n".format(sampRep1))
	sfout.write("\n")
	if sampRep2:
		sfout.write("[replicate2]\n")
		sfout.write("mapped_reads = {}\n".format(sampRep2))
	sfout.close()
	print("Created sample conf file {}".format(sampleConfFile))
	
	cfout = open(controlConfFile,'w')
	cfout.write("[peakseq]\n")
	cfout.write("control_mapped_reads = {}\n".format(controls))
	cfout.write("results_dir = {}\n".format(controlResultsDir))
	cfout.write("temporary_dir = {}\n".format(controlTempDir))
	cfout.write("run_name = {}\n".format(controlName + "_control"))
	cfout.write("genome = {}\n".format(genome))
	cfout.close()
	print("Created control conf file {}".format(controlConfFile))
	sout.write("\t".join(line) + "\n")
sout.close()
bout.close()
