import sqlite3
from Barcode import Barcode

class PlushieDb:
	STMT_BARCODE_BY_ID = ("select pkey, barcode_value, "
		"freeplays, added_by_admin from barcode where pkey = ?;")
	STMT_BARCODE_BY_VALUE = ("select pkey, barcode_value, "
	"freeplays, added_by_admin from barcode where barcode_value = ?;")

	STMT_INSERT_ACCESS_LOG = ("insert into access_log(barcode_fk, "
		"scanner_id, authorized)"
		" values(?,?,?);")
	STMT_INSERT_BARCODE =("insert into barcode(barcode_value) values(?);")
	STMT_UPDATE_FREEPLAYS = ("update barcode set freeplays = ? "
		"where pkey = ?;")

	STMT_RETRIEVE_LASTPLAY = ("select access_log.access_timestamp, "
		"access_log.scanner_id, access_log.authorized " 
		"from access_log join "
		"barcode on access_log.barcode_fk = barcode.pkey "
		"where barcode.pkey = ? "
		"and access_log.authorized = 1 "
		"and access_log.scanner_id = ? order "
		"by access_timestamp DESC limit 1;")
		
	def __init__(self, dbfile):
		self.dbfile = dbfile
		self.con = sqlite3.connect(self.dbfile) 
	
	def rollback(self):
		print("Rolling back... ")
		self.con.rollback()	
	def commit(self):
		print("Committing... ")
		self.con.commit()
	def close(self):
		print("Closing connection to DB")
		self.con.close()
	
	def retrieveLastPlayTime(self, barcodePkey, scannerId):
		''' @return datetime of last play for this scanner ''' 
		cur = self.con.cursor()
		cur.execute(PlushieDb.STMT_RETRIEVE_LASTPLAY, 
			(barcodePkey, scannerId))
		retval = cur.fetchone()
		if retval is None: 
			return None
		return retval[0]

	def insertAccessLog(self, barcodePkey, scannerId, authorized):
		cur = self.con.cursor()
		cur.execute(PlushieDb.STMT_INSERT_ACCESS_LOG, (barcodePkey,
			scannerId, authorized));
		if cur.rowcount != 1:
			return None
		return cur.lastrowid

	def insert_barcode(self, barcodeValue):
		cur = self.con.cursor()
		cur.execute(PlushieDb.STMT_INSERT_BARCODE, (barcodeValue,))
		if cur.rowcount != 1:
			return None
		return cur.lastrowid 

	def updateFreeplays(self, pkey, freeplaysValue):
		cur = self.con.cursor()
		cur.execute(PlushieDb.STMT_UPDATE_FREEPLAYS, (freeplaysValue, 
			pkey))
		print("Updating barcode pkey %d with freeplays %d" % (
			pkey, freeplaysValue))

		if cur.rowcount != 1:
			print "Failed updating"
			return False 
		print "Successfully updated"
		return True
		
	def retrieveBarcodeById(self, bc_id):
		barcode = None
		cur = self.con.cursor()
		print ("Looking up barcode ID: %d" % bc_id)
		cur.execute(PlushieDb.STMT_BARCODE_BY_ID, (bc_id,))
	        bc_tuple = cur.fetchone()	
		if bc_tuple is not None:
			barcode = Barcode()
			barcode.pkey = bc_tuple[0]
			barcode.value = bc_tuple[1]
			barcode.freeplays = bc_tuple[2]
			barcode.addedByAdmin = bc_tuple[3]
		return barcode

	def retrieveBarcodeByValue(self, bc_value):
		barcode = None
		cur = self.con.cursor()
		print ('Looking up barcode value %s' % bc_value)
		cur.execute(PlushieDb.STMT_BARCODE_BY_VALUE, (bc_value,))
	        bc_tuple = cur.fetchone()	
		if bc_tuple is not None:
			barcode = Barcode()
			barcode.pkey = bc_tuple[0]
			barcode.value = bc_tuple[1]
			barcode.freeplays = bc_tuple[2]
			barcode.addedByAdmin = bc_tuple[3]
		return barcode
