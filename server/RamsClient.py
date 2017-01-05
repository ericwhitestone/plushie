from rpctools.jsonrpc import ServerProxy

BASE_URL = "https://super2017.uber.magfest.org:4444/jsonrpc"

# the client certificate .crt provided to you by an administrator
your_client_cert_crt = "rams_client.crt"

# the client certificate .key provided to you by an administrator
your_client_cert_key = "rams_client.key"

service = ServerProxy(
    uri=BASE_URL,
    cert_file=your_client_cert_crt,
    key_file=your_client_cert_key
)


class RamsClient(object):
	
	
	def isValidBarcode(self, barcode):
		record = None
		''' Reach out to rams database; check to see if barcode is
		valid for this event. 
		@return True if valid, False if not''' 
		try:
			record = service.barcode.lookup_attendee_from_barcode(barcode_value=barcode)
		except Exception as e:
			print ("The following occured attempting to authenticate barcode: %s "
				"against the rams database: %s" % (barcode, e)) 
		if record is None:
			return False
		else:
			print ("Received record from rams: %s" % record)
			return True
			#print ("Rams auth currently being bypassed: Modify RamsClient.py "
			#	"and set proper parameters")	
			#''' Return False here when wiring in ''' 

		return True
