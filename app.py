from flask import Flask, session, redirect, url_for, escape, request, render_template
from flask_mail import Mail, Message
import json
from threading import Thread

from config import MAIL_ADDRESS


app = Flask(__name__)
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

@app.route('/catalog', methods = ['GET'])
def catalog():
    if 'email_address' in session:
        return render_template('catalog.html', catalog_list=catalog_list)
    else:
        return redirect(url_for('login'))

@app.route('/order/<item_id>', methods = ['POST'])
def order(item_id=None):
    send_email([session['email_address']], item_id)
    return redirect(url_for('complete'))

@app.route('/complete', methods = ['GET'])
def complete():
    return render_template('complete.html')


# Async email support
def send_async_email(msg):
    with app.app_context():
        mail.send(msg)

def send_email(recipients, order_name):
    subject = "PACKAGE RECEIPT NOTIFICATION"
    msg = Message(subject, sender=MAIL_ADDRESS, recipients=recipients)
    msg.body = "YO WHAT UP BITCH! You ordered {}".format(order_name)
    thr = Thread(target=send_async_email, args=[msg])
    thr.start()
