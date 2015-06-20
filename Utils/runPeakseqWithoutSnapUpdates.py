#!/usr/bin/env python

import json
from argparse import ArgumentParser
import gbsc_utils #module load gbsc/endode (which in turn loads gbsc/gbsc_utils)
import SyapseUtils #module load gbsc/encode

description = ""
parser = ArgumentParser(description=description)

parser.add_argument('--syapse-mode',required=True,help="A string indicating which Syapse host to use. Must be one of elemensts given in {knownModes}.".format(knownModes=SyapseUtils.Syapse.knownModes))
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

pythonCmd = "python {scoringPipelineScript} -c macs -m trupti@stanford.edu -m scg_scoring@lists.stanford.edu -n {runName} -l {sampInputsDir}".format(scoringPipelineScript=conf.scoringPipelineScript,runName=runName,sampInputsDir=sampInputsDir)

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

qsubCmd = "qsub -sync y -wd {sampDir} -m ae -M {notifyEmail} #{pythonCmd}".format(sampDir=sampDir,notifyEmail=notifyEmail)
logfh.write(qsubCmd)
try:
	stdout,stderr = gbsc_utils.createSubprocess(cmd=qsubCmd,checkRetcode=True)
except Exception as e:
	subject = "Chip Scoring: Error running {program}".format(program=sys.argv[0])
	body = e.message
	emailCmd = "mandrill_general.py --subject {subject} --to {notifyEmail} --body {body} ".format(subject=subject,notifyEmail=notifyEmail,body=body)
	gbsc_utils.createSubprocess(cmd=emailCmd,checkRetcode=True)
#set scoring status of ChIP Seq Scoring object in Syapse to "Running Analysis"
syapse = SyapseUtils(mode=args.syapse_mode)


#update Syapse's Chip Seq Scoring object's Scoring Status attribute to 'Running Analysis'
logfh.close()
