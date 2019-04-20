#!/usr/bin/env python3
# services.py

import json
import pymongo
import requests

from pymongo import UpdateOne
from socket import inet_ntoa
from six.moves import input
from zeroconf import ServiceBrowser, Zeroconf
from servicesKeys import canvasAPIKey, canvasCourseID
from flask import Flask, jsonify, make_response, request, abort
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()
app = Flask(__name__)


# BEGIN AUTH


# this helper fn compares provided usernames & known passwords
@auth.get_password
def get_password(username):
    coll = authenticator.getCollection()
    auth_pair = coll.find_one({"username": username})
    if auth_pair:
        return auth_pair["password"]
    return None


# this helper fn handles unauthorized auth. attempts
@auth.error_handler
def unauthorized():
    return make_response(jsonify({
        'error': 'Unauthorized access attempted. ' +
        'Please provide valid credentials with your query.'
    }), 401)

# BEGIN APP


@app.route("/")
# @auth.login_required
def root_get():
    return make_response(jsonify({
        'success': 'Root is not a valid route. See /info'
    }), 200)


@app.route("/info")
# @auth.login_required
def root_info_get():
    return make_response(jsonify({
        'success': 'Choose from the following routes: ' +
        '/Canvas or ' +
        '/LED'
    }), 200)


@app.route("/Canvas/info")
# @auth.login_required
def canvas_info_get():
    return make_response(jsonify({
        'success': 'GET /Canvas accepts the following params: ' +
        '\'file\': file name search term (required)'
    }), 200)


@app.route("/Canvas")
@auth.login_required
def canvas_get():
    if not request.args or 'file' not in request.args:
        return make_response(jsonify({
            'error': 'No search term provided (use ?file=)'}), 400)
    else:
        searchTerm = request.args['file']

    # if param not found in query string, check the data object
    if searchTerm is None:
        if not request.json or 'file' not in request.json:
            return make_response(jsonify({
                'error': 'No search term provided. (use ?file=)'}), 400)
        else:
            searchTerm = request.json['file']

    # send our request to Canvas via their API
    # sort results by "name is matching" and "most recently created"
    r = requests.get(
        'https://vt.instructure.com/api/v1/courses/' +
        canvasCourseID + '/files' +
        '?access_token=' + canvasAPIKey +
        '&search_term=' + searchTerm +
        '&sort=' + 'created_at' +
        '&order=' + 'desc')
    json_res = r.json()

    # handle the Canvas response
    if not json_res:
        return make_response(jsonify({
            'error': 'No file names matched your search term.'
        }), 404)
    elif json_res:
        # if multiple results, we choose the most recently created
        doc = json_res[0]
        doc_name = doc["display_name"]
        doc_url = doc["url"]
        r = requests.get(doc_url)

        # download file to the working directory
        open(doc_name, 'wb').write(r.content)

    return make_response(jsonify({
        'success': 'Saved the document titled \'' + doc_name +
        '\' locally on the Services RPi.'}), 201)


@app.route("/LED/info")
# @auth.login_required
def led_info_get():
    colors_allowed = listener.getColors()
    return make_response(jsonify({
        'success': 'GET /LED requires no params. ' +
        'PUT /LED accepts the following params: ' +
        '\'status\': [\'on\', \'off\'] (optional), ' +
        '\'color\': ' + str(colors_allowed) + ' (optional), ' +
        '\'intensity\': int(0 to 100) (optional)'}), 200)


@app.route("/LED", methods=['GET'])
@auth.login_required
def led_get():
    # get the latest information about the LED RPi
    ip = listener.getIP()
    port = listener.getPort()
    colors_allowed = listener.getColors()

    # Handle cases where LED RPi or its service is not available.
    if None not in (ip, port, colors_allowed):
        pass
    else:
        return make_response(jsonify({
            'error': 'LED RPi appears to be offline. Please try again.'
        }), 502)

    # send our request to LED RPi via its API
    try:
        r = requests.get('http://' + str(ip) + ':' + str(port) + '/LED/info')
        res_body = r.json()
    except Exception:
        return make_response(jsonify({
            'error': 'LED RPi service is unavailable. Please try again.'
        }), 503)

    # pass this response to the end user
    if r.status_code == requests.codes.ok:
        return make_response(jsonify(res_body), 201)
    else:
        return make_response(jsonify(res_body), 400)


@app.route("/LED", methods=['PUT'])
@auth.login_required
def led_put():
    # get the latest information about the LED RPi
    ip = listener.getIP()
    port = listener.getPort()
    colors_allowed = listener.getColors()

    # handle cases where LED RPi and its service is not available.
    if None not in (ip, port, colors_allowed):
        pass
    else:
        return make_response(jsonify({
            'error': 'LED RPi appears to be offline. Please try again.'
        }), 502)

    # at least one paramater is required
    status, color, intensity = getLEDParams(request.args, request.json)
    if status or color or intensity is not None:
        pass
    else:
        return make_response(jsonify({
            'error': '/LED requires at least one param.' +
            'See /LED/info'}), 400)

    # handle invalid user request params
    if status and status not in ("on", "off"):
        return make_response(jsonify({
            'error': '/LED \'status\' only accepts the following options: ' +
            '[\'on\', \'off\']'}), 400)

    if color and color not in colors_allowed:
        return make_response(jsonify({
            'error': '/LED \'color\' only accepts the following options: ' +
            str(colors_allowed)}), 400)

    try:
        if intensity is not None:
            intensity = int(intensity)
    except Exception:
        return make_response(jsonify({
            'error': '/LED \'intensity\' only accepts the following options: ' +
            'int(0 to 100)'}), 400)

    if intensity and intensity not in range(0, 101):
        return make_response(jsonify({
            'error': '/LED \'intensity\' only accepts the following options: ' +
            'int(0 to 100)'}), 400)

    # build the query string to be sent to the LED RPi
    queryString = "?"
    if status is not None:
        queryString += "status=" + str(status) + '&'
    if color is not None:
        queryString += "color=" + str(color) + '&'
    if intensity is not None:
        queryString += "intensity=" + str(intensity)

    # send our LED change request to the LED RPi
    try:
        r = requests.put(
            'http://' + str(ip) + ':' + str(port) +
            '/LED/change' + queryString)
        res_body = r.json()
    except Exception:
        return make_response(jsonify({
            'error': 'LED RPi service is unavailable. Please try again.'
        }), 503)

    # pass this response to the end user
    if r.status_code == requests.codes.ok:
        return make_response(jsonify(res_body), 201)
    else:
        return make_response(jsonify(res_body), 400)


# this is a helper function that extracts query params
# from the end user's request for clean forwarding to
# the LED RPi
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

    return status, color, intensity


# this is a helper function that handles blanket 404 errors
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({
        'error': 'Invalid route. ' +
        'See /info'
    }), 404)


# this class manages our zeroconf discovery of the LED RPi
class MyListener(object):

    def __init__(self):
        self.ip, self.port, self.colors = None, None, None

    def remove_service(self, zeroconf, type, name):
        self.ip, self.port, self.colors = None, None, None
        print("Service removed with name", name)

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if "led_rpi_13" not in name:
            pass
        elif "led_rpi_13" in name:
            ipv4_address = inet_ntoa(info.address)
            colors_array = info.properties[
                b'colors'].decode('utf-8').split(',')

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


# this fn initializes our mongodb instance and collection
# and adds a short list of usernames and passwords to it
class MyAuth(object):

    def __init__(self):
        self._client = pymongo.MongoClient("mongodb://localhost:27017/")
        self._db = self._client.auth
        self.collection = self._db.creds

    # adds a username + password iff username does not already exist
    def add_iff_dne(self):
        operations = [
            UpdateOne({"username": "admin"},
                      {"$setOnInsert":
                       {"username": "admin", "password": "admin"}
                       }, upsert=True),
            UpdateOne({"username": "guest"},
                      {"$setOnInsert":
                       {"username": "guest", "password": "guest"}
                       }, upsert=True),
            UpdateOne({"username": "alice"},
                      {"$setOnInsert":
                       {"username": "alice", "password": "dogsRcool"}
                       }, upsert=True),
            UpdateOne({"username": "bob"},
                      {"$setOnInsert":
                       {"username": "bob", "password": "Baseb@ll!"}
                       }, upsert=True)
        ]
        self.collection.bulk_write(operations)

    def getCollection(self):
        return self.collection


if __name__ == "__main__":
    authenticator = MyAuth()
    listener = MyListener()
    browser = ServiceBrowser(Zeroconf(), "_http._tcp.local.", listener)
    app.run(host='0.0.0.0', port=8080, debug=False)
