
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
			PlushieHandler.put_authorizedPlay(s, parsed_url)
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
		rams = RamsClient()
		data_access = PlushieDb(DB_FILE)	
		qs_args = PlushieHandler.parse_params(self, parsed_url)
		if qs_args is None:
			self.send_response(404)
			data_access.close()
			return
		scanner_id = qs_args['scannerId']
		barcode = qs_args['barcode']
		barcode_record = data_access.retrieveBarcodeByValue(
			barcode)

		if barcode_record is None:
			if not rams.isValidBarcode(barcode):
				#TODO: add to garbage table
				self.send_response(404)
				self.wfile.write("Invalid barcode")
				data_access.close()
				return
			pkey = data_access.insert_barcode(barcode)		
			if pkey is None:
				self.send_response(500)
				self.wfile.write("Failed inserting record in db")	
				data_access.rollback()
				data_access.close()
				return
			barcode_record = data_access.retrieveBarcodeById(pkey)

		if barcode_record is None:
			self.send_response(500)
			self.wfile.write("Failed retrieving new barcode")
			data_access.close()
			data_access.rollback()
			return
		print("Inserting access log for %s" % barcode_record)
		a_id = data_access.insertAccessLog(str(barcode_record.pkey), 
			str(scanner_id))
		data_access.commit()
		data_access.close()
		if a_id is not None:
			self.send_response(200)
			self.wfile.write(a_id)
			return
		self.send_response(500)
		self.wfile.write("Failed to insert access record")	
			
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
		self.send_header("Content-type", "application/json")
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
