#!/usr/bin/env python3
# led.py
import RPi.GPIO as GPIO
from flask import Flask, request, abort, jsonify, make_response
from zeroconf import ServiceBrowser, Zeroconf

app = Flask(__name__)

# Suppress Warnings
GPIO.setwarnings(False)

# setup pins
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT) # Red
GPIO.setup(13, GPIO.OUT) # Green
GPIO.setup(15, GPIO.OUT) # Blue
p = GPIO.PWM(11, 100)
w = GPIO.PWM(13, 100)
m = GPIO.PWM(15, 100)

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
	global INTENSITY
	p.ChangeDutyCycle(INTENSITY)
	w.ChangeDutyCycle(INTENSITY)
	m.ChangeDutyCycle(INTENSITY)

def setLEDR():
    # red LED
	global INTENSITY
	p.ChangeDutyCycle(INTENSITY)
	w.ChangeDutyCycle(0)
	m.ChangeDutyCycle(0)
	
	print("5", INTENSITY)

def setLEDG():
    # green LED
	global INTENSITY
	p.ChangeDutyCycle(0)
	w.ChangeDutyCycle(INTENSITY)
	m.ChangeDutyCycle(0)

def setLEDB():
    # blue LED
	global INTENSITY
	p.ChangeDutyCycle(0)
	w.ChangeDutyCycle(0)
	m.ChangeDutyCycle(INTENSITY)

def setLEDM():
    # magenta LED
	global INTENSITY
	p.ChangeDutyCycle(INTENSITY)
	w.ChangeDutyCycle(0)
	m.ChangeDutyCycle(INTENSITY)

def setLEDC():
    # cyan LED
	global INTENSITY
	p.ChangeDutyCycle(0)
	w.ChangeDutyCycle(INTENSITY)
	m.ChangeDutyCycle(INTENSITY)

def setLEDY():
    # yellow LED
	global INTENSITY
	p.ChangeDutyCycle(INTENSITY)
	w.ChangeDutyCycle(INTENSITY)
	m.ChangeDutyCycle(0)
	
def setLEDO():
    # orange LED
	global INTENSITY
	p.ChangeDutyCycle(INTENSITY)
	w.ChangeDutyCycle(INTENSITY*.25)
	m.ChangeDutyCycle(0)
	
def setLEDP():
	# purple LED
	global INTENSITY
	p.ChangeDutyCycle(INTENSITY*.33)
	w.ChangeDutyCycle(0)
	m.ChangeDutyCycle(INTENSITY)
	
	
@app.route("/LED/info", methods=['GET'])
def send_info():
	global STATE, COLOR, INTENSITY
	
	info = {
		'status': STATE,
		'color': COLOR,
		'intensity': str(INTENSITY)
	}
	return jsonify(info), 200

def LED_Branch():
	global COLOR
	
	print("4", COLOR)
	
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
	elif COLOR == 'orange':
		setLEDO()
	elif COLOR == 'purple':
		setLEDP()
	else:
		abort(404)
	
@app.route("/LED/change", methods=['PUT'])
def change_LED():

	#if not request.json or not 'title' in request.json:
    #    abort(400)
	global STATE
	global COLOR
	global INTENSITY
    
	try:
		newSTATE = request.args['status']
	except:
		newSTATE = None
	print(newSTATE)
	try:
		newCOLOR = request.args['color']
	except:
		newCOLOR = None
	print(newCOLOR)
	try:
		newINTENSITY = int(request.args['intensity'])
	except:
		newINTENSITY = None
	print(newINTENSITY)
	if newSTATE == 'on' and STATE == 'off':	
		STATE = newSTATE
		print("1", STATE)
		if newINTENSITY != None:
			INTENSITY = newINTENSITY
		else:
			INTENSITY = 100
		print("2", INTENSITY)
		if newCOLOR != None:
			COLOR = newCOLOR
		else:
			COLOR = 'white'
		print("3", COLOR)
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
	else:
		abort(404)

	print("6: EXIT") 
	return make_response(jsonify({'success': 'yay'})), 200

"""
class MyListener(object):  
    def remove_service(self, zeroconf, type, name):
        print("Service %s removed" % (name,))

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        # print name, info.get_name(), info.server,
        print(name, info)
"""	

if __name__ == "__main__":
	initializeLEDs()
	app.run(host='0.0.0.0', port=8080, debug=False)
	"""
	zeroconf = Zeroconf()
	listener = MyListener()
	browser = ServiceBrowser(zeroconf, "_http._tcp.local", listener)
	try:  
		input("Press enter to exit...\n\n")
	finally:  
		zeroconf.close()
	"""
