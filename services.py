#!/usr/bin/env python3
# services.py
#
from servicesKeys import canvasAPIKey, canvasCourseID

from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

from flask import Flask, jsonify, make_response, request, abort
app = Flask(__name__)

import requests, json

# BEGIN AUTH

@auth.get_password
def get_password(username):
    if username == 'ben':
        return 'jammin'
    return None

@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)

# BEGIN APP

# GET /api/v1/courses/:course_id/files
#

@app.route("/")
def hello():
    # return "Hello World"
    return jsonify({'error': 'No endpoint chosen.'})

@app.route("/Canvas")
def file_download():
    if not request.args or not 'file' in request.args:
        return jsonify({'error': 'No search term provided.'})
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

tasks = [
    {
        'id': 1,
        'title': u'Buy groceries',
        'description': u'Milk, Cheese, Pizza, Fruit, Tylenol',
        'done': False
    },
    {
        'id': 2,
        'title': u'Learn Python',
        'description': u'Need to find a good Python tutorial on the web',
        'done': False
    }
]

@app.route('/todo/api/v1.0/tasks', methods=['GET'])
@auth.login_required
def get_tasks():
    return jsonify({'tasks': tasks})

@app.route('/todo/api/v1.0/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = [task for task in tasks if task['id'] == task_id]
    if len(task) == 0:
        abort(404)
    return jsonify({'task': task[0]})

# curl -i -H "Content-Type: application/json" -X POST -d "{"title":"Read a book"}" http://localhost:5000/todo/api/v1.0/tasks

@app.route('/todo/api/v1.0/tasks', methods=['POST'])
def create_task():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': tasks[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    tasks.append(task)
    return jsonify({'task': task}), 201

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)