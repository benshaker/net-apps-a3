#!/usr/bin/env python3
# services.py

from servicesKeys import canvasAPIKey, canvasCourseID

from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

from flask import Flask, jsonify, make_response, request, abort
app = Flask(__name__)

import requests, json

from six.moves import input
from zeroconf import ServiceBrowser, Zeroconf

LED_PI_IP = None
LED_PI_PORT = None
COLORS_ALLOWED = None

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
def root():
    return jsonify({'error': 'No endpoint chosen. See /info'})

@app.route("/info")
# @auth.login_required
def root_info():
    return jsonify({'success': 'Choose from the following enpoints: '+
                                '/Canvas or '+
                                '/LED'})

@app.route("/Canvas")
# @auth.login_required
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

@app.route("/LED")
# @auth.login_required
def led_info():
    return jsonify({'success': '/LED accepts the following params: '+
                            'status (optional) '+
                            'color (optional) ' +
                            'intensity (optional)'})

@app.route("/LED")
# @auth.login_required
def led_modify():
    #?status=on&color=red&intensity=50
    status, color, intensity = getLEDParams(request.args, request.json)
    if None not in (status, color, intensity):
        pass
    else:
        return jsonify({'error': '/LED requires at least one param.' +
                            'See /LED/info' })

    if color not in COLORS_ALLOWED:
        return jsonify({'error': '/LED only accepts the following colors: ' +
                            str(COLORS_ALLOWED) })

    queryString = "?"
    if intensity is not None and intensity in ("on", "off"):
        queryString += "status=" + str(status)
    if color is not None:
        queryString += "color=" + str(color)
    if intensity is not None and intensity in range(0, 101):
        queryString += "intensity=" + str(intensity)

    LED_PI_IP = None
    LED_PI_PORT = None
    r = requests.put(LED_PI_IP + ':' + LED_PI_PORT + '/' + queryString)
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
    def remove_service(self, zeroconf, type, name):
        LED_PI_IP = None
        LED_PI_PORT = None
        COLORS_ALLOWED = None
        print("Service %s removed" % (name,))

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        byte_address = info.address.decode('utf-8')
        ipv4_address = '.'.join(str(ord(i)) for i in byte_address)
        colors_array = info.properties[b'colors'].decode('utf-8').split(',')

        if "led_rpi_13" not in name:
            return

        LED_PI_IP = ipv4_address
        LED_PI_PORT = info.port
        COLORS_ALLOWED = colors_array
        print("Service added", LED_PI_IP)

if __name__ == "__main__":
    browser = ServiceBrowser(Zeroconf(), "_http._tcp.local.", MyListener())
    app.run(host='0.0.0.0', port=8080, debug=True)

