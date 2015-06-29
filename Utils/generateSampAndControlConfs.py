import shutil
import argparse
import re
import os
from SequencingRuns import runPaths
import gbsc_utils
import conf

genome = "hg19_male"
mappability_file = "/srv/gs1/apps/snap_support/production/current/hg19_male.txt"
q_value_thresholds = "0.1,0.05,0.01,0.001"
bin_size = 10000
peakseq_binary = "/srv/gs1/projects/scg/Scoring/Peak-Seq_v1.02/Peak-Seq_v1.02"

description = """
OVERVIEW:
Generates the sample config file and the control config file for each scoring request in the input file, which contains one request per line in the format given below. For each request, creates the run folder if it doesn't exist already, as well as the run folder subdirectories called 'inputs', 'results', and 'tmp'. The equivalent happens for the control name. There must be at least one sample and one control replicate (BAM file), and they must be in the first sample and first control field, respectively, of the input file. For any BAM files that are given but can't be found, it will be logged in the BAM log file (-b). For scoring requests that are successfully prepared, they will be logged to the ready-to-score file (-s). A notification email will be sent to the email addresses specified in the conf file if there are any scoring requests that have a control or replicate BAM file that can't be located on tthe server, and the message contents will be that of the BAM log file. The format of that log file is given in the help description of the -b argument. The contents of that log file will be emailed as the message body.  Lastly, if the --pipeline argument is specified, then this script will kick of the batch scoring process. If there is a failure in that script, the details of the failure will be emailed to the same email addresses as mentioned above.

INPUT FILE FORMAT (-i/--infile):

	0) Scoring run name
	1) scoring status   #no longer used
	2) Whether or not samples are paired-end #no longer used
	3) BAM file name for sample replicate 1
	4) BAM file name for sample replicate 2
	5) control name
	6) BAM file name for control replicate 1
	7) BAM file name for control replicate 2
	"""

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,description=description)
parser.add_argument('-i','--infile',required=True,help="The input file with parameter settings. The file must be formatted as indicated in the program description above.")
parser.add_argument('--header',action="store_true",help="Presence of this option indicates that there is a single field-header line as the first line in --infile.")
parser.add_argument('-b',required=True,help="The output file for runs that need bam files. If the file pre-exists, it will be overwritten. For any BAM file that isn't found, a line will be logged in this file with the tab-delimited fields 'runName, rundir,lane,fileName'.")
parser.add_argument('-s',required=True,help="The output file to send runs ready for scoring. If the file pre-exists, it will be overwritten. Formatted the same as --infile. For each scoring request in --infile that is valid (has BAM files that can be found), that scoring request (line) is copied to this file.")
parser.add_argument('--pipeline',action="store_true", help="Presence of this option indicates to start the batch scoring by calling the script batchScore.py")
parser.add_argument('-v','--verbose',action="store_true",help="Turn on verbosity")

def logMissingBam(scoringName,runName,lane,bamfilename):
	"""
	Function : Checks if the given BAM file name exists in it's run or run and lane directory. If so, returns the path, otherwise logs the missing BAM file.
	Args     : scoringName - str. Name of the scoring run, parsed from the first field of a line in --infile.
						 runName     - str. Name of the sequecing run.
						 lane        - str. The sequencing lane on the sequencing run (i.e. L1).
						 bamfilename - str. The name of the BAM file.
	"""
	global bout
	bout.write(scoringName + "\t" + runName + "\t" + lane + "\t" + bamfilename + "\n")

def getBamFilePath(scoringName,rundir,bamfilename):
	"""
	Function : A wrapper for runPaths.getBamFile so that it logs any unfound BAM file.
	Args     : scoringName - the name of the scoring run
						 rundir      - the run directory path to the published results.
						 bamfilename - the name of the BAM file to find in the published results.
	"""
	path = runPaths.getBamFilePath(rundir=rundir,fileName=bamfilename)
	if not path:
		lane = runPaths.getLaneReg.search(bamfilename).groups()[0]
		logMissingBam(scoringName=scoringName,runName=os.path.basename(rundir),lane=lane,bamfilename=bamfilename)
		return None	
	return path

args = parser.parse_args()
verbose = args.verbose
batchScore = args.pipeline
dico = {}
if os.path.exists(args.b):
	os.remove(args.b)
bout = open(args.b,'a')
if os.path.exists(args.s):
	os.remove(args.s)
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
	scoringRunName = line[0]
	runPath = os.path.join(conf.sampleScoringPrefixPath,scoringRunName)
	print()
	print("Processing run {}".format(scoringRunName))
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
	rundir = runPaths.getPubPath(sampRep1_runName)
	sampRep1 = getBamFilePath(scoringRunName,rundir,sampRep1)
	if not sampRep1:
		continue #bam doesn't exist (logged to bout)
	sampRep2 = line[4]
	if sampRep2:
		sampRep2_runName = runPaths.getRunNameFlf(sampRep2)
		rundir = runPaths.getPubPath(sampRep2_runName)
		sampRep2 = getBamFilePath(scoringRunName,rundir,sampRep2)
		if not sampRep2:
			continue #bam doesn't exist (logged to bout)
	controlName = line[5]
	controlDir = os.path.join(conf.controlScoringPrefixPath,controlName)
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
	rundir = runPaths.getPubPath(controlRep1_runName)
	controlRep1 = getBamFilePath(scoringRunName,rundir,controlRep1)
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
		rundir = runPaths.getPubPath(controlRep2_runName)
		controlRep2 = getBamFilePath(scoringRunName,rundir,controlRep2)

		if not controlRep2:
			continue #bam doesn't exist (logged to bout)
		controls += "," + controlRep2
	controlConfFile = os.path.join(controlInputsDir,"control.conf")
	sampleConfFile = os.path.join(sampInputsDir,"sample.conf")
	sfout = open(sampleConfFile,'w')

	sfout.write("[general]\n")
	sfout.write("run_name = {}\n".format(scoringRunName))
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

bout.seek(0,2) #go to end of file

ccEmails = " ".join(conf.ccEmails)

if bout.tell():
	bout.close()
	#send email to notify about scoring runs that can't proceed due to missing BAMs.
	subject = "ChIP Scoring Warning: BAMS not found"
	print(subject)
	cmd = "mandrill_general_email.py --subject \"{subject}\"  --body {body} --to {toEmails} --sender {signature}".format(subject=subject,body=bout.name,signature=conf.sender,toEmails=" ".join(conf.toEmails))
	if ccEmails:
		cmd += " --cc {}".join(ccEmails)
	gbsc_utils.createSubprocess(cmd=cmd,checkRetcode=True)
bout.close()

if batchScore:
	cmd = "python batchScore.py -i {infile} -p".format(infile=sout.name)
	try:
		stdout,stderr = gbsc_utils.createSubprocess(cmd=cmd,checkRetcode=True) #an Exception will have been raised with details on cmd, stdout,stderr, and returncode if the command failed.
	except Exception as e:
		subject = "ChIP Scoring Failure: batchScore.py failed"
		cmd = "mandrill_general_email.py --subject \"{subject}\" --body {body} --to {toEmails} --cc {ccEmails} --sender {signature}".format(subject=subject,body=e.message,signature=conf.sender,toEmails=" ".join(conf.toEmails),ccEmails=" ".join(conf.ccEmails))
	if ccEmails:
		cmd += " --cc {}".join(ccEmails)
	gbsc_utils.createSubprocess(cmd=cmd,checkRetcode=True)
