#!/bin/env python

### NOTE:  Assuming read file has already been filtered for only uniquely
## mappable reads.

import sys

def main(read_file, filtered_eland, output_file=None):
	rf = open(read_file, 'r')
	fsam = open(filtered_eland, 'w')
	chrs = {}
	m_1 = 0
	m_distinct = 0
	for line in rf:
		if line.startswith('@'):
			fsam.write(line)
			continue
		fields = line.rstrip('\n').split('\t')
		chr = fields[6]
		start = int(fields[7])
		if chr not in chrs:
			chrs[chr] = {start:1}
			m_1 += 1
			m_distinct += 1
			fsam.write(line)
		elif start not in chrs[chr]:
			chrs[chr][start] = 1
			m_1 += 1
			m_distinct += 1
			fsam.write(line)
		else:
			chrs[chr][start] += 1
			if chrs[chr][start] == 2:
				m_1 -= 1

	if not output_file:
		print read_file.split('/')[-1], m_1, m_distinct, float(m_1) / float(m_distinct)
	else:
		of = open(output_file, 'a')
		of.write('\t'.join([read_file.split('/')[-1], str(m_1), str(m_distinct), str(float(m_1) / float(m_distinct)),]) + '\n')
		of.close()
	
if __name__ == '__main__':
	if len(sys.argv) == 3:
		main(sys.argv[1], sys.argv[2])
	if len(sys.argv) == 4:
		main(sys.argv[1], sys.argv[2], sys.argv[3])
	else:
		print "Usage:  filter_dup_reads_eland.py <ELAND file> <Filtered ELAND file> [stats_output_file]"
		raise SystemExit(1)
	
