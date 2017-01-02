
import time
import BaseHTTPServer
from urlparse import urlparse
from urlparse import parse_qs
import os
import sys
from PlushieDb import PlushieDb
from Barcode import Barcode
from RamsClient import RamsClient
import json

HOST_NAME = '0.0.0.0'
PORT_NUMBER = 8080
DB_FILE = 'plushie.db'
QS_PARAM_BARCODE = 'barcode'
QS_PARAM_SCANNER_ID = 'scannerId'

class ServerErrorException(Exception):
	pass
class NotFoundException(Exception):
	pass
class PlushieHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	
		
	def do_GET(s):
		parsed_url = urlparse(s.path)
		if parsed_url.path == '/barcode':
			PlushieHandler.get_barcode(s, parsed_url)
		elif parsed_url.path == '/help':
			PlushieHandler.get_help(s, parsed_url)
		else:
			s.send_response(404)

	def do_PUT(s):
		parsed_url = urlparse(s.path)
		if parsed_url.path == '/authorizedPlay':
			try:
				PlushieHandler.put_authorizedPlay(s, parsed_url)
			except (NotFoundException) as e:
				print(e)
				s.send_response(404)
				s.send_header("Content-type", "text/html")
				s.end_headers()
				s.wfile.write(e)
			except (ServerErrorException) as e:
				print (e)
				s.send_response(500)
				s.send_header("Content-type", "text/html")
				s.end_headers()
				s.wfile.write(e)
		else:
			s.send_response(404)

	def parse_params(self, parsed_url):
		''' return dict of the url params, null if invalid '''
		qs_args = parse_qs(parsed_url.query)	
		if QS_PARAM_BARCODE not in qs_args:
			return None
		if QS_PARAM_SCANNER_ID not in qs_args:
			return None
		return qs_args
	
	def put_authorizedPlay(self, parsed_url):
		try:
			playAuthorized = False
			rams = RamsClient()
			data_access = PlushieDb(DB_FILE)	
			qs_args = PlushieHandler.parse_params(self, parsed_url)
			if qs_args is None:
				raise NotFoundException("Invalid arguments")
			scanner_id = qs_args[QS_PARAM_SCANNER_ID][0]
			barcode = qs_args[QS_PARAM_BARCODE][0]
			barcode_record = (data_access.retrieveBarcodeByValue(
				barcode))

			if barcode_record is None:
				pkey = data_access.insert_barcode(barcode)		
				if pkey is None:
					raise ServerErrorException("Failed inserting "
						"record in db")
				barcode_record = data_access.retrieveBarcodeById(pkey)
			if barcode_record is None:
				raise ServerErrorException("Failed retrieving new barcode")
			if self.requiresFreeplay(data_access, barcode_record): 
				if barcode_record.freeplays > 0:
					self.useFreeplay(data_access, barcode_record)
					playAuthorized = True
			else:
				playAuthorized = True
					
			a_id = data_access.insertAccessLog(barcode_record.pkey, 
				scanner_id, playAuthorized)
			if a_id is None:
				raise ServerErrorException("Failed to insert access record")	
			data_access.commit()
			data_access.close()
			#If everything up to this point was ok, but 
			#is an invalid barcode, commit the transaction
			#to store all accesses, but send back a not found
			if not rams.isValidBarcode(barcode):
				self.send_response(404)	
				self.send_header("Content-type", "text/html")
				self.end_headers()
				self.wfile.write("Barcode not valid RAMS barcode")
			elif playAuthorized:
				self.send_response(200)
			else:
				self.send_response(403)
				self.send_header("Content-type", "text/html")
				self.end_headers()
				self.wfile.write("Must wait")
		except (Exception) as e:
			data_access.rollback()
			data_access.close()
			raise

	def requiresFreeplay(self, data_access, barcode):
		return False

	def useFreeplay(self, data_access, barcode):
		print("Current freeplays: %d" % barcode.freeplays)
		barcode.freeplays = barcode.freeplays - 1
		update_success = data_access.updateFreeplays(barcode.pkey,
			barcode.freeplays)
		if update_success is not True:
			raise ServerErrorException("Failed updating freeplays")
		print(("Using freeplay for %s, "
			"freeplays remaining: %d" % (
			 barcode.value,
			 barcode.freeplays)))

	def get_barcode(self, parsed_url):
		data_access = PlushieDb(DB_FILE)	
		qs_args = parse_qs(parsed_url.query)	
		if QS_PARAM_BARCODE not in qs_args:
			self.send_response(404)
			return
		
		barcode = qs_args['barcode']
		print ( 'received args: %s' % qs_args)
		barcode_record = (
			data_access.retrieveBarcodeByValue(barcode))
		if barcode_record is None:
			self.send_response(404)
			self.wfile.write("Barcode is not in local db")
			return
				
		"""Respond to GET"""
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		self.wfile.write(json.dumps(barcode_record.__dict__))

	def get_help(s, parsed_url):
		
		s.send_response(200)
		s.send_header("Content-type", "application/json")
		s.end_headers()
		s.wfile.write("/authorizedPlay?barcode=<barcode>"
		"&;scannerId=<scannerId>\n\n")
		s.wfile.write("GET\n")
		s.wfile.write("\tQuery to see if barcode is "
		"authorized from scannerId\n")
		s.wfile.write("PUT\n")
		s.wfile.write("\tUpdate an authorized play for barcode "
		"from scannerId\n")	

	
if __name__ == '__main__':
	try:
		statinfo = os.stat(DB_FILE)
	except:
		print ('The file %s has not been created.\n'
		'Run the db create script before starting the server'
		 % DB_FILE)
		sys.exit(2)
	server_class = BaseHTTPServer.HTTPServer
	httpd = server_class((HOST_NAME, PORT_NUMBER), PlushieHandler)
	print time.asctime(), "Server Started - %s:%s" % (HOST_NAME, PORT_NUMBER)
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass
	httpd.server_close()
	print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)
