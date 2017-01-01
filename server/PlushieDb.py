import sqlite3
from Barcode import Barcode

class PlushieDb:
	STMT_BARCODE_BY_ID = ("select pkey, barcode_value, "
		"freeplays, added_by_admin from barcode where pkey = ?;")
	STMT_BARCODE_BY_VALUE = ("select pkey, barcode_value, "
	"freeplays, added_by_admin from barcode where barcode_value = ?;")

	STMT_INSERT_ACCESS_LOG = ("insert into access_log(barcode_fk, scanner_id)"
		" values(?,?);")
	STMT_INSERT_BARCODE =("insert into barcode(barcode_value) values(?);")
		
	def __init__(self, dbfile):
		self.dbfile = dbfile
		self.con = sqlite3.connect(self.dbfile) 
	
	def rollback(self):
		self.con.rollback()	
	def commit(self):
		self.con.commit()
	def close(self):
		self.con.close()

	def insertAccessLog(self, barcodePkey, scannerId):
		cur = self.con.cursor()
		cur.execute(PlushieDb.STMT_INSERT_ACCESS_LOG, (barcodePkey,
			scannerId));
		if cur.rowcount != 1:
			return None
		return cur.lastrowid

	def insert_barcode(self, barcodeValue):
		cur = self.con.cursor()
		cur.execute(PlushieDb.STMT_INSERT_BARCODE, (barcodeValue,))
		if cur.rowcount != 1:
			return None
		return cur.lastrowid 
			
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
