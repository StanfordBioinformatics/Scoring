#!/srv/gs1/software/python/3.2.3/bin/python3

import sys
import os


archivePrefix = "/srv/gs1/projects/scg/Archive/IlluminaRuns/"

months = {
	"01":"jan",
	"02":"feb",
	"03":"mar",
	"04":"apr",
	"05":"may",
	"06":"jun",
	"07":"jul",
	"08":"aug",
	"09":"sep",
	"10":"oct",
	"11":"nov",
	"12":"dec"
}

archive = sys.argv[1]
date = archive.split("_")[0]
year = "20" + str(date[:2])
monthNum = str(date[2:4])
month = months[monthNum]

path = os.path.join(archivePrefix,year,month,archive)
print(path)
