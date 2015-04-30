#!/bin/bash

#Create Experiment Directories
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine1_Control1_submitted
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine1_Control2_submitted
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine1_Control3_submitted
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine2_Control4_submitted
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine2_Control5_submitted
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine2_Control6_submitted
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine2_Control7_submitted
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine9_Control8_submitted
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine9_Control9_submitted
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine9_Control10_submitted
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine4_Control11_submitted
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine4_Control12_submitted
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine4_Control13_submitted
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine4_Control14_submitted
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine6_Control15_submitted
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine6_Control16_submitted
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine6_Control17_submitted
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine6_Control18_submitted
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine209_Control19_submitted
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine209_Control20_submitted
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine209_Control21_submitted
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine223_Control22_submitted
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine223_Control23_submitted
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine223_Control24_submitted
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine223_Control25_submitted
mkdir -p /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine223_Control26_submitted


#ADD RESULTS
ln -s /srv/gs1/projects/scg/Scoring/results/human/GM12878/Control_SL_V2 /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine1_Control1_submitted/results
ln -s /srv/gs1/projects/scg/Scoring/results/human/GM12878/UCD_Control /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine1_Control2_submitted/results
ln -s /srv/gs1/projects/scg/Scoring/results/human/GM12878/IgG_Rabbit_Control /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine1_Control3_submitted/results

ln -s /srv/gs1/projects/scg/Scoring/results/human/K562/Control_MouseIgG /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine2_Control4_submitted/results
ln -s /srv/gs1/projects/scg/Scoring/results/human/K562/Control_Std /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine2_Control5_submitted/results
ln -s /srv/gs1/projects/scg/Scoring/results/human/K562/Control_Farnham /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine2_Control6_submitted/results
ln -s /srv/gs1/projects/scg/Scoring/results/human/K562/Control_Harvard /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine2_Control7_submitted/results

ln -s /srv/gs1/projects/scg/Scoring/results/human/hES/Control4 /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine9_Control8_submitted/results
ln -s /srv/gs1/projects/scg/Scoring/results/human/hES/Control3 /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine9_Control9_submitted/results
ln -s /srv/gs1/projects/scg/Scoring/results/human/hES/Control4 /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine9_Control10_submitted/results

ln -s /srv/gs1/projects/scg/Scoring/results/human/HepG2/Control /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine4_Control11_submitted/results
ln -s /srv/gs1/projects/scg/Scoring/results/human/HepG2/UCD_Control /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine4_Control12_submitted/results
ln -s /srv/gs1/projects/scg/Scoring/results/human/HepG2/Control_V2/ /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine4_Control13_submitted/results
ln -s /srv/gs1/projects/scg/Scoring/results/human/HepG2/Control_V2/ /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine4_Control14_submitted/results

ln -s /srv/gs1/projects/scg/Scoring/results/human/HeLa/Control_MouseIgG /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine6_Control15_submitted/results
ln -s /srv/gs1/projects/scg/Scoring/results/human/HeLa/Control /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine6_Control16_submitted/results
ln -s /srv/gs1/projects/scg/Scoring/results/human/HeLa/Control_UCD /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine6_Control17_submitted/results
ln -s /srv/gs1/projects/scg/Scoring/results/human/HeLa/Control_Yale /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine6_Control18_submitted/results

ln -s /srv/gs1/projects/scg/Scoring/results/mouse/CH12/Rabbit_IgG_mm9_female /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine209_Control19_submitted/results
ln -s /srv/gs1/projects/scg/Scoring/results/mouse/CH12/ZM_Control /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine209_Control20_submitted/results
ln -s /srv/gs1/projects/scg/Scoring/results/mouse/CH12/Control3 /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine209_Control21_submitted/results

ln -s /srv/gs1/projects/scg/Scoring/results/mouse/MEL/Control /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine223_Control22_submitted/results
ln -s /srv/gs1/projects/scg/Scoring/results/mouse/MEL/Control_ZM /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine223_Control23_submitted/results
ln -s /srv/gs1/projects/scg/Scoring/results/mouse/MEL/Control2 /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine223_Control24_submitted/results
ln -s /srv/gs1/projects/scg/Scoring/results/mouse/MEL/Control4 /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine223_Control25_submitted/results
ln -s /srv/gs1/projects/scg/Scoring/results/mouse/MEL/Control5 /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine223_Control26_submitted/results


#Add INPUTS
ln -s /srv/gs1/projects/scg/Scoring/inputs/human/GM12878/Control_SL_V2 /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine1_Control1_submitted/inputs
ln -s /srv/gs1/projects/scg/Scoring/inputs/human/GM12878/UCD_Control /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine1_Control2_submitted/inputs
ln -s /srv/gs1/projects/scg/Scoring/inputs/human/GM12878/IgG_Rabbit_Control /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine1_Control3_submitted/inputs

ln -s /srv/gs1/projects/scg/Scoring/inputs/human/K562/Control_MouseIgG /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine2_Control4_submitted/inputs
ln -s /srv/gs1/projects/scg/Scoring/inputs/human/K562/Control_Std /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine2_Control5_submitted/inputs
ln -s /srv/gs1/projects/scg/Scoring/inputs/human/K562/Control_Farnham /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine2_Control6_submitted/inputs
ln -s /srv/gs1/projects/scg/Scoring/inputs/human/K562/Control_Harvard /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine2_Control7_submitted/inputs

ln -s /srv/gs1/projects/scg/Scoring/inputs/human/hES/Control4 /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine9_Control8_submitted/inputs
ln -s /srv/gs1/projects/scg/Scoring/inputs/human/hES/Control3 /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine9_Control9_submitted/inputs
ln -s /srv/gs1/projects/scg/Scoring/inputs/human/hES/Control4 /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine9_Control10_submitted/inputs

ln -s /srv/gs1/projects/scg/Scoring/inputs/human/HepG2/Control /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine4_Control11_submitted/inputs
ln -s /srv/gs1/projects/scg/Scoring/inputs/human/HepG2/UCD_Control /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine4_Control12_submitted/inputs
ln -s /srv/gs1/projects/scg/Scoring/inputs/human/HepG2/Control_V2/ /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine4_Control13_submitted/inputs
ln -s /srv/gs1/projects/scg/Scoring/inputs/human/HepG2/Control_V2/ /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine4_Control14_submitted/inputs

ln -s /srv/gs1/projects/scg/Scoring/inputs/human/HeLa/Control_MouseIgG /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine6_Control15_submitted/inputs
ln -s /srv/gs1/projects/scg/Scoring/inputs/human/HeLa/Control /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine6_Control16_submitted/inputs
ln -s /srv/gs1/projects/scg/Scoring/inputs/human/HeLa/Control_UCD /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine6_Control17_submitted/inputs
ln -s /srv/gs1/projects/scg/Scoring/inputs/human/HeLa/Control_Yale /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine6_Control18_submitted/inputs

ln -s /srv/gs1/projects/scg/Scoring/inputs/mouse/CH12/Rabbit_IgG_mm9_female /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine209_Control19_submitted/inputs
ln -s /srv/gs1/projects/scg/Scoring/inputs/mouse/CH12/ZM_Control /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine209_Control20_submitted/inputs
ln -s /srv/gs1/projects/scg/Scoring/inputs/mouse/CH12/Control3 /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine209_Control21_submitted/inputs

ln -s /srv/gs1/projects/scg/Scoring/inputs/mouse/MEL/Control /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine223_Control22_submitted/inputs
ln -s /srv/gs1/projects/scg/Scoring/inputs/mouse/MEL/Control_ZM /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine223_Control23_submitted/inputs
ln -s /srv/gs1/projects/scg/Scoring/inputs/mouse/MEL/Control2 /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine223_Control24_submitted/inputs
ln -s /srv/gs1/projects/scg/Scoring/inputs/mouse/MEL/Control4 /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine223_Control25_submitted/inputs
ln -s /srv/gs1/projects/scg/Scoring/inputs/mouse/MEL/Control5 /srv/gs1/projects/scg/SNAP_Scoring/production/controls/human/CellLine223_Control26_submitted/inputs



