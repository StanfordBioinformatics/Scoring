#100907_COLUMBO_FC62GGG 101103_GENTLY_00035_FC62NRU 101214_SPADE_00044_FC630AR 110311_SPADE_00061_FC634TY 101012_MAGNUM_00032_FC62LTC 100629_GENTLY_FC624NP 100819_ROCKFORD_FC62E5K 111020_MAGNUM_00103_FC64KFD 101201_COLUMBO_00044_FC70EUE 101018_COLUMBO_FC62TOW

for i in ${@}
do
  proj=$(/srv/gs1/software/gbsc/gbsc/snap/getOldArchivePath.py $i)
	#check if bams exists. If so, then skip this archive
	bams=$(ls ${proj}/*.bam 2>/dev/null)
	if [[ $? -eq 0 ]]
  then
		echo "Skipping project ${i}, which already has BAM files."
		continue
	fi

  for j in $proj/*_pf.fastq.gz
    do
      echo "Generating BAMs for project $i"
      kwality.py --outdir=${proj} -s ${j%%.*}_createBams.sjm --run  -c /srv/gs1/software/gbsc/kwality/1.0/instances/bwa-aln-se.json fastq=$j  
      echo;echo
    done
done
