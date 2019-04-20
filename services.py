#!/usr/bin/env python3
# services.py

import json
import pymongo
import requests

from socket import inet_ntoa
from six.moves import input
from zeroconf import ServiceBrowser, Zeroconf
from servicesKeys import canvasAPIKey, canvasCourseID
from flask import Flask, jsonify, make_response, request, abort
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()
app = Flask(__name__)

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client.database
collection = db.creds
collection.insert_many([
    {"username": "admin", "password": "admin"},
    {"username": "alice", "password": "dogsRcool"},
    {"username": "bob", "password": "Baseb@ll!"}
])

# BEGIN AUTH


@auth.get_password
def get_password(username):
    auth_pair = collection.find_one({"username": username})
    if auth_pair:
        return auth_pair["password"]
    return None


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)

# BEGIN APP


@app.route("/")
# @auth.login_required
def root_get():
    return jsonify({'error': 'No endpoint chosen. See /info'})


@app.route("/info")
# @auth.login_required
def root_info():
    return jsonify({
        'success': 'Choose from the following endpoints: ' +
        '/Canvas or ' +
        '/LED'
        })


@app.route("/Canvas")
@auth.login_required
def file_get():
    if not request.args or 'file' not in request.args:
        return jsonify({'error': 'No search term provided (use ?file=).'})
    else:
        searchTerm = request.args['file']

    if searchTerm is None:
        if not request.json or 'file' not in request.json:
            return jsonify({'error': 'No search term provided.'})
        else:
            searchTerm = request.json['file']

    r = requests.get(
        'https://vt.instructure.com/api/v1/courses/' +
        canvasCourseID + '/files' +
        '?access_token=' + canvasAPIKey +
        '&search_term=' + searchTerm +
        '&sort=' + 'created_at' +
        '&order=' + 'desc')
    json_res = r.json()

    if not json_res:
        return make_response(jsonify({
            'error': 'No matching files found.'
            }), 404)
    if json_res:
        doc = json_res[0]

        doc_name = doc["display_name"]
        doc_url = doc["url"]
        r = requests.get(doc_url)
        open(doc_name, 'wb').write(r.content)

        msg = 'Saved the document titled \'' + doc_name + '\' locally on the Servives RPi.'

    return make_response(jsonify({'success': msg}), 201)


@app.route("/LED/info")
# @auth.login_required
def led_info():
    return jsonify({
        'success': 'Choose from the following endpoints: ' +
        '/LED (via GET or PUT). ' +
        'PUT /LED accepts the following params: ' +
        'status (optional) ' +
        'color (optional) ' +
        'intensity (optional)'})


@app.route("/LED", methods=['GET'])
@auth.login_required
def led_get():
    ip = listener.getIP()
    port = listener.getPort()
    colors_allowed = listener.getColors()

    # Handle cases where LED RPi and its service is not available.
    if None not in (ip, port, colors_allowed):
        pass
    else:
        return make_response(jsonify({'error': 'LED RPi unavailable'}), 400)

    r = requests.put('http://' + str(ip) + ':' + str(port) + '/LED/info')
    json_res = r.json()

    return make_response(json_res, 201)


@app.route("/LED", methods=['PUT'])
@auth.login_required
def led_put():
    ip = listener.getIP()
    port = listener.getPort()
    colors_allowed = listener.getColors()

    # Handle cases where LED RPi and its service is not available.
    if None not in (ip, port, colors_allowed):
        pass
    else:
        return make_response(jsonify({'error': 'LED RPi unavailable'}), 400)

    # TO DO: HANDLE NO PARAMS AT ALL
    status, color, intensity = getLEDParams(request.args, request.json)
    print(status, color, intensity)
    if None not in (status, color, intensity):
        pass
    else:
        return make_response(jsonify({
            'error': '/LED requires at least one param.' +
            'See /LED/info'}), 400)

    if color not in colors_allowed:
        return jsonify({
            'error': '/LED only accepts the following colors: ' +
            str(colors_allowed)})

    queryString = "?"
    if status is not None and status in ("on", "off"):
        queryString += "status=" + str(status) + '&'
    if color is not None:
        queryString += "color=" + str(color) + '&'
    if intensity is not None and int(intensity) in range(0, 101):
        queryString += "intensity=" + str(intensity) + '&'

    r = requests.put(
        'http://' + str(ip) + ':' + str(port) +
        '/LED/change' + queryString)
    json_res = r.json()

    return make_response(jsonify({'success': 'yayyay'}), 201)


def getLEDParams(args, json):
    status, color, intensity = None, None, None
    if not args or 'status' not in args:
        return jsonify({'error': 'No params provided.'})
    else:
        status = args['status']

    if status is None:
        if not json or 'status' not in json:
            return jsonify({'error': 'No params provided.'})
        else:
            status = json['status']

    if not args or 'color' not in args:
        return jsonify({'error': 'No params provided.'})
    else:
        color = args['color']

    if color is None:
        if not json or 'color' not in json:
            return jsonify({'error': 'No params provided.'})
        else:
            color = json['color']

    if not args or 'intensity' not in args:
        return jsonify({'error': 'No params provided.'})
    else:
        intensity = args['intensity']

    if intensity is None:
        if not json or 'intensity' not in json:
            return jsonify({'error': 'No params provided.'})
        else:
            intensity = json['intensity']

    return status, color, intensity


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


class MyListener(object):
    def __init__(self):
        self.ip = None
        self.port = None
        self.colors = None

    def remove_service(self, zeroconf, type, name):
        self.ip = None
        self.port = None
        self.colors = None
        print("Service %s removed" % (name,))

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if "led_rpi_13" not in name:
            pass
        elif "led_rpi_13" in name:
            ipv4_address = inet_ntoa(info.address)
            colors_array = info.properties[b'colors'].decode('utf-8').split(',')

            self.port = info.port
            self.ip = ipv4_address
            self.colors = colors_array
            print("Service added with addresss", self.ip)

    def getColors(self):
        return self.colors

    def getPort(self):
        return self.port

    def getIP(self):
        return self.ip


if __name__ == "__main__":
    listener = MyListener()
    browser = ServiceBrowser(Zeroconf(), "_http._tcp.local.", listener)
    app.run(host='0.0.0.0', port=8080, debug=False)
