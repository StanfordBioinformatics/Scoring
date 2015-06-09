from argparse import ArgumentParser

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

def cleanSyapseBarcode(barcode):
	"""
	Function : Syapse barcodes are prefixed with a number and a colon, i.e. 2:ATCGGA. This function
             strips off that number and colon prefix from the barcode.
	Args     : barcode - str.
	Returns  : str.
	"""
	barcode = barcode.split(":")
	if len(barcode) == 2:
		return barcode[1]
	else:
		return barcode[0]

def createSampleReplicateName(runName,lane,barcode):
	"""
	Function :
	Args     : runName - str. The name of a sequencing run.
						 lane    - str or int. Number of the lane sequencing. Must be a number w/o leading zeros.
						 barcode - str. The barcode sequenced on the lane.
	"""
	lane = str(lane)
	return runName + 	_"L" + lane + "_" + "pf.bam"

def generateControlName(scoringNameUid,controlLibraryName):
	"""
	Function : Generates a pseudo control name. This will serve as a directory name on the filesystem in which will contain the scorings results for the given control.
	Args     : scoringNameUid - str. The Syapse ChIP Seq Scoring Object's UID.
						 controlLibraryName -str. the Syapse "Record Name" for a given control library.
	Returns  :
	"""
	newName = scoringNameUid + controlLibraryName.rstrip("_",1)
	return newName


description = ""
parser = ArgumentParser(description=description)
parser.add_argument('-i','--infile',required=True,help="The tab-delimited file containing results from the Syapse query defined in the encode repository at encode/dcc_submit/SyapseUtils.getReadyToScore(). See documentation in that funciton for information on the format of the returned fields.")
parser.add_argument('-o','--outfile',required=True,help="The output file name that will be used as input into the batch scoring pipeline.")

args = parser.parse_args()

infile = args.infile
outfile = args.outfile

fh = open(infile,'r')
scorings = {} #Each key is a scoring run name (ChIP Seq Scoring UID), valued by a dict containing whose keys are all 
for line in fh:
	line = line.split("\t")
	scoringNameUid = line[0]
	expLibrary = line[1]
	expRunName = line[3]
	expLane = line[4]
	expBarcode = cleanSyapseBarcode(line[5])
	ctlLibraryUid = line[6]
	ctlRunName = line[8]
	ctlLane = line[9]
	ctlBarcode = cleanSyapseBarcode(line[10])
	ctlLibraryName = line[11]
	
	expReplicateName = createSampleReplicateName(runName=expRunName,lane=expLane,barcode=expBarcode)
	ctlReplicateName = createSampleReplicateName(runName=ctlRunName,lane=ctlLane,barcode=ctlBarcode)

	controlName = generateControlName(scoringNameUid=scoringNameUid,controlLibraryName=ctlLibraryName)
	if scoringNameUid not in scorings:
		scorings[scoringNameUid] = {"controlName": controlName,"expReplicates": [],"ctlReplicates": []}
	scorings[scoringNameUid]["expReplicates"].append(expReplicateName)
	scorings[scoringNameUid]["ctlReplicates"].append(ctlReplicateName)
	

fh.close()
fout = open(outfile,'w')
for s in scorings: #s is the scoring name
	control = s['control']
	ereps = s['expReplicates']
	creps = s['ctlReplicates']
	fout.write(s + "\t\t\t") #scoringName + 2 empty, nolonger used fields
	fout.write(ereps[0] + "\t") #must be at least one experiment replicate
	if len(ereps) > 1:
		fout.write(ereps[0] + "\t") #may have more than two reps, but pipeline only supports upto two replicates
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
	


