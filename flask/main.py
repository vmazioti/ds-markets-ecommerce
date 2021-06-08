from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from flask import Flask, request, jsonify, redirect, Response
import json, os
import uuid
import time

# Connect to our local MongoDB
mongodb_hostname = os.environ.get("MONGO_HOSTNAME", "localhost")
client = MongoClient('mongodb://' + mongodb_hostname + ':27017/')

# Choose database
db = client['InfoSys']

# Choose collections
students = db['Students']
users = db['Users']

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/createUser', methods=['POST'])
def create_user():
    # Request JSON data
    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data == None:
        return Response("bad request", status=500, mimetype='application/json')
    if not "username" in data or not "password" in data:
        return Response("Information incomplete", status=500, mimetype="application/json")

    username_from_request = data['username']
    users_with_same_name_from_request = list(students.find({'username': username_from_request}))
    if not users_with_same_name_from_request:
        users.insert_one({'username': username_from_request, 'password': data['password']})
        # Μήνυμα επιτυχίας
        return Response(data['username'] + " was added to the MongoDB", status=200,
                        mimetype='application/json')  # ΠΡΟΣΘΗΚΗ STATUS
    else:
        return Response("A user with the given email already exists", status=500,
                        mimetype='application/json')  # ΠΡΟΣΘΗΚΗ STATUS


if __name__ == '__main__':
    app.run(debug=True)
