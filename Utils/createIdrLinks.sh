#!/bin/bash -eu

#AUTHOR: Nathaniel Watson

###
#Program Description#
#	Input Arguments:
#		1) Name of a scoring run, i.e one of the folders in /srv/gsfs0/projects/gbsc/SNAP_Scoring/production/replicates/human/, such as hES_ZFP36_T5327.
###
snapRes=/srv/gsfs0/projects/gbsc/SNAP_Scoring/production/replicates/human
cd $snapRes
indir=${1}/results/idr
basePath=https://scg-data.stanford.edu/ChipScorings #ChipScorings on nummel is a symlink to ${snapRes}
basePath=${basePath//#/%23} #URL-encoding
out=${indir}/idrResults.html
escOut=${out//#/%23}
if [[ -e $out ]]
then
	rm $out
fi

pageName="${1} IDR Results"

echo "<!DOCTYPE html>" >> $out
echo "<html>" >> $out
echo "<head>" >> $out
echo "<title>${pageName}</title>" >> $out
echo "</head>" >> $out
echo "<body>" >> $out
echo "<h2>${pageName}</h2>" >> $out
for i in $(find ${indir} -maxdepth 1 -name "*.*" -print) #-name "*.*" means all files with an ext.
do 
	i=${i//#/%23}
	echo "<a href=\"${basePath}/${i}\">$(basename $i)</a><br/>" >> $out
done

echo "</body><br/>" >> $out
echo "</html><br/>" >> $out

htmlLink="${basePath}/${escOut}"
echo $htmlLink
