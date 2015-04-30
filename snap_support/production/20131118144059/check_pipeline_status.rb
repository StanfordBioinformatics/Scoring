#######################################################################################################################################
class PipelineStatusChecker
  require 'rexml/document'
  require 'net/https'
  require 'uri'
  
  #***************************************************************************************************************************************  
  def initialize(environment, hostname, url, logfile_name)
    @logfile = nil
    @logfile_name = logfile_name
    @show_peakseq_request_url_suffix = "/api/peakseq_inputs/show?experiment_run_id="
    @show_running_peakseq_requests_url_suffix = "/api/peakseq_inputs/show_matching_peakseq_runs?status=Running+Analysis&set_status=false"    
    # @update_peakseq_request_results_url_suffix = "/api/peakseq_results/update"
    @update_scoring_request_status_url_suffix = "/api/peakseq_results/update_scoring_request_status"

    case environment
    when "development"
      @environment = environment
      @hostname = "localhost:3002"
      @root_url = "http://localhost:3002"
    when "staging"
      @environment = environment
      @hostname = hostname
      @root_url = url
    when "production"
      @environment = environment
      @hostname = hostname
      @root_url = url
    else
      die("No environment specified.  Options are: 'development', 'staging', and 'production'") 
    end  
  end
  
  #***************************************************************************************************************************************
  #Obtain current running pipeline/snap jobs
  #Check to see if the jobs are still running or have failed (parse sjm file)
  #Post updates to SNAP based upon the results  
  def check_for_failed_pipeline_jobs
    #Query SNAP for current Running Jobs
    doc = self.send_get_request_to_snap(@show_running_peakseq_requests_url_suffix)
    
    #Iterate through all jobs and parse their sjm log file
    #Check to see if a job has failed
    experiment_run_ids = self.parse_running_peakseq_runs(doc)
    for id in experiment_run_ids
      puts "Found Experiment Run ID"

      
      
      if self.check_job_failed(id)
        puts "Job #{id.to_s} has failed"
        
        #If the job failed, send a post to SNAP to update 
        params = Hash.new
        params["experiment_run[id]"] = id
        params["experiment_run[status]"] = "Scoring Failed"
        self.send_post_request_to_snap(@update_scoring_request_status_url_suffix, params)
        puts "Updated SNAP"
      else
        puts "Job #{id.to_s} is running fine"
      end
    end
  end # check_for_failed_pipeline_jobs()
  
  #***************************************************************************************************************************************
  def check_job_failed(id)
    doc = self.send_get_request_to_snap(@show_peakseq_request_url_suffix, id)
    self.initialize_logfile(doc)
    @logfile.syswrite("Checking status of Scoring Request: " + id.to_s + "\n")
    root = doc.root
    #Generate Peakseq Sample.conf input textfile
    if root.name == "peakseq_input"
      root_elem = root.elements
      
      #PRODUCTION
      #Check if File path and all parent directories exist, if not, then create them
      if !self.check_file_path_exists(root_elem['directory_list'].elements['sample_inputs_directory'].text)
        FileUtils.mkdir_p(root_elem['directory_list'].elements['sample_inputs_directory'].text)
      else
        puts "Exception: Directory " + root_elem['directory_list'].elements['sample_inputs_directory'].text + " already exists for this Run\n"
      end
      
      #Create and Initialize File
      sjm_file_path = root_elem['directory_list'].elements['sample_inputs_directory'].text + "/PeakSeq_#{id}_#{@environment}.jobs.status.log"
      
      sjm_file = File.new(sjm_file_path, "r") || die("Could not read SJM Log file")
      
      result = self.parse_pipeline_jobs_log(sjm_file)
      
      return result
    elsif root.name == "exception"
      @logfile.syswrite("Exception: #{root.elements['message'].text}")
      return nil
    else
      @logfile.syswrite("Error: Unrecognized response from SNAP API when accessing scoring request #{id}")
      return nil
    end
  end # check_job_failed()
  
  #***************************************************************************************************************************************
  #Parses the SJM jobs file for a particular scoring Request
  #Searches for:
  # 1) Scoring requests with at least one failed job
  # 2) Scoring Requests whose log files have not updated for at least XXXX amount of time
  def parse_pipeline_jobs_log(sjm_file)
    return_val = false
    last_time = Hash.new
    counter = 0
    while (line = sjm_file.gets)
      counter = counter + 1
      
      #Remove blank lines
      if line == "\n"
        next
        #Remove comment lines
      elsif line =~ /\A#.*\Z/
        next
      end
      
      if line =~ /\A(\w\w\w)\s(\w\w\w)\s(\d\d)\s(\d\d):(\d\d):(\d\d)\s(\d\d\d\d):\s(.+)\Z/
        #DEBUG
        # puts "***#{counter}: #{line}"
        #Calculate how much time has passed since previous message    
        last_time = Hash.new
        last_time["Day"] = $1
        last_time["Month"] = $2
        last_time["Date"] = $3
        last_time["Hour"] = $4
        last_time["Minute"] = $5
        last_time["Second"] = $6
        last_time["Year"] = $7  
      elsif line =~ /\AFailed jobs:\Z/
        puts "FOUND FAILED JOB!"
        return_val = true
      else
        puts "Could not parse this line"
      end
    end
    #DEBUG
    # puts "Day: #{last_time["Day"]}"
    # puts "Month: #{last_time["Month"]}"
    # puts "Date: #{last_time["Date"]}"
    # puts "Hour: #{last_time["Hour"]}"
    # puts "Minute: #{last_time["Minute"]}"
    # puts "Second: #{last_time["Second"]}"
    # puts "Year: #{last_time["Year"]}"    

    current_time = Time.now
    final_time = self.format_time(last_time)
    time_diff_limit = 15 + 60
    if self.is_time_diff_greater?(final_time, current_time, time_diff_limit)
      puts "TIME DIFFERENCE TOO BIG!"
      return_val = true
    end
    
    return return_val
  end  # parse_pipeline_jobs_log()
  
  #***************************************************************************************************************************************
  def format_time(time_hash, utc_offset=nil)
    if utc_offset.nil?
      utc_offset = "+08:00"
    end
    
    formatted_time = Time.mktime(time_hash["Year"], time_hash["Month"], time_hash["Date"], time_hash["Hour"], time_hash["Minute"], time_hash["Second"], utc_offset)
    
    return formatted_time
  end # format_time()

  #***************************************************************************************************************************************
  def is_time_diff_greater?(start_time, end_time, time_diff_limit)
    time_diff = end_time - start_time
    
    #DEBUG
    # puts "Time Diff limit: #{time_diff_limit}"
    # puts "Time Difference: #{time_diff}"
    if time_diff > time_diff_limit
      return true
    else 
      return false
    end
  end # is_time_diff_greater?()
    
  
  #***************************************************************************************************************************************
  #Generates Sample.conf file for Peakseq
  def parse_running_peakseq_runs(doc)
    experiment_run_ids = Array.new
    root = doc.root
    #Generate Peakseq Sample.conf input textfile
    if root.name == "peakseq_runs"
      #root_elem = root.elements

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
  def initialize_logfile(doc)
    root = doc.root
    #Generate Peakseq Sample.conf input textfile
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
      @logfile.syswrite("Log file Path: #{logfile_path}\n")

    elsif root.name == "exception"
      puts "Exception: #{root.elements['message'].text}"
      # @logfile.syswrite("Exception: #{root.elements['message'].text}")
      return nil
    else
      puts "Unrecognized response"
      # @logfile.syswrite("Unrecognized response")
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
    end

    res = Net::HTTP.start(@hostname) {|http|  
    # res = Net::HTTP.start("www.scg-snap-new.stanford.edu") {|http|  
      
      http.get(full_url_suffix)
    }
    doc = REXML::Document.new(res.body)
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

end # class PipelineStatusChecker


#######################################################################################################################################
class OptparsePipelineStatusChecker
  #Class that parses command line options
  require 'optparse'
  require 'optparse/time'
  require 'ostruct'

  #***************************************************************************************************************************************
  # Build & Return a structure describing the command line options.
  def self.parse(args)
    options = OpenStruct.new
    # options.environment = :staging
    options.logfile = "/check_pipeline_status.log"

    opts = OptionParser.new do |opts|
      opts.banner = "Usage: ruby check_pipeline_status.rb [options]"
      opts.separator ""
      opts.separator "Specific options:"

      # Optional argument with keyword completion.
      opts.on("-e", "--environment [TYPE]", [:development, :staging, :production],
      "Mandatory environment type (development, staging, or production)") do |e|
        options.environment = e
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
    raise OptionParser::MissingArgument if options.hostname.nil?
    raise OptionParser::MissingArgument if options.url.nil?
    
    return options
  end # parse()

end # class OptparsePipelineStatusChecker


#######################################################################################################################################  
# begin Main()

#Parse command line args
options = OptparsePipelineStatusChecker.parse(ARGV)

#Build new PeakseqCaller and then execute
pipeline_checker = PipelineStatusChecker.new(options.environment.to_s, options.hostname.to_s, options.url.to_s, options.logfile.to_s)
pipeline_checker.check_for_failed_pipeline_jobs

# end Main()
