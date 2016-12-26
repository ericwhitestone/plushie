
import time
import BaseHTTPServer
from urlparse import urlparse
from urlparse import parse_qs
import os
import sys

HOST_NAME = '192.168.1.5'
PORT_NUMBER = 8080
DB_FILE = 'plushie.db'

class PlushieHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def do_GET(s):
		parsed_url = urlparse(s.path)
		if parsed_url.path == '/authorizedPlay':
			PlushieHandler.get_authorizedPlay(s, parsed_url)
		elif parsed_url.path == '/help':
			PlushieHandler.get_help(s, parsed_url)
		else:
			s.send_response(404)
		
		
	def get_authorizedPlay(s, parsed_url):
		
		qs_args = parse_qs(parsed_url.query)
		if 'barcode' not in qs_args:
			s.send_response(404)
			return
		if 'scannerId' not in qs_args:
			s.send_response(404)
			return
		barcode = qs_args['barcode']
		scanner_id = qs_args['scannerId']
		print ( 'received args: %s' % qs_args)
		"""Respond to GET"""
		s.send_response(200)
		s.send_header("Content-type", "application/json")
		s.end_headers()
		s.wfile.write("{status:ok}")

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
	print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass
	httpd.server_close()
	print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)
