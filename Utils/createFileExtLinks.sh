#!/bin/bash -eu

#AUTHOR: Nathaniel Watson

###
#Program Description#
#	Input Arguments:
#		1) A scoring run name, i.e one of the folers in /srv/gsfs0/projects/gbsc/SNAP_Scoring/production/replicates/human/, such as hES_ZFP36_T5327.
#		2) A file extension, i.e. bed, sgr, ... Case sensitive, so enter the case that the files use.
###
snapRes=/srv/gsfs0/projects/gbsc/SNAP_Scoring/production/replicates/human
cd $snapRes
indir=${1}/results
fileExt=${2#.}
basePath=https://scg-data.stanford.edu/ChipScorings #ChipScorings on nummel is a symlink to ${snapRes}
basePath=${basePath//#/%23} #URL-encoding
out=${indir}/${fileExt}Files.html
escOut=${out//#/%23}
if [[ -e $out ]]
then
	rm $out
fi

echo "<!DOCTYPE html>" >> $out
echo "<html>" >> $out
echo "<head>" >> $out
echo "<title>Chip Scoring Run ${1}</title>" >> $out
echo "</head>" >> $out
echo "<body>" >> $out
echo "<h1>All BED File Links</h1>" >> $out
for i in $(find ${indir} -name "*.${fileExt}" -print)
do 
	i=${i//#/%23}
	echo "<a href=\"${basePath}/${i}\">$(basename $i)</a><br/>" >> $out
done

echo "</body><br/>" >> $out
echo "</html><br/>" >> $out

htmlLink="${basePath}/${escOut}"
echo $htmlLink
