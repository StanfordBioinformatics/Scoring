#######################################################################################################################################
class PeakseqCaller
  require 'net/http'
  require 'rexml/document'
  require 'fileutils'
  require 'uri'
  #DESCRIPTION
  #Calls SNAP's API to retrieve Peakseq Input data
  #Receives data in XML, parses XML
  #Creates control.conf and sample.conf files required for peakseq
  #Calls Peakseq

  #***************************************************************************************************************************************
  #Initialize PeakseqCaller Object
  attr_reader :force
  def initialize(environment, peakseq_executable, hostname, url, logfile_name,paired_end=false,force=false,rescore_control=false,genome=false,no_control_lock=false)
		@genome = genome
		@no_control_lock = no_control_lock
		@rescore_control = rescore_control
		@force = force
		@paired_end = paired_end
    @logfile = nil
    @logfile_name = logfile_name
    @show_peakseq_request_url_suffix = "/api/peakseq_inputs/show?experiment_run_id="
    # @show_unscored_peakseq_requests_url_suffix = "/api/peakseq_inputs/show_unscored_peakseq_runs"
    @show_unscored_peakseq_requests_url_suffix = "/api/peakseq_inputs/show_matching_peakseq_runs?status=Awaiting+Scoring&set_status=true"
    @update_peakseq_request_results_url_suffix = "/api/peakseq_results/update"
    @update_scoring_request_status_url_suffix = "/api/peakseq_results/update_scoring_request_status"

    case environment
    when "development"
      @environment = environment
      @peakseq_executable = peakseq_executable
      @hostname = "localhost:3002"
      @root_url = "http://localhost:3002"
      @control_conf_file_path = "."
      @sample_conf_file_path = "."
      @run_info_file_path = "."
    when "staging"
      @environment = environment
      @peakseq_executable = peakseq_executable
      @hostname = hostname
      @root_url = url
      @control_conf_file_path = ""
      @sample_conf_file_path = ""
      @run_info_file_path = ""
    when "production"
      @environment = environment
      @peakseq_executable = peakseq_executable
      @hostname = hostname
      @root_url = url
      @control_conf_file_path = ""
      @sample_conf_file_path = ""
      @run_info_file_path = ""
    else
      die("No environment specified.  Options are: 'development', 'staging', and 'production'") 
    end
  end # initialize()

  #***************************************************************************************************************************************
  #Obtain all uninitialized Scoring Requests and Run analysis on them  
  

	def runPeakseqWithoutSnapUpdates(experiment_run_id,snap=false)
		#Author: Nathen Watson; Date: April 25, 2014
		#	This expectst he run ids to exist in snap, and it will fetch information from snap about those runs.
		#	However, it will not perform any updates in snap. Useful for doing reruns when it's not desired to overwite anything on snap.
		doc = self.send_get_request_to_snap(@show_peakseq_request_url_suffix, experiment_run_id)
		root_elem = doc.root.elements
		if @genome: 
			#if I manually reset the genome, then I need to update all fields that are in the doc.  See example doc at http://scg-snap.stanford.edu/api/peakseq_inputs/show?experiment_run_id=388.
			#	I'm guessing that this doc is created based on the snap request in the LIMS.
			root_elem['genome_build'].text=(@genome)
			root_elem['mappability_file'].text=("/srv/gs1/apps/snap_support/production/current/#{@genome}.txt")
		end
#		puts root_elem['genome_build'].text
#		puts root_elem['genome_build'].methods.sort
		self.initialize_logfile(doc)
		puts "Initialized Logfile"
		@logfile.syswrite("Initializing Peakseq for Scoring Request: " + experiment_run_id.to_s + "\n")
    sample_config_file_path = self.generate_sample_conf_file(doc)
    control_config_file_path = self.generate_control_conf_file(doc)
		input_directory_path = self.get_input_directory(doc)
		self.generate_run_info_file(doc)
		self.run_peakseq(doc, sample_config_file_path, control_config_file_path, input_directory_path,snap=snap)
	end

  def run_scoring_requests
    doc = self.send_get_request_to_snap(@show_unscored_peakseq_requests_url_suffix)
    experiment_run_ids = self.parse_unscored_peakseq_runs(doc)
    for id in experiment_run_ids
      params = Hash.new
      params["experiment_run[id]"] = id
      params["experiment_run[status]"] = "Received Scoring Request Information"
      self.send_post_request_to_snap(@update_scoring_request_status_url_suffix, params)

      self.call_peakseq(id)

      params = Hash.new
      params["experiment_run[id]"] = id
      params["experiment_run[status]"] = "Running Analysis"
      @logfile.syswrite("Sending second Status update to SNAP\n")
      self.send_post_request_to_snap(@update_scoring_request_status_url_suffix, params)
    end
  end # run_scoring_jobs()

  #***************************************************************************************************************************************
  #Initializes logfile for single run
  #Generates sample.conf and control.conf file
  #Runs Peakseq Analysis Job
  def call_peakseq(experiment_run_id)
    puts "Sending GET request for Scoring Request: #{experiment_run_id}"
    doc = self.send_get_request_to_snap(@show_peakseq_request_url_suffix, experiment_run_id)
    self.initialize_logfile(doc)
    puts "Initialized Logfile"
    @logfile.syswrite("Initializing Peakseq for Scoring Request: " + experiment_run_id.to_s + "\n")
    sample_config_file_path = self.generate_sample_conf_file(doc)
    control_config_file_path = self.generate_control_conf_file(doc)
    run_info_file_path = self.generate_run_info_file(doc)
    #Hack to run Peakseq in specified folder so that peakseq log files are stored in the correct directory
    input_directory_path = self.get_input_directory(doc)

    #Kick off the Peakseq Analysis Job
    self.run_peakseq(doc, sample_config_file_path, control_config_file_path, input_directory_path,snap=true)

  end # call_peakseq()  

  #***************************************************************************************************************************************
  #Builds up Peakseq executable command, then executes it
  #Note: Semi-Hardcoded
  def run_peakseq(doc, sample_config_file_path, control_config_file_path, input_directory_path,snap=true)
    #Build up Peakseq Command
    root = doc.root
    root_elem = root.elements

    cmd = "python "
    cmd += @peakseq_executable
    #DEPRECATED
    # cmd = "/srv/gs1/projects/scg/Scoring/pipeline/pipeline.py"
    cmd += " -n " + root_elem['name'].text
    cmd += " -l " + input_directory_path.to_s
    
    analysis_type = root_elem['analysis_type'].text
    analysis_type = analysis_type.downcase
    cmd += " -c " + analysis_type
	  
		if snap
    	cmd += " --snap"
		end

		if @no_control_lock
			cmd += " --no-control-lock"
		end
	
		if @rescore_control
			cmd += " --rescore_control"
		end

		if @paired_end
			cmd += " --paired_end"
		end

		if @genome
			cmd += " --genome #{@genome}"
		end

		if @force:
			cmd += " --force"
		end
    #Parse Users/Emails    
    all_user_elements = doc.elements.to_a( "//user" )
    for i in 0..all_user_elements.length-1
      all_email_elements = all_user_elements[i].elements.to_a( "./email" )
      for j in 0..all_email_elements.length-1
        cmd += " -m " + all_email_elements[j].text
      end
    end

    cmd += " " + control_config_file_path
#		puts "Control config file path: #{control_config_file_path}"
    cmd += " " + sample_config_file_path
    ##Nathaniel Watson - added peakseq_logfile and tee'd output
		peakseq_logfile = File.join(File.dirname(@logfile.path),File.basename(@peakseq_executable) + "_stdout.txt")
		peakseq_errfile = File.join(File.dirname(@logfile.path),File.basename(@peakseq_executable) + "_stderr.txt")
		cmd += " 2>#{peakseq_errfile} | tee #{peakseq_logfile}"

    @logfile.syswrite("Peakseq Command: " + cmd + "\n")

#		puts "Command is: #{cmd}"
    system(cmd)
    #stdout = `#{cmd}`
    #@logfile.syswrite(stdout)
    #@logfile.syswrite("\n")
  end # run_peakseq()

  #***************************************************************************************************************************************
  #Generates Sample.conf file for Peakseq
  def generate_run_info_file(doc)
    root = doc.root
    #Generate Peakseq Sample.conf input textfile
    if root.name == "peakseq_input"
      root_elem = root.elements

      #Create and Initialize File
      run_info_file_path = root_elem['directory_list'].elements['sample_inputs_directory'].text + "/run_info.snap"
      @logfile.syswrite("SNAP Run Info File Path: #{run_info_file_path}\n")

      #PRODUCTION
      #Check if File path and all parent directories exist, if not, then create them
      if !self.check_file_path_exists(root_elem['directory_list'].elements['sample_inputs_directory'].text)
        FileUtils.mkdir_p(root_elem['directory_list'].elements['sample_inputs_directory'].text)
      else
        # @logfile.syswrite("Exception: Directory already exists for this Run\n")
      end
      run_info_file = File.new(run_info_file_path, "w+") || die("Could not create run_info.snap file")


      #Parse Peakseq Sample Parameters
      run_info_file.syswrite("[Scoring_Request]\n")
      run_info_file.syswrite("run_name=#{root_elem['unique_name'].text}\n")
      run_info_file.syswrite("run_id=#{root_elem['run_id'].text}\n")
      run_info_file.syswrite("control_results_dir=#{root_elem['directory_list'].elements['control_results_directory'].text}\n")
      run_info_file.syswrite("results_dir=#{root_elem['directory_list'].elements['sample_results_directory'].text}\n")
      #Parse Peakseq Sample Parameters      
      run_info_file.syswrite("temporary_dir=#{root_elem['directory_list'].elements['sample_temporary_directory'].text}\n")

      #Parse the Eland Extended files for this control
      all_replicate_elements = doc.elements.to_a( "//replicate" )
      for i in 0..all_replicate_elements.length-1
        all_lane_elements = all_replicate_elements[i].elements.to_a( "./lane" )
        num = i + 1
        run_info_file.syswrite("[Replicate=Rep#{num.to_s}]\n")
        run_info_file.syswrite("rep_name=Rep#{num.to_s}\n")
        run_info_file.syswrite("snap_name=#{all_replicate_elements[i].elements['name'].text}\n")
        run_info_file.syswrite("unique_name=#{all_replicate_elements[i].elements['unique_name'].text}\n")
        run_info_file.syswrite("rep_id=#{all_replicate_elements[i].elements['id'].text}\n")
        for j in 0..all_lane_elements.length-1
          run_info_file.syswrite("flowcell_lane=")
          run_info_file.syswrite(all_lane_elements[j].elements['sequencing_run_name'].text)
          run_info_file.syswrite(",")
          run_info_file.syswrite(all_lane_elements[j].elements['lane_number'].text)
        end
        run_info_file.syswrite("\n")
      end

      return run_info_file_path

    elsif root.name == "exception"
      @logfile.syswrite("Exception: #{root.elements['message'].text}")
      return nil
    else
      @logfile.syswrite("Unrecognized response")
      return nil
    end
  end # generate_run_info_file()

  #***************************************************************************************************************************************
  #Generates the control.conf file for Peakseq
  def generate_control_conf_file(doc)
    root = doc.root
    #Generate Peakseq Control.conf input textfile
    if root.name == "peakseq_input"
      root_elem = root.elements

      #Create File
      control_conf_file_path = root_elem['directory_list'].elements['control_inputs_directory'].text + "/control.conf" 
      @logfile.syswrite("Control Conf File Path: #{control_conf_file_path}\n")

      #PRODUCTION
      #Check if File path and all parent directories exist, if not, then create them
      if !self.check_file_path_exists(root_elem['directory_list'].elements['control_inputs_directory'].text)
        FileUtils.mkdir_p(root_elem['directory_list'].elements['control_inputs_directory'].text)
      else
        @logfile.syswrite("Control Directory already exists for this Run\n")
      end
      controlFile = File.new(control_conf_file_path, "w+") || die("Could not create control.conf file")
      #DEVELOPMENT
      #self.check_file_path_exists("/Users/alwon/scg/rails/peakseq_inputs")
      #controlFile = File.new("/Users/alwon/scg/rails/test_junk/peakseq_inputs/control.conf", "w+") || die("Could not create control.conf file")

      #Initialize File
      controlFile.syswrite("[peakseq]\n")
      controlFile.syswrite("control_mapped_reads = ")
      all_control_elements = doc.elements.to_a( "//control" )

      #Parse the Eland Extended files for this control
      for i in 0..all_control_elements.length-1
        all_eland_elements = all_control_elements[i].elements.to_a( "./eland_extended_file" )
        first_flag = 1
        for j in 0..all_eland_elements.length-1
          if first_flag == 0
            controlFile.syswrite(",")
          end
          controlFile.syswrite(all_eland_elements[j].text)
          first_flag = 0
        end
        controlFile.syswrite("\n")
      end

      #Parse Directories
      controlFile.syswrite("results_dir = #{root_elem['directory_list'].elements['control_results_directory'].text}\n")
      controlFile.syswrite("temporary_dir = #{root_elem['directory_list'].elements['control_temporary_directory'].text}\n")
      #Parse Run Name and Genome Build
      controlFile.syswrite("run_name = #{root_elem['control'].elements['control_unique_name'].text}_control\n")
      controlFile.syswrite("genome = #{root_elem['genome_build'].text}\n")     

      return control_conf_file_path 
    elsif root.name == "exception"
      @logfile.syswrite("Exception: #{root.elements['message'].text}")
      return nil
    else
      @logfile.syswrite("Unrecognized response")
      return nil
    end 
  end # generate_control_conf_file()

  #***************************************************************************************************************************************
  #Generates Sample.conf file for Peakseq
  def generate_sample_conf_file(doc)
    root = doc.root
    #Generate Peakseq Sample.conf input textfile
    if root.name == "peakseq_input"
      root_elem = root.elements

      #Create and Initialize File
      sample_conf_file_path = root_elem['directory_list'].elements['sample_inputs_directory'].text + "/sample.conf"
      @logfile.syswrite("Sample Conf File Path: #{sample_conf_file_path}\n")

      #PRODUCTION
      #Check if File path and all parent directories exist, if not, then create them
      if !self.check_file_path_exists(root_elem['directory_list'].elements['sample_inputs_directory'].text)
        FileUtils.mkdir_p(root_elem['directory_list'].elements['sample_inputs_directory'].text)
      else
        # @logfile.syswrite("Exception: Directory already exists for this Run\n")
      end
      sampleFile = File.new(sample_conf_file_path, "w+") || die("Could not create sample.conf file")
      #DEVELOPMENT
      # self.check_file_path_exists("/Users/alwon/scg/rails/peakseq_inputs")
      # sampleFile = File.new("/Users/alwon/scg/rails/test_junk/peakseq_inputs/sample.conf", "w+") || die("Could not create sample.conf file")


      #Parse Peakseq Sample Parameters
      sampleFile.syswrite("[general]\n")
      sampleFile.syswrite("run_name = #{root_elem['name'].text}\n")
      sampleFile.syswrite("control_results_dir = #{root_elem['directory_list'].elements['control_results_directory'].text}\n")
      sampleFile.syswrite("results_dir = #{root_elem['directory_list'].elements['sample_results_directory'].text}\n")
      sampleFile.syswrite("genome = #{root_elem['genome_build'].text}\n")   
      sampleFile.syswrite("mappability_file = #{root_elem['mappability_file'].text}\n")
      sampleFile.syswrite("q_value_thresholds = ")

      #Parse QValues    
      first_flag = 1
      all_q_value_elements = doc.elements.to_a( "//q_value" )
      for i in 0..all_q_value_elements.length-1
        if first_flag == 0
          sampleFile.syswrite(",")
        end
        sampleFile.syswrite(all_q_value_elements[i].text)
        first_flag = 0
      end
      sampleFile.syswrite("\n")
      #Parse Peakseq Sample Parameters      
      sampleFile.syswrite("temporary_dir = #{root_elem['directory_list'].elements['sample_temporary_directory'].text}\n")
      sampleFile.syswrite("bin_size = #{root_elem['bin_size'].text}\n")
      sampleFile.syswrite("peakseq_binary = #{root_elem['peakseq_binary'].text}\n")

      #Parse the Eland Extended files for this control
      all_replicate_elements = doc.elements.to_a( "//replicate" )
      for i in 0..all_replicate_elements.length-1
        all_eland_elements = all_replicate_elements[i].elements.to_a( "./eland_extended_file" )
        num = i + 1
        sampleFile.syswrite("\n[replicate" + num.to_s + "]\n")
        sampleFile.syswrite("mapped_reads = ")
        first_flag = 1
        for j in 0..all_eland_elements.length-1
          if first_flag == 0
            sampleFile.syswrite(",")
          end
          sampleFile.syswrite(all_eland_elements[j].text)
          first_flag = 0
        end
        sampleFile.syswrite("\n")
      end
      sampleFile.syswrite("\n")

      return sample_conf_file_path

    elsif root.name == "exception"
      @logfile.syswrite("Exception: #{root.elements['message'].text}")
      return nil
    else
      @logfile.syswrite("Unrecognized response")
      return nil
    end
  end # generate_sample_conf_file()

  #***************************************************************************************************************************************
  def initialize_logfile(doc)
    root = doc.root
    #Generate Peakseq Sample.conf input textfile
    puts root.name
#		puts root
    if root.name == "peakseq_input"
      root_elem = root.elements

      #Create and Initialize File
      logfile_path = root_elem['directory_list'].elements['sample_inputs_directory'].text + @logfile_name.to_s

      #PRODUCTION
      #Check if File path and all parent directories exist, if not, then create them
      if !self.check_file_path_exists(root_elem['directory_list'].elements['sample_inputs_directory'].text)
        FileUtils.mkdir_p(root_elem['directory_list'].elements['sample_inputs_directory'].text)
      else
        puts "Exception: Directory " + root_elem['directory_list'].elements['sample_inputs_directory'].text + " already exists for this Run\n"
        # @logfile.syswrite("Exception: Directory " + root_elem['directory_list'].elements['sample_inputs_directory'].text + " already exists for this Run\n")
      end
      @logfile = File.new(logfile_path, "w+") || die("Could not create Log file")
			puts "Log file path: #{@logfile.path}"
      @logfile.syswrite("Log file Path: #{logfile_path}\n")

      #DEVELOPMENT
      # logfile_dir = "/Users/alwon/scg/rails/peakseq_inputs"
      # logfile_path = logfile_dir + @logfile_name
      # if !self.check_file_path_exists(logfile_dir)
      #   FileUtils.mkdir_p(logfile_dir)
      # else
      #   puts "Exception: Directory " + logfile_dir + " already exists for this Run\n"
      # end
      # @logfile = File.new(logfile_path, "w+") || die("Could not create Log file")
      # @logfile.syswrite("Log file Path: #{sample_conf_file_path}\n")
    elsif root.name == "exception"
      # puts "Exception: #{root.elements['message'].text}"
      @logfile.syswrite("Exception: #{root.elements['message'].text}")
      return nil
    else
      # puts "Unrecognized response"
      @logfile.syswrite("Unrecognized response")
      return nil
    end
  end # initialize_logfile()

  #***************************************************************************************************************************************
  #Sends a HTTP GET request to the SNAP API
  #URL specified by instance variable @root_url, url_suffix, and (possibly) resource_id
  #If resource_id is nil, it will be excluded from url construction
  def send_get_request_to_snap(url_suffix, resource_id=nil)
    if resource_id.nil?
      full_url_suffix = url_suffix
    else
      full_url_suffix = url_suffix + resource_id.to_s
			#i.e. http://scg-snap.stanford.edu/api/peakseq_inputs/show?experiment_run_id=388
    end
#		puts "##{full_url_suffix}#"
#		puts "##{@hostname}##"
    res = Net::HTTP.start(@hostname) {|http|  
      http.get(full_url_suffix)
    }
#		puts res
    doc = REXML::Document.new(res.body)
#		puts doc
    return doc

  end # get_request_to_snap_api()

  #***************************************************************************************************************************************
  #Sends a HTTP POST request to the SNAP API
  #URL specified by instance variable @root_url, url_suffix, and (possibly) resource_id
  #If resource_id is nil, it will be excluded from url construction  
  def send_post_request_to_snap(url_suffix, params, resource_id=nil)
    #Post Data
    if resource_id.nil?
      host_url = @root_url + url_suffix
    else
      host_url = @root_url + url_suffix + resource_id.to_s
    end

    uri = URI.parse(host_url) 
    http = Net::HTTP.new(uri.host, uri.port)

    request = Net::HTTP::Post.new(uri.request_uri)
    request.set_form_data(params)
    response = http.request(request)

  end # post_request_to_snap_api()

  #***************************************************************************************************************************************
  #Generates Sample.conf file for Peakseq
  def parse_unscored_peakseq_runs(doc)
    experiment_run_ids = Array.new
    root = doc.root
    #Generate Peakseq Sample.conf input textfile
    if root.name == "peakseq_runs"

      all_experiment_run_id_elements = doc.elements.to_a( "//experiment_run_id" )
      for i in 0..all_experiment_run_id_elements.length-1
        experiment_run_ids[i] = all_experiment_run_id_elements[i].text
      end
      return experiment_run_ids
    elsif root.name == "exception"
      @logfile.syswrite("Exception: #{root.elements['message'].text}")
      return nil
    else
      @logfile.syswrite("Unrecognized response")
      return nil
    end  

  end # parse_unscored_peakseq_runs_xml()

  #***************************************************************************************************************************************
  #Hack to run Peakseq in specified folder so that log files are stored in the correct directory
  def get_input_directory(doc)
    root = doc.root
    #Generate Peakseq Sample.conf input textfile
    if root.name == "peakseq_input"
      root_elem = root.elements

      #Create and Initialize File
      input_directory_path = root_elem['directory_list'].elements['sample_inputs_directory'].text

      return input_directory_path
    end

  end # get_input_directory()

  #***************************************************************************************************************************************
  def check_file_path_exists(file_path)
    if File.directory?(file_path)
      return true
    else
      return false
    end
  end # check_file_path_exists()

  #***************************************************************************************************************************************
  def die(message)
    @logfile.syswrite(message)
    exit 1
  end # die()

end # class PeakseqCaller



#######################################################################################################################################
class OptparseSnapPeakseqCaller
  #Class that parses command line options
  require 'optparse'
  require 'optparse/time'
  require 'ostruct'

  #***************************************************************************************************************************************
  # Build & Return a structure describing the command line options.
  def self.parse(args)
    options = OpenStruct.new
    options.logfile = "/snap_peakseq_caller.log"

    opts = OptionParser.new do |opts|
      opts.banner = "Usage: ruby snap_peakseq_caller.rb [options]"
      opts.separator ""
      opts.separator "Specific options:"
	

			opts.on("--genome") do |genome|
				options.genome = genome
			end

			opts.on("--no-control-lock") do 
				options.no_control_lock = true
			end

			opts.on("--paired_end","Indicates that the input BAM files are paired-end.") do |pe|
				options.paired_end = true
			end

			opts.on("--rescore_control","Rescore controls if any were already scored.") do |rescore_control|
				options.rescore_control = true
			end

      # Optional argument with keyword completion.
      opts.on("-e", "--environment [TYPE]", [:development, :staging, :production],
      "Mandatory environment type (development, staging, or production)") do |e|
        options.environment = e
      end

      # Mandatory argument.
      opts.on("-p", "--peakseq PEAKSEQ_EXECUTABLE",
      "Mandatory path to the peakseq executable") do |peakseq_executable|
        options.peakseq_executable = peakseq_executable
      end
      
      # Mandatory argument.
      opts.on("-h", "--hostname HOSTNAME",
      "Mandatory web hostname") do |hostname|
        options.hostname = hostname
      end
      
      # Mandatory argument.
      opts.on("-u", "--url WEB_URL",
      "Mandatory url to the website") do |url|
        options.url = url
      end

      # Mandatory argument.
      opts.on("-l", "--logfile LOGFILE_NAME",
      "Require the path to the log file") do |logfile|
        options.logfile << logfile
      end

      # List of arguments.
      opts.on("-m", "--manual_request ID1,ID2,..", Array, "Switch to manual mode, Running Peakseq on the Scoring Request IDs provided.  Will override auto-checking for list of scoring requests.") do |list|
        options.manual_request = list
      end

      opts.separator ""
      opts.separator "Common options:"
      # No argument, shows at tail.  This will print an options summary.
      # Try it and see!
      opts.on_tail("-h", "--help", "Show this message") do
        puts opts
        exit
      end
    end

    opts.parse!(args)
    raise OptionParser::MissingArgument if options.environment.nil?
    raise OptionParser::MissingArgument if options.peakseq_executable.nil?
    raise OptionParser::MissingArgument if options.hostname.nil?
    raise OptionParser::MissingArgument if options.url.nil?
    
    return options
  end # parse()

end # class OptparseSnapPeakseqCaller



#######################################################################################################################################  
# begin Main()

#Parse command line args
if __FILE__ == $0
	options = OptparseSnapPeakseqCaller.parse(ARGV)
	#Build new PeakseqCaller and then execute
	peakseq_caller = PeakseqCaller.new(environment=options.environment.to_s,peakseq_executable=options.peakseq_executable.to_s,hostname=options.hostname.to_s,url=options.url.to_s,logfile_name=options.logfile.to_s,paired_end=options.paired_end,force=options.force,rescore_control=options.rescore_control,genome=options.genome,no_control_lock=options.no_control_lock)
	peakseq_caller.run_scoring_requests
	# end Main()
end
