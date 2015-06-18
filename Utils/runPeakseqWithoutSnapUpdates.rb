#!/usr/bin/ruby
#
require 'optparse'
require 'ostruct'
require 'json'

confFh = File.open("conf.json","r")
conf = JSON.load(confFh)
sampleRunPath = conf["scoringPathPrefix"]["sample"]
notifyEmail = conf["email"]["to"][0]

#require 'snap_peakseq_caller'

options = OpenStruct.new
options.rescore_control = 0
#options.genome = "hg19_male"

opt_parser = OptionParser.new do |opts|
	
#	opts.on("-i","--id ID") do |idd|
#		options.idd = idd
#	end
	
	opts.on("--name NAME") do |name|
		options.run_name = name
	end

	opts.on("--control CONTROL") do |control|
		options.control = control
	end
#	opts.on("--control-conf CONTROL_CONF") do |cconf|
#		options.cconf = cconf
#	end

#	opts.on("--sample-conf SAMPLE_CONF") do |sconf|
#		options.sconf = sconf
#	end

#	opts.on("--genome GENOME") do |genome|
#		options.genome = genome
#	end

	opts.on("--snap") do
		options.snap = true
	end

	opts.on("--force") do
		options.force = true
	end

	opts.on("--paired-end") do 
		options.paired_end = true
	end

	opts.on("--rescore-control DAYS") do |days|
		options.rescore_control = days.to_i
	end

#	opts.on("--purge-inputs-dir") do 
#		options.purge_inputs_dir = true
#	end
	
	opts.on("--no-control-lock") do
	#for when pipeline.py calls control_scoring.check_for_control()
		options.no_control_lock = true
	end
end

opt_parser.parse!(ARGV)

#if options.purge_inputs_dir
#	directory = "/srv/gs1/projects/scg/SNAP_Scoring/production/replicates/human/MACS_#{options.idd}_production/inputs"
#	if File.directory?(directory)
#		ret=`rm -rf #{directory}`
#		Dir.mkdir(directory)
#	end
#end

#ps = PeakseqCaller.new(environment=ENV['SNAP_ENVIRONMENT'], peakseq_executable=ENV['SNAP_PEAKSEQ_EXECUTABLE'], hostname=ENV['SNAP_HOSTNAME'], url=ENV['SNAP_URL'],logfile_name="/snap_peakseq_caller.log", paired_end=options.paired_end,,force=options.force,rescore_control=options.rescore_control,genome=options.genome,no_control_lock=options.no_control_lock)

#ps.runPeakseqWithoutSnapUpdates(experiment_run_id=options.idd,snap=options.snap)

#generate command for pipeline.py

runName = options.run_name
control = options.control
sampDir = "/srv/gsfs0/projects/gbsc/SNAP_Scoring/production/replicates/human/#{runName}"
sampInputsDir = "#{sampDir}/inputs"
controlDir = "/srv/gsfs0/projects/gbsc/SNAP_Scoring/production/controls/human/#{control}"
sampConf = "#{sampInputsDir}/sample.conf"
controlConf = "#{controlDir}/inputs/control.conf"
#scfh = File.open(sampConf,'r')
#scfh.each_line do |line|
#	line.chomp!
#	if line.start_with?("run_name")
#  if line.starts_with?("
#		line = line.split("=")[1]
#		line.strip!
#		runName = line
#	end
#end


stdout = "#{sampInputsDir}/pipeline.py_stdout.txt"
stderr = "#{sampInputsDir}/pipeline.py_stderr.txt"
snapLog = "#{sampInputsDir}/snap_log.txt"

pythonCmd = "python /srv/gs1/projects/scg/Scoring/pipeline2/pipeline.py -c macs -m trupti@stanford.edu -m scg_scoring@lists.stanford.edu -n #{runName} -l #{sampInputsDir}"
#if snap
#	pythonCmd += " --snap"
#end 

#if options.no_control_lock
#	pythonCmd += " --no-control-lock"
#end 

if options.rescore_control > 0
	pythonCmd += " --rescore_control=#{options.rescore_control}"
end 

if options.paired_end
	pythonCmd += " --paired_end"
end 

#if options.genome
pythonCmd += " --genome hg19_male"
#end 

if options.force:
	pythonCmd += " --force"
end 

pythonCmd += " #{controlConf} #{sampConf}"
pythonCmd += " 2> #{stderr}"
putToLog = "echo #{pythonCmd} >> #{snapLog}"
system(putToLog)

t = Time.new #current time
timeVal = t.year.to_s + "-" + t.month.to_s + "-" + t.day.to_s 
#set scoring status of ChIP Seq Scoring object in Syapse to "Running Analysis"
qsubCmd = "qsub -sync y -wd #{sampleRunPath} -m ae -M #{notifyEmail} #{pythonCmd}"
putToLog = "echo #{qsubCmd} >> #{snapLog}"
system(putToLog)

#system() runs a command in a subshell. Returns true if the command gives zero exit status, false for non zero exit status. 
# Returns nil if command execution fails. An error status is available in $?. The arguments are processed in the same way as for Kernel.spawn.

#update Syapse's Chip Seq Scoring object's Scoring Status attribute to 'Running Analysis'
res = system(qsubCmd)
puts $?.to_i
if not res or $?.to_i  > 0 #if res is nil, nil.to_i = 0
	puts "Error running '#{qsubCmd}'. Tried to run command in runPeakseqWithoutSnapUpdates.rb."
	exit(1)
end

#t2 = Time.new
#tw = t.year.to_s + "-" + t.month.to_s + "-" + t.day.to_s
#system("echo 'Start Time: #{t}' >> #{snapLog}")
#system("echo 'End Time: #{t2}' >> #{snapLog}")
#python /srv/gs1/projects/scg/Scoring/pipeline2/pipeline.py -n GM12878_Bmi1NBP196140_Score_14Jun03_102907 -l /srv/gs1/projects/scg/SNAP_Scoring/production/replicates/human/MACS_390_production/inputs -c macs --rescore_control --paired_end --genome hg19_male --force -m trupti@stanford.edu -m scg_scoring@lists.stanford.edu /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine1_Control516/inputs/control.conf /srv/gs1/projects/scg/SNAP_Scoring/production/replicates/human/MACS_390_production/inputs/sample.conf 2>/srv/gs1/projects/scg/SNAP_Scoring/production/replicates/human/MACS_390_production/inputs/pipeline.py_stderr.txt | tee /srv/gs1/projects/scg/SNAP_Scoring/production/replicates/human/MACS_390_production/inputs/pipeline.py_stdout.txt")
#
