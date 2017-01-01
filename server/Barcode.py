


class Barcode(object):

	def __init__(self):
		self.pkey = None
		self.value = None
		self.freeplays = None
		self.addedByAdmin = None
	def __str__(self):
		return ( ("Pkey: %s Value: %s Free Plays:"
			" %s Added By Admin: %s") % 
			(self.pkey, self.value,
			 self.freeplays, self.addedByAdmin))

	
