#######################################################################################################################################
class PeakseqReportParser
  require 'rexml/document'
  require 'net/https'
  require 'uri'
  require 'pp'


  #***************************************************************************************************************************************
  # def initialize(environment, peakseq_report, hostname, url, peakseq_results_path, idr_results_path=nil, xcorr_results_path=nil)
  def initialize(environment, hostname, url, sample_config_path, idr_results_path=nil, xcorr_results_path=nil)
    #Hash that will contain all parsed data to be saved in SNAP
    @dataset = Hash.new
    @replicates = Array.new
    @replicate_hash = Hash.new
    @q_values = Array.new
    @scoring_request_id = ""
    @scoring_request_name = ""
    @scoring_run_tar_file = ""
    @xml_doc = REXML::Document.new
    
    #HACK to temporarily determine idr and XCorr files
    #Should just pass it directly via Philip's pipeline    
    # if environment == "staging"
      # peakseq_results_reverse = peakseq_results_path.reverse
      items = /\A(\S+)\/(.+)\/(.*)\Z/.match(sample_config_path)
      curr_dir = items[1]
      run_info_path = curr_dir + "/inputs/run_info.snap"
      rep_stats_path = curr_dir + "/results/rep_stats"
      idr_results_path = curr_dir + "/results/idr_results.txt"
      xcorr_results_path = curr_dir + "/results/spp_stats.txt"
    # end  
    
    #Open Input Files
    @run_info_file = ""
    if FileTest::exist?(run_info_path)
      @run_info_file = File.open(run_info_path, 'r')
    else
      puts "Could not find or open Run Information file: #{run_info_path}"
      exit(1)
    end
    
    @rep_stats_file = ""
    if FileTest::exist?(rep_stats_path)
      @rep_stats_file = File.open(rep_stats_path, 'r')
    else
      puts "Could not find or open Rep stats file: #{rep_stats_path}"
      exit(1)
    end
    
    @idr_report_file = ""
    if FileTest::exist?(idr_results_path)
      @idr_report_file = File.open(idr_results_path, 'r')
    else      
      puts "Could not find or open idr report file: #{idr_results_path}"
      exit(1)
    end
    
    @xcorr_report_file = ""  
    if FileTest::exist?(xcorr_results_path)
      @xcorr_report_file = File.open(xcorr_results_path, 'r')
    else
      puts "Could not find or open xcorr report file: #{xcorr_results_path}"
      exit(1)
    end
    
  end # initialize()

  #***************************************************************************************************************************************
  def parse_run_info_file
    parsing_replicate_flag = 0
    parsing_scoring_run_flag = 0
    current_replicate = nil
    @run_info_file.each_line do |line|
      #Remove blank lines
      if line == "\n"
        next
        #Remove comment lines
      elsif line =~ /\A#.*\z/
        next
        #Remove Trailing Comments
      elsif line =~ /\A(.+)\s#.*\z/
        line_items =  /\A(.+)\s#.*\z/.match(line)
        line = line_items[1]
      end
      
      #Remove Trailing New Lines
      line.gsub!(/[\n]*, ""/)
      
      #Parse/sort the file items
      #If new Replicate
      if line =~ /\A\[(.+)=(.+)\]\Z/
        @replicate_hash[$2] = Hash.new
        current_replicate = $2
        parsing_replicate_flag = 1
        parsing_scoring_run_flag = 0
      elsif line =~ /\A\[(.+)\]\Z/
        if $1 == "Scoring_Request"
          parsing_scoring_run_flag = 1
          parsing_replicate_flag = 0
        end
      #If key-value pair
      elsif line =~ /\A(\S+)=(.*)\Z/
        items = /\A(\S+)=(.*)\Z/.match(line)
        key = items[1]
        value = items[2]
        #Parse Scoring Request LEvel data
        if parsing_replicate_flag == 0
          case key
          when "run_name"
            @scoring_request_name= value
            if value =~ /\A(PeakSeq|MACS|MACS2)_(.+)_(production)\Z/
              @scoring_run_id = $2
              @environment = $3
              @hostname = 'nummel.stanford.edu'
              @root_url = "http://scg-snap.stanford.edu"
            elsif value =~ /\A(PeakSeq|MACS|MACS2)_(.+)_(staging)\Z/
              @scoring_run_id = $2
              @environment = $3
              @hostname = 'snively.stanford.edu'
              @root_url = "http://scg-snap-new.stanford.edu"    
            elsif value =~ /\A(PeakSeq|MACS|MACS2)_(.+)_(development)\Z/
              @scoring_run_id = $2
              @environment = $3
              @hostname = 'oreo.stanford.edu'
              @root_url = "http://localhost:3002"              
            else
              abort("Error: Cannot Resolve Hostname\n")
            end
            # /\A(\S+)_(\d+)_(.+)\Z/.match(value)
            # @environment=$3
          when "run_id"
            @scoring_request_id = value
          when "control_results_dir"
          when "results_dir"
          when "temporary_dir"
          else
            #DO NOTHING
          end
        #Parse Replicate level data
        else
          case key
          when "rep_name","snap_name", "rep_id", "unique_name"
            @replicate_hash[current_replicate][key] = value
          when "flowcell_lane"
            if @replicate_hash[current_replicate]["lanes"].nil?
              @replicate_hash[current_replicate]["lanes"] = Array.new
            end
            if value =~/\A(.+),(\d+)\Z/
              @replicate_hash[current_replicate]["lanes"][@replicate_hash[current_replicate]["lanes"].length] = Hash.new
              @replicate_hash[current_replicate]["lanes"][@replicate_hash[current_replicate]["lanes"].length-1]["sequencing_run_name"] = $1
              @replicate_hash[current_replicate]["lanes"][@replicate_hash[current_replicate]["lanes"].length-1]["lane_number"] = $2
            end
          else
            #DO NOTHING
          end
        end
      end
    end
    puts "Scoring Request name = #{@scoring_request_name}"
    puts "Scoring Request id = #{@scoring_request_id}"
    pp @replicate_hash
  end

  #***************************************************************************************************************************************
  def parse_idr_report_file
    idr_keys = ["self_consistency_hits", "pooled_hits", "compared_hits"]
    @idr_report_file.each_line do |line|
      #Remove blank lines
      if line == "\n"
        next
        #Remove comment lines
      elsif line =~ /\A#.*\z/
        next
        #Remove Trailing Comments
      elsif line =~ /\A(.+)\s#.*\z/
        line_items =  /\A(.+)\s#.*\z/.match(line)
        line = line_items[1]
      end
      
      #Remove Trailing New Lines
      line.gsub!(/[\n]*, ""/)
      
      #Split line differently on "_VS" or on "_PR1"
      #Then use replicate name to add to @dataset using store_data()
      if line =~ /\A(.+\d+)_PR1_VS_PR2=(\d+)/
        current_replicate = $1
        add_new_replicate(current_replicate)
        self_consistency_hits = $2
        self.store_data("self_consistency_hits", self_consistency_hits, nil, current_replicate)
      elsif line =~ /\A(.+All)_PR1_VS_PR2=(\d+)/
        pooled_hits = $2
        current_replicate = $1
        # replicate_list = get_all_unique_replicates()
        self.store_data("pooled_hits", pooled_hits, nil, current_replicate)
      elsif line =~ /\A(.+\d+)_VS_(.+\d+)=(\d+)/
        replicate1=$1
        add_new_replicate(replicate1)
        replicate2=$2
        add_new_replicate(replicate2)
        compared_hits = $3
        self.store_data("compared_hits", compared_hits, nil, replicate1, replicate2)
      else
        puts "Could not determine the item: \"#{line}\" from idr results file\n"
        exit(1)
      end
    end
  end # parse_idr_report_file()
  
  #***************************************************************************************************************************************
  def parse_xcorr_report_file
    xcorr_keys = ["replicate_name", "num_unique_mapped_reads", "fragment_length", "cross_correlation_value", "phantom_peak", "phantom_peak_correlation", "lowest_strand_shift", "minimum_cross_correlation", "normalized_strand_cross_correlation_coefficient", "relative_strand_cross_correlation_coefficient", "quality_tag"]
    @xcorr_report_file.each_line do |line|
      item_num = 0
          
      current_replicate = nil
      #Remove blank lines
      if line == "\n"
        next
        #Remove comment lines
      elsif line =~ /\A#.*\z/
        next
        #Remove Trailing Comments
      elsif line =~ /\A(.+)\s#.*\z/
        uncommented_line_items =  /\A(.+)\s#.*\z/.match(line)
        line = uncommented_line_items[1]
      end
      
      #Split Line on Spaces
      line_items = line.split(" ")
      
      for item in line_items
        puts "Item: #{item}"
        if item_num == 0
          if item =~ /\A(.+)\.tagAlign\Z/
            puts "xcorr Rep: #{$1}\n"
            current_replicate = $1
            item_num = item_num + 1
          else
            puts "Error: Cannot resolve Replicate in X-Correlation file!\n"
            exit(1)
          end
        else
          #Assign each item using the store_data() method
          #DEBUG
          # puts "Item Num: #{item_num}\n"
          # puts "Storing xcorr item: " + xcorr_keys[item_num].to_s + "\n"
          self.store_data(xcorr_keys[item_num], item, nil, current_replicate)
          item_num = item_num + 1
        end
      end
    end
  end # parse_xcorr_report_file()
    
  #***************************************************************************************************************************************   
  #Returns of list of all replicates in @replicates excluding the "_All" replicate
  def get_all_unique_replicates
    replicate_list=Array.new
    for replicate in @replicates
      if replicate =~ /(.+_All)/
        #Do Nothing
      else
        replicate_list.push(replicate)
      end
    end
    return replicate_list
  end # get_all_unique_replicates()
  
  #*************************************************************************************************************************************** 
  #Adds new_replicate to @replicates list if it is indeed new 
  def add_new_replicate(new_replicate)
    new_replicate_flag = 1
    for replicate in @replicates
      if replicate == new_replicate
        new_replicate_flag = 0
      end
    end
    
    if new_replicate_flag == 1
      @replicates.push($1)
      return 1
    else
      return 0
    end
  end  # add_new_replicate()

  #***************************************************************************************************************************************
  #Parses peakseq output from the specified peakseq_report_file (generally 'full_text')
  #Stores information in hash
  def parse_rep_stats_file
    rep1 = nil
    q_value = nil
    rep2 = nil

    @rep_stats_file.each_line do |line|
      #Filter out useless information
      #Remove blank lines
      if line == "\n"
        next
      #Remove comment lines
      elsif line =~ /\A#.*\Z/
        next
      #Remove Trailing Comments
      elsif line =~ /\A(.+)\s#.*\Z/
        line_items =  /\A(.+)\s#.*\Z/.match(line)
        line = line_items[1]
      end
    
      if line =~ /\A(.+)(\d)=(.+)_VS_(.+)_(.+)=(.+)\Z/
        #HACK SPECIFIC: Only parse "total_hits1"
        if $2 == "1"
        key = $1
        value = $6
        q_value = $5
        rep1=$3
        rep2=$4
        else
          next
        end
      elsif line =~ /\A(.+)=(.+)_VS_(.+)_(.+)=(.+)\Z/
        key = $1
        value = $5
        q_value = $4
        rep1=$2
        rep2=$3
      elsif line =~ /\A(.+)=(.+)=(.+)\Z/
        key = $1
        value=$3
        rep1=$2
        qvalue = nil
        rep2 = nil
      elsif line =~ /\A(.+)=(.+)\Z/
        key = $1
        value = $2
        rep1=nil
        qvalue = nil
        rep2 = nil
        if key == "sample_tar_complete"
          @scoring_run_tar_file = value
        elsif key == "control_tar_complete"
          @scoring_run_tar_file = value
        end
      else
        #DO Nothing
      end
      
      if !@replicates.include?(rep1) && !rep1.nil?
        @replicates.push(rep1)
      end
      
      if !q_value.nil? && !@q_values.include?(q_value)
        @q_values.push(q_value)
      end
      puts "Key = #{key}"
      puts "Value = #{value}"
      puts "QValue = #{q_value}"
      puts "rep1 = #{rep1}"
      puts "rep2 = #{rep2}"
      self.store_data(key, value, q_value, rep1, rep2)
    end
    pp @dataset
  end # parse_rep_stats_file()

  #***************************************************************************************************************************************
  def calculate_ratios
    for replicate1 in @replicates
      for replicate2 in @replicates
        if replicate1 != replicate2 && replicate1 != "RepAll" && replicate2 != "RepAll"
          #NOT DETERMINED BY Q VALUE
          #NEED NEW WAY OF HANDLING THIS
          #NEED TO UPDATE DATABASE
          #SIMILAR TO IDR COMPARSION HIT
          # if @dataset[replicate2]["num_reads"].to_f != 0 
          #   mapped_reads_ratio = @dataset[replicate1]["num_reads"].to_f/@dataset[replicate2]["num_reads"].to_f
          # else
          #   mapped_reads_ratio = 0
          # end
          # self.store_data("mapped_reads_ratio", mapped_reads_ratio, nil, replicate1, replicate2)
          for qvalue in @q_values
            if @dataset[replicate2][qvalue]["total_hits"].to_i != 0
              hits_ratio = @dataset[replicate1][qvalue]["total_hits"].to_f/@dataset[replicate2][qvalue]["total_hits"].to_f
            else
              hits_ratio = 0
            end
            self.store_data("hits_ratio", hits_ratio, qvalue, replicate1, replicate2)
          end
        end
      end
    end
    pp @dataset
  end

  #***************************************************************************************************************************************
  # def store_data(key, value, current_replicate, current_qvalue, compare_replicate)
  def store_data(key, value, current_qvalue=nil, *replicate_list)
    if replicate_list.size < 1
      puts "Replicate list size is zero\n"
      exit(1)
    end
    for replicate in replicate_list
      # puts "Verifying replicates passed in: #{replicate}"
    end
    # puts "Key: #{key}"
    # puts "Value: #{value}"
    # puts "Current qvalue: #{current_qvalue}"
    # puts "Replicate 1 = #{replicate_list[0]}"
    # puts "Replicate 2 = #{replicate_list[1]}"
    # 
    chr_sgr_count = 0
    chr_bed_count = 0
    #Based upon key term, store the item in the dataset hash
    case key
    when "sample_tar_complete", "control_tar_complete"
      #Store files...
    when "read_files"
      #DO something here...
    when "num_reads"
      self.initialize_dataset(nil, current_qvalue, replicate_list[0])
      @dataset[replicate_list[0]][key] = value
    when "total_hits","filtered_bed"
      self.initialize_dataset(nil, current_qvalue, replicate_list[0])
      @dataset[replicate_list[0]][current_qvalue][key] = value
    when "rep_overlap"
      if replicate_list.size < 2
        puts "Replicate list size is less than one for a replicate group comparison: #{replicate_list[0]}\n"
        exit(1)
      end
      puts "Replicate Comparison Key: #{key}"
      self.initialize_dataset("peakseq_replicate_group", current_qvalue, *replicate_list)
      @dataset[replicate_list[0]][current_qvalue][replicate_list[1]]["percent_overlap"] = value
    when "mapped_reads_ratio", "hits_ratio"
      if replicate_list.size < 2
        puts "Replicate list size is less than one for a replicate group comparison: #{replicate_list[0]}\n"
        exit(1)
      end
      puts "Replicate Comparison Key: #{key}"
      self.initialize_dataset("peakseq_replicate_group", current_qvalue, *replicate_list)
      @dataset[replicate_list[0]][current_qvalue][replicate_list[1]][key] = value
      
      puts "Just saved: @dataset[#{replicate_list[0]}][#{current_qvalue}][#{replicate_list[1]}][#{key}] = #{@dataset[replicate_list[0]][current_qvalue][replicate_list[1]][key]}"
      puts "length: #{@dataset[replicate_list[0]][current_qvalue][replicate_list[1]].size}"
    when "chr_bed"
      value =~ /\A(.+)(chr.+)\_hits.bed\Z/
      @dataset[replicate_list[0]]["#{$2}_bed"] = value
    when "chr_sgr"
      value =~ /\A(.+)(chr.+)\.sgr\Z/
      @dataset[replicate_list[0]]["#{$2}_sgr"] = value
    when "num_unique_mapped_reads"
      @dataset[replicate_list[0]]["xcorr_num_unique_mapped_reads"] = value
    when "fragment_length"
      @dataset[replicate_list[0]]["xcorr_fragment_length"] = value
    when "cross_correlation_value"
      @dataset[replicate_list[0]]["xcorr_cross_correlation_value"] = value  
    when "phantom_peak"
      @dataset[replicate_list[0]]["xcorr_phantom_peak"] = value
    when "phantom_peak_correlation"
      @dataset[replicate_list[0]]["xcorr_phantom_peak_correlation"] = value
    when "lowest_strand_shift"
      @dataset[replicate_list[0]]["xcorr_lowest_strand_shift"] = value                  
    when "minimum_cross_correlation"
      @dataset[replicate_list[0]]["xcorr_minimum_cross_correlation"] = value
    when "normalized_strand_cross_correlation_coefficient"
      @dataset[replicate_list[0]]["xcorr_normalized_strand_cross_correlation_coefficient"] = value
    when "relative_strand_cross_correlation_coefficient"
      @dataset[replicate_list[0]]["xcorr_relative_strand_cross_correlation_coefficient"] = value          
    when "quality_tag"
      @dataset[replicate_list[0]]["xcorr_quality_tag"] = value
    when "self_consistency_hits"  
      @dataset[replicate_list[0]]["idr_self_consistency_hits"] = value
    when "pooled_hits"
      @dataset[replicate_list[0]]["idr_self_consistency_hits"] = value
    when "compared_hits"
      self.initialize_dataset("idr_compared_replicate_group", nil, *replicate_list)
      puts "Outside count = #{@idr_compared_replicate_group_count}"
      @dataset["idr_compared_replicate_group"][@idr_compared_replicate_group_count-1]["idr_compared_hits"] = value
    else
      puts "Exiting...unable to determine what the key \"#{key}\" is.  Unable to store data.\n"
      exit(1)
    end
  end # store_data()
  
  #***************************************************************************************************************************************
  def initialize_dataset(group_type, current_qvalue=nil, *replicate_list)
    if replicate_list.nil?
      puts "Error: Cannot Initialize Dataset, replicate list is null\n"
      exit(1)
    end
    
    if @idr_compared_replicate_group_count.nil?
      @idr_compared_replicate_group_count = 0
    end
    
    for replicate in replicate_list
      if group_type.nil? || group_type == "peakseq_replicate_group"
        if @dataset[replicate].nil?
          # puts "initializing replicate: #{replicate}\n"
          @dataset[replicate] = Hash.new
        end
    
        if @dataset[replicate][current_qvalue].nil? && !current_qvalue.nil?
          # puts "initializing qvalue: #{current_qvalue}\n"
          @dataset[replicate][current_qvalue] = Hash.new
        end
        
        if group_type == "peakseq_replicate_group"
          puts "found peakseq_replicate_group"
          if @dataset[replicate_list[0]][current_qvalue][replicate_list[1]].nil?
            puts "initialize repilcate comparison: #{replicate_list[0]} vs #{replicate_list[1]} at q_value: #{current_qvalue}\n"
            @dataset[replicate_list[0]][current_qvalue][replicate_list[1]] = Hash.new
          end
        end
      elsif group_type == "idr_compared_replicate_group"
        # puts "Found a idr_compared_replicate_group!"
        if @dataset[group_type].nil?
          @dataset[group_type] = Array.new
        end
      
        puts "current idr count = #{@idr_compared_replicate_group_count}"
        if @dataset[group_type][@idr_compared_replicate_group_count].nil?
          # puts "initializing array"
          @dataset[group_type][@idr_compared_replicate_group_count] = Hash.new
        end
        
        if @dataset[group_type][@idr_compared_replicate_group_count]["replicates"].nil?
          # puts "initializing replicates hash"
          @dataset[group_type][@idr_compared_replicate_group_count]["replicates"] = Hash.new
        end
        
        if @dataset[group_type][@idr_compared_replicate_group_count]["replicates"][replicate].nil?
          @dataset[group_type][@idr_compared_replicate_group_count]["replicates"][replicate] = true
        end
      else
        puts "Error: Could not determing Dataset to initialize...Exiting\n"
        exit(1)
      end
      
    end
    
    if group_type == "idr_compared_replicate_group"
      @idr_compared_replicate_group_count = @idr_compared_replicate_group_count + 1
    end
    
  end # initialize_dataset()

  
  #***************************************************************************************************************************************
  #Builds up a large params hash containing all peakseq results and POSTs it to SNAP
  def save_peakseq_report_results_snap
    #Build up 
    #Save Experiment Run Data
    params = Hash.new
    
    params["experiment_run[id]"] = @scoring_request_id
    params["experiment_run[file_paths][peakseq_results_tar_file]"] = @scoring_run_tar_file

    #peak_caller_run_length = 0
    #Save Peak Caller Run Data
    for replicate1 in @replicates

      puts "Saving Replicate now: " + replicate1 + "\n"
      
      if replicate1 == "RepAll"
        rep_all_name = @scoring_request_name + "_All"
        params["experiment_run[peak_caller_runs][#{rep_all_name}][peakseq_name]"] = rep_all_name
        repall_keys = @dataset["RepAll"].keys
        for key in repall_keys
          params["experiment_run[peak_caller_runs][#{rep_all_name}][#{key}]"] = @dataset["RepAll"][key]
        end
      else
        params["experiment_run[peak_caller_runs][#{@replicate_hash[replicate1]["unique_name"]}][peakseq_name]"] = @replicate_hash[replicate1]["unique_name"]
        params["experiment_run[peak_caller_runs][#{@replicate_hash[replicate1]["unique_name"]}][replicate_name]"] = @replicate_hash[replicate1]["snap_name"]
      
        #For each Chromosome bed or sgr file
        for file_key in @dataset[replicate1].keys
          is_q_value_flag = 0
          for q_value in @q_values
            if file_key == q_value
              is_q_value_flag = 1
            end
          end

          if is_q_value_flag == 0
            if file_key =~ /\A.*bed.*\Z/
              params["experiment_run[peak_caller_runs][#{@replicate_hash[replicate1]["unique_name"]}][bed_files][#{file_key}]"] = @dataset[replicate1][file_key]
            elsif file_key =~ /\A.*sgr.*\Z/
              params["experiment_run[peak_caller_runs][#{@replicate_hash[replicate1]["unique_name"]}][sgr_files][#{file_key}]"] = @dataset[replicate1][file_key]
            elsif file_key == "idr_self_consistency_hits" || "xcorr_num_unique_mapped_reads" || "xcorr_fragment_length" || "xcorr_cross_correlation_value" || "xcorr_phantom_peak" || "xcorr_phantom_peak_correlation" || "xcorr_lowest_strand_shift" || "xcorr_minimum_cross_correlation" || "xcorr_normalized_strand_cross_correlation_coefficient" || "xcorr_relative_strand_cross_correlation_coefficient" || "xcorr_quality_tag"
              params["experiment_run[peak_caller_runs][#{@replicate_hash[replicate1]["unique_name"]}][#{file_key}]"] = @dataset[replicate1][file_key]
            else
              #Cannot determine what key item is
            end
          end
        end   

        #For each Q-Value/Filter_run    
        filter_run_length = 0    
        for q_value in @q_values
          if !@dataset[replicate1][q_value].nil?

            dataset_keys1 = @dataset[replicate1][q_value].keys
            dataset_keys1 = dataset_keys1.sort.reverse
            for key1 in dataset_keys1
              replicate_group_flag = 0
              for replicate_group_element in @replicates
                if replicate_group_element == key1
                  replicate_group_flag = 1
                end
              end
              if replicate_group_flag == 0
                params["experiment_run[peak_caller_runs][#{@replicate_hash[replicate1]["unique_name"]}][filter_runs][#{q_value}][#{key1}]"] = @dataset[replicate1][q_value][key1]
              end
            end
          end

          for replicate2 in @replicates
            if !(replicate1 =~ /\ARepAll\Z/ || replicate2 =~ /\ARepAll\Z/ || replicate1 == replicate2)
              dataset_keys2 = @dataset[replicate1][q_value][replicate2].keys
              for key2 in dataset_keys2
                 params["experiment_run[peak_caller_runs][#{@replicate_hash[replicate1]["unique_name"]}][filter_runs][#{q_value}][replicate_groups][#{@replicate_hash[replicate2]["unique_name"]}][#{key2}]"] = @dataset[replicate1][q_value][replicate2][key2]
              end
            end
          end

          filter_run_length += 1
        end
        #peak_caller_run_length += 1
      end
    end

    #Set IDR params
    for num in 0..@idr_compared_replicate_group_count-1
      puts "Num = #{num}"
      for idr_replicate in @dataset["idr_compared_replicate_group"][num]["replicates"].keys
        params["experiment_run[idr_compared_replicate_group][#{num}][replicates][#{@replicate_hash[idr_replicate]["unique_name"]}]"] = true
      end
      params["experiment_run[idr_compared_replicate_group][#{num}][idr_compared_hits]"] = @dataset["idr_compared_replicate_group"][num]["idr_compared_hits"]
    end
    
    
    # self.post_data_to_snap(params, "http://localhost:3002/api/peakseq_results/update")
    puts "Scoring Run Id: #{@scoring_request_id}\n"
    puts "Environment: #{@environment}\n"
    puts "Root URL: #{@root_url}\n"
    puts "Hostname: #{@hostname}\n"
    puts "posting data to: #{@root_url}/api/peakseq_results/update\n"
    self.post_data_to_snap(params, "#{@root_url}/api/peakseq_results/update")
    puts "Finished Posting data\n"

  end # save_peakseq_report_results_snap()

  #***************************************************************************************************************************************
  #Prints the value of a dataset ot a specified file
  #For debugging purposes
  #Arguments are a single dataset and an output file handle
  def print_dataset(output_file_path) 

    output_file = File.new(output_file_path, "w")
    if output_file.nil?
      puts "Could not find or open printing output file"
      exit(1)
    end
     
    output_file.puts "Scoring Run #{@scoring_request_id}\n"
    output_file.puts "Sample Tar File  #{@scoring_run_tar_file}\n"

    for replicate1 in @replicates
      output_file.puts "\n\n\n"
      output_file.puts "Replicate  #{replicate1}\n"
      for file_key in @dataset[replicate1].keys
        is_q_value_flag = 0
        for q_value in @q_values
          if file_key == q_value
            is_q_value_flag = 1
          end
        end

        if is_q_value_flag == 0
          output_file.puts "#{file_key}  #{@dataset[replicate1][file_key]}\n"
        end
      end

      for q_value in @q_values
        output_file.puts "\n"
        output_file.puts "QValue  #{q_value}\n"
        if !@dataset[replicate1][q_value].nil?
          dataset_keys1 = @dataset[replicate1][q_value].keys
          dataset_keys1 = dataset_keys1.sort.reverse
          for key in dataset_keys1
            skip_flag = 0
            for repeat_replicate in @replicates
              if repeat_replicate == key
                skip_flag = 1
              end
            end
            if skip_flag == 0
              item = @dataset[replicate1][q_value][key]
              output_file.puts "#{key}  #{item}\n"
            end
          end
        end
        for replicate2 in @replicates
          if !(replicate1 =~ /\A.+_All\Z/ || replicate2 =~ /\A.+_All\Z/ || replicate1 == replicate2)
            output_file.puts "Replicate Group #{replicate1},#{replicate2}\n"
            # puts "Rep Group fields length: #{@dataset[replicate1][q_value][replicate2].size}"
            
            dataset_keys2 = @dataset[replicate1][q_value][replicate2].keys
            for key in dataset_keys2
              item = @dataset[replicate1][q_value][replicate2][key]
              output_file.puts "#{key}  #{item}\n"
            end
          end
        end
      end
    end

    output_file.puts "\n\n"

    # for num in 0..@idr_compared_replicate_group_count-1
    #       puts "num = #{num}"
    #       puts "count = #{@idr_compared_replicate_group_count}"
    #       for replicate in @dataset["idr_compared_replicate_group"][num]["replicates"].keys
    #         output_file.puts "IDR Comparison Group Item #{replicate}"
    #       end
    #       output_file.puts "Comparison hits: #{@dataset["idr_compared_replicate_group"][num]["compared_hits"]}"
    #     end
    #     output_file.puts "\n"
    #     for replicate in @dataset["idr_pooled_replicate_group"]["replicates"].keys
    #       output_file.puts "IDR Pooled Group Item #{replicate}"
    #     end
    #     output_file.puts "Pooled hits: #{@dataset["idr_pooled_replicate_group"]["pooled_hits"]}"
    
    output_file.puts "\n"
  end # print_dataset()
  
  #***************************************************************************************************************************************
  def post_data_to_snap(params, host_url)
    #Post Data
    uri = URI.parse(host_url) 
#		puts "uri is: #{uri}"
#		puts "params are: #{params}"
    http = Net::HTTP.new(uri.host, uri.port)
    request = Net::HTTP::Post.new(uri.request_uri)
    request.set_form_data(params)
    response = http.request(request)
  end # post_data_to_snap()

  #***************************************************************************************************************************************
  def die(message)
    puts message
    exit 1
  end # die()

end # class PeakseqReportParser


#######################################################################################################################################
class OptparsePeakseqReportParser
  #Class that parses command line options
  require 'optparse'
  require 'optparse/time'
  require 'ostruct'

  #***************************************************************************************************************************************
  # Build & Return a structure describing the command line options.
  def self.parse(args)
    options = OpenStruct.new
    # options.environment = :staging
    options.logfile = "/peakseq_results.log"

    opts = OptionParser.new do |opts|
      opts.banner = "Usage: ruby snap_peakseq_caller.rb [options]"
      opts.separator ""
      opts.separator "Specific options:"

      # Optional argument with keyword completion.
      opts.on("-e", "--environment [TYPE]", [:development, :staging, :production],
      "Mandatory environment type (development, staging, or production)") do |e|
        options.environment = e
      end
      
      # Mandatory argument.
      opts.on("-s", "--sample_config SAMPLE_CONFIG_FILE",
      "Mandatory sample config file path") do |sample_config|
        options.sample_config = sample_config
      end
      
      # Mandatory argument.
      opts.on("-r", "--run_info RUN_INFO_FILE",
      "Mandatory run information file path") do |run_info|
        options.run_info = run_info
      end
      
      # Optional argument with keyword completion.
      opts.on("-p", "--peakseq_results PEAKSEQ_RESULTS_FILE",
      "Mandatory peakseq results file path") do |peakseq_results|
        options.peakseq_results = peakseq_results
      end
      
      # Optional argument with keyword completion.
      opts.on("-i", "--idr_results IDR_RESULTS_FILE",
      "Mandatory idr results file path") do |idr_results|
        options.idr_results = idr_results
      end
      
      # Optional argument with keyword completion.
      opts.on("-x", "--xcorr_results XCORR_RESULTS_FILE",
      "Mandatory X-Correlation results file path") do |xcorr_results|
        options.xcorr_results = xcorr_results
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
    raise OptionParser::MissingArgument if options.sample_config.nil?
    # raise OptionParser::MissingArgument if options.run_info.nil?
    # raise OptionParser::MissingArgument if options.peakseq_results.nil?
    # raise OptionParser::MissingArgument if options.idr_results.nil?
    # raise OptionParser::MissingArgument if options.xcorr_results.nil?
    raise OptionParser::MissingArgument if options.hostname.nil?
    raise OptionParser::MissingArgument if options.url.nil?
    
    return options
  end # parse()

end # class OptparsePeakseqReportParser

#######################################################################################################################################
#Start Main portion of Program
#######################################################################################################################################

#Parse command line args
options = OptparsePeakseqReportParser.parse(ARGV)
#Initialize report parser
peakseq_result_parser = PeakseqReportParser.new(options.environment.to_s, options.hostname.to_s, options.url.to_s, options.sample_config.to_s, options.idr_results.to_s, options.xcorr_results.to_s)  

#Parse Peakseq/IDR/XCorr report files and temporarily store
puts "Parsing Run INFO!"
peakseq_result_parser.parse_run_info_file
peakseq_result_parser.parse_rep_stats_file
peakseq_result_parser.parse_xcorr_report_file
peakseq_result_parser.parse_idr_report_file

peakseq_result_parser.calculate_ratios

#Submit Data into SNAP Database
peakseq_result_parser.save_peakseq_report_results_snap

#DEBUG
#text_output_file = "/home/alwon/peakseq_dataset_hash.txt"
#peakseq_result_parser.print_dataset(text_output_file)

exit(0)
