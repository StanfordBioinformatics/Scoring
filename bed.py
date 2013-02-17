class PeakSeqBED:
	
	def __init__(self, chr, start, stop, sample_tags, control_tags, enrichment,
					excess, p_value, q_value=0.0, localmax=0):
		self.chr = chr
		self.start = int(start)
		self.stop = int(stop)
		self.sample_tags = sample_tags
		self.control_tags = control_tags
		self.enrichment = enrichment
		self.excess = excess
		self.p_value = float(p_value)
		self.q_value = float(q_value)
		self.localmax = localmax
		
	def __str__(self):
		return '\t'.join([self.chr, str(self.start), str(self.stop), self.sample_tags,
							self.control_tags, self.enrichment, self.excess,
							str(self.localmax), str(self.p_value), str(self.q_value)])
							
	def __cmp__(self, other):
		'''Compare on p_value'''
		return cmp(self.p_value, other.p_value)
		
class PeakSeqBEDParser:

	def __init__(self):
		pass
		
	def parse(self, line):
		fields = line.rstrip('\n').split('\t')
		if len(fields) == 8:
			return PeakSeqBED(
								chr=fields[0],
								start=fields[1],
								stop=fields[2],
								sample_tags=fields[3],
								control_tags=fields[4],
								enrichment=fields[5],
								excess=fields[6],
								p_value=float(fields[7])
							)
		elif len(fields) == 10:
			return PeakSeqBED(
								chr=fields[0],
								start=fields[1],
								stop=fields[2],
								sample_tags=fields[3],
								control_tags=fields[4],
								enrichment=fields[5],
								excess=fields[6],
								localmax=fields[7],
								p_value=fields[8],
								q_value=fields[9],
							)
		else:
			raise Exception("Incorrect number of fields.  Found %i expected 8 or 10." % len(fields))
			
class NarrowPeakBED(PeakSeqBED):
	def __init__(self, chr, start, stop, name, score, strand, signal_value, p_value, q_value, peak):
		self.chr = chr
		self.start = int(start)
		self.stop = int(stop)
		self.name = name
		self.score = int(score)
		self.strand = strand
		self.signal_value = float(signal_value)
		self.p_value = float(p_value)
		self.q_value = float(q_value)
		self.peak = int(peak)
		
	def __str__(self):
		return '\t'.join([self.chr, str(self.start), str(self.stop), self.name, str(self.score), self.strand, str(self.signal_value), str(self.p_value), str(self.q_value), str(self.peak),])
			
class NarrowPeakBEDParser:
	def __init__(self):
		pass
		
	def parse(self, line):
		fields = line.rstrip('\n').split('\t')
		if len(fields) != 10:
			raise Exception("Incorrect number of fields.  Found %i, expected 10." % len(fields))
		return NarrowPeakBED(
								chr=fields[0],
								start=fields[1],
								stop=fields[2],
								name=fields[3],
								score=fields[4],
								strand=fields[5],
								signal_value=fields[6],
								p_value=fields[7],
								q_value=fields[8],
								peak=fields[9],
							)
		
