#!/bin/bash

#Set up Environment Modules
#source /srv/gs1/apps/Modules/default/init/bash
module add ruby/1.8.7 rubygems/1.8 gem/1.5.2 sjm/1.2 python/2.7 snap/$1 #sge/scg1

#Call Check Pipeline Failed
ruby /srv/gs1/apps/snap_support/$SNAP_ENVIRONMENT/current/check_pipeline_status.rb -e $SNAP_ENVIRONMENT -h $SNAP_HOSTNAME -u $SNAP_URL
