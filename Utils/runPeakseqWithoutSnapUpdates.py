#!/usr/bin/env python

import json
from argparse import ArgumentParser

description = ""
parser = ArgumentParser(description=description)


parser.add_argument('--name',required=True,help="The name of the scoring run (This should be the ChIP Seq Scoring object's UID in Syapse).")
parser.add_argument('--control',required=True,help="The control name.")
parser.add_argument('--genome',default="hg19_male",help="The genome to which the sample and control replicates were mapped.")
parser.add_argument('--single-end',action="store_true",help="The sample and control replicates are Single End reads.")
parser.add_argument('--rescore-control',type=int,default=0,help="The number of days old the control scoring should be in order for it to be rescored. This option is mainly used to rescore a control that is a paired-end (PE) and that was scored using all reads instead of just the forward reads.  So, this option would be helpful to use if the control is paired-end (PE). Up until May 2014, all scoring was done with both forward and reverse reads, so in order to rescore a control with just the forward reads, you'd wan't to incude the --paired-end option and set --rescore_control to the number of since since May 1, 2014.")
parser.add_argument('--force',action="store_true",help="Presence of this option indicates to pass this flag to the scoring command pipeline.py.")

args = parser.parse_args()

runName = args.name
control = args.control
rescoreControl = args.rescore_control
singleEnd = args.single_end #bool
genome = args.genome
force = args.force #bool

confFh = open("conf.json","r")
conf = json.load(confFh)
sampleRunPathPrefix = conf["scoringPathPrefix"]["sample"]
controlRunPathPrefix = conf["scoringPathPrefix"]["control"]
notifyEmail = conf["email"]["to"][0]

sampDir = os.path.join(sampleRunPathPrefix,runName)
sampInputsDir = os.path.join(sampDir,"inputs")
controlDir = os.path.join(controlRunPathPrefix,control)
controlInputsDir = os.path.join(controlDir,"inputs")
sampConf = os.path.join(sampInputsDir,"sample.conf")
controlConf = os.path.join(controlInputsDir,"ontrol.conf")

stdout = os.path.join(sampInputsDir,"pipeline.py_stdout.txt")
if os.path.exists(stdout):
	os.remove(stdout)
stderr = os.path.join(sampInputsDir,"pipeline.py_stderr.txt")
if os.path.exists(stderr):
	os.remove(stderr)
snapLog = os.path.join(sampInputsDir,"snap_log.txt")
if os.path.exists(snapLog):
	os.remove(snapLog)
logfh = open(snapLog,'w')

pythonCmd = "python /srv/gs1/projects/scg/Scoring/pipeline2/pipeline.py -c macs -m trupti@stanford.edu -m scg_scoring@lists.stanford.edu -n {runName} -l {sampInputsDir}".format(runName=runName,sampInputsDir=sampInputsDir)

if rescoreControl > 0:
	pythonCmd += " --rescore_control={rescore_control}".format(rescoreControl=rescoreControl)

if not singleEnd:
	pythonCmd += " --paired_end"

pythonCmd += " --genome {genome}".format(genome=genome)

if force:
	pythonCmd += " --force"

pythonCmd += " {controlConf} {sampConf}".format(controlConf=controlConf,sampConf=sampConf)
pythonCmd += " 2> {stderr}".format(stderr=stderr)
logfh.write(pythonCmd + "\n")

#set scoring status of ChIP Seq Scoring object in Syapse to "Running Analysis"
qsubCmd = "qsub -sync y -wd {sampDir} -m ae -M {notifyEmail} #{pythonCmd}".format(sampDir=sampDir,notifyEmail=notifyEmail)
logfh.write(qsubCmd)

#system() runs a command in a subshell. Returns true if the command gives zero exit status, false for non zero exit status. 
# Returns nil if command execution fails. An error status is available in $?. The arguments are processed in the same way as for Kernel.spawn.

#update Syapse's Chip Seq Scoring object's Scoring Status attribute to 'Running Analysis'
res = system(qsubCmd)
puts $?.to_i
if not res or $?.to_i  > 0 #if res is nil, nil.to_i = 0
	puts "Error running '#{qsubCmd}'. Tried to run command in runPeakseqWithoutSnapUpdates.rb."
	exit(1)
end
logfh.close()

#t2 = Time.new
#tw = t.year.to_s + "-" + t.month.to_s + "-" + t.day.to_s
#system("echo 'Start Time: #{t}' >> #{snapLog}")
#system("echo 'End Time: #{t2}' >> #{snapLog}")
#python /srv/gs1/projects/scg/Scoring/pipeline2/pipeline.py -n GM12878_Bmi1NBP196140_Score_14Jun03_102907 -l /srv/gs1/projects/scg/SNAP_Scoring/production/replicates/human/MACS_390_production/inputs -c macs --rescore_control --paired_end --genome hg19_male --force -m trupti@stanford.edu -m scg_scoring@lists.stanford.edu /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine1_Control516/inputs/control.conf /srv/gs1/projects/scg/SNAP_Scoring/production/replicates/human/MACS_390_production/inputs/sample.conf 2>/srv/gs1/projects/scg/SNAP_Scoring/production/replicates/human/MACS_390_production/inputs/pipeline.py_stderr.txt | tee /srv/gs1/projects/scg/SNAP_Scoring/production/replicates/human/MACS_390_production/inputs/pipeline.py_stdout.txt")
#
