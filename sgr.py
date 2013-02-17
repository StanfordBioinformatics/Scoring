class SGR:
	
	def __init__(self, chr, coordinate, signal):
		self.chr = chr
		self.coordinate = coordinate
		self.signal = signal
		
	def __str__(self):
		return '\t'.join([self.chr, str(self.coordinate), str(self.signal)])
		
		
