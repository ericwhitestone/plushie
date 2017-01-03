


class ScannerBuffer(object):

	def __init__(self):
		self.shiftOn = False
		self.scannerBuffer = ""
	
	def reset(self):
		self.scannerBuffer = ""
		self.shiftOn = False
			
	
