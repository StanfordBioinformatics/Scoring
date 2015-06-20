import json

conffh = open("conf.json",'r')
conf = json.load(conffh)

controlScoringPrefixPath = conf['scoringPathPrefix']['control']
sampleScoringPrefixPath  = conf['scoringPathPrefix']['sample']

scoringPipelineScriptPath = conf['scoringPipelineScriptPath']

toEmails = conf['email']['to'] #list
ccEmails = conf['email']['cc'] #list
sender   = conf['email']['sender'] #string
