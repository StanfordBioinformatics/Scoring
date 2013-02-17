import re
import sys
import gzip
import bz2
import traceback

eland_match_re = re.compile(r'^([\w\.]+):(\d+)([FR])(\w+)$')  # Eland Match Description
eland_match_no_chr_re = re.compile(r'^(\d+)([FR])(\w+)$') # Eland Match Description without the leading chr name


class ElandMatch:
	def __init__(self, chr_name, coordinate, strand, match_code):
		self.chr_name = chr_name
		self.coordinate = coordinate
		self.strand = strand
		self.match_code = match_code
		
	def number_of_mismatches(self):
		if self.match_code == 'U0':
			return 0
		elif self.match_code == 'U1':
			return 1
		elif self.match_code == 'U2':
			return 2
		else:
			raise Exception("Invalid match code %s" % self.match_code)
			

class ElandExtendedMatch(ElandMatch):

	def __init__(self, chr_name, coordinate, strand, match_description):
		self.chr_name = chr_name
		self.coordinate = coordinate
		self.strand = strand
		self.match_description = match_description
		
	def number_of_mismatches(self):
		count = 0
		for c in self.match_description:
			if c in ['A', 'T', 'C', 'G']:
				count += 1
		return count
		
	def match_code(self):
		return 'U' + str(self.number_of_mismatches())
	
	def __str__(self):
		return '%s:%s%s%s' % (self.chr_name, self.coordinate, self.strand, self.match_description)
		
		
class ElandMultiMatch(ElandExtendedMatch):

	def number_of_mismatches(self):
		return int(self.match_description)
		

class ElandHit:

	def __init__(self, read_name, sequence, match_code, num_exact, num_1_error,
					num_2_error, chr_name='', coordinate='', strand='', 
					n_interpretation='DD'):
		max_length = 32
		self.read_name = read_name
		self.sequence = sequence
		self.match_code = match_code
		self.num_exact = num_exact
		self.num_1_error = num_1_error
		self.num_2_error = num_2_error
		self.chr_name = chr_name
		self.coordinate = coordinate
		self.strand = strand
		self.n_interpretation = 'DD'
		if len(self.sequence) > max_length:
			if self.strand == 'F':
				self.sequence = self.sequence[:max_length]
			elif self.strand == 'R':
				self.sequence = self.sequence[-max_length:]
				self.coordinate = int(self.coordinate) + (len(self.sequence) - max_length)
				
	def best_matches(self):
		if self.match_code not in ['U0', 'U1', 'U2']:
			return []
		return[ElandMatch(self.chr_name, self.coordinate, self.strand, self.match_code),]
		
	def convert_to_eland(self):
		return self
		
	def __str__(self):
		return '\t'.join([self.read_name, self.sequence, self.match_code, 
							str(self.num_exact), str(self.num_1_error),
							str(self.num_2_error), self.chr_name,
							str(self.coordinate), self.strand, 
							self.n_interpretation])
							
class ElandHitParser:

	def __init__(self):
		pass
	
	def parse(self, line):
		fields = line.rstrip('\n').split('\t')
		if len(fields) > 6:
			return ElandHit(
								read_name=fields[0],
								sequence=fields[1],
								match_code=fields[2],
								num_exact=int(fields[3]),
								num_1_error=int(fields[4]),
								num_2_error=int(fields[5]),
								chr_name=fields[6],
								coordinate=fields[7],
								strand=fields[8],
								n_interpretation=fields[9]
							)
		elif len(fields) > 3:
			return ElandHit(
								read_name=fields[0],
								sequence=fields[1],
								match_code=fields[2],
								num_exact=int(fields[3]),
								num_1_error=int(fields[4]),
								num_2_error=int(fields[5]),
							)
		else:
			return ElandHit(
								read_name=fields[0],
								sequence=fields[1],
								match_code=fields[2],
								num_exact=0,
								num_1_error=0,
								num_2_error=0,
							)
						
class ElandExtendedParser:
	
	def __init__(self):
		pass
		
	def parse(self, line):
		fields = line.rstrip('\n').split('\t')
		return ElandExtendedLine(
									read_name=fields[0],
									sequence=fields[1],
									initial_matches=fields[2],
									matches=self.form_matches(fields[3]),
								)
								
	def form_matches(self, line):
		matches = []
		if line == '-':
			return []
		fields = line.split(',')
		for f in fields:
			if ':' in f:
				m = eland_match_re.match(f)
				if not m:
					raise Exception("Eland match description invalid.\n%s" % line)
				matches.append(ElandExtendedMatch(m.group(1), m.group(2), m.group(3), m.group(4)))
				last_chr = m.group(1)
			else:
				# Consecutive matches in the same chromosome may omit the chr
				# portion of description, thus the parsing is slightly different
				m = eland_match_no_chr_re.match(f)
				if not m:
					raise Exception("Eland match description invalid.\n%s" % line)
				matches.append(ElandExtendedMatch(last_chr, m.group(1), m.group(2), m.group(3)))
		return matches
		

class ElandMultiParser(ElandExtendedParser):

	def __init__(self):
		pass
		
	def parse(self, line):
		fields = line.rstrip('\n').split('\t')
		if len(fields) < 4:
			matches = []
		else:
			matches = self.form_matches(fields[3])
		return ElandMultiLine(
								read_name=fields[0],
								sequence=fields[1],
								initial_matches=fields[2],
								matches=matches,
								)
								
								

class ElandExtendedLine:

	def __init__(self, read_name, sequence, initial_matches, matches):
		self.read_name = read_name
		self.sequence = sequence
		self.initial_matches = initial_matches  # Not reliable
		self.matches = matches
							
	def __str__(self):
		s = '\t'.join([self.read_name, self.sequence, self.initial_matches])
		s += '\t'
		s += ','.join([str(m) for m in self.matches])
		
		
	def best_matches(self):
		'''Returns list of matches with the lowest number of mismatches'''
		
		match_list = []
		best_mismatch = 999
		for m in self.matches:
			if m.number_of_mismatches() < best_mismatch:
				best_mismatch = m.number_of_mismatches()
				match_list = [m,]
			elif best_mismatch == m.number_of_mismatches():
				match_list.append(m)
			else:
				continue
		return match_list
		
	def convert_to_eland(self):
		'''Returns a regular Eland Hit line.  Only works for unique best
		matches'''
		
		if len(self.best_matches()) > 1:
			raise Exception("Can only convert unique hits.")
		elif len(self.best_matches()) == 0:
			raise Exception("No good matches.")
		m = self.best_matches()[0]
		if m.number_of_mismatches() > 2:
			raise Exception("More than two mismatches, cannot convert.")
		errors = [0, 0, 0]
		errors[m.number_of_mismatches()] = 1
		return ElandHit(self.read_name, self.sequence, m.match_code(),
						errors[0], errors[1], errors[2], m.chr_name, 
						m.coordinate, m.strand)

						
class ElandMultiLine(ElandExtendedLine):
	pass
	
	
class BwaSamLine:

	def __init__(self, qname, strand, chr, position, mapq, cigar, sequence, quality, edit_distance, mismatching_positions, num_best_hits, num_mismatches, alternative_hits=None):
		self.qname = qname
		self.strand = strand
		self.chr = chr
		self.position = position
		self.mapq = mapq
		self.cigar = cigar
		self.sequence = sequence
		self.quality = quality
		self.edit_distance = edit_distance
		self.mismatching_positions = mismatching_positions
		self.num_best_hits = num_best_hits
		self.num_mismatches = num_mismatches
		if alternative_hits is not None:
			self.alternative_hits = alternative_hits
		else:
			self.alternative_hits = []
		
	def convert_to_eland(self):
		'''Returns a regular Eland Hit line.'''
		match_code = 'U' + str(self.num_mismatches)
		if self.num_mismatches == 0:
			num_exact = 1
		else:
			num_exact = 0
		if self.num_mismatches == 1:
			num_1_error = 1
		else:
			num_1_error = 0
		if self.num_mismatches == 2:
			num_2_error = 1
		else:
			num_2_error = 0
		for h in self.alternative_hits:
			if h.num_mismatches == 0:
				num_exact += 1
			elif h.num_mismatches == 1:
				num_1_error += 1
			elif h.num_mismatches == 2:
				num_2_error += 1
		if self.strand == '+':
			strand = 'F'
		elif self.strand == '-':
			strand = 'R'
		return ElandHit(self.qname, self.sequence, match_code, num_exact, num_1_error, num_2_error, self.chr + '.fa', self.position, strand)
		
class BwaAlternativeHit:
	
	def __init__(self, chr, strand, position, cigar, num_mismatches):
		self.chr = chr
		self.strand = strand
		self.position = position
		self.cigar = cigar
		self.num_mismatches = num_mismatches
		
class BwaSamParser:

	def __init__(self):
		pass
		
	def parse(self, line):
		if line is None:
			raise Exception("Cannot parse line of NoneType")
		fields = line.rstrip('\n').split('\t')
		flag = int(fields[1])
		if flag & 0x0100 == 0x0100:
			raise Exception("Hit not primary alignment.  Do not use for scoring.")
		if flag & 0x0010 == 0x0010:
			strand = '-'
		else:
			strand = '+'
		if flag & 0x0004 == 0x0004:
			# No match
			return BwaSamLine(
							qname=fields[0],
							strand=strand,
							chr=fields[2],
							position=int(fields[3]),
							mapq=fields[4],
							cigar=fields[5],
							sequence=fields[9],
							quality=fields[10],
							edit_distance=0,
							mismatching_positions=0,
							num_best_hits=0,
							num_mismatches=0,
							alternative_hits=[]
						)
		
		tags = {}
		for unpacked_tag in fields[11:]:
			ts = unpacked_tag.split(':')
			if len(ts) != 3:
				continue
			tags[ts[0]] = ts[2]
		alt_hits = []
		if 'XA' in tags:
			for unpacked_hit in tags['XA'].split(':'):
				unpacked_hit = unpacked_hit.rstrip(';')
				hs = unpacked_hit.split(',')
				if len(hs) != 4:
					continue
				if int(hs[1]) < 0:
					h_strand = '-'
					hs[1] = int(hs[1]) * -1
				else:
					h_strand = '+'
					hs[1] = int(hs[1])
				alt_hits.append(BwaAlternativeHit(hs[0], strand, hs[1], hs[2], int(hs[3])))
			
		return BwaSamLine(
							qname=fields[0],
							strand=strand,
							chr=fields[2],
							position=int(fields[3]),
							mapq=fields[4],
							cigar=fields[5],
							sequence=fields[9],
							quality=fields[10],
							edit_distance=tags['NM'],
							mismatching_positions=tags['MD'],
							num_best_hits=int(tags['X0']),
							num_mismatches=int(tags['XM']),
							alternative_hits=alt_hits
						)

							
class BowtieSamParser:
	def __init__(self):
		pass
		
	def parse(self, line):
		if line is None:
			raise Exception("Cannot parse line of NoneType")
		fields = line.rstrip('\n').split('\t')
		flag = int(fields[1])
		if flag & 0x4 == 0x4:
			raise Exception("No reported alignments for read.")
		if flag & 0x10 == 0x10:
			strand = '-'
		else:
			strand = '+'
		tags = {}
		for unpacked_tag in fields[11:]:
			ts = unpacked_tag.split(':')
			if len(ts) != 3:
				continue
			tags[ts[0]] = ts[2]
		if 'XM' in tags:
			num_hits = int(tags['XM'])
		else:
			num_hits = 1
		return BowtieSamLine(
							qname=fields[0],
							strand=strand,
							chr=fields[2],
							position=int(fields[3]),
							mapq=fields[4],
							cigar=fields[5],
							sequence=fields[9],
							quality=fields[10],
							edit_distance=int(tags['NM']),
							mismatching_positions=tags['MD'],
							num_hits=num_hits
							)
							
class BowtieSamLine:
	def __init__(self, qname, strand, chr, position, mapq, cigar, sequence, quality, edit_distance, mismatching_positions, num_hits):
		self.qname = qname
		self.strand = strand
		self.chr = chr
		self.position = position
		self.mapq = mapq
		self.cigar = cigar
		self.sequence = sequence
		self.quality = quality
		self.edit_distance = edit_distance
		self.mismatching_positions = mismatching_positions
		self.num_hits = num_hits
		
	def convert_to_eland(self):
		'''Returns a regular Eland Hit line.'''
		match_code = 'U' + str(self.edit_distance)
		if self.edit_distance == 0:
			num_exact = 1
		else:
			num_exact = 0
		if self.edit_distance == 1:
			num_1_error = 1
		else:
			num_1_error = 0
		if self.edit_distance == 2:
			num_2_error = 1
		else:
			num_2_error = 0
		if self.strand == '+':
			strand = 'F'
		elif self.strand == '-':
			strand = 'R'
		return ElandHit(self.qname, self.sequence, match_code, num_exact, num_1_error, num_2_error, self.chr + '.fa', self.position, strand)
		
		
class ElandSamParser:
	def __init__(self):
		pass
		
	def parse(self, line):
		if line is None:
			raise Exception("Cannot parse line of NoneType")
		fields = line.rstrip('\n').split('\t')
		flag = int(fields[1])
		if flag & 0x4 == 0x4:
			raise Exception("No reported alignments for read.")
		if flag & 0x10 == 0x10:
			strand = '-'
		else:
			strand = '+'
		tags = {}
		for unpacked_tag in fields[11:]:
			ts = unpacked_tag.split(':')
			if len(ts) != 3:
				continue
			tags[ts[0]] = ts[2]
		if 'XA' in tags:
			num_hits = int(tags['XA']) + 1
		else:
			num_hits = 1
		return BowtieSamLine(
							qname=fields[0],
							strand=strand,
							chr=fields[2],
							position=int(fields[3]),
							mapq=fields[4],
							cigar=fields[5],
							sequence=fields[9],
							quality=fields[10],
							edit_distance=int(tags['NM']),
							mismatching_positions=tags['MD'],
							num_hits=num_hits
							)
							
class IlluminaSamParser:
	def __init__(self):
		pass
		
	def parse(self, line):
		if line is None:
			raise Exception("Cannot parse line of NoneType")
		fields = line.rstrip('\n').split('\t')
		flag = int(fields[1])
		if flag & 0x4 == 0x4:
			raise Exception("No reported alignments for read.")
		if flag & 0x10 == 0x10:
			strand = '-'
		else:
			strand = '+'
		tags = {}
		for unpacked_tag in fields[11:]:
			ts = unpacked_tag.split(':')
			if len(ts) != 3:
				continue
			tags[ts[0]] = ts[2]
		num_hits = 1 		# NOTE:  Illumina doesn't report this info, assume prefiltered
		mismatching_positions = 0
		for c in tags['XD']:
			if c in ['A','T','G','C']:
				mismatching_positions += 1
		return BowtieSamLine(
							qname=fields[0],
							strand=strand,
							chr=fields[2],
							position=int(fields[3]),
							mapq=fields[4],
							cigar=fields[5],
							sequence=fields[9],
							quality=fields[10],
							edit_distance=0,
							mismatching_positions=mismatching_positions,
							num_hits=num_hits
							)

class ElandFile:
	
	def __init__(self, file_path, mode='r'):
		if file_path.endswith('.gz'):
			self.file = gzip.open(file_path, mode)
		elif file_path.endswith('.bz2'):
			self.file = bz2.BZ2File(file_path, mode)
		else:
			self.file = open(file_path, mode)
		self.mode = mode
		self.parser = ElandHitParser()
		
	def next(self):
		while True:
			try:
				return self.parser.parse(self.file.next())
			except StopIteration:
				raise StopIteration
			except Exception, e:
				# Just skip the line if there's a parsing error
				sys.stderr.write(str(e) + '\n')
				#return self.parser.parse(self.file.next())
				continue
			
	def close(self):
		self.file.close()
		
	def seek(self, offset, whence=None):
		self.file.seek(offset, whence)
		
	def write(self, line):
		self.file.write(str(line) + '\n')
		
	def __iter__(self):
		return self
		
							
class ElandExtendedFile(ElandFile):
	
	def __init__(self, file_path, mode='r'):
		if file_path.endswith('.gz'):
			self.file = gzip.open(file_path, mode)
		elif file_path.endswith('.bz2'):
			self.file = bz2.BZ2File(file_path, mode)
		else:
			self.file = open(file_path, mode)
		self.mode = mode
		self.parser = ElandExtendedParser()
		
class ElandMultiFile(ElandFile):
	
	def __init__(self, file_path, mode='r'):
		if file_path.endswith('.gz'):
			self.file = gzip.open(file_path, mode)
		elif file_path.endswith('.bz2'):
			self.file = bz2.BZ2File(file_path, mode)
		else:
			self.file = open(file_path, mode)
		self.mode = mode
		self.parser = ElandMultiParser()
		
class BwaSamFile(ElandFile):
	
	def __init__(self, file_path, mode='r'):
		if file_path.endswith('.gz'):
			self.file = gzip.open(file_path, mode)
		elif file_path.endswith('.bz2'):
			self.file = bz2.BZ2File(file_path, mode)
		else:
			self.file = open(file_path, mode)
		self.mode = mode
		self.parser = BwaSamParser()
		self.current_line = self.file.next()
		self.line_num = 0
		self.file_path = file_path
		self.headers = []
		while self.current_line.startswith('@'):
			self.headers.append(self.current_line)
			self.current_line = self.file.next()
			self.line_num += 1
		
	def next(self):
		while True:
			line = self.current_line
			if line is None:
				raise StopIteration
			try:
				self.current_line = self.file.next()
				self.line_num += 1
				return self.parser.parse(line)
			except StopIteration:
				print "StopIteration:", self.file_path
				line = self.current_line
				self.current_line = None
				try:
					return self.parser.parse(line)
				except:
					continue
			except Exception, e:
				# Just skip the line if there's a parsing error
				traceback.print_exc()
				sys.stderr.write(str(self.line_num) + ': ' + self.current_line + str(e) + '\n')
				continue
			
class BowtieSamFile(ElandFile):

	def __init__(self, file_path, mode='r'):
		if file_path.endswith('.gz'):
			self.file = gzip.open(file_path, mode)
		elif file_path.endswith('.bz2'):
			self.file = bz2.BZ2File(file_path, mode)
		else:
			self.file = open(file_path, mode)
		self.mode = mode
		self.parser = BowtieSamParser()
		self.current_line = self.file.next()
		self.line_num = 0
		self.file_path = file_path
		self.headers = []
		while self.current_line.startswith('@'):
			self.headers.append(self.current_line)
			self.current_line = self.file.next()
			self.line_num += 1
		
	def next(self):
		while True:
			line = self.current_line
			if line is None:
				raise StopIteration
			try:
				self.current_line = self.file.next()
				self.line_num += 1
				return self.parser.parse(line)
			except StopIteration:
				print "StopIteration:", self.file_path
				line = self.current_line
				self.current_line = None
				try:
					return self.parser.parse(line)
				except:
					continue
			except Exception, e:
				# Just skip the line if there's a parsing error
				traceback.print_exc()
				sys.stderr.write(str(self.line_num) + ': ' + self.current_line + str(e) + '\n')
				continue
				
class ElandSamFile(ElandFile):

	def __init__(self, file_path, mode='r'):
		if file_path.endswith('.gz'):
			self.file = gzip.open(file_path, mode)
		elif file_path.endswith('.bz2'):
			self.file = bz2.BZ2File(file_path, mode)
		else:
			self.file = open(file_path, mode)
		self.mode = mode
		self.parser = ElandSamParser()
		self.current_line = self.file.next()
		self.line_num = 0
		self.file_path = file_path
		self.headers = []
		while self.current_line.startswith('@'):
			self.headers.append(self.current_line)
			self.current_line = self.file.next()
			self.line_num += 1
		
	def next(self):
		while True:
			line = self.current_line
			if line is None:
				raise StopIteration
			try:
				self.current_line = self.file.next()
				self.line_num += 1
				return self.parser.parse(line)
			except StopIteration:
				print "StopIteration:", self.file_path
				line = self.current_line
				self.current_line = None
				try:
					return self.parser.parse(line)
				except:
					continue
			except Exception, e:
				# Just skip the line if there's a parsing error
				traceback.print_exc()
				sys.stderr.write(str(self.line_num) + ': ' + self.current_line + str(e) + '\n')
				continue	
				
class IlluminaSamFile(ElandFile):

	def __init__(self, file_path, mode='r'):
		if file_path.endswith('.gz'):
			self.file = gzip.open(file_path, mode)
		elif file_path.endswith('.bz2'):
			self.file = bz2.BZ2File(file_path, mode)
		else:
			self.file = open(file_path, mode)
		self.mode = mode
		self.parser = IlluminaSamParser()
		self.current_line = self.file.next()
		self.line_num = 0
		self.file_path = file_path
		self.headers = []
		while self.current_line.startswith('@'):
			self.headers.append(self.current_line)
			self.current_line = self.file.next()
			self.line_num += 1
		
	def next(self):
		while True:
			line = self.current_line
			if line is None:
				raise StopIteration
			try:
				self.current_line = self.file.next()
				self.line_num += 1
				return self.parser.parse(line)
			except StopIteration:
				print "StopIteration:", self.file_path
				line = self.current_line
				self.current_line = None
				try:
					return self.parser.parse(line)
				except:
					continue
			except Exception, e:
				# Just skip the line if there's a parsing error
				traceback.print_exc()
				sys.stderr.write(str(self.line_num) + ': ' + self.current_line + str(e) + '\n')
				continue	
	
			
			
		
