import os
import re
from argparse import ArgumentParser
import conf


controlScoringPrefixPath = conf.controlScoringPrefixPath
sampleScoringPrefixPath = conf.sampleScoringPrefixPath

class ScoringRun(object):
	"""
	Parses all the results that normally end-up in an email when the scoring pipeline runs. In the scoring pipeline, the contents of the email are stored in a file called full_results.txt within the results directory of the run. I'm parsing the same stuff here, but from the raw result files that were used to build the full_results.txt report.
	"""
	numReg = re.compile(r'\d+$')
	def __init__(self,runName):
		self.runName = runName	
		self.repDir = os.path.join(sampleScoringPrefixPath,runName)
		self.sampleConfFile = os.path.join(self.repDir,"inputs","sample.conf")
		self.sampleConf = parseConfFile(self.sampleConfFile)
		self.controlConfFile = self.sampleConf['general']['control_results_dir'].rstrip("results") + "inputs/control.conf" 
		self.controlConf = parseConfFile(self.controlConfFile)
		resultsDir = os.path.join(self.repDir,"results")
		self.sppFile = os.path.join(resultsDir,'spp_stats.txt')
		if not os.path.exists(self.sppFile):
			raise OSError("Can't locate spp stats file that was expected to be at '{sppFile}'".format(sppFile=self.sppFile))
		self.sppStats = self.parseSppStats()
		self.idrFile = os.path.join(resultsDir,'idr_results.txt')
		if not os.path.exists(self.idrFile):
			raise OSError("Can't locate idr results file that was expected to be at '{idrFile}'".format(idrFile=self.idrFile))
		self.idrStats = self.parseIdrStats()
#RepStats WILL NOT BE IMPLEMENTED. Trupti only uses this for herself, and it's not clear whether snap even stores this informaiton. It's not used for DCC upload
#		self.repStatsFile = os.path.join(resultsDir,"rep_stats")
#		self.repStats = False
#		if not os.path.exists(self.repStatsFile):
#			if repStats:
#				raise OSError("Can't locate rep stats file that was expected to be at '{repStatsFile}'".format(repStatsFile=self.repStatsFile))
#			self.repStatsFile = False
#		else:
#			self.repStats = self.parseRepStats()
		self.pbcStatsFile = os.path.join(resultsDir,"pbc_stats.txt")
		if not os.path.exists(self.pbcStatsFile):
			raise OSError("Can't locate pbc stats file that was expected to be at '{pbcStatsFile}'".format(pbcStatsFile=pbcStatsFile))
		self.pbcStats = self.parsePbcStats()


	def parsePbcStats(self):
		"""
		Function : Parses the same information that is reported in the section called 'PBC Results' in the full_results.txt report, but from the raw results file pbc_stats.txt.
							 Parses the results from the pbc_stats.txt file. Not sure what the 3 fields for each rep line mean, but I know the last field equals
               the first field divided by the second field.
               Each line gives pbc results for a single replicate. For experiment run SK-N-SH_IRF3_SC-9082_rep1vs2, the pbc_stats.txt file contains (header line not incluted in file):
			
								Replicate_Number	Genomic_Locations(Read 1)	Genomic_Locations(Total Mapped)	Percent_of_One_Read_Maps
		  					Rep1	9784754	  13256811	0.738092592555
		  					Rep2	15174859	17573090	0.863528212739

		Returns : dict. For the input given in the Function description, the return object would like like this:

							{ 1 : {
                      "one_read": 9784754,
                      "total_mapped": 13256811,
										  "perc_one_read": 0.738092592555
										},
								2 : {'
											"one_read": 15174859,
											"total_mapped": 17573090,
											"perc_one_read": 0.863528212739
										}
							}	

		"""
		if not self.pbcStatsFile:
			return {}
		dico = {}
		fh = open(self.pbcStatsFile,'r')
		for line in fh:
			line = line.strip("\n")
			if not line:
				continue
			line = line.split("\t")
			rep = int(line[0].lstrip("Rep"))
			dico[rep] = {}
			dico[rep]["one_read"] = int(line[1])
			dico[rep]["total_mapped"] = int(line[2])
			dico[rep]["perc_one_read"] = float(line[3])
		return dico
		

#	def parseRepStats(self):
#		"""
#		WILL NOT BE IMPLEMENTED. Trupti only uses this for herself, and it's not clear whether snap even stores this informaiton. It's not used for DCC upload.
#
#		Function : Parses the same information that is reported in the section called 'Replicate Statistics' in the full_results.txt report, but from the raw results file rep_stats.
#		Returns  : dict
#		"""

#		if not self.repStatsFile:
#			return {}
#
#		stats = {}
#
#		def getRepName(line):
#			repName = line.split("=")[1].split("=")[0]
#			repName = int(self.numReg.search(repName).group())
#			if repName not in stats:
#				stats[repName] = {}
#			return repName
#
#		fh = open(self.repStatsFile,'r')
#		for line in fh:
#			line = line.strip()
#			if not line:
#				continue
#			line = line.split("\t")
#			if line[0].startswith("num_reads"):
#				repName = getRepName(line)
#				stats[repName]['uniqMr'] = line.split("=",2)[-1]
#			elif line[0].startswith("read_files"):
#				repName = getRepName(line)
#				stats[repName]['readFiles'] = " ".join(line.split("=",2)[-1])
#			elif line[0].startswith("num_reads=RepAll"):
#				val = int(line[0].split("="))


	def parseIdrStats(self):
		"""
		Function : Parses the same information that is reported in the section called 'IDR Consistency Results' in the full_results.txt report, but from the raw results idr_results.txt.  
		Returns  : dict. For example, for an example with two replicates, we can look at the experiment run HeLa-S3_ARID3A_NB100-279. The idr_results.txt file for that run contains the lines:

								Rep1_VS_Rep2=374
								Rep1_PR1_VS_PR2=273
								Rep2_PR1_VS_PR2=5145
								RepAll_PR1_VS_PR2=3080

							The resulting dict would be:
	
		{
		  "vs":              { 1: 
														{ 2: 374},
		                     },

		  "selfConsistency": { 1: 273,
                           2: 5145
                         },

		  "pooled":          3080
		}


							Whenever a key is a replicate number and the value is a dict whose keys are also replicate numbers, the former key will be the smaller of the replicate numbers.

		"""
		SELFC_KEY = "selfConsistency"
		idr = {}
		fh = open(self.idrFile,'r')
		for line in fh:
			line = line.strip()
			if not line:
				continue
			val = int(line.split("=")[-1])
			if line.startswith("RepAll"):
				idr["pooled"] = val #Pooled Self Consistency (#hits)
			else:
				repName = line.split("_")[0]
				repNumber = int(self.numReg.search(repName).group())
				if line.startswith(repName + "_PR1_VS_PR2"):  #then it's a self-consistency score
					if SELFC_KEY not in idr:
						idr[SELFC_KEY] = {}
					idr[SELFC_KEY][repNumber] = val	
				elif line.startswith(repName + "_VS_"): #then it's a replicate v. another replicate
					otherRepName = line.split("_VS_")[1].split("=")[0]
					otherRepNumber = int(self.numReg.search(otherRepName).group())
					if "vs" not in idr:
						idr['vs'] = {}
					smallestRepNumber = min(repNumber,otherRepNumber)
					largestRepNumber = max(repNumber,otherRepNumber)
					if smallestRepNumber not in idr['vs']:
						idr['vs'][smallestRepNumber] = {}
					idr['vs'][smallestRepNumber][largestRepNumber] = val
				else: raise ValueError("Unknown result line {line} in file {idrFile}".format(line=line,idrFile=self.idrFile))
		return idr


	def parseSppStats(self):
		"""
		Function : Parses the same information that is reported in the section called 'Cross Correlation Analysis' in the full_results.txt report, 
							 but from the raw results file spp_stats.txt.
		Returns  : dict. The keys of the dict are the replicate names as integers.  For example, in the file from which the information is parsed, 
							 replicate names begin with the string 'Rep' followeb by a number. I only use the number portion to idenify the replicate. The 
							 value of each of these replicate name key is a nested dict. See example below for what the keys are in the nested dict.

		Example:   The returned dict would like below for the first replicate (not that I only indicate the data-type in place of values in the nested-dict., 
               and it would be the same for the 2nd replicate. Other replicates would be in the dict in the same manner.
	
							 { 1: {
                      'uniqMr'            : int,   #num uniquely mapped reads
											'est_frag_len'      : int,   #estimated fragment length
										  'corssCorrVal'      : float, #cross-correlation value
                      'phantomPeak'       : int,   #phantom peak
											'phantomPeakCorr'   : float, #phantom peak correlation
											'lowestStrandShift' : int,   #lowest strand shift
                      'minCrossCorr       : float, #min. cross-correlation
                      'nsc'               : float, #Normalized Strand Cross-Correlation Coefficient 
							        'rsc'               : float, #Relative Strand Cross-Correlation Coefficient
                      'qualityTag'        : int    #quality tag
										}
							} 
		"""
		spp = {}
		fh = open(self.sppFile,'r')
		for line in fh:
			line = line.strip("\n")
			if not line:
				continue
			if not line.startswith("Rep"):
				raise ValueError("Unknown line {line} in file {sppFile} - Replicate name at start of line does not begin with 'Rep'".format(line=line,sppFile=self.sppFile))
			line = line.split()
			repName = line[0].lstrip("Rep")
			repName = repName.rstrip(".tagAlign")
			repName = int(repName)
			spp[repName] = {}
			spp[repName]['uniqMr'] = int(line[1]) #num uniquely mapped reads
			#NOTE for the estimated fragment length field below, sometimes I see this value as a single int, sometimes a series of 3 ints. For an example of what I'm talking about,
			#  see the full_report.txt file of experiment run SK-N-SH_IRF3_SC-9082_rep1vs2. I will only take the first int, as it appears that is the only one that snap takes.
			spp[repName]['est_frag_len'] = int(line[2].split(",")[0])   #estimated fragment length. Can be one or several comma-delimited ints.
			spp[repName]['crossCorrVal'] = float(line[3].split(",")[0])   #cross-correlation value(s). Can be one or several comma-delimited floats. I'll only take the first one as 
                                               # it appears that that's the only one that snap uses.
			spp[repName]['phantomPeak'] = int(line[4]) #phantom peak
			spp[repName]['phantomPeakCorr'] = float(line[5]) #phantom peak correlation
			spp[repName]['lowestStrandShift'] = int(line[6]) #lowest strand shift`
			spp[repName]['minCrossCorr'] = float(line[7]) #min. cross-correlation 
			spp[repName]['nsc'] = float(line[8]) #Normalized Strand Cross-Correlation Coefficient
			spp[repName]['rsc'] = float(line[9]) # Relative Strand Cross-Correlation Coefficient
			spp[repName]['qualityTag'] = int(line[10]) #quality tag
		fh.close()
		return spp	


def parseConfFile(confFile):
	"""
	FUNCTION:
	This method can be used to parse both the sample conf file and the control conf file. For examples of these files, see 
	/srv/gsfs0/projects/gbsc/SNAP_Scoring/production/replicates/human/SK-N-SH_IRF3_SC-9082_rep1vs2/inputs/sample.conf and 
	/srv/gsfs0/projects/gbsc/SNAP_Scoring/production/controls/human/SK-N-SH_Rabbit_IgG/inputs/control.conf, respectively. The sample.conf file as it exists at
	now (9/4/2014) contains sections containing configuration lines particular to that section. A section is delcared at the start of a line and is of the form "[tag]",
    where "tag" is the section name.

  Sections in sample.conf:
    The sample.conf contains a "general" section and a section for each replicate.  Replicate sections begin with the word "replicate",
	and are followed by a replicate number (i.e. [replicate1] is the section for replicate number 1. There is a replicate section for each sample replicate.

	Sections in control.conf:
	The control.conf contains a single section, which is called "peakset".

	Regarding both the sample.conf and the control.conf, each line within a section contains a key and value pair, separated by an "=" sign.
	
	ARGS: confFile - path to a sample or control configuration file
	RETURNS: dict. Each key in the dict is a section that was parsed in the conf file. All keys in the dict are the same as the section names found in the conf file,
                   with the exception of replicate sections, which only have the replicate number forming the key.  The value of each section key in the dict is another dict, 
								 where the keys are the same as the keys found within a section of the conf file, and the values are the same as the key's values in the conf file.
	"""
	sections = {}
	sectionReg = re.compile(r'^\[(\w+)\]')
	splitReg = re.compile(r'\s*=\s*')
	fh = open(confFile,'r')
	section = "unknown"
	for line in fh:
		line = line.strip()
		if not line:
			continue
		if sectionReg.match(line):
			section = sectionReg.match(line).groups()[0]
			if section.startswith("replicate"):
				section = int(section.lstrip("replicate")) #only keep integer ID part
			sections[section] = {}
		else:
			key,val = splitReg.split(line)
			sections[section][key] = val
	return sections


if __name__ == "__main__":
	description = "Parses all the results that normally end-up in an email when the scoring pipeline runs. In the scoring pipeline, the contents of the email are stored in a file called full_results.txt within the results directory of the run. I'm parsing the same stuff here, but from the raw result files that were used to build the full_results.txt report."
	parser = ArgumentParser(description=description)
	parser.add_argument('-r','--run-name',required=True,help="The name of the scoring run (directory name w/o leading directory path).")
	#parser.add_argument('--no-rep-stats',action="store_false",help="Presence of this option indicates that there aren't any sample replicates, hence, no replicates statistics can be generated.")
	
	args = parser.parse_args()
	runName = args.run_name
	#noRepStats = args.no_rep_stats
	s = ScoringRun(runName=runName)
