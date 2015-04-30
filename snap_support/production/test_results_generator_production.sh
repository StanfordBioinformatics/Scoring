#!/bin/bash

#Set up Environment Modules
source /srv/gs1/apps/Modules/default/init/bash

INIT_DIR_NAME="pipeline_2_test"
NAME="PeakSeq_$1_production"

NEW_DIR=/srv/gs1/projects/scg/SNAP_Scoring/production/replicates/human/$NAME
RESULTS_DIR=/srv/gs1/projects/scg/SNAP_Scoring/production/replicates/human/$NAME/results
INPUTS_DIR=$NEW_DIR/inputs
GOLD_DIR=/srv/gs1/projects/scg/SNAP_Scoring/gold/$INIT_DIR_NAME

mkdir $NEW_DIR
mkdir $NEW_DIR/results
mkdir $NEW_DIR/inputs

#cp $GOLD_DIR/full_report $RESULTS_DIR
cp $GOLD_DIR/inputs/run_info.snap $INPUTS_DIR
cp $GOLD_DIR/results/rep_stats $RESULTS_DIR
cp $GOLD_DIR/results/spp_stats.txt $RESULTS_DIR
cp $GOLD_DIR/results/idr_results.txt $RESULTS_DIR
#sed -i s/"${INIT_DIR_NAME}"/"${NAME}"/g $RESULTS_DIR/full_report
#sed -i s/"${INIT_DIR_NAME}"/"${NAME}"/g $RESULTS_DIR/rep_stats
#sed -i s/"${INIT_DIR_NAME}"/"${NAME}"/g $RESULTS_DIR/spp_stats.txt
#sed -i s/"${INIT_DIR_NAME}"/"${NAME}"/g $RESULTS_DIR/idr_results.txt

#sed -i s/"${INIT_DIR_NAME}"/"${NAME}"/ $RESULTS_DIR/spp_stats.txt
#sed -i s/"${INIT_DIR_NAME}"/"${NAME}"/ $RESULTS_DIR/spp_stats.txt
#sed -i s/"${INIT_DIR_NAME}"/"${NAME}"/ $RESULTS_DIR/idr_results.txt

