from flask import Flask, session, redirect, url_for, escape, request, render_template

app = Flask(__name__)
app.secret_key = 'no one will ever guess this'

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
        return render_template('catalog.html')
    else:
        return redirect(url_for('login'))

@app.route('/order/<item_id>', methods = ['POST'])
def order(item_id=None):
    return 'ordered {}'.format(item_id)
