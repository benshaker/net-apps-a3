#!/usr/bin/env python3
# services.py

import requests, json

from six.moves import input
from zeroconf import ServiceBrowser, Zeroconf

from servicesKeys import canvasAPIKey, canvasCourseID

from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

from flask import Flask, jsonify, make_response, request, abort
app = Flask(__name__)

# import pymongo
# client = pymongo.MongoClient("mongodb://localhost:27017/")
# db = client.database
# collection = db.creds
# collection.insert_many(
# 		[{"username": "admin",
# 		"password": "admin"},
# 		{"username": "alice",
# 		"password": "dogsRcool"},
# 		{"username": "bob",
# 		"password": "Baseb@ll!"}]
# )

# BEGIN AUTH

@auth.get_password
def get_password(username):
	# auth_pair = collection.find_one({"username": username})
	# if auth_pair:
	# 	return auth_pair["password"]
	return None

@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)

# BEGIN APP

@app.route("/")
@auth.login_required
def root():
    return jsonify({'error': 'No endpoint chosen. See /info'})

@app.route("/info")
@auth.login_required
def root_info():
    return jsonify({'success': 'Choose from the following enpoints: '+
                                '/Canvas or '+
                                '/LED'})

@app.route("/Canvas")
@auth.login_required
def file_download():
    if not request.args or not 'file' in request.args:
        return jsonify({'error': 'No search term provided (use ?file=).'})
    else:
        searchTerm = request.args['file']

    if searchTerm is None:
        if not request.json or not 'file' in request.json:
            return jsonify({'error': 'No search term provided.'})
        else:
            searchTerm = request.json['file']

    r = requests.get('https://vt.instructure.com/api/v1/courses/' +
                        canvasCourseID + '/files' +
                        '?access_token=' + canvasAPIKey +
                        '&search_term=' + searchTerm +
                        '&sort=' + 'created_at' +
                        '&order=' + 'desc')
    json_res = r.json()

    if not json_res:
        return make_response(jsonify({'error': 'No matching files found.'}), 404)
    if json_res:
        doc = json_res[0]

        doc_name = doc["display_name"]
        doc_url = doc["url"]
        r = requests.get(doc_url)
        open(doc_name, 'wb').write(r.content)

        msg = 'Saved the document titled \'' + doc_name + '\' locally on the Servives RPi.'

    return make_response(jsonify({'success': msg}), 201)

@app.route("/LED/info")
@auth.login_required
def led_info():
    return jsonify({'success': '/LED accepts the following params: '+
                            'status (optional) '+
                            'color (optional) ' +
                            'intensity (optional)'})

@app.route("/LED")
@auth.login_required
def led_modify():
    #?status=on&color=red&intensity=50
    status, color, intensity = getLEDParams(request.args, request.json)
    print(status, color, intensity)
    if None not in (status, color, intensity):
        pass
    else:
        return jsonify({'error': '/LED requires at least one param.' +
                            'See /LED/info' })
    print("what?",listener.getColors())

    ip = listener.getIP()
    port = listener.getPort()
    colors_allowed = listener.getColors()

    print("testing",colors_allowed)

    if color not in colors_allowed:
        return jsonify({'error': '/LED only accepts the following colors: ' +
                            str(colors_allowed) })

    queryString = "?"
    if intensity is not None and intensity in ("on", "off"):
        queryString += "status=" + str(status)
    if color is not None:
        queryString += "color=" + str(color)
    if intensity is not None and intensity in range(0, 101):
        queryString += "intensity=" + str(intensity)

    r = requests.put(str(ip) + ':' + str(port) + '/' + queryString)
    json_res = r.json()

def getLEDParams(args, json):
    status, color, intensity = None, None, None
    if not request.args or not 'status' in request.args:
        return jsonify({'error': 'No params provided.'})
    else:
        status = request.args['status']

    if status is None:
        if not request.json or not 'status' in request.json:
            return jsonify({'error': 'No params provided.'})
        else:
            status = request.json['status']

    if not request.args or not 'color' in request.args:
        return jsonify({'error': 'No params provided.'})
    else:
        color = request.args['color']

    if color is None:
        if not request.json or not 'color' in request.json:
            return jsonify({'error': 'No params provided.'})
        else:
            color = request.json['color']

    if not request.args or not 'intensity' in request.args:
        return jsonify({'error': 'No params provided.'})
    else:
        intensity = request.args['intensity']

    if intensity is None:
        if not request.json or not 'intensity' in request.json:
            return jsonify({'error': 'No params provided.'})
        else:
            intensity = request.json['intensity']

    return status, color, intensity

# tasks = [
#     {
#         'id': 1,
#         'title': u'Buy groceries',
#         'description': u'Milk, Cheese, Pizza, Fruit, Tylenol',
#         'done': False
#     },
#     {
#         'id': 2,
#         'title': u'Learn Python',
#         'description': u'Need to find a good Python tutorial on the web',
#         'done': False
#     }
# ]

# @app.route('/todo/api/v1.0/tasks', methods=['GET'])
# @auth.login_required
# def get_tasks():
#     return jsonify({'tasks': tasks})

# @app.route('/todo/api/v1.0/tasks/<int:task_id>', methods=['GET'])
# def get_task(task_id):
#     task = [task for task in tasks if task['id'] == task_id]
#     if len(task) == 0:
#         abort(404)
#     return jsonify({'task': task[0]})

# curl -i -H "Content-Type: application/json" -X POST -d "{"title":"Read a book"}" http://localhost:5000/todo/api/v1.0/tasks

# @app.route('/todo/api/v1.0/tasks', methods=['POST'])
# def create_task():
#     if not request.json or not 'title' in request.json:
#         abort(400)
#     task = {
#         'id': tasks[-1]['id'] + 1,
#         'title': request.json['title'],
#         'description': request.json.get('description', ""),
#         'done': False
#     }
#     tasks.append(task)
#     return jsonify({'task': task}), 201

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
        byte_address = info.address.decode('utf-8')
        ipv4_address = '.'.join(str(ord(i)) for i in byte_address)
        colors_array = info.properties[b'colors'].decode('utf-8').split(',')

        if "led_rpi_13" not in name:
            return

        self.ip = ipv4_address
        self.port = info.port
        self.colors = colors_array
        print("Service added", self.ip)

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
