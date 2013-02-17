#!/bin/env python

import subprocess
import os
import sys

import sjm
import conf

QUEUE = conf.QUEUE
BIN_DIR = conf.BIN_DIR
MYSQL_PASSWORD_FILE = conf.MYSQL_PASSWORD_FILE
CONTROL_DB_HOST = conf.CONTROL_DB_HOST
CONTROL_DB_USER = conf.CONTROL_DB_USER
CONTROL_DB = conf.CONTROL_DB
CONTROL_DB_PORT = conf.CONTROL_DB_PORT

def query_control_db(conn, name, peakcaller):
	'''Checks MySQL control DB to check control scoring status.
	
	Args:
		conn:  Open MySQLdb connection to control DB
		name:  Control name (usually the results directory)
	Returns:
		-1 if there is no scoring for this control
		0 if there is a scoring in progress
		1 if there is a completed scoring
	'''
	cursor = conn.cursor()
	sql = "SELECT ready FROM encode_controls WHERE name='%s' AND peakcaller='%s'" % (name, peakcaller)
	cursor.execute(sql)
	result = cursor.fetchone()
	conn.commit()
	if not result:
		return -1
	return int(result[0])
	
def complete_control_db(conn, name, peakcaller):
	'''Updates Control status to completed.'''
	
	cursor = conn.cursor()
	sql = "UPDATE encode_controls SET ready=1 WHERE name='%s' AND peakcaller='%s'" % (name, peakcaller)
	cursor.execute(sql)
	conn.commit()
	
def wait_for_control(conn, name, peakcaller):
	'''Waits until control scoring is completed.
	
	Args:
		conn:  Open MySQLdb connection to control DB
		name:  Control name (usually the results directory)
		peakcaller:  Peak calling pipeline used (e.g. peakseq, macs)
	'''
	import time
	running_time = 0
	while(query_control_db(conn, name, peakcaller) < 1):
		print "Waiting for %s to finish scoring.  Time waited:  %i sec" % (name, running_time)
		running_time += 300
		if running_time > 120000:
			raise Exception("Maximum waiting time reached.  Control scoring for %s appears stuck."  % name)
		time.sleep(60)
	print "%s is finished scoring."  % name

def check_for_control(results_dir, peakcaller, use_control_lock=True):
	if not use_control_lock:
		return False
	import MySQLdb
	f = open(MYSQL_PASSWORD_FILE, 'r')
	passwd = f.readline().rstrip('\n')
	f.close()
	conn = MySQLdb.connect(host=CONTROL_DB_HOST, user=CONTROL_DB_USER, port=CONTROL_DB_PORT, passwd=passwd, db=CONTROL_DB)
	control_status = query_control_db(conn, results_dir, peakcaller)
	if control_status == 1:
		return True
	elif control_status == 0:
		wait_for_control(conn, results_dir, peakcaller)
		return check_for_control(results_dir, peakcaller)
	else:
		try:
			sql = "INSERT INTO encode_controls SET name='%s', ready=0, peakcaller='%s'" % (results_dir, peakcaller)
			cursor = conn.cursor()
			cursor.execute(sql)
			cursor.close()
			conn.commit()
			return False
		except Exception, e:
			# Insert failed, probably because of racing condition
			print e
			conn.rollback()
			wait_for_control(conn, results_dir, peakcaller)
			return True
			
def remove_lock(results_dir, peakcaller, use_control_lock=True):
	if not use_control_lock:
		return
	import MySQLdb
	f = open(MYSQL_PASSWORD_FILE, 'r')
	passwd = f.readline().rstrip('\n')
	f.close()
	conn = MySQLdb.connect(host=CONTROL_DB_HOST, user=CONTROL_DB_USER, port=CONTROL_DB_PORT, passwd=passwd, db=CONTROL_DB)
	if query_control_db(conn, results_dir, peakcaller) == 0:
		try:
			sql = "DELETE FROM encode_controls WHERE name='%s' AND peakcaller='%s'" % (results_dir, peakcaller)
			cursor = conn.cursor()
			cursor.execute(sql)
			cursor.close()
			conn.commit()
		except Exception, e:
			print e
			conn.rollback()
	