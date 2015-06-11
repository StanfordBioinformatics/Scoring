import json

conffh = open("conf.json",'r')
conf = json.loads(conffh)

controlScoringPrefixPath = conf.scoringPathPrefix["control"]
sampleScoringPrefixPath  = conf.scoringPathPrefix["sample"]

toEmails = email.to #list
ccEmails = email.cc #list
sender   = emails.sender #string
