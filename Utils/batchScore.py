import argparse
import subprocess
import shutil
import os
import datetime

#sampleRunPrefix = "/srv/gs1/projects/scg/SNAP_Scoring/production/replicates/human" #old path on gs1
sampleRunPrefix = "/srv/gsfs0/projects/gbsc/SNAP_Scoring/production/replicates/human" #new path on gsfs0
controlRunPrefix = "/srv/gsfs0/projects/gbsc/SNAP_Scoring/production/controls/human"
description = "Runs multiple scoring jobs in parallel, calling runPeakseqWithoutSnapUpdates.rb. The script generateSampAndControlConfs.py needs to have been first called because it's responsible for creating the sample and control configuration files that the pipeline uses."
parser = argparse.ArgumentParser(description=description)
parser.add_argument('-i','--infile',required=True,help="Batch input file.")
parser.add_argument('-r','--run-field-pos',default=0,help="Run name field position (0-base).")
parser.add_argument('-c','--control-field-pos',default=5,help="Control name field position (0-base).")
parser.add_argument('-l','--limit',type=int,help="The number of scoring jobs to run (which will run in parallel as well). For example, a limit of 5 would amount to only running the first 5 jobs (rows) in --infile.")
parser.add_argument('-p','--paired-end',action="store_true",help="Presence of this option indicates that reads are paired-end.")
parser.add_argument('--rm-results-dirs',action="store_true",help="Presence of this option indicates that the results directory for the control and sample are to be removed. Useful for when doing a rerun.")
parser.add_argument('--purge-inputs-dirs',action="store_true",help="Presence of this option indicates that all files are to be removed from the control and sample inputs directories, execpt for the control and sample conf fiels, respectively.")
parser.add_argument('--rescore-control',type=int,default=0,help="The number of days old the control scoring should be in order for it to be rescored. This option is mainly used to rescore a control that is a paired-end (PE) and that was scored using all reads instead of just the forward reads.  So, this option would be helpful to use if the control is paired-end (PE). Up until May 2014, all scoring was done with both forward and reverse reads, so in order to rescore a control with just the forward reads, you'd wan't to incude the --paired-end option and set --rescore_control to the number of since since May 1, 2014.")
#parser.add_argument('--sample-time',action="store_true")
args = parser.parse_args()

limit = args.limit
count = 0
fh = open(args.infile,'r')
for line in fh:
	line = line.strip("\n")
	if not line:
		continue
	if line.startswith("#"):
		continue
	line = line.split("\t")
	run = line[args.run_field_pos].strip()
	#print("#{run}#".format(run=run))
	control = line[args.control_field_pos].strip()
	sampleRunPath = os.path.join(sampleRunPrefix,run)
	sampleResultsPath = os.path.join(sampleRunPath,"results")
	sampleInputsPath = os.path.join(sampleRunPath,"inputs")
	sampleConf = os.path.join(sampleInputsPath,"sample.conf")
	controlRunPath = os.path.join(controlRunPrefix,control)
	controlResultsPath = os.path.join(controlRunPath,"results")
	controlInputsPath = os.path.join(controlRunPath,"inputs")
	controlConf = os.path.join(controlInputsPath,"control.conf")
	if args.rm_results_dirs:
		if os.path.exists(sampleResultsPath):
			shutil.rmtree(sampleResultsPath)
#		if os.path.exists(controlResultsPath):
#			shutil.rmtree(controlResultsPath)

	if args.purge_inputs_dirs:
		if os.path.exists(sampleInputsPath):
			for i in os.listdir(sampleInputsPath):
				i = os.path.join(sampleInputsPath,i)
				if i != sampleConf:
					if os.path.isfile(i):
						os.remove(i)
					elif os.path.isdir(i):
						shutil.rmtree(i)
		if os.path.exists(controlInputsPath):
			for i in os.listdir(controlInputsPath):
				i = os.path.join(controlInputsPath,i)
				if i != controlConf:
					if os.path.isfile(i):
						os.remove(i)
					elif os.path.isdir(i):	
						shutil.rmtree(i)
#	refTime = datetime.datetime(2014,6,20)
#	if args.sample_time:
#		try:
#			mtime = os.path.getmtime(sampleResultsPath)
#		except OSError:
#			mtime = 0
#		if mtime:
#			dte = datetime.datetime.fromtimestamp(mtime)	
#			if dte > refTime:
#				print("Continuing")
#				continue  #assume that scoring is still ongoing
	cmd = "qsub -sync y -wd {wd} -m ae -M nathankw@stanford.edu -V runPeakseqWithoutSnapUpdates.rb --name {run} --control {control} --force".format(wd=sampleRunPath,run=run,control=control)
	if args.paired_end:
		cmd += " --paired-end"
	if args.rescore_control > 0:
		cmd += " --rescore-control={}".format(args.rescore_control)
	print(cmd)
	subprocess.Popen(cmd,shell=True)
	if limit:
		count += 1
		if count >= limit:
			break
fh.close()
