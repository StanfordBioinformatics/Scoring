"""Wrapper for simple job manager (sjm)"""

import subprocess
import os.path
import sys
import random
import time

SJM_COMMAND = 'sjm'

class Job:
	def __init__(self, name, commands, time=None, memory=None, queue=None, host=None, dependencies=None,modules = [], project=None, sched_options=None):
		self.name = name
		if not type(commands) is list:
			self.commands = [commands,]
		else:
			self.commands = commands
		self.time = time
		self.memory = memory
		self.modules = modules
		self.queue = queue
		self.host = host
		if not dependencies:
			self.dependencies = []
		else:
			self.dependencies = dependencies
		self.project = project
		self.sched_options = sched_options
		
	def job_definition(self):
		'''Returns a string with the job definition in sjm format'''
		output = 'job_begin\n'
		output += '  name %s\n' % self.name
		if self.modules:
			for mod in self.modules:
				output += "  module {mod}\n".format(mod=mod)
		if self.time:
			output += '  time %s\n' % str(self.time)
		if self.memory:
			output += '  memory %s\n' % str(self.memory)
		if self.queue:
			output += '  queue %s\n' % str(self.queue)
		if self.host:
			output += '  host %s\n' % str(self.host)
		if self.project:
			output += '  project %s\n' % str(self.project)
		if len(self.commands) == 1:
			output += '  cmd %s\n' % str(self.commands[0])
		else:
			output += '  cmd_begin\n'
			output += '    %s\n' % ' &&'.join(self.commands)
			output += '  cmd_end\n'

		output += '  sched_options %s\n' % str("-A chipseq_scoring")
		output += 'job_end\n'

		return output
		
	def add_dependency(self, job):
		self.dependencies.append(job)

	def add_module(module):
		self.modules.append(module)
		
	def dependency_definition(self):
		'''Returns a string with the dependency definition in sjm format'''
		output = ''
		for job in self.dependencies:
			output += 'order %s after %s\n' % (self.name, job.name)
		return output
		
	def __str__(self):
		return self.name
	
		
class Submission:
	def __init__(self, jobs, log_directory=None, notify=None):
		self.jobs = jobs
		self.log_directory = log_directory
		if not notify:
			self.notify = []
		elif not type(notify) == list:
			self.notify = [notify,]
		else:
			self.notify = notify
		
	def build(self, job_description_file):
		if not type(job_description_file) is file:
			job_description_file = open(job_description_file, 'w')
		for j in self.jobs:
			job_description_file.write(j.job_definition())
		for j in self.jobs:
			job_description_file.write(j.dependency_definition())
		if self.log_directory:
			job_description_file.write('log_dir %s\n' % self.log_directory)
		job_description_file.close()
		return job_description_file

	def run(self, job_description_file,foreground=False):
		"""Run sjm jobs. Wait for sjm to complete."""
		job_description_file = self.build(job_description_file)
		
		cmd = SJM_COMMAND
		if foreground:
			cmd += " -i"
		if self.log_directory:
			cmd += " -l %s " % os.path.join(self.log_directory, job_description_file.name + '.status.log')
		for n in self.notify:
			cmd += " --mail %s" % n
		print("Running sjm command '%s %s\n'" % (cmd,job_description_file.name))
		rand = str(random.random())
		curTime = time.time()
		ferr = open(str(curTime) + "_" + rand + "_sjm-run_stderr.txt","w")
		try:
			subprocess.check_call("%s %s" % (cmd, job_description_file.name), shell=True,stderr=ferr)
		except subprocess.CalledProcessError as e:
			msg = "Error with return code {retcode} while running command {cmd}:".format(retcode=e.returncode,cmd=e.cmd)
			msg += open(ferr.name,'r').read()
			sys.stderr.write(msg)
			raise
		finally:
			os.remove(ferr.name)


	
