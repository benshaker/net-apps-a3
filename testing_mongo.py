import pymongo
from flask import Flask, request
import json
from bson import json_util
from bson.objectid import ObjectId

client = pymongo.MongoClient("mongodb://localhost:27017/")

db = client.datab # database
collection = db.creds # collection
collection.insert_many(
		[{"username": "admin",
		"password": "admin"},
		{"username": "alice",
		"password": "dogsRcool"},
		{"username": "bob",
		"password": "Baseb@ll!"}]
)

def toJson(data):
	return json.dumps(data, default=json_util.default)

@app.route('/authenticate/<username><password>', methods=['GET'])
def authenticate(username, password):
	document = collection.find_one({"username": username})
	if document.password != password:
		return false
	return true
