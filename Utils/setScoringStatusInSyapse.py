import logging
from argparse import ArgumentParser

import syapse_scgpm

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch= logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
f_formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:   %(message)s')
ch.setFormatter(f_formatter)
logger.addHandler(ch) 

#Create a default connection to prod so that I can retrieve the set of allowed property values
# of the Scoring Status propery of a ChIP Seq Scoring object.
prodMode = "prod"
syapse = syapse_scgpm.al.Utils(mode=syapse_scgpm.syapse.Syapse.knownModes[prodMode])
kbclass_id = "ScgpmFSnapScoring"
statusValues = syapse.getPropertyEnumRangeFromKbClassId(kbclass_id=kbclass_id,propertyName="scoringStatus")

description = "Sets the 'Scoring Status' attribute of a ChIP Seq Scoring object in Syapse to one of the supported values."
parser = ArgumentParser(description=description)	
parser.add_argument('--mode',required=True,help="A string indicating which Syapse host to use. Must be one of elemensts given in {knownModes}.".format(knownModes=syapse_scgpm.syapse.Syapse.knownModes.keys()))
parser.add_argument('--name',required=True,help="The name of the scoring run (This should be the ChIP Seq Scoring object's UID in Syapse).")
parser.add_argument('--status',choices=statusValues,required=True,help="What to set the 'Scoring Status' attribute to.")

args = parser.parse_args()
mode = args.mode
name = args.name
status = args.status

scoringStatusPropertyName = "scoringStatus"

if not mode == prodMode:
	syapse = syapse_scgpm.al.Utils(mode=mode)

syapse.setProperty(propertyName=scoringStatusPropertyName,value=status,unique_id=name)
