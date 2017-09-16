from flask import Flask, session, redirect, url_for, escape, request, render_template
from flask_mail import Mail, Message
import json
import os
from threading import Thread
import time
from bson.objectid import ObjectId
import random
from pymongo import MongoClient
from datetime import datetime

from config import MAIL_ADDRESS

CLIENT = MongoClient(os.environ.get('MONGODB_URI', 'localhost:27107'))
DB = CLIENT.mailroom
ORDERS = DB.orders

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'no one will ever guess this'
app.config.from_object('config')
mail = Mail(app)

with open('config/catalog.json') as catalog_file:
    catalog_list = json.load(catalog_file)

@app.route('/')
def index():
    if 'email_address' in session:
        return redirect(url_for('catalog'))
    else:
        return redirect(url_for('login'))

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['email_address'] = request.form['emailAddress']
        return redirect(url_for('catalog'))
    else:
        return render_template('login.html')

@app.route('/logout', methods = ['GET'])
def logout():
    session.pop('email_address')
    return redirect(url_for('login'))


@app.route('/catalog', methods = ['GET'])
def catalog():
    if 'email_address' in session:
        return render_template('catalog.html', catalog_list=catalog_list)
    else:
        return redirect(url_for('login'))


@app.route('/admin', methods=['GET'])
def admin():
    if 'email_address' in session:
        return render_template('admin.html', orders=list(ORDERS.find({"served": False})))
    else:
        return redirect(url_for('login'))

@app.route('/admin/<order_id>', methods=['POST'])
def serve(order_id):
    order = ORDERS.find_one({"_id": ObjectId(order_id)})
    send_email([order['email']], order['drink'])
    ORDERS.update({"_id": ObjectId(order_id)}, {"served": True})
    return redirect(url_for('admin'))


@app.route('/order/<item_id>', methods=['POST'])
def order(item_id=None):
    # Tell them to chill if it's been less than 15 minutes since last order
    last_drink = (time.time() - session.get('last_drink', 0)) / 60
    if last_drink < 15:
        response = {
            "success": False,
            "message": "You ordered a drink {} minutes ago, please wait at least 15 minutes between \
orders #TIPS #StaySafeStayFun #Orientation".format(int(last_drink))
        }
    else:
        session['last_drink'] = time.time()
        ORDERS.insert({"email": session['email_address'], "drink": item_id, "served": False})
        response = {
            "success": True,
            "message": "Your order has been received. You will get an email from Mailroom Services when it's ready!"
        }
    return json.dumps(response)


@app.route('/complete', methods=['GET'])
def complete():
    return render_template('complete.html')


# Async email support
def send_async_email(msg):
    with app.app_context():
        # time.sleep(random.randint(10,100))
        mail.send(msg)

def send_email(recipients, order_name):
    subject = "PACKAGE RECEIPT NOTIFICATION"
    msg = Message(subject, sender=MAIL_ADDRESS, recipients=recipients)
    msg.body = """
    Your Package Has Arrived! You can pick your package up during open window
    hours, which are posted outside the mailroom in the lower level of the Campus
    Center.


    Package Details:

         Item Name...:  {}
         Tracking No.:  {}
         Carrier.....:  The 'Pony' Express ;)
         Service.....:

         Received From Carrier.....:  {}
         Signed For By.............:  BACKSUITE BOYS

    Received From:

         Company.....:
         Address.....:
         C/S/Z.......:

         Contact.....:

    """.format(order_name,
               ''.join(random.choice('0123456789ABCDEF') for i in range(16)),
               datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    thr = Thread(target=send_async_email, args=[msg])
    thr.start()
