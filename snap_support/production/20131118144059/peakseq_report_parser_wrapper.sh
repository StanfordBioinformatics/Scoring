#!/bin/bash

#Set up Environment Modules
#source /srv/gs1/apps/Modules/default/init/bash
module add ruby/1.8.7 rubygems/1.8 gem/1.5.2 sjm/1.2 python/2.7 snap/$1 #sge/scg2

# #Call Snap Peakseq Caller
ruby /srv/gs1/apps/snap_support/$1/current/peakseq_report_parser.rb -e $SNAP_ENVIRONMENT -s $2 -h $SNAP_HOSTNAME -u $SNAP_URL
exit 0
