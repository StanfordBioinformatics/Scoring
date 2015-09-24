#!/bin/bash

function help() {
	echo "Enter the names of one or more scoring runs, separated by a space."
}

while getopts "h" opt
do
	case $opt in 
		h) 
			help
			exit 0
			;;
	esac
done

module load sjm/1.3.0
snapRes=$(jq -r .scoringPathPrefix.sample  conf.json )
for i in $@
do
	if ! [[ -d $snapRes/${i} ]]
	then
		continue
	fi
	cd $snapRes/${i}/inputs
	statusFiles=$(ls -t ${i}*.status)	
	statusFiles=($statusFiles)
	newest=${statusFiles[0]}
	sjm --mail nathankw@stanford.edu $newest
done
