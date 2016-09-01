#!/usr/bin/env python

###
#Nathaniel Watson
#nathankw@stanford.edu
#2016-8-31
###

import os
import shutil
import glob
from argparse import ArgumentParser

description = ""

parser = ArgumentParser(description=description)
parser.add_argument('-d',"--directory",required=True,help="Scoring run directory")

args = parser.parse_args()

scoring_dir = args.directory
if not scoring_dir.startswith("/srv/gsfs0/projects/gbsc/SNAP_Scoring/production/replicates/human"):
	raise Exception("Disallowed path {}".format(scoring_dir))

inputs_dir = os.path.join(scoring_dir,"inputs")
results_dir = os.path.join(scoring_dir,"results")
tmp_dir = os.path.join(scoring_dir,"tmp")
idr_dir = os.path.join(inputs_dir,"idr")

for i in glob.glob(os.path.join(inputs_dir,"*")):
	basename = os.path.basename(i)
	if basename in ["sample.conf","snap_log.txt","pipeline.py_stderr.txt"]:
		continue
	if ".jobs" in basename:
		#don't delte, keep SJM job/status file.
		continue
	if os.path.isfile(i):
		print("Removing file {}.".format(i))
		#os.remove(i)
	else:
		print("Removing directory {}.".format(i))
		#shutil.rmtree(i)
		
if os.path.exists(tmp_dir):
	print("Removing directory {}.".format(tmp_dir))
	#shutil.rmtree(tmp_dir)

if os.path.exists(idr_dir):
	print("Removing directory {}.".format(idr_dir))
	#shutil.rmtree(idr_dir)

for i in glob.glob(os.path.join(results_dir,"*")):
	if os.path.isdir(i):
		print("Removing {}".format(i))
		#shutil.rmtree(i)






