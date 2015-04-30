#!/srv/gs1/software/python/3.2.3/bin/python3

from argparse import ArgumentParser 
import subprocess
import os
import glob

parser = ArgumentParser()

parser.add_argument('-r','--run-name',required=True,help="Sequencing run name.")

args = parser.parse_args()
run = args.run_name

path = subprocess.Popen("getOldArchivePath.py {run}".format(run=run),shell=True,stdout=subprocess.PIPE).communicate()[0].strip()

os.chdir(path)
for i in range(1,9):
	lane = "L" + str(i)
	if not os.path.isdir(lane):
		os.mkdir(lane)
	for bam in glob.glob("*_{lane}_*.bam".format(lane=lane)):
		newName = os.path.join(lane,bam)
		os.rename(bam,newName)
	for bai in glob.glob("*_{lane}_*.bai".format(lane=lane)):
		newName = os.path.join(lane,bai)
		os.rename(bai,newName)
