#!/bin/bash

#Set up Environment Modules
#source /usr/share/Modules/init/bash
#module add ruby/1.8.7 rubygems/1.8 gem/1.5.2 
module add sjm/1.2 python/2.7 snap/$1 #scg3-oge-new 

cmd="ruby /srv/gs1/apps/snap_support/$SNAP_ENVIRONMENT/current/snap_peakseq_caller.rb -e $SNAP_ENVIRONMENT -p $SNAP_PEAKSEQ_EXECUTABLE -h $SNAP_HOSTNAME -u $SNAP_URL"

if [[ -n $2 ]]
then
	cmd="$cmd --paired_end"
fi
#Call Snap Peakseq Caller
