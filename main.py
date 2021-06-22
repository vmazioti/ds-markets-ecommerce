import pymongo
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from flask import Flask, request, jsonify, redirect, Response, session
import json, os
import uuid
import time
from datetime import timedelta

mongodb_hostname = os.environ.get("MONGO_HOSTNAME", "localhost")
client = MongoClient('mongodb://' + mongodb_hostname + ':27017/')

db = client['DSMarkets']

users = db['Users']
products = db['Products']

app = Flask(__name__)

app.secret_key = "3088122373"

users_sessions = {}


@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=10)


def create_session(email):
    user_uuid = str(uuid.uuid1())
    users_sessions[user_uuid] = (email, time.time())
    return user_uuid


def is_session_valid(user_uuid):
    return user_uuid in users_sessions

@app.route('/signUp', methods=['POST'])
def sign_up():
    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=400, mimetype='application/json')
    if data == None:
        return Response("bad request", status=400, mimetype='application/json')
    if not "name" in data or not "password" or not "email" in data:
        return Response("Information incomplete", status=400, mimetype="application/json")

    email_inserted = list(users.find({'email': data['email']}))
    if not email_inserted:
        users.insert_one({'email': data['email'], 'name': data['name'], 'password': data['password'],
                          'category': "user", 'orderHistory': 0})
        return Response(data['name'] + " was added to the Database", status=200,
                        mimetype='application/json')
    else:
        return Response("A user with the given email already exists", status=400,
                        mimetype='application/json')


@app.route('/login', methods=['POST'])
def login():
    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=400, mimetype='application/json')
    if data == None:
        return Response("bad request", status=400, mimetype='application/json')
    if not "email" in data or not "password" in data:
        return Response("Information incomplete", status=400, mimetype="application/json")

    while (users.find({'email': data['email']}).count() == 0) and (
            users.find({'password': data['password']}).count() == 0):
        return Response("Wrong username or password.", status=400, mimetype='application/json')

    user_uuid = create_session(data['email'])
    res = {"uuid": user_uuid}
    return Response(json.dumps(res), status=200, mimetype='application/json')


@app.route('/adminLogin', methods=['POST'])
def admin_login():
    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=400, mimetype='application/json')
    if data == None:
        return Response("bad request", status=400, mimetype='application/json')
    if not "email" in data or not "password" in data:
        return Response("Information incomplete", status=400, mimetype="application/json")

    while (users.find({'email': data['email']}).count() == 0) and (
            users.find({'password': data['password']}).count() == 0):
        return Response("Wrong username or password.", status=400, mimetype='application/json')

    user_uuid = create_session(data['email'])
    res = {"uuid": user_uuid}
    return Response(json.dumps(res), status=200, mimetype='application/json')


@app.route('/searchProductByName', methods=['POST'])
def search_product_by_name():
    uuid = request.headers.get('authorization')
    if not is_session_valid(uuid):
        return Response("User is not authenticated", status=401, mimetype='application/json')

    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=400, mimetype='application/json')
    if data == None:
        return Response("bad request", status=400, mimetype='application/json')
    if not "product_name" in data:
        return Response("Information incomplete", status=400, mimetype="application/json")

    product = list(products.find({'name': data['product_name']}, {'stock': 0}))
    if product is not None:
        return Response(json.dumps(product), status=200, mimetype='application/json')
    else:
        return Response("Product not found", status=400, mimetype='application/json')


@app.route('/searchProductByCategory', methods=['POST'])
def search_product_by_category():
    uuid = request.headers.get('authorization')
    if not is_session_valid(uuid):
        return Response("User is not authenticated", status=401, mimetype='application/json')

    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=400, mimetype='application/json')
    if data == None:
        return Response("bad request", status=400, mimetype='application/json')
    if not "product_category" in data:
        return Response("Information incomplete", status=400, mimetype="application/json")

    product = list(products.find({'category': data['product_category']}, {'stock': 0}).sort('price', pymongo.ASCENDING))
    if product is not None:
        return Response(json.dumps(product), status=200, mimetype='application/json')
    else:
        return Response("Product not found", status=400, mimetype='application/json')


@app.route('/searchProductById', methods=['POST'])
def search_product_by_id():
    uuid = request.headers.get('authorization')
    if not is_session_valid(uuid):
        return Response("User is not authenticated", status=401, mimetype='application/json')

    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=400, mimetype='application/json')
    if data == None:
        return Response("bad request", status=400, mimetype='application/json')
    if not "product_id" in data:
        return Response("Information incomplete", status=400, mimetype="application/json")

    product = list(products.find({'_id': data['product_id']}, {'stock': 0}))
    if product is not None:
        return Response(json.dumps(product), status=200, mimetype='application/json')
    else:
        return Response("Product not found", status=400, mimetype='application/json')


@app.route('/adminInsertProduct', methods=['POST'])
def admin_insert_product():
    uuid = request.headers.get('authorization')
    if not is_session_valid(uuid):
        return Response("User is not authenticated", status=401, mimetype='application/json')

    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=400, mimetype='application/json')
    if data == None:
        return Response("bad request", status=400, mimetype='application/json')
    if not "_id" in data or not "name" in data or not "price" in data or not "description" in data or not "category" in data or not "stock" in data:
        return Response("Information incomplete", status=400, mimetype="application/json")

    product = products.insert_one({"_id": data['_id'], "name": data['name'], "price": data['price'],
                                   "description": data['description'], "category": data['category'],
                                   "stock": data['stock']})
    if product is not None:
        return Response("Product was inserted", status=200, mimetype='application/json')
    else:
        return Response("Product was not inserted", status=400, mimetype='application/json')


@app.route('/adminDeleteProduct', methods=['POST'])
def admin_delete_product():
    uuid = request.headers.get('authorization')
    if not is_session_valid(uuid):
        return Response("User is not authenticated", status=401, mimetype='application/json')

    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=400, mimetype='application/json')
    if data == None:
        return Response("bad request", status=400, mimetype='application/json')
    if not "_id" in data:
        return Response("Information incomplete", status=400, mimetype="application/json")

    product = products.delete_one({"_id": data['_id']})
    if product is True:
        return Response("Product was deleted", status=200, mimetype='application/json')
    else:
        return Response("Product was not found", status=400, mimetype='application/json')


@app.route('/adminUpdateProduct', methods=['POST'])
def admin_update_product():
    uuid = request.headers.get('authorization')
    if not is_session_valid(uuid):
        return Response("User is not authenticated", status=401, mimetype='application/json')

    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=400, mimetype='application/json')
    if data == None:
        return Response("bad request", status=400, mimetype='application/json')
    if not "_id" in data:
        return Response("Information incomplete", status=400, mimetype="application/json")

    updated_values = {}

    if "name" in data:
        updated_values["name"] = data['name']

    if "price" in data:
        updated_values["price"] = data['price']

    if "description" in data:
        updated_values["description"] = data['description']

    if "stock" in data:
        updated_values["stock"] = data['stock']

    product = products.find_one_and_update({"_id": data['_id']}, {"$set": updated_values})

    if product is not None:
        return Response("Product was Updated", status=200, mimetype='application/json')
    else:
        return Response("Product was not found", status=400, mimetype='application/json')


@app.route('/addToCart', methods=['POST'])
def add_to_cart():
    uuid = request.headers.get('authorization')
    if not is_session_valid(uuid):
        return Response("User is not authenticated", status=401, mimetype='application/json')

    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=400, mimetype='application/json')
    if data == None:
        return Response("bad request", status=400, mimetype='application/json')
    if not "_id" in data or not "quantity" in data:
        return Response("Information incomplete", status=400, mimetype="application/json")

    product = products.find_one({"_id": data['_id']})
    if products.find_one({"_id": data['_id']}) is None:
        return Response("Product not found", status=400, mimetype='application/json')
    if 'cart' not in session:
        session['cart'] = {}

    if 'total' not in session['cart']:
        session['cart']['total'] = 0

    cart_quantity = 0
    if product['_id'] in session['cart']:
        cart_quantity = session['cart'][product['_id']]

    product_quantity = data['quantity'] + cart_quantity
    product_stock = product['stock']
    if product_quantity > product_stock:
        return Response("Not enough in stock", status=400, mimetype='application/json')
    else:
        new_stock = product_stock - product_quantity
        products.update_one({"_id": data['_id']}, {"$set": {"stock": new_stock}})

    session['cart'][product['_id']] = product_quantity
    session['cart']['total'] += product['price'] * product_quantity

    return Response(json.dumps(session['cart']), status=200, mimetype='application/json')


@app.route('/showCart', methods=['GET'])
def show_cart():
    uuid = request.headers.get('authorization')
    if not is_session_valid(uuid):
        return Response("User is not authenticated", status=401, mimetype='application/json')

    return Response(json.dumps(session['cart']), status=200, mimetype='application/json')


@app.route('/deleteFromCart', methods=['POST'])
def delete_from_cart():
    uuid = request.headers.get('authorization')
    if not is_session_valid(uuid):
        return Response("User is not authenticated", status=401, mimetype='application/json')

    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=400, mimetype='application/json')
    if data == None:
        return Response("bad request", status=400, mimetype='application/json')
    if not "_id" in data:
        return Response("Information incomplete", status=400, mimetype="application/json")

    product = products.find_one({"_id": data['_id']})
    if not product['_id'] in session['cart']:
        return Response("This product is not in your cart", status=400, mimetype='application/json')

    session['cart']['total'] -= product['price'] * session['cart'][product['_id']]
    del session['cart'][product['_id']]
    return Response("The product was deleted from your cart", status=200, mimetype='application/json')


@app.route('/checkout', methods=['POST'])
def checkout():
    uuid = request.headers.get('authorization')
    if not is_session_valid(uuid):
        return Response("User is not authenticated", status=401, mimetype='application/json')

    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=400, mimetype='application/json')
    if data == None:
        return Response("bad request", status=400, mimetype='application/json')
    if not "card_number" in data:
        return Response("Information incomplete", status=400, mimetype="application/json")

    card_number = data['card_number']
    card_number_len = len(card_number)
    while card_number_len != 16:
        return Response("Card number is incorrect", status=400, mimetype='application/json')

    response = json.dumps(session['cart'])
    del session['cart']
    return Response(response, status=200, mimetype='application/json')
    #Εδώ θα έπρεπε να προσθέτει το καλάθι του πελάτη στο ιστορικό παραγγελιών ώστε να μπορεί να έχει πρόσβαση
    # σε αυτό για το ζητούμενο, αλλά λόγω χρόνου δεν κατάφερα να το υλοποιήσω


@app.route('/deleteAccount', methods=['POST'])
def delete_account():
    uuid = request.headers.get('authorization')
    if not is_session_valid(uuid):
        return Response("User is not authenticated", status=401, mimetype='application/json')

    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=400, mimetype='application/json')
    if data == None:
        return Response("bad request", status=400, mimetype='application/json')
    if not "email" in data:
        return Response("Information incomplete", status=400, mimetype="application/json")

    user = users.find_one({"email": data['email']})
    if user:
        users.delete_one({"email": data['email']})
        return Response("Your account was deleted", status=200, mimetype='application/json')
    else:
        return Response("No account found", status=400, mimetype='application/json')


if __name__ == '__main__':
    app.run(debug=True)
