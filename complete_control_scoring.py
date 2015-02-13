#!/bin/env python

import MySQLdb
import sys

import conf

MYSQL_PASSWORD_FILE = conf.MYSQL_PASSWORD_FILE
CONTROL_DB_HOST = conf.CONTROL_DB_HOST
CONTROL_DB_USER = conf.CONTROL_DB_USER
CONTROL_DB = conf.CONTROL_DB
CONTROL_DB_PORT = conf.CONTROL_DB_PORT

if __name__ == '__main__':
	if len(sys.argv) < 3:
		print "Usage:  complete_control_scoring.py <control_results_dir> <peakcaller>"
		raise SystemExit(64)
	
	results_dir = sys.argv[1]
	peakcaller = sys.argv[2]

	f = open(MYSQL_PASSWORD_FILE, 'r')
	passwd = f.readline().rstrip('\n')
	f.close()
	conn = MySQLdb.connect(host=CONTROL_DB_HOST, user=CONTROL_DB_USER, port=CONTROL_DB_PORT, passwd=passwd, db=CONTROL_DB)
	cursor = conn.cursor()
	
	sql = "UPDATE encode_controls SET ready=1 WHERE name='%s' AND peakcaller='%s'" % (results_dir, peakcaller)
	cursor.execute(sql)
	cursor.close()
	conn.commit()
