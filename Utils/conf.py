import os
import json

conffh = open(os.path.join(os.path.dirname(__file__),"conf.json"),'r')
conf = json.load(conffh)

peakseq_binary = conf["peakseq_binary"]
mappability_file = conf["mappability_file"]
controlScoringPrefixPath = conf['scoringPathPrefix']['control']
sampleScoringPrefixPath  = conf['scoringPathPrefix']['sample']

scoringPipelineScriptPath = conf['scoringPipelineScriptPath']

toEmails = conf['email']['to'] #list
ccEmails = conf['email']['cc'] #list
sender   = conf['email']['sender'] #string
