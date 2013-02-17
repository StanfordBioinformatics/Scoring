#!/bin/env python

### NOTE:  Assuming read file has already been filtered for only uniquely
## mappable reads.

import sys

def main(read_file, output_file=None, name=None):
	rf = open(read_file, 'r')
	chrs = {}
	m_1 = 0
	m_distinct = 0
	if not name:
		name = read_file.split('/')[-1]
	for line in rf:
		if line.startswith('@'):
			continue
		fields = line.rstrip('\n').split('\t')
		if read_file.endswith('_eland.txt'):
			chr = fields[6]
			start = int(fields[7])
		else:
			chr = fields[2]
			start = int(fields[3])
		if chr not in chrs:
			chrs[chr] = {start:1}
			m_1 += 1
			m_distinct += 1
		elif start not in chrs[chr]:
			chrs[chr][start] = 1
			m_1 += 1
			m_distinct += 1
		else:
			chrs[chr][start] += 1
			if chrs[chr][start] == 2:
				m_1 -= 1

	if not output_file:
		print name, m_1, m_distinct, float(m_1) / float(m_distinct)
	else:
		of = open(output_file, 'a')
		of.write('\t'.join([name, str(m_1), str(m_distinct), str(float(m_1) / float(m_distinct)),]) + '\n')
		of.close()
	
if __name__ == '__main__':
	if len(sys.argv) == 2:
		main(sys.argv[1])
	if len(sys.argv) == 3:
		main(sys.argv[1], sys.argv[2])
	if len(sys.argv) == 4:
		main(sys.argv[1], sys.argv[2], sys.argv[3])
	else:
		print "Usage:  calc_pcb.py <SAM or eland file> [output_stats_file] [name]"
		raise SystemExit(1)
	
