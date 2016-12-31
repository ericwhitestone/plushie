import sqlite3



class PlushieDb:
	STMT_BARCODE_BY_VALUE = ("select pkey, barcode_value "
	"freeplays, added_by_admin from barcode where barcode_value = ?")
		
	def __init__(self, dbfile):
		self.dbfile = dbfile
	
	def retrieveBarcode(self, bc_value):
		con = sqlite3.connect(self.dbfile)
		cur = con.cursor()
		print (PlushieDb.STMT_BARCODE_BY_VALUE)
		cur.execute(PlushieDb.STMT_BARCODE_BY_VALUE, (bc_value))
	        print cur.fetchone()	
