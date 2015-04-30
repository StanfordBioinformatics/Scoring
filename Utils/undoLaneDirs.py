#!/srv/gs1/software/python/3.2.3/bin/python3

from argparse import ArgumentParser 
import subprocess
import os
import glob
import datetime

parser = ArgumentParser()

parser.add_argument('-r','--run-name',required=True,help="Sequencing run name.")

args = parser.parse_args()
run = args.run_name

path = subprocess.Popen("getOldArchivePath.py {run}".format(run=run),shell=True,stdout=subprocess.PIPE).communicate()[0].strip()

os.chdir(path)
for i in range(1,9):
	lane = "L" + str(i)
	if os.path.isdir(lane):
		reftime = datetime.datetime(2014,5,19)
		lanemtime = datetime.datetime.fromtimestamp(os.path.getmtime(lane))
		if lanemtime > reftime:
			print("Fixing stuff in run {}".format(run))
			for i in os.listdir(lane):
				i = os.path.join(os.getcwd(),lane,i)
				bname = os.path.basename(i)
				newname = os.path.join(os.getcwd(),bname)
				os.rename(i,newname)
			os.rmdir(lane)
