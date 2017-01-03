#!/usr/bin/python

#
# SUPER BETA APP FOR MAGFEST 2017
#
# Reads Linux input buffer for separate barcode scanners (HID devices)
# Authenticates against server
# If server says okay, coins up redemption machine for free play
#    GPIO triggered to coin up machine
# If server says not okay, echos this out to display at machine
#
# Written against Raspbian / Python 2.7 / RPi 3

# Configs still inline in code
#  -  Scanner ID for authentication URL to separate games
#  -  URL 
#  -  Error message delay
#  -  GPIO Pins



#
# Imports
#

import string
import time
import os
import pygame
import random
import requests
from ScannerBuffer import ScannerBuffer
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO! Check lib availability and run as root.")


#
# Var Inits
# 
usermessage=["","Booted","Up"]
usermessagetime=int(time.time())

#
# PyGame Screen Poop
#

class pyscope :
    screen = None;

    def __init__(self):
        "Ininitializes a new pygame screen using the framebuffer"
        # Based on "Python GUI in Linux frame buffer"
        # http://www.karoltomala.com/blog/?p=679
        disp_no = os.getenv("DISPLAY")
        if disp_no:
            print "I'm running under X display = {0}".format(disp_no)

        # Check which frame buffer drivers are available
        # Start with fbcon since directfb hangs with composite output
        drivers = ['fbcon', 'directfb', 'svgalib']
        found = False
        for driver in drivers:
            # Make sure that SDL_VIDEODRIVER is set
            if not os.getenv('SDL_VIDEODRIVER'):
                os.putenv('SDL_VIDEODRIVER', driver)
            try:
                pygame.display.init()
            except pygame.error:
                print 'Driver: {0} failed.'.format(driver)
                continue
            found = True
            break

        if not found:
            raise Exception('No suitable video driver found!')

        size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        print "Framebuffer size: %d x %d" % (size[0], size[1])
        self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
        # Clear the screen to start
        self.screen.fill((0, 0, 0))
        # Initialise font support
        pygame.font.init()
        # Render the screen
        pygame.display.update()

    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."

    def background(self):
        bgImg = pygame.image.load('bg-1280.jpg')
        self.screen.blit(bgImg, (0,0))
        # Fill the screen with red (255, 0, 0)
        # red = (255, 0, 0)
        # self.screen.fill(red)
        # Update the display
        pygame.display.update()

def text_objects(text, font):
        textSurface = font.render(text, True, (200, 200, 200))
        return textSurface, textSurface.get_rect()

def message_display(text, X, Y):
        font = pygame.font.Font("font.ttf", 37)
        TextSurf, TextRect = text_objects(text, font)
        TextRect.center = (X, Y)
        scope.screen.blit(TextSurf, TextRect)
        pygame.display.update()


        


#
#
# Redraw screen, two player text variables.
# Write last update time to variable
# that gets wiped if time is too long (to clear status 
# messages)
 
def redrawscreen():
        scope.background()
        message_display(usermessage[0], 640, 540)
        message_display(usermessage[1], 640, 750)





#
# GPIO Setup
#

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

coin_outputs = [3,5,7,11]
GPIO.setup(coin_outputs, GPIO.OUT, initial=GPIO.LOW)


#
# GPIO coin-up function
# use ex:   coinup(3)
#

def coinup( player ):
    print "Coining up output pin", player
    GPIO.output(player, GPIO.HIGH)
    time.sleep(.300)
    GPIO.output(player, GPIO.LOW)
    return








#
# Authentication function
# host:8080/authorizedPlay?barcode=<barcode>&;scannerId=<scannerId>\n\n" 
#
# Scanner with regards to server communications is an identifier for machine
# Scanner with regards to local machine is to track multiple players for coinup

def barcodeauth( scanner, barcode ):
        global usermessagetime
	print "authentication phase"
	payload = {'barcode': barcode, 'scannerId': '1'}
	r = None
	try:
            r = requests.put('http://127.0.0.1:8080/authorizedPlay', params=payload, timeout=2)
        except Exception as e: 
            print ("Server Comm Error: %s" % e)
	    usermessagetime=int(time.time())
            usermessage[int(scanner)] = "Server Comm Error"
            redrawscreen()
	if r is not None:
		print(r.url)
		print(r.status_code)
		if r.status_code == 200:
		  print "Status code 200, good to play"
                  usermessagetime=int(time.time())
                  usermessage[int(scanner)] = "Play enabled!"
                  redrawscreen()
		elif r.status_code == 403:
		  print "Status code 403, ", r.text
                  usermessagetime=int(time.time())
                  usermessage[int(scanner)] = r.text
                  redrawscreen()
		else:
		  print "Error."
                  usermessagetime=int(time.time())
                  usermessage[int(scanner)] = "Invalid Barcode"
                  redrawscreen()

    # Need to relay http feedback in here
















#
# Barcode Scanner Conversion Table 
#

from evdev import InputDevice, categorize, ecodes
from select import select

keys = "X^1234567890-=XXqwertzuiopXXXXasdfghjklXXXXXyxcvbnmXXXXXXXXXXXXXXXXXXXXXXX"
shiftkeys = "X^!@#$%^&*()_+XXQWERTYUIOPXXXXASDFGHJKLXXXXXZXCVBNMXXXXXXXXXXXXXXXXXXXXXXX"
#devOne = InputDevice('/dev/input/by-id/usb-WIT_Electron_Company_WIT_122-UFS_V2.03-event-kbd')

devices = [InputDevice('/dev/input/event0'),
	InputDevice('/dev/input/event1')]

scannerMap = {}
for d in devices: 
	scannerMap[d.fd] = ScannerBuffer()
# 
# Init display
#
scope = pyscope()
scope.background()
redrawscreen()


#
# Read from barcode scanner
#


while True:
   
   # Barcode reading loop
   # 
 
   r,w,x = select(devices, [], [], 4)
   # Blank statuses after X seconds
   if (usermessagetime + 3) < int(time.time()): 
	usermessage[1] = ""
	usermessage[2] = ""
	redrawscreen()


   for dev in r:
	   for event in dev.read():
		if  event.value == 0 and (event.type == 1 or event.code == ecodes.KEY_ENTER ):
			scanner = scannerMap[dev.fd]
			if scanner is None:
				print ("Device does not exist in map - fd: %d" % dev.fd)
				continue
			if event.code == ecodes.KEY_ENTER:
				barcode = scanner.scannerBuffer
				scanner_id = scannerMap.keys().index(dev.fd)
				print ("Checking authrorization of scanner_id: %d barcode: %s" %(
						scanner_id, barcode))
				barcodeauth(scanner_id, barcode)
				scanner.reset()
			elif event.code == 42:
				scanner.shiftOn = True
			else:
				if scanner.shiftOn:
					scanner.scannerBuffer += shiftkeys[ event.code ]
					scanner.shiftOn = False 
				else:	
					scanner.scannerBuffer += keys[ event.code ]

