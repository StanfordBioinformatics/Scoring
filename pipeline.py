#!/srv/gs1/software/python/python-2.7/bin/python
import subprocess
import datetime
import time
import glob
import sys
import os

import sjm
import control_scoring
import idr
from conf import ConfigControl, ConfigSample
import conf
import SyapseUtils

BIN_DIR = conf.BIN_DIR
ARCHIVE_DIR = conf.ARCHIVE_DIR
DOWNLOAD_BASE = conf.DOWNLOAD_BASE
SJM_NOTIFY = conf.SJM_NOTIFY
QUEUE = conf.QUEUE
PROJECT = conf.SGE_PROJECT
SCH_OPT = conf.SCHED_OPTIONS
SNAP_RUN = False
GBSC_DIR = "/srv/gsfs0/projects/gbsc/"

class ScoringJobs:
	def add_jobs(self, jobs_name, jobs):
		if not jobs_name in self.jobs:
			self.jobs[jobs_name] = jobs
		else:
			self.jobs[jobs_name] += jobs
	
	def all_jobs(self):
		all_jobs = []
		for jn, js in self.jobs.iteritems():
			all_jobs += js
		return all_jobs
				

class Control(ScoringJobs):
	def __init__(self, run_name, results_dir, temp_dir, genome, mapped_read_files, conf, peakcaller):
		self.run_name = run_name
		self.results_dir = results_dir
		self.temp_dir = temp_dir
		self.genome = genome
		self.mapped_read_files = mapped_read_files
		self.conf = conf
		self.archive_file = os.path.join(ARCHIVE_DIR, run_name + peakcaller + '.tar.gz')
		self.archive_file_download = DOWNLOAD_BASE + run_name + peakcaller + '.tar.gz'
		self.sgr_dir = os.path.join(results_dir, 'sgr')
		self.jobs = {}
		self.peakcaller = peakcaller
		self.merged_file_location = os.path.join(self.results_dir, self.run_name + '_merged_eland.txt')
		
	def __str__(self):
		return self.run_name
		
class Sample(ScoringJobs):
	def __init__(self, run_name, results_dir, temp_dir, genome, replicates, conf):
		self.run_name = run_name
		self.results_dir = results_dir
		self.temp_dir = temp_dir
		self.genome = genome
		self.replicates = replicates
		self.conf = conf
		self.archive_file = os.path.join(ARCHIVE_DIR, run_name + '.tar.gz')
		self.archive_file_download = DOWNLOAD_BASE + run_name + '.tar.gz'
		self.idr_dir = os.path.join(results_dir, 'idr')
		sppFile = os.path.join(results_dir, 'spp_stats.txt')
		if os.path.exists(sppFile):
			os.remove(sppFile)
		repStatsFile = os.path.join(results_dir,"rep_stats")
		if os.path.exists(repStatsFile):
			os.remove(repStatsFile)
		idrResultsFile = os.path.join(results_dir,"idr_results.txt")
		if os.path.exists(idrResultsFile):
			os.remove(idrResultsFile)
		pbcStatsFile = os.path.join(results_dir,"pbc_stats.txt")
		if os.path.exists(pbcStatsFile):
			os.remove(pbcStatsFile)
		self.spp_stats = sppFile
		self.jobs = {}
		self.combined_replicate = CombinedReplicate([])
		for r in self.replicates:
			self.combined_replicate.mapped_read_files += r.mapped_read_files
			
	def __str__(self):
		return self.run_name
		
class SampleReplicate:
	def __init__(self, rep_num, mapped_read_files):
		self.rep_num = rep_num
		self.mapped_read_files = mapped_read_files
		self.hit_files = {}
		
	def rep_name(self, sample):
		return 'Rep%i' % self.rep_num
		
	def results_dir(self, sample):
		return os.path.join(sample.results_dir, 'Rep%i' % self.rep_num)
		
	def sgr_dir(self, sample):
		return os.path.join(self.results_dir(sample), 'sgr')
		
	def temp_dir(self, sample):
		return os.path.join(sample.temp_dir, sample.run_name + '_' + self.rep_name(sample))
		
	def __str__(self):
		return "Rep%i" % self.rep_num
		
class CombinedReplicate(SampleReplicate):
	def __init__(self, mapped_read_files):
		self.mapped_read_files = mapped_read_files
		self.hit_files = {}
		
	def rep_name(self, sample):
		return 'RepAll'
		
	def results_dir(self, sample):
		return os.path.join(sample.results_dir, 'RepAll')
		
	def __str__(self):
		return "RepAll"

def add_dependencies(primary_jobs, dependent_jobs):
	for dj in dependent_jobs:
		for pj in primary_jobs:
			dj.add_dependency(pj)		
	
def elandToBamFileName(infile):
	"""
	Added by Nathaniel Watson on May 12, 2014
	Function: Converts a mapping file name from eland-name format to bam-name format.
	Args    : infile - str. file name
	Returns : str. updated file name.
	Examle  :  input- /srv/gs1/projects/scg/Archive/IlluminaRuns/2012/jan/120123_MAGNUM_00122_FC63A4Y/120123_MAGNUM_00122_FC63A4Y_L2_eland_extended_pf.txt.gz
						output- /srv/gs1/projects/scg/Archive/IlluminaRuns/2012/jan/120123_MAGNUM_00122_FC63A4Y/120123_MAGNUM_00122_FC63A4Y_L2_pf.bam
	"""
	basename = os.path.basename(infile)
	newBasename = basename.split("_eland")[0] + "_pf.bam"
	return os.path.join(os.path.dirname(infile),newBasename)

def checkControlScored(control):
	"""
	Args : control - a Control instance
	"""
	resdir = control.results_dir
	elandFile = glob.glob(resdir + "/" + "*merged_eland*")
	if elandFile:
		elandFile = elandFile[0]
	else:
		return False
	return getFileAgeMinutes(elandFile)

def getFileAgeMinutes(infile):
	"""
	Function : Calculates the age of a file in hours. Partial hours are always rounded down a whole number.
	Raises an IOError of the input file doens't exist.
	"""
	if not os.path.exists(infile):
		raise IOError("Can't check age of non-existant file '{infile}'".format(infile=infile))
	mtime = datetime.datetime.fromtimestamp(os.path.getmtime(infile))
	now = datetime.datetime.now()
	diff = now - mtime
	seconds = diff.total_seconds()
	minutes = seconds/60
	return minutes
	
	
def main(syapseMode,peakcaller, run_name, control_conf, sample_conf=None, print_cmds=False, log_dir=None, no_duplicates=False, archive_results=True, emails=None, peakcaller_options=None, xcorrelation_options=None, remove_duplicates=False, paired_end=False,force=False,rescore_control=0,genome=False,no_control_lock=False):
	rescore_control = 24 * rescore_control #convert from days to hours

	scriptDir = os.path.dirname(__file__)
	if not emails:
		emails = []
	if not log_dir:
		log_dir = os.getcwd()
	if not peakcaller_options:
		peakcaller_options = {}
	if not xcorrelation_options:
		xcorrelation_options = {}
	control_conf = ConfigControl(control_conf) #parse fields out of control file
	if sample_conf:
		sample_conf = ConfigSample(sample_conf)
	if genome:
		sample_conf.GENOME=genome

	###Several runs from early on, such as in the beginning of 2012, had not BAM files as input, but instead eland files. These eland file names are in the SNAP lims for many runs. Those eland files are no longer in the archive,
	### and for these runs, all input should now be bam.  The code below converts an eland file name to a bam file name. If the bam file doens't exist, then the pipeline will crash and the bam files must be created in 
	### a separate task. 
	count = -1
	for i in control_conf.CONTROL_MAPPED_READS:
		count += 1
		if i.startswith("/opt/scg/scg1_prd_10/"):
			i = i.lstrip("/opt/scg/scg1_prd_10/") #some runs, such is ID 388 have this incorrect path
			i = GBSC_DIR + i
		##The following check for .Eland in the dirname accounts for the numerous cases where the mapping file path is like:
		##  /srv/gs1/projects/scg/Archive/IlluminaRuns/2012/may/120501_ROCKFORD_00145_FC64VL1.Eland/L4/120501_ROCKFORD_00145_FC64VL1_L4_pf.bam
		## and it should instaed lack the ".Eland" part (i.e. see http://scg-snap.stanford.edu/api/peakseq_inputs/show?experiment_run_id=380).
		if ".Eland" in i:
			i = i.replace(".Eland","")
		basename = os.path.basename(i)
		if "_eland" in basename:
			i = elandToBamFileName(i)
		control_conf.CONTROL_MAPPED_READS[count] = i
		
	if sample_conf:
		replicates = [x[0] for x in sample_conf.REPLICATES] #sample_conf.REPLICATE is a list of 1-item lists
		count = -1
		for rep in replicates:
			count += 1
			if rep.startswith("/opt/scg/scg1_prd_10/"):
				rep = rep.lstrip("/opt/scg/scg1_prd_10/")
				rep = GBSC_DIR + rep
			if ".Eland" in rep:
				rep = rep.replace(".Eland","")
			basename = os.path.basename(rep)
			if "_eland" in basename:
				sample_conf.REPLICATES[count] = [elandToBamFileName(rep)]

	###NW End code to convert file names from eland to bam names.
	###


	###Nathaniel Watson. May 12, 2014.
  ### Now, need to check if BAM files exist. If so, good, otherwise, generate BAM files.
	###Currently, only support for making single-end mappings on the fly
#	if not paired_end:
#		if sample_conf:
			
	
	if paired_end:
		controls = control_conf.CONTROL_MAPPED_READS
		all_mapped_reads = controls[:]
#		print ("Controls: " +  str(controls) + "\n")
		if sample_conf:
			replicates = [x[0] for x in sample_conf.REPLICATES] #sample_conf.REPLICATE is a list of 1-item lists
#			print ("Replicates are: " + str(replicates) + "\n")
			all_mapped_reads.extend(replicates) 
		jobs = []
		forwardReadExt = "_forwardReads.bam"
		progressReadExt = "_forwardReads.bam.encours"
		for i in all_mapped_reads:
			frf = i.rstrip(".bam") + forwardReadExt		
			frf_progress = i.rstrip(".bam") + progressReadExt
			if os.path.exists(frf) or os.path.exists(frf_progress):
				bamDone = False
				countLimit = 5
				count = 0
				while count < countLimit:
					count += 1
					try:
						age = getFileAgeMinutes(frf)
					except IOError:
						age = 0
						try:
							progressFileAge = getFileAgeMinutes(frf_progress)
						except IoError:
							progressFileAge=0
						if (progressFileAge >= 20) or (progressfileAge == 0):
							raise Exception("Expected to find forward reads file {frf} since the progress sentinal file {frf_progress} is present, but unable to do so.".format(frf=frf,frf_progress=frf_progress))
						pass
					if age >= 20:
						bamDone = True
						break
					else:
						#sleep an hour
						time.sleep(600)
				if not bamDone:
					raise Exception("Waited too long for BAM file {} from other project to finish to finish being made. Exiting.".format(frf))
			else:
				print("Need to create a single-end reads only file from file {frf}.".format(frf=frf))
				cmd = "samtools view -hbF 0x40 {peFile} > {seFile}".format(peFile=i,seFile=frf)
				jobname = "toSingleEnd_{0}".format(os.path.basename(i))
				job = sjm.Job(jobname,cmd,modules = ["samtools"],queue=conf.QUEUE,memory="5G",sched_options="-m e")
				jobs.append(job)
		if jobs:
			submission = sjm.Submission(jobs=jobs,log_directory=log_dir,notify=SJM_NOTIFY)		
			sjmfile = os.path.join(log_dir, run_name + '_MakeSingleEndMappings.jobs')
			print ("Removing reverse reads in control and sample BAM files. Commands are in SJM file {sjmfile}".format(sjmfile=sjmfile))
			try:
				submission.run(sjmfile)
			except subprocess.CalledProcessError:
				raise

		control_conf.CONTROL_MAPPED_READS = [x.rstrip(".bam") + forwardReadExt for x in controls]
		sample_conf.REPLICATES = [ [x.rstrip(".bam") + forwardReadExt] for x in replicates]
	print ("Controls: " + "  ".join(control_conf.CONTROL_MAPPED_READS) + "\n")
	print ("Replicates: " + "  ".join([x[0] for x in sample_conf.REPLICATES]))

	print " archive results: ", archive_results
	jobs = []	

	sample = None
	if sample_conf:
		sample = Sample(sample_conf.RUN_NAME, sample_conf.RESULTS_DIR, sample_conf.TEMP_DIR, sample_conf.GENOME, [SampleReplicate(i+1, x)for i, x in enumerate(sample_conf.REPLICATES)], sample_conf)

	control_lock = peakcaller.USE_CONTROL_LOCK
	if no_control_lock:
		control_lock = False

	control = Control(control_conf.RUN_NAME, control_conf.RESULTS_DIR, control_conf.TEMP_DIR, control_conf.GENOME, control_conf.CONTROL_MAPPED_READS, control_conf, peakcaller.NAME)

	controlScored = False
	countLimit = 5
	count = 0
	while count < countLimit:
		count += 1
		scoreTime = checkControlScored(control)
		if not scoreTime:
			#means it returned False b/c control output file didn't exist, so never scored.
			break
		#otherwise, it returned a number of hours as a float that the control file has been untouched
		elif  scoreTime >= 1:
			controlScored = True
			break
		else:
			#sleep an hour
			time.sleep(3600)
	
	if not controlScored and count == countLimit:
		raise Exception("Waited too long for control scoring from other project to finish. Exiting.")

	doRescore = False
	if rescore_control and (scoreTime > rescore_control):
		doRescore = True
	elif (not scoreTime) or doRescore:
			peakcaller.form_control_files('form_control_files', control) #add job merge_and_filter_reads.py
			if archive_results:
				peakcaller.archive_control('archive_control', control,force=force)
				add_dependencies(control.jobs['form_control_files'], control.jobs['archive_control'])
			jobs += control.all_jobs()

###nathankw comment out below on 2014-06-08
#	if not control_scoring.check_for_control(results_dir=control_conf.RESULTS_DIR, peakcaller=control.peakcaller,use_control_lock=control_lock) or rescore_control:
#		try:
#			peakcaller.check_control_inputs(control) #checks that genome and BAMS of control exist
#			peakcaller.form_control_files('form_control_files', control) #add job merge_and_filter_reads.py
#			#The call below peakcaller.complete_control() adds the job complete_control_scoring.py if USE_CONTROL_LOCK is True, whose goal is to run the below command
#			# "UPDATE encode_controls SET ready=1 WHERE name='%s' AND peakcaller='%s'" % (results_dir, peakcaller)
#			#  Which menas that the control is now scored.
#			peakcaller.complete_control('complete_control', control) 
#			add_dependencies(control.jobs['form_control_files'], control.jobs['complete_control'])
#			if archive_results:
#				peakcaller.archive_control('archive_control', control,force=force)
#				add_dependencies(control.jobs['form_control_files'], control.jobs['archive_control'])
#			jobs += control.all_jobs()
#		except Exception, e:
#			import traceback
# 			print "error detected, removing control lock"
# 			traceback.print_exc()
# 			control_scoring.remove_lock(control.results_dir, control.peakcaller, control_lock)
# 			raise e
#	else:
#		print " Control %s already scored, skipping." % control.run_name

	if sample_conf:
		peakcaller.check_sample_inputs(sample,force=force)
		
		if remove_duplicates:
			print "rm dups"
			peakcaller.form_sample_files_nodups('form_sample_files', sample)
		else:
			print "no dups"
			peakcaller.form_sample_files('form_sample_files', sample)
		
		peakcaller.calc_pbc('calc_pbc', control, sample)
		peakcaller.run_name, emails))
	#jobs.append(peakcaller.cleanup(sample, control))
	
	if SNAP_RUN and sample_conf:
		scriptPath = os.path.join(scriptDir,"snap_support/production/current/peakseq_report_parser_wrapper.sh")
		snap_job = sjm.Job("SNAP", "bash " + scriptPath + " production %s >& %s/peakseq_report_out " % (sample_conf.path,sample_conf.RESULTS_DIR),  queue=QUEUE, project=PROJECT, host='localhost', dependencies=sample.all_jobs(), sched_options='-m e -A chipseq_scoring')
		jobs.append(snap_job)
				
	if control.jobs:
		peakcaller.prep_control(control)
	if sample.jobs:
		peakcaller.prep_sample(sample)

	
	#scoringStatusCmd="setScoringStatusProp.py --syapse-mode {syapseMode} -p scoringStatus --value Scored --unique-id {runName}".format(syapseMode=syapseMode,runName=runName))
	#scoringStatusJobName = run_name + "_setScoringStatusFlagToComplete"
	#job = sjm.Job(name=scoringStatusJobName,commands=scoringStatusCmd,modules=["gbsc/encode/prod"],dependencies=["mail_results"])
	#jobs.append(job)

	submission = sjm.Submission(jobs, log_directory=log_dir, notify=SJM_NOTIFY)
	if print_cmds:
		submission.build(run_name + '.jobs') 
		raise SystemExit(1)
	if log_dir:
		submission.run(os.path.join(log_dir, run_name + '.jobs'),foreground=True)
	else:
		submission.run(run_name + '.jobs',foreground=True)
	
	
if __name__ == '__main__':

	from optparse import OptionParser
	description = "Runs PeakSeq scoring pipeline for ChipSeq data. There are two positional arguments: 1) (Mandatory) The path to the control conf file, and 2) (Optional, but mostly used) The path to the sample conf file."
	parser = OptionParser(description=description)
	parser.add_option('--syapse-mode',help="(Required) A string indicating which Syapse host to use. Must be one of elemensts given in {knownModes}.".format(knownModes=SyapseUtils.Syapse.knownModes))
	parser.add_option("-f","--force",action="store_true",help="forces running of pipeline, even if results already exist")
	parser.add_option("-d","--no_duplicates",action="store_true",help="runs cross correlation analysis assuming duplicated reads have already been filtered out of the mapped reads.  Uncommon, so defaults to false.")
	parser.add_option("-a","--no_archive",action="store_false",dest="archive_results",help="do not archive the control and sample results.")
	parser.add_option("-p","--print",action="store_true",dest="print_cmds",help="prints the job commands, but does not dispatch them to the cluster")
	parser.add_option("-l","--log",dest="log_dir",default=None,help="log directory, current working directory if not specified")
	parser.add_option("-n","--name",dest="run_name",default="Pipeline",help="name for the pipeline run")
	parser.add_option("-m","--mail",action="append",dest="emails",help="email address to send summary and result location.")
	parser.add_option("-g","--genome")
	parser.add_option("-c","--peakcaller",default="macs2",help="specify the peakcaller to be used.  Current options are peakseq, macs,macs2, spp. Defaults to macs2.")
	parser.add_option("--snap",action="store_true",help="make a call to the SNAP LIMS after completion")
	parser.add_option("--rmdups",action="store_true",dest="remove_duplicates",help="Filter out all duplicate reads in sample read files before peakcalling.  Use when PCR amplification errors are present.  (i.e., PBC value is low)")
	parser.add_option("--paired_end",action="store_true",help="Indicates that the input BAM files are paired-end.  Since the pipeline can't support PE mappings, it will filter out the reverse reads from the BAM files.")
	parser.add_option("--rescore_control",default=0,type="int",help="The number of days old the control scoring should be in order for it to be rescored. This option is mainly used to rescore a control that is a paired-end (PE) and that was scored using all reads instead of just the forward reads.  So, this option would be helpfuf to used if the control is paired-end (PE). Up until May 2014, all scoring was done with both forward and reverse reads, so in order to rescore a control with just the forward reads, you'd wan't to incude the --paired-end option and set --rescore_control to the number of since since May 1, 2014.")
	parser.add_option("--no-control-lock",action="store_true")
	parser.add_option("--filtchr",help="SPP option to ignore a chromosome during analysis.  Used to fix bug that chrs with low read counts causes SPP to fail")

	options,arguments = parser.parse_args()
	syapseMode = options.syapse_mode
	if not syapseMode:
		parser.error("You must supply the --mode argument!")	

	peakcaller_options = {}
	xcorrelation_options = {}
	filtchr = options.filtchr
	if filtchr:
		if 'filtchr' in peakcaller_options:
			peakcaller_options['filtchr'].append(filtchr)
			xcorrelation_options['filtchr'].append(filtchr)
		else:
			peakcaller_options['filtchr'] = [filtchr,]
			xcorrelation_options['filtchr'] = [filtchr,]

	if len(arguments) < 1:
		parser.error("You must supply the control_conf_path argument. Optionally, the sample_conf_path may be specified as a 2nd argument.")
	control_conf = arguments[0]
	if len(arguments) > 1:
		sample_conf = arguments[1]
	else:
		sample_conf = None

	peakcaller = options.peakcaller
	if peakcaller == 'peakseq':
		import peakseq
		peakcaller_module = peakseq
	elif peakcaller == 'macs':
		import macs
		peakcaller_module = macs
	elif peakcaller == 'macs2':
		print 'running macs2 ...'
		import macs2
		peakcaller_module = macs2
	elif peakcaller == 'spp':
		import spp
		peakcaller_module = spp
	elif peakcaller == 'spp_nodups':
		import spp_nodups
		peakcaller_module = spp_nodups
	else:
		parser.error("Invalid Peakcaller selected.  Options are 'peakseq', 'macs', 'macs2',  'spp' or 'spp_nodups'")

	main(syapseMode,peakcaller_module, options.run_name, control_conf, sample_conf, options.print_cmds, options.log_dir, options.no_duplicates, options.archive_results, options.emails, peakcaller_options, xcorrelation_options, options.remove_duplicates,options.paired_end,options.force,options.rescore_control,options.genome,options.no_control_lock)
	syapse = SyapseUtils.Syapse(mode="prod")
	conn = syapse.connect()
	ai = conn.kb.retrieveAppIndividualByUniqueId(options.run_name)
	ai.scoringStatus.set("Scoring Completed")
	ai = conn.kb.saveAppIndividual(ai)
