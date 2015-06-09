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


description = ""
parser = ArgumentParser(description=description)
parser.add_argument('-i','--infile',required=True,help="The tab-delimited file containing results from the Syapse query defined in the encode repository at encode/dcc_submit/SyapseUtils.getReadyToScore(). See documentation in that funciton for information on the format of the returned fields.")

args = parser.parse_args()

infile = args.infile
fh = open(infile,'r')
scorings = {} #Each key is a scoring run name (ChIP Seq Scoring UID), valued by a dict containing whose keys are all 
for line in fh:
	line = line.split("\t")
	scoringName = line[0]
	expLibrary = line[1]
	expRunName = line[3]
	expLane = line[4]
	expBarcode = cleanSyapseBarcode(line[5])
	ctlLibrary = line[6]
	ctlRunName = line[8]
	ctlLane = line[9]
	ctlBarcode = cleanSyapseBarcode(line[10])
	
	expReplicateName = createSampleReplicateName(runName=expRunName,lane=expLane,barcode=expBarcode)
	ctlReplicateName = createSampleReplicateName(runName=ctlRunName,lane=ctlLane,barcode=ctlBarcode)

	experiment = {
		"expReplicateName": expReplicateName,
		"ctlReplicateName": ctlReplicateName,
	}
	
	if scoringName not in scorings:
		scorings[scoringName] = {"library":"","experiments": []}
	if not in scorings[scoringName]["library"]:
		scorings[scoringName]["library"] = ctlLibrary
	else:
		if ctlLibrary != scorings[scoringName]["library"]:
			raise Exception("Error processing scoring request {scoringName}: The control library between control replicates differs!".format(scoringName=scoringName))
	scorings[scoringName][ctlLibrary] = experiment
	


