#!/usr/bin/env python3
# led.py
import RPi.GPIO as GPIO
from flask import Flask, request
from zeroconf import ServiceBrowser, Zeroconf

app = Flask(__name__)

# Suppress Warnings
GPIO.setwarnings(False)

# setup pins
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT) # Red
GPIO.setup(13, GPIO.OUT) # Green
GPIO.setup(15, GPIO.OUT) # Blue
p = GPIO.PWM(11, 50)
w = GPIO.PWM(13, 50)
m = GPIO.PWM(15, 50)

# Info
STATE = 'off'
COLOR = None
INTENSITY = 0

def setLEDOFF():
	p.stop()
	w.stop()
	m.stop()
	
def initializeLEDs():
	p.start(0)
	w.start(0)
	m.start(0)
	
def setLEDW():
    # white LED - Waiting for command
	p.ChangeDutyCycle(INTENSITY)
	w.ChangeDutyCycle(INTENSITY)
	m.ChangeDutyCycle(INTENSITY)

def setLEDR():
    # red LED
	p.ChangeDutyCycle(INTENSITY)
	w.ChangeDutyCycle(0)
	m.ChangeDutyCycle(0)

def setLEDG():
    # green LED
	p.ChangeDutyCycle(0)
	w.ChangeDutyCycle(INTENSITY)
	m.ChangeDutyCycle(0)

def setLEDB():
    # blue LED
	p.ChangeDutyCycle(0)
	w.ChangeDutyCycle(0)
	m.ChangeDutyCycle(INTENSITY)

def setLEDM():
    # magenta LED
	p.ChangeDutyCycle(INTENSITY)
	w.ChangeDutyCycle(0)
	m.ChangeDutyCycle(INTENSITY)

def setLEDC():
    # cyan LED
	p.ChangeDutyCycle(0)
	w.ChangeDutyCycle(INTENSITY)
	m.ChangeDutyCycle(INTENSITY)

def setLEDY():
    # yellow LED
	p.ChangeDutyCycle(INTENSITY)
	w.ChangeDutyCycle(INTENSITY)
	m.ChangeDutyCycle(0)
	
	
@app.route("/LED/info", methods=['GET'])
def send_info():
	info = {
		'status': STATE,
		'color': COLOR,
		'intensity': str(INTENSITY)
	}
	return jsonify(info), 200

def LED_Branch():
	if COLOR == 'white':
		setLEDW()
	elif COLOR == 'red':
		setLEDR()
	elif COLOR == 'green':
		setLEDG()
	elif COLOR == 'blue':
		setLEDB()
	elif COLOR == 'cyan':
		setLEDC()
	elif COLOR == 'magenta':
		setLEDM()
	elif COLOR == 'yellow':
		setLEDY()
	else:
		abort(404)
	
@app.route("/LED/change", methods=['PUT'])
def change_LED():

	#if not request.json or not 'title' in request.json:
    #    abort(400)
	try:
		newSTATE = request.json['status']
	except:
		newSTATE = None
		
	try:
		newCOLOR = request.json['color']
	except:
		newCOLOR = None
	
	try:
		newINTENSITY = int(request.json['intensity'])
	except:
		newINTENSITY = None
		
	if newSTATE == 'on' and STATE == 'off':	
		STATE = newSTATE
		if newINTENSITY != None:
			INTENSITY = newINTENSITY
		else:
			INTENSITY = 100
		if newCOLOR != None:
			COLOR = newCOLOR
		else:
			COLOR = 'white'
		LED_Branch()
	elif newSTATE == 'on' and STATE == 'on':
		if newINTENSITY != None:
			INTENSITY = newINTENSITY
		if newCOLOR != None:
			COLOR = newCOLOR
		LED_Branch()
	elif newSTATE == 'off':
		STATE = 'off'
		INTENSITY = 0
		COLOR = None
		setLEDOFF()
	elif newSTATE == None:
		if STATE == 'off':
			abort(404)
			
		if newINTENSITY != None:
			INTENSITY = newINTENSITY
		if newCOLOR != None:
			COLOR = newCOLOR
		LED_Branch()

	return 200
    
	
class MyListener(object):  
    def remove_service(self, zeroconf, type, name):
        print("Service %s removed" % (name,))

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        # print name, info.get_name(), info.server,
        print(name, info)
		

if __name__ == "__main__":
	app.run(debug=False)
	zeroconf = Zeroconf()
	listener = MyListener()
	browser = ServiceBrowser(zeroconf, "", listener)
	try:  
		input("Press enter to exit...\n\n")
	finally:  
		zeroconf.close()
	# ?
