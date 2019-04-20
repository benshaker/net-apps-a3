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
GPIO.setup(11, GPIO.OUT)  # Red
GPIO.setup(13, GPIO.OUT)  # Green
GPIO.setup(15, GPIO.OUT)  # Blue
p = GPIO.PWM(11, 100)
w = GPIO.PWM(13, 100)
m = GPIO.PWM(15, 100)

# Info
STATE = 'off'
COLOR = None
INTENSITY = 0


def initializeLEDs():
    p.start(0)
    w.start(0)
    m.start(0)


def resetFrequency():
    p.ChangeFrequency(100)
    w.ChangeFrequency(100)
    m.ChangeFrequency(100)


def setLEDW():
    # white LED - Waiting for command
    global INTENSITY
    resetFrequency()
    p.ChangeDutyCycle(INTENSITY)
    w.ChangeDutyCycle(INTENSITY)
    m.ChangeDutyCycle(INTENSITY)


def setLEDR():
    # red LED
    global INTENSITY
    resetFrequency()
    p.ChangeDutyCycle(INTENSITY)
    w.ChangeDutyCycle(0)
    m.ChangeDutyCycle(0)


def setLEDG():
    # green LED
    global INTENSITY
    resetFrequency()
    p.ChangeDutyCycle(0)
    w.ChangeDutyCycle(INTENSITY)
    m.ChangeDutyCycle(0)


def setLEDB():
    # blue LED
    global INTENSITY
    resetFrequency()
    p.ChangeDutyCycle(0)
    w.ChangeDutyCycle(0)
    m.ChangeDutyCycle(INTENSITY)


def setLEDM():
    # magenta LED
    global INTENSITY
    resetFrequency()
    p.ChangeDutyCycle(INTENSITY)
    w.ChangeDutyCycle(0)
    m.ChangeDutyCycle(INTENSITY)


def setLEDC():
    # cyan LED
    global INTENSITY
    resetFrequency()
    p.ChangeDutyCycle(0)
    w.ChangeDutyCycle(INTENSITY)
    m.ChangeDutyCycle(INTENSITY)


def setLEDY():
    # yellow LED
    global INTENSITY
    resetFrequency()
    p.ChangeDutyCycle(INTENSITY)
    w.ChangeDutyCycle(INTENSITY)
    m.ChangeDutyCycle(0)


def setLEDO():
    # orange LED
    global INTENSITY
    resetFrequency()
    p.ChangeDutyCycle(INTENSITY)
    w.ChangeDutyCycle(INTENSITY*.25)
    m.ChangeDutyCycle(0)


def setLEDP():
    # purple LED
    global INTENSITY
    resetFrequency()
    p.ChangeDutyCycle(INTENSITY*.33)
    w.ChangeDutyCycle(0)
    m.ChangeDutyCycle(INTENSITY)


def setLEDDisco():
    # disco LED
    global INTENSITY
    p.ChangeDutyCycle(INTENSITY)
    w.ChangeDutyCycle(INTENSITY)
    m.ChangeDutyCycle(INTENSITY)

    p.ChangeFrequency(2)
    w.ChangeFrequency(4)
    m.ChangeFrequency(8)


def setLEDOFF():
    # LED off entirely
    resetFrequency()
    p.ChangeDutyCycle(0)
    w.ChangeDutyCycle(0)
    m.ChangeDutyCycle(0)


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
    elif COLOR == 'disco':
        setLEDDisco()
    else:
        return make_response(jsonify({
                'error': 'Invalid color requested'}), 404)


@app.route("/LED/change", methods=['PUT'])
def change_LED():

    global STATE, COLOR, INTENSITY

    # at least one paramater is required
    newSTATE, newCOLOR, newINTENSITY = getLEDParams(request.args, request.json)
    if newSTATE or newCOLOR or newINTENSITY is not None:
        pass
    else:
        return make_response(jsonify({
            'error': '/LED/change requires at least one param.'}), 400)

    # LED should turn to ON from OFF
    if newSTATE == 'on' and STATE == 'off':
        STATE = newSTATE
        if newINTENSITY is not None:
            INTENSITY = newINTENSITY
        else:
            INTENSITY = 100
        if newCOLOR is not None:
            COLOR = newCOLOR
        else:
            COLOR = 'white'
        LED_Branch()
    # LED should stay ON
    elif newSTATE == 'on' and STATE == 'on':
        if newINTENSITY is not None:
            INTENSITY = newINTENSITY
        if newCOLOR is not None:
            COLOR = newCOLOR
        LED_Branch()
    # LED should turn OFF
    elif newSTATE == 'off':
        STATE = 'off'
        INTENSITY = 0
        COLOR = None
        setLEDOFF()
    # LED state was not provided
    elif newSTATE is None:
        if STATE == 'on':
            pass
        elif STATE == 'off':
            return make_response(jsonify({
                'error': 'LED cannot be updated in an \'off\' state'}), 400)

        if newINTENSITY is not None:
            INTENSITY = newINTENSITY
        if newCOLOR is not None:
            COLOR = newCOLOR
        LED_Branch()
    else:
        return make_response(jsonify({
            'error': 'Invalid combination attempted'}), 400)

    return make_response(jsonify({
        'success': 'LED updated successfully'}), 200)


# this is a helper function that extracts query params
# from the Service RPi's request for use in LED update
def getLEDParams(args, json):
    status = None
    if not args or 'status' not in args:
        if not json or 'status' not in json:
            pass
        else:
            status = json['status']
    else:
        status = args['status']

    color = None
    if not args or 'color' not in args:
        if not json or 'color' not in json:
            pass
        else:
            color = json['color']
    else:
        color = args['color']

    intensity = None
    if not args or 'intensity' not in args:
        if not json or 'intensity' not in json:
            pass
        else:
            intensity = json['intensity']
    else:
        intensity = args['intensity']

    if intensity is not None:
        intensity = int(intensity)

    return status, color, intensity


if __name__ == "__main__":
    initializeLEDs()
    app.run(host='0.0.0.0', port=8080, debug=False)
