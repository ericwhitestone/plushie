
import time
import BaseHTTPServer
from urlparse import urlparse
from urlparse import parse_qs
import os
import sys
from PlushieDb import PlushieDb
from Barcode import Barcode
from RamsClient import RamsClient
from datetime import datetime
import json

HOST_NAME = '0.0.0.0'
PORT_NUMBER = 8080
DB_FILE = 'plushie.db'
QS_PARAM_BARCODE = 'barcode'
QS_PARAM_SCANNER_ID = 'scannerId'
COOLOFF_PERIOD_SECONDS = 60*60


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
		'''TODO: break this up, perhaps return a tuple 
			of (staus_code, msg) so calling function
			can just write the response. A bit hurried here
			and re-learning python at the same time as 
			getting something working   '''
		try:
			playAuthorized = False
			rams = RamsClient()
			validRams = False
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
			cooloffPeriodSec = self.retrieveCoolOff(data_access, scanner_id,
				 barcode_record)
			if cooloffPeriodSec:
				if barcode_record.freeplays > 0:
					self.useFreeplay(data_access, barcode_record)
					playAuthorized = True
			else:
				playAuthorized = True
			validRams = rams.isValidBarcode(barcode)	
			"""
				Set the authorized value to true only if it authenticates
				against rams/uber, and it was previously authorized 
				based on a local db check for a cooloff period on this
				scanner id
			"""	
			playAuthorize = playAuthorized and validRams
			a_id = data_access.insertAccessLog(barcode_record.pkey, 
				scanner_id, playAuthorized)
			if a_id is None:
				raise ServerErrorException("Failed to insert access record")
			#At this point, all the record keeping is finished, so commit	
			data_access.commit()

			if not validRams:
				self.send_response(404)	
				self.send_header("Content-type", "text/html")
				self.end_headers()
				self.wfile.write("Barcode not a valid Magfest barcode")
			elif playAuthorized:
				self.send_response(200)
			else:
				self.send_response(403)
				self.send_header("Content-type", "text/html")
				self.end_headers()
				self.wfile.write(("%d minutes %d seconds remaining "
					"in cooldown period") % ((cooloffPeriodSec/60),
					(cooloffPeriodSec % 60)))
		except (Exception) as e:
			data_access.rollback()
			raise
		finally:
			data_access.close()	
	def retrieveCoolOff(self, data_access, scannerId, barcode):
		''' @return seconds left in cooloff period ''' 
		last = data_access.retrieveLastPlayTime(barcode.pkey,
			scannerId)
		print ("Last play time for barcode %s on scanner %s: %s " % (
			barcode.value, scannerId, last))
		if last is None:
			return 0
		currentTime = datetime.now()
		lastDatetime = datetime.strptime(last,
			"%Y-%m-%d %H:%M:%S")
		print ("Current time: %s Lastplay: %s" %(
			currentTime, lastDatetime))
		difftime = currentTime - lastDatetime
		timeRemaining = (COOLOFF_PERIOD_SECONDS 
			- difftime.total_seconds())
			 
		return 0 if timeRemaining <= 0 else timeRemaining

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
