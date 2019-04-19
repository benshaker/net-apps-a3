#!/usr/bin/env python3
# led.py
import RPi.GPIO as GPIO

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

def setLEDOFF():
	p.stop()
	w.stop()
	m.stop()
	
def initializeLEDs():
	p.start(0)
	w.start(0)
	m.start(0)
	
def setLEDW(intensity):
    # white LED - Waiting for command
	p.ChangeDutyCycle(intensity)
	w.ChangeDutyCycle(intensity)
	m.ChangeDutyCycle(intensity)

def setLEDR(intensity):
    # red LED
	p.ChangeDutyCycle(intensity)
	w.ChangeDutyCycle(0)
	m.ChangeDutyCycle(0)

def setLEDG(intensity):
    # green LED
	p.ChangeDutyCycle(0)
	w.ChangeDutyCycle(intensity)
	m.ChangeDutyCycle(0)

def setLEDB(intensity):
    # blue LED
	p.ChangeDutyCycle(0)
	w.ChangeDutyCycle(0)
	m.ChangeDutyCycle(intensity)

def setLEDM(intensity):
    # magenta LED
	p.ChangeDutyCycle(intensity)
	w.ChangeDutyCycle(0)
	m.ChangeDutyCycle(intensity)

def setLEDC(intensity):
    # cyan LED
	p.ChangeDutyCycle(0)
	w.ChangeDutyCycle(intensity)
	m.ChangeDutyCycle(intensity)

def setLEDY(intensity):
    # yellow LED
	p.ChangeDutyCycle(intensity)
	w.ChangeDutyCycle(intensity)
	m.ChangeDutyCycle(0)