#!/usr/bin/env python

import os
# Flask imports
from flask import Flask, abort, request, jsonify, g, url_for
from flask.ext.httpauth import HTTPBasicAuth
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from flask.ext.pymongo import PyMongo

# useful imports
import json
import random
from datetime import datetime
from uuid import uuid4

# imports from files
import lib
import constants

# initialization of the Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'This is my secret key, or passphrase can we say, long enough? I think so.'
app.config['MONGO_PORT'] = 27017
app.config['MONGO_DBNAME'] = 'golfBallDispenserDatas'

# creation of a mongoDB container for Flask
mongo = PyMongo(app)

# creation of a authentication system for Flask
auth = HTTPBasicAuth()

class User:
    def __init__(self, username=None, uid=None):
        if username is None:
            userFromDB = mongo.db.user.find_one({'uid':uid})
            if userFromDB is None:
                self.uid = None
                self.username = None
            else:
                self.uid = uid
                self.username = userFromDB.get('username')
        else:
            userFromDB = mongo.db.user.find_one({'username':username})
            if userFromDB is None:
                self.username = None
                self.uid = None
            else:
                self.username = username
                self.uid = userFromDB.get('uid')
        if userFromDB is not None:
            self.password_hash = userFromDB.get('password')
            self.balance = userFromDB.get('balance')
            self.name = userFromDB.get('name')
            self.surname = userFromDB.get('surname')
            self.statement = userFromDB.get('statement')
            self.devices = userFromDB.get('devices')

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.uid})

    def get_device_id(self, android_id):
        userFromDB = mongo.db.user.find_one({'username':self.username, 'devices.androidId':android_id})
        if userFromDB is None:
            return self.create_device(android_id)
        else:
            for device in userFromDB.get('devices'):
                if device.get('androidId') == android_id:
                    return device.get('uid')
        return None

    def create_device(self, android_id):
        deviceId = self.generate_device_id()
        activation_date = datetime.now()
        category = 'smartphone'
        status = constants.STA_DEVICE_ACTIVE 

        user = mongo.db.user.find_one({"username": self.username})

        # create the new device
        newDevice = {"uid":deviceId, "status":status, "activationDate":activation_date, "androidId":android_id, "category":category}
        # add the new device to the list
        user['devices'].append(newDevice)
        # remove the _id from user (required to make a $set)
        del user['_id']
        
        # update user
        query = {"uid": user['uid'] }
        update = { "$set": user }
        mongo.db.user.update(query, update)

        return deviceId

    def generate_device_id(self):
        uid = []
        uid.append(random.randint(0,255))
        uid.append(random.randint(0,255))
        uid.append(random.randint(0,255))
        uid.append(random.randint(0,255))
        return lib.toHexString(uid)

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None    # valid token, but expired
        except BadSignature:
            return None    # invalid token
        user = User(uid=data['id'])
        return user

    def get_user_info(self):
        user = mongo.db.user.find_one(
                {"uid":self.uid}, 
                {'_id': 0, 'username': 1, 'name': 1, 'surname': 1, 'balance': 1, 'statement' : 1, 'registrationDate': 1}
            )
        return user

    def get_last_transactions(self, quantity):
        transactions = mongo.db.transaction.find(
                {'userId':self.uid}, 
                {'_id': 0, 'amount': 1, 'transactionType': 1, 'transactionDate': 1, 'deviceId': 1, 'dispenserId': 1}
            ).limit(quantity).sort("transactionDate", -1)
        trs = []
        for transaction in transactions:
            trs.append(transaction)
        return trs

@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if user is None:
        # try to authenticate with username/password
        user = User(username=username_or_token)
        if user.username is None or not user.verify_password(password):
            return False
    g.user = user
    return True

@app.route('/')
def home_page():
    return 'Welcome on the NFC GOLF BALL DISPENSER APIs<br />The APIs are accessible via vlenfc.hevs.ch/api/...'

@app.route('/api/newpassword', methods=['GET'])
def set_new_password():
    username = request.args.get('username', '')
    password = request.args.get('password', '')
    password_hash = pwd_context.encrypt(password)

    query = {"username" : username}
    newPwd = {"password" : password_hash}
    update = {"$set" : newPwd}
    mongo.db.user.update(query, update)
    return "password registered"

@app.route('/api/newaccount', methods=['POST'])
def set_new_account():
    username = request.json.get('username', '')
    name = request.json.get('name', '')
    surname = request.json.get('surname', '')
    password = request.json.get('password', '')
    password_hash = pwd_context.encrypt(password)

    # check if the username already exists
    userFromDB = mongo.db.user.find_one({'username':username})
    if userFromDB is None:
        uid = str(uuid4())
        balance = 10
        registrationDate = datetime.now()
        statement = constants.STA_USER_ACTIVE
        devices = []

        user = {"uid":uid, 
            "username":username, 
            "password":password_hash, 
            "balance":balance, 
            "registrationDate":registrationDate, 
            "statement":statement, 
            "devices":devices}

        if name:
            user['name'] = name
        if surname:
            user['surname'] = surname

        # creation of the user
        mongo.db.user.insert(user)

        # Success code 201 = CREATED
        return "Account sucessfully created", 201
    else:
        # Fail code 403 = FORBIDDEN
        abort(403)

@app.route('/api/token')
@auth.login_required
def get_auth_token():
    # ex : curl -u username:password -i -X GET http://localhost:5000/api/token
    # ou : curl -u token:dontcare -i -X GET http://localhost:5000/api/token
    token = g.user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})

@app.route('/api/deviceid/<androidid>')
@auth.login_required
def get_device_id(androidid):
    device_id = g.user.get_device_id(androidid)
    return jsonify({'uid': '%s' % device_id})

@app.route('/api/balance')
@auth.login_required
def get_balance():
    return jsonify({'balance': '%s' % g.user.balance})

@app.route('/api/devices')
@auth.login_required
def get_devices():
    return jsonify({'devices' : '%s' % g.user.devices})

@app.route('/api/user')
@auth.login_required
def get_user():
    return jsonify({'user': g.user.get_user_info()})

@app.route('/api/transactions')
@auth.login_required
def get_transactions():
    return jsonify({'transactions' : g.user.get_last_transactions(10)})
    
if __name__ == '__main__':
    #app.run(debug=True, host='127.0.0.1')       # to run locally on port 5000
    app.run(debug=True, host='0.0.0.0', port=80) # to run on a server
