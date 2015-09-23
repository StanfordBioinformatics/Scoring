##
# Adding additional species/genome builds is done here.  There are five
# steps.
# 1.  	Add a mapping from genome chromosome FASTA file to chromosome name.
#		This is necessary because eland displays the results by the source
#		chromosome reference file.
# 2.	Add chr mapping to the genomes map.
# 3.	Create a IDR binary directory for the genome.  The directory
#		should contain all the IDR binaries along with a genome_table.txt
#		tailored for the genome.  (See IDR documentation)  The directory
#		path should be added to the IDR_BIN_DIR mapping.  This duplication
#		is necessary because of a limitation of IDR.
#               Manually edit batch-consistency-analysis.r to change the hard coded
#               source (line 55) and chr.file (line 58) paths.
# 4.	Select the IDR filtering thresholds in the IDR_THRESHOLDS mapping.
# (5a.)	Specify the whole genome size in macs_genome_size 
#		to be used as a parameter for MACS. The default MACS parameters
#		should already be set.
# (5b.)	If using PeakSeq, set the location of the pre-generated mappability
#		file in peakseq_mappability_file
##


ucsc_hg18 = {
	'chr1.fa' : 'chr1',
	'chr10.fa' : 'chr10',
	'chr11.fa' : 'chr11',
	'chr12.fa' : 'chr12',
	'chr13.fa' : 'chr13',
	'chr14.fa' : 'chr14',
	'chr15.fa' : 'chr15',
	'chr16.fa' : 'chr16',
	'chr17.fa' : 'chr17',
	'chr18.fa' : 'chr18',
	'chr19.fa' : 'chr19',
	'chr2.fa' : 'chr2',
	'chr20.fa' : 'chr20',
	'chr21.fa' : 'chr21',
	'chr22.fa' : 'chr22',
	'chr3.fa' : 'chr3',
	'chr4.fa' : 'chr4',
	'chr5.fa' : 'chr5',
	'chr6.fa' : 'chr6',
	'chr7.fa' : 'chr7',
	'chr8.fa' : 'chr8',
	'chr9.fa' : 'chr9',
	'chrM.fa' : 'chrM',
	'chrX.fa' : 'chrX',
	'chrY.fa' : 'chrY',
}

hg19_female = {
	'chr1.fa' : 'chr1',
	'chr10.fa' : 'chr10',
	'chr11.fa' : 'chr11',
	'chr12.fa' : 'chr12',
	'chr13.fa' : 'chr13',
	'chr14.fa' : 'chr14',
	'chr15.fa' : 'chr15',
	'chr16.fa' : 'chr16',
	'chr17.fa' : 'chr17',
	'chr18.fa' : 'chr18',
	'chr19.fa' : 'chr19',
	'chr2.fa' : 'chr2',
	'chr20.fa' : 'chr20',
	'chr21.fa' : 'chr21',
	'chr22.fa' : 'chr22',
	'chr3.fa' : 'chr3',
	'chr4.fa' : 'chr4',
	'chr5.fa' : 'chr5',
	'chr6.fa' : 'chr6',
	'chr7.fa' : 'chr7',
	'chr8.fa' : 'chr8',
	'chr9.fa' : 'chr9',
	'chrM.fa' : 'chrM',
	'chrX.fa' : 'chrX',
}

hg19_male = {
	'chr1.fa' : 'chr1',
	'chr10.fa' : 'chr10',
	'chr11.fa' : 'chr11',
	'chr12.fa' : 'chr12',
	'chr13.fa' : 'chr13',
	'chr14.fa' : 'chr14',
	'chr15.fa' : 'chr15',
	'chr16.fa' : 'chr16',
	'chr17.fa' : 'chr17',
	'chr18.fa' : 'chr18',
	'chr19.fa' : 'chr19',
	'chr2.fa' : 'chr2',
	'chr20.fa' : 'chr20',
	'chr21.fa' : 'chr21',
	'chr22.fa' : 'chr22',
	'chr3.fa' : 'chr3',
	'chr4.fa' : 'chr4',
	'chr5.fa' : 'chr5',
	'chr6.fa' : 'chr6',
	'chr7.fa' : 'chr7',
	'chr8.fa' : 'chr8',
	'chr9.fa' : 'chr9',
	'chrM.fa' : 'chrM',
	'chrX.fa' : 'chrX',
	'chrY.fa' : 'chrY',
}

mm_ncbi_37 = {
	'chr1.fa' : 'chr1',
	'chr10.fa' : 'chr10',
	'chr11.fa' : 'chr11',
	'chr12.fa' : 'chr12',
	'chr13.fa' : 'chr13',
	'chr14.fa' : 'chr14',
	'chr15.fa' : 'chr15',
	'chr16.fa' : 'chr16',
	'chr17.fa' : 'chr17',
    'chr18.fa' : 'chr18',
	'chr19.fa' : 'chr19',
	'chr2.fa' : 'chr2',
	'chr3.fa' : 'chr3',
	'chr4.fa' : 'chr4',
	'chr5.fa' : 'chr5',
	'chr6.fa' : 'chr6',
	'chr7.fa' : 'chr7',
	'chr8.fa' : 'chr8',
	'chr9.fa' : 'chr9',
	'chrM.fa' : 'chrM',
	'chrX.fa' : 'chrX',
	'chrY.fa' : 'chrY',
	}

mm9_male = {
	'chr1.fa' : 'chr1',
	'chr10.fa' : 'chr10',
	'chr11.fa' : 'chr11',
	'chr12.fa' : 'chr12',
	'chr13.fa' : 'chr13',
	'chr14.fa' : 'chr14',
	'chr15.fa' : 'chr15',
	'chr16.fa' : 'chr16',
	'chr17.fa' : 'chr17',
	'chr18.fa' : 'chr18',
	'chr19.fa' : 'chr19',
	'chr2.fa' : 'chr2',
	'chr3.fa' : 'chr3',
	'chr4.fa' : 'chr4',
	'chr5.fa' : 'chr5',
	'chr6.fa' : 'chr6',
	'chr7.fa' : 'chr7',
	'chr8.fa' : 'chr8',
	'chr9.fa' : 'chr9',
	'chrM.fa' : 'chrM',
	'chrX.fa' : 'chrX',
	'chrY.fa' : 'chrY',
	        }

mm9_female = {
	'chr1.fa' : 'chr1',
	'chr10.fa' : 'chr10',
	'chr11.fa' : 'chr11',
	'chr12.fa' : 'chr12',
	'chr13.fa' : 'chr13',
	'chr14.fa' : 'chr14',
	'chr15.fa' : 'chr15',
	'chr16.fa' : 'chr16',
	'chr17.fa' : 'chr17',
	'chr18.fa' : 'chr18',
	'chr19.fa' : 'chr19',
	'chr2.fa' : 'chr2',
	'chr3.fa' : 'chr3',
	'chr4.fa' : 'chr4',
	'chr5.fa' : 'chr5',
	'chr6.fa' : 'chr6',
	'chr7.fa' : 'chr7',
	'chr8.fa' : 'chr8',
	'chr9.fa' : 'chr9',
	'chrM.fa' : 'chrM',
	'chrX.fa' : 'chrX',
	        }

mm9_male_yale = {
    'mm_ref_chr1.fa' : 'chr1',
    'mm_ref_chr2.fa' : 'chr2',
    'mm_ref_chr3.fa' : 'chr3',
    'mm_ref_chr4.fa' : 'chr4',
    'mm_ref_chr5.fa' : 'chr5',
    'mm_ref_chr6.fa' : 'chr6',
    'mm_ref_chr7.fa' : 'chr7',
    'mm_ref_chr8.fa' : 'chr8',
    'mm_ref_chr9.fa' : 'chr9',
    'mm_ref_chrM.fa' : 'chrM',
    'mm_ref_chrX.fa' : 'chrX',
    'mm_ref_chrY.fa' : 'chrY',
}

maize_agpv1 = {
	'ZmB73_AGPv1_chr1.fa' : 'chr1',
	'ZmB73_AGPv1_chr2.fa' : 'chr2',
	'ZmB73_AGPv1_chr3.fa' : 'chr3',
	'ZmB73_AGPv1_chr4.fa' : 'chr4',
	'ZmB73_AGPv1_chr5.fa' : 'chr5',
	'ZmB73_AGPv1_chr6.fa' : 'chr6',
	'ZmB73_AGPv1_chr7.fa' : 'chr7',
	'ZmB73_AGPv1_chr8.fa' : 'chr8',
	'ZmB73_AGPv1_chr9.fa' : 'chr9',
	'ZmB73_AGPv1_chr10.fa' : 'chr10',
	}

arabidopsis_tair9 = {
	'chr1.fa' : 'chr1',
	'chr2.fa' : 'chr2',
	'chr3.fa' : 'chr3',
	'chr4.fa' : 'chr4',
	'chr5.fa' : 'chr5',
	'chrC.fa' : 'chrC',
	'chrM.fa' : 'chrM',
	}

yeast = {
	'chrI.fa' : 'chrI',
	'chrII.fa' : 'chrII',
	'chrIII.fa' : 'chrIII',
	'chrIV.fa' : 'chrIV',
	'chrIX.fa' : 'chrIX',
	'chrM.fa' : 'chrM',
	'chrV.fa' : 'chrV',
	'chrVI.fa' : 'chrVI',
	'chrVII.fa' : 'chrVII',
	'chrVIII.fa' : 'chrVIII',
	'chrX.fa' : 'chrX',
	'chrXI.fa' : 'chrXI',
	'chrXII.fa' : 'chrXII',
	'chrXIII.fa' : 'chrXIII',
	'chrXIV.fa' : 'chrXIV',
	'chrXV.fa' : 'chrXV',
	'chrXVI.fa' : 'chrXVI',
}

fly_dm3 = {
	'chr2L.fa' : 'chr2L',
	'chr2R.fa' : 'chr2R',
	'chr3L.fa' : 'chr3L',
	'chr3R.fa' : 'chr3R',
	'chr4.fa' : 'chr4',
	'chrX.fa' : 'chrX',
	'chrU.fa' : 'chrU',
	'chrM.fa' : 'chrM',
}

fly_r5_32 = {
	'3RHet.fa' : 'chr3RHet',
	'2RHet.fa' : 'chr24Het',
	'4.fa' : 'chr4',
	'X.fa' : 'chrX',
	'2R.fa' : 'chr2R',
	'2L.fa' : 'chr2L',
	'Uextra.fa' : 'chrUextra',
	'YHet.fa' : 'chrYHet',
	'3R.fa' : 'chr3R',
	'3L.fa' : 'chr3L',
	'U.fa' : 'chrU',
	'dmel_mitochondrion_genome.fa' : 'chrM',
	'3LHet.fa' : 'chr3LHet',
	'XHet.fa' : 'chrXHet',
	'2LHet.fa' : 'chr2LHet',
}

panTro2 = {
	'chr1.fa' : 'chr1',
	'chr2.fa' : 'chr2',
	'chr2a.fa' : 'chr2a',
	'chr2b.fa' : 'chr2b',
	'chr3.fa' : 'chr3',
	'chr4.fa' : 'chr4',
	'chr5.fa' : 'chr5',
	'chr6.fa' : 'chr6',
	'chr7.fa' : 'chr7',
	'chr8.fa' : 'chr8',
	'chr9.fa' : 'chr9',
	'chr10.fa' : 'chr10',
	'chr11.fa' : 'chr11',
	'chr12.fa' : 'chr12',
	'chr13.fa' : 'chr13',
	'chr14.fa' : 'chr14',
	'chr15.fa' : 'chr15',
	'chr16.fa' : 'chr16',
	'chr17.fa' : 'chr17',
	'chr18.fa' : 'chr18',
	'chr19.fa' : 'chr19',
	'chr20.fa' : 'chr20',
	'chr21.fa' : 'chr21',
	'chr22.fa' : 'chr22',
}

rheMac2 = {
	'chr1.fa' : 'chr1',
	'chr2.fa' : 'chr2',
	'chr3.fa' : 'chr3',
	'chr4.fa' : 'chr4',
	'chr5.fa' : 'chr5',
	'chr6.fa' : 'chr6',
	'chr7.fa' : 'chr7',
	'chr8.fa' : 'chr8',
	'chr9.fa' : 'chr9',
	'chr10.fa' : 'chr10',
	'chr11.fa' : 'chr11',
	'chr12.fa' : 'chr12',
	'chr13.fa' : 'chr13',
	'chr14.fa' : 'chr14',
	'chr15.fa' : 'chr15',
	'chr16.fa' : 'chr16',
	'chr17.fa' : 'chr17',
	'chr18.fa' : 'chr18',
	'chr19.fa' : 'chr19',
	'chr20.fa' : 'chr20',
	'chrX.fa' : 'chrX',
 }

WS182 = {
	'I.fa' : 'I',
	'II.fa' : 'II',
	'III.fa' : 'III',
	'IV.fa' : 'IV',
	'V.fa' : 'V',
	'X.fa' : 'X',
	'MtDNA.fa' : 'MtDNA',
}
	

genomes = {
	'ucsc_hg18' : ucsc_hg18,
	'mm_ncbi_37' : mm_ncbi_37,
	'maize' : maize_agpv1,
	'hg19_female' : hg19_female,
	'hg19_male' : hg19_male,
	'arabidopsis_tair9' : arabidopsis_tair9,
	'yeast_scg_5_08' : yeast,
	'mm9_male' : mm9_male,
	'mm9_female' : mm9_female,
	'panTro2' : panTro2,
	'rheMac2' : rheMac2,
	'WS182' : WS182,
	'WS220' : WS182,
	'mm9_male_yale' : mm9_male_yale,
	'fly_dm3' : fly_dm3,
	'r5-32' : fly_r5_32,
}


peakseq_mappability_file = {
	'hg19_female' : '/srv/gsfs0/projects/gbsc/workspace/nathankw/Scoring/mappability/hg19_female.txt',
	'hg19_male' : '/srv/gsfs0/projects/gbsc/workspace/nathankw/Scoring/mappability/hg19_male.txt',
	'maize' : '/srv/gsfs0/projects/gbsc/workspace/nathankw/Scoring/mappability/maize_agpv1.txt',
	'mm9_female' : '/srv/gsfs0/projects/gbsc/workspace/nathankw/Scoring/mappability/mm9_female.txt',
	'mm9_male' : '/srv/gsfs0/projects/gbsc/workspace/nathankw/Scoring/mappability/mm9_male.txt',
	'mm9_male_yale' : '//srv/gsfs0/projects/gbsc/workspace/nathankw/Scoring/mappability/mm9_male.txt',
	'panTro2' : '/srv/gsfs0/projects/gbsc/workspace/nathankw/Scoring/mappability/panTro2.txt',
	'rheMac2' : '/srv/gsfs0/projects/gbsc/workspace/nathankw/Scoring/mappability/rheMac2.txt',
	'ucsc_hg18' : '/srv/gsfs0/projects/gbsc/workspace/nathankw/Scoring/mappability/ucsc_hg18.txt',
	'WS182' : '/srv/gsfs0/projects/gbsc/workspace/nathankw/Scoring/mappability/WS182.txt',
	'WS220' : '/srv/gsfs0/projects/gbsc/workspace/nathankw/Scoring/mappability/WS182.txt',
	'yeast_scg_5_08' : '/srv/gsfs0/projects/gbsc/workspace/nathankw/Scoring/mappability/yeast_scg_5_08.txt',
	'arabidopsis_tair9' : '/srv/gsfs0/projects/gbsc/workspace/nathankw/Scoring/mappability/arabidopsis_tair9.txt',
}


macs_genome_size = {
	# If not one of the default MACS genomes, specify the specific number
	# of bases in the whole genome. (e.g. 'hg18' : '3164700000')
	'ucsc_hg18' : 'hs',
	'hg19_female' : 'hs',
	'hg19_male' : 'hs',
	'mm_ncbi_37' : 'mm',
	'mm9_male' : 'mm',
	'mm9_female' : 'mm',
	'mm9_male_yale' : 'mm',
	'WS182' : 'ce',
	'WS220' : 'ce',
	'fly_dm3' : 'dm',
	'r5-32' : 'dm',
	'panTro2' : '3350447512',
	'rheMac2' : '2864106071',
}

IDR_THRESHOLDS = {
	# Set IDR filtering thresholds.  Order is:
	# 	1.  Rep VS Rep threshold
	#	2.  Rep Self Consistency threshold
	#	3.  Pooled Self Consistency threshold
	'hg19_female' : (0.02, 0.02, 0.02),
	'hg19_male' : (0.02, 0.02, 0.02),
	'mm9_male' : (0.02, 0.02, 0.02),
	'mm9_female' : (0.02, 0.02, 0.02),
	'fly_dm3' : (0.1, 0.1, 0.1),
	'r5-32' : (0.1, 0.1, 0.1),
	'WS182' : (0.1, 0.1, 0.1),
	'WS220' : (0.1, 0.1, 0.1),
	'panTro2' : (0.01, 0.02, 0.0025),
	'rheMac2' : (0.01, 0.02, 0.0025),
}

IDR_BIN_DIR = {
	# Verify that IDR directories contain both IDR binaries AND
	# a correct genome_table.txt file (see IDR documentation)
	'hg19_female' : '/srv/gsfs0/projects/gbsc/workspace/nathankw/Scoring/idr/bins/human_hg19',
	'hg19_male' : '/srv/gsfs0/projects/gbsc/workspace/nathankw/Scoring/idr/bins/human_hg19',
	'fly_dm3' : '/srv/gsfs0/projects/gbsc/workspace/nathankw/Scoring/idr/bins/fly_dm3',
	'r5-32' : '/srv/gsfs0/projects/gbsc/workspace/nathankw/Scoring/idr/bins/fly_r5_32',
	'WS182' : '/srv/gsfs0/projects/gbsc/workspace/nathankw/Scoring/idr/bins/worm_ws220',
	'WS220' : '/srv/gsfs0/projects/gbsc/workspace/nathankw/Scoring/idr/bins/worm_ws220',
	'mm_ncbi_37' : '/srv/gsfs0/projects/gbsc/workspace/nathankw/Scoring/idr/bins/mouse_mm9',
	'mm9_male' : '/srv/gsfs0/projects/gbsc/workspace/nathankw/Scoring/idr/bins/mouse_mm9',
	'mm9_female' : '/srv/gsfs0/projects/gbsc/workspace/nathankw/Scoring/idr/bins/mouse_mm9',
	'panTro2' : '/srv/gsfs0/projects/gbsc/workspace/nathankw/Scoring/idr/bins/chimp_pantro2',
	'rheMac2' : '/srv/gsfs0/projects/gbsc/workspace/nathankw/Scoring/idr/bins/rhesus_rhemac2',
}


def get_chr_mapping(genome):
	if genome not in genomes:
		raise Exception("%s does not have chr mapping." % genome)
	return genomes[genome]
	
