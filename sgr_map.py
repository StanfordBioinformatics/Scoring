#!/bin/env python

from bisect import bisect, bisect_left
from sgr import SGR

class SGRChr:
	def __init__(self, coordinates, scores):
		self.coordinates = coordinates
		self.scores = scores
		
	def score(self, coordinate):
		coordinate = int(coordinate)
		if coordinate > self.coordinates[-1]:
			return self.scores[-1]
		else:
			return self.scores[bisect(self.coordinates, coordinate)]
		
	def next_coordinate(self, coordinate):
		coordinate = int(coordinate)
		index = bisect_left(self.coordinates, coordinate)
		if (index + 2) >= len(self.coordinates):
			return 9999999999
		else:
			return self.coordinates[index + 1]
		
class SGRMap:
	def __init__(self):
		self.chrs = {}
		
	def load_from_file(self, filename, chr):
		f = open(filename, 'r')
		coords = []
		scores = [0,]
		for line in f:
			fields = line.rstrip('\n').split('\t')
			s = SGR(fields[0], int(fields[1]), int(fields[2]))
			if not chr == s.chr:
				raise Exception('SGR file must only have one chromosome. [found %s expected %s]' % (s.chr, chr))
			coords.append(s.coordinate)
			scores.append(s.signal)
		if chr in self.chrs:
			raise Exception('Chromosome %s already exists in map' % chr)
		self.chrs[chr] = SGRChr(coords, scores)
		f.close()

	def remove_sgr_chr(self, chr):
		if chr in self.chrs:
			self.chrs[chr] = None
		
	def score(self, chr, coordinate):
		if chr not in self.chrs:
			raise Exception('Chromosome %s not in SGR Map' % chr)
		return self.chrs[chr].score(coordinate)
		
	def next_coordinate(self, chr, coordinate):
		if chr not in self.chrs:
			raise Exception('Chromosome %s not in SGR Map' % chr)
		return self.chrs[chr].next_coordinate(coordinate)
		
	def localmax(self, chr, start, stop):
		start = int(start)
		stop = int(stop)
		localstart = start
		localstop = stop
		max = self.score(chr, start)
		i = self.next_coordinate(chr, start)
		while i < stop:
			if self.score(chr, i) < max and localstop > i:
				localstop = i - 1
			if self.score(chr, i) > max:
				localstart = i
				localstop = stop
				max = self.score(chr, i)
			i = self.next_coordinate(chr, i)
		midpoint = (localstart + localstop) / 2
		return SGR(chr, midpoint, max)
		
	def localmaxes(self, sgr_file, chr, hits):
		self.load_from_file(sgr_file, chr)
		localmaxes = []
		for hit in hits:
			if hit.chr != chr:
				raise Exception("Hit must be in chromosome %s" % chr)
			localmaxes.append(self.localmax(hit.chr, hit.start, hit.stop))
		self.remove_sgr_chr(chr)
		return localmaxes
			
	
