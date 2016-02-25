
import os

import syapse_scgpm
from gbsc_utils import gbsc_utils


def cleanLane(lane):
	"""
	Function : Given a sequencing lane, removes any non-integer prefix, including leading zeros. 
	Args     : lane - str.
	Returns  : str.
	Ex       ; cleanLane("L01") #returns "1"
	"""
	lane = lane.lstrip("L")
	lane = lane.lstrip("0")
	return lane

def createSampleReplicateName(runName,lane,barcode):
	"""
	Function : With the given arguments, contstructs a BAM file name using the file-naming logic from the inhouse sequencing analysis pipeline that uses APF.
	Args     : runName - str. The name of a sequencing run.
						 lane    - str or int. Number of the lane sequencing. Must be a number w/o leading zeros.
						 barcode - str. The barcode sequenced on the lane.
	Example : Given runName="150619_TENNISON_0369_AC7CM2ACXX", lane=1, barcode="GATCAG"
						Returns "150619_TENNISON_0369_AC7CM2ACXX_L1_GATCAG_pf.bam".
	"""
	lane = str(lane)
	return runName + 	"_L" + lane + "_" + barcode + "_pf.bam"

def generateControlName(scoringNameUid,controlLibraryName):
	"""
	Function : Generates a pseudo control name. This will serve as a directory name on the filesystem in which will contain the scorings results for the given control.
	Args     : scoringNameUid - str. The Syapse ChIP Seq Scoring Object's UID.
						 controlLibraryName -str. the Syapse "Record Name" for a given control library.
	Returns  :
	"""
	#print("###" + controlLibraryName + "###")
	newName = scoringNameUid + "_" + controlLibraryName.rsplit("_",1)[0]
	#print("###" + newName + "###")
	return newName


def convertAllQueryRows(rows):
	"""
	Function : Converts the records from the query issued in getScoringsReadyFromSyapse() to a dictionary structure that can be easily used to create a file formatted for scoring input to the scoring pipeline.
	Args     : rows - a list of lists, where each sublist represents a row returned from the query executed in getScoringsReadyFromSyapse(). Basically, 'rows' is the output of a call to that function.
	Returns  : scorings - dict. with keys being the scoring run name. The value of each key is another dict. with keys 'controlName' (the name of the control), 'expReplicates' (a list of experiment sample replicate names), and
												'ctlReplicates' (a list of control sample replicate names). Note that the controlName is a generated name that convertQueryResultRecord() creates with a call to generateControlName(). Recall that each
												 control replicate is typically a different replicate of the same control, and that in Sypase the library 'record name' for a given control is the control name with the suffix number appended.
	"""
	scorings = {} #Each key is a scoring run name (ChIP Seq Scoring UID), valued by a dict containing whose keys are all 
	for row in rows:
		conversion = convertQueryResultRecord(record=row)
		scoringRunName = conversion["scoringRunName"]
		expReplicateName = conversion["expReplicateName"]
		ctlReplicateName = conversion["ctlReplicateName"]
		ctlName = conversion["ctlName"]
		if scoringRunName not in scorings:
			scorings[scoringRunName] = {"ctlName": ctlName,"expReplicates": [],"ctlReplicates": []}
		scorings[scoringRunName]["expReplicates"].append(expReplicateName)
		scorings[scoringRunName]["ctlReplicates"].append(ctlReplicateName)
	return scorings

def convertQueryResultRecord(record):
	"""
	Function : Converts an individual record (row) from the result of the query issued in getScoringsReadyFromSyapse() to a dictionary.
	Args     : record - list representing one of the rows returned by getScoringsReadyFromSyapse().
	Returns  : dict. with the structure defined below, where the key is given on the left side, and the data type and definition on the right.
							"scoringRunName"   : str. The name of the scoring run
							"expReplicateName" : str. The name of the experiment sample replicate
							"ctlReplicateName" : str. The name of the control sample replicate
							"ctlName"          : str. The name of the control.
	"""
	scoringNameUid = record[0]
	#expLibraryUid = record[1] #not needed
	expRunName = record[3]
	expLane = record[4]
	expBarcode = syapse_scgpm.al.processSyapseBarcode(record[5])
	#ctlLibraryUid = record[6] #not needed
	ctlRunName = record[8]
	ctlLane = record[9]
	ctlBarcode = syapse_scgpm.al.processSyapseBarcode(record[10])
	ctlLibraryName = record[11]
	
	#constrution bam file name as used by seq_center pipeline
	expReplicateName = createSampleReplicateName(runName=expRunName,lane=expLane,barcode=expBarcode)
	ctlReplicateName = createSampleReplicateName(runName=ctlRunName,lane=ctlLane,barcode=ctlBarcode)

	ctlName = generateControlName(scoringNameUid=scoringNameUid,controlLibraryName=ctlLibraryName)
	conversion = {"scoringRunName": scoringNameUid, "expReplicateName": expReplicateName, "ctlReplicateName": ctlReplicateName, "ctlName": ctlName}
	return conversion


if __name__ == "__main__":
	import logging
	import sys
	from argparse import ArgumentParser
	description = "Either performs a query against Syapse to get all Scoring Requests that are with status 'Awaiting Scoring', or accepts an input file with all the scoring requests that need to be scored. When no input file is supplied, the former occurs, queyring Syapse with the function call syapse_scgpm.syapseQueries.getScoringsReady(). See the documentation of that function for details about the fields returned for each result. When infile is supplied, it must have tab delimited fields, where each line represents a row returned by the query in the function just mentioned. An output file is created with the query results transformed into the format that the scoring pipeline understands for batch input. Finally, the scoring pipeline can optionally be initiated when the --run-pipeline option is provided."
	parser = ArgumentParser(description=description)
	parser.add_argument('-i','--infile',help="The tab-delimited file containing results from the Syapse query defined in syapse_scgpm.syapseQueries.getScoringsReady(). See documentation in that funciton for information on the format of the returned fields.")
	parser.add_argument('-o','--outfile',required=True,help="The output file name that will be used as input into the batch scoring pipeline. If this file exists already, it will be overwritten.")
	parser.add_argument('-m','--mode',required=True,choices=list(syapse_scgpm.syapse.Syapse.knownModes.keys()),help="Mode indicating which Syapse host account to use.")
	parser.add_argument('-r','--run-pipeline',action="store_true",help="Presence of this option indicates to initiate the scoring pipeline after the query data has been formatted to that which the pipeine requires batch input.")
	
	args = parser.parse_args()
	infile = args.infile
	outfile = args.outfile
	outfileDirectory = os.path.dirname(os.path.realpath(outfile))
	outputDirectory = os.path.dirname(outfile)
	mode = args.mode
	runPipeline = args.run_pipeline

	logger = logging.getLogger(__name__)
	logger.setLevel(logging.DEBUG)
	ch= logging.StreamHandler(sys.stdout)
	ch.setLevel(logging.DEBUG)
	f_formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:   %(message)s')
	ch.setFormatter(f_formatter)
	logger.addHandler(ch)	

	syapse = syapse_scgpm.al.Utils(mode=mode)

	if infile:
		fh = open(infile,'r')
		allLines = fh.readlines() # list of strings.
		allLines = [x.rstrip("\n") for x in allLines] 
		allLines = [x.split("\t") for x in allLines if x.strip()] #-> list of lists
		conversion = convertAllQueryRows(allLines)
		fh.close()

	else:
		logger.info("Querying Syapse for experiments ready to be scored.")
		queryResultRows = syapse.kb.executeSyQLQuery(syapse_scgpm.syapseQueries.getScoringsReady(mode=mode)).rows
		logger.info("Query Results:")
		logger.debug(queryResultRows)
		conversion = convertAllQueryRows(queryResultRows)

	fout = open(outfile,'w')
	for s in conversion: #s is the scoring name
		control = conversion[s]['ctlName']
		ereps = conversion[s]['expReplicates']
		creps = conversion[s]['ctlReplicates']
		fout.write(s + "\t\t\t") #scoringName + 2 empty, nolonger used fields
		fout.write(ereps[0] + "\t") #must be at least one experiment replicate
		if len(ereps) > 1:
			fout.write(ereps[1] + "\t") #may have more than two reps, but pipeline only supports upto two replicates
		else:
			fout.write("\t\t")
		fout.write(control + "\t")
		fout.write(creps[0] + "\t") #must be at least one control replicate
		if len(creps) > 1:
			fout.write(creps[1] + "\t")
		else:
			fout.write("\t\t")
		fout.write("\n")
	fout.close()
		
	if runPipeline:
		curTime = gbsc_utils.getCurTime() #year-month-day.hour.minute.second
		needsBamsFileName = os.path.join(outfileDirectory,curTime + "_scoringsNeedingBams.txt")
		readyToScoreFileName = os.path.join(outfileDirectory,curTime + "_readyToScore.txt")
		logger.info("Generating the conf files for the sample and control")
		cmd = "python generateSampAndControlConfs.py	-i {outfile} -s {readyToScoreFileName} -b {needsBamsFileName} ".format(outfile=fout.name,readyToScoreFileName=readyToScoreFileName,needsBamsFileName=needsBamsFileName)
		logger.info(cmd)
		stdout,stderr = gbsc_utils.createSubprocess(cmd=cmd,checkRetcode=True)
		logger.info("Starting the batch scoring pipeline")
		cmd = "batchScore.py -i {infile} -p --syapse-mode {mode}".format(infile=readyToScoreFileName,mode=mode)
		logger.info(cmd)
		stdout,stderr = gbsc_utils.createSubprocess(cmd=cmd,checkRetcode=True)
