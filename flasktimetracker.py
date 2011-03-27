from flask import Flask, render_template, send_from_directory, request, Response
from flask import session, escape, flash, redirect, url_for
from functools import wraps
from flaskext.wtf import Form,TextField,PasswordField
from wtforms import validators
import os

# configuration
DEBUG = True
SECRET_KEY = "66&r+=abre8AKaprE!acR87=P?esAd"
CSRF_ENABLED = False

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

class LoginForm(Form):
    username = TextField("username",[validators.required()])
    password = PasswordField("password",[validators.required()])
    
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not "id" in session:
            flash("login required.")
            return redirect(url_for('login'))
        else:
            return f(*args, **kwargs)
    return decorated

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/login')
def login():
    return render_template('login.html', form=LoginForm())

@app.route('/checkLogin',  methods=['POST'])
def check_login():
    form = LoginForm(request.form)
    if form.validate_on_submit() and form.name.data == "admin" and form.password.data =="geheim":   
        session["id"] = 1
        flash("login successfully.")
        return redirect(url_for('hello_world'))
    else:
        flash("user/pw invalid.")
        return redirect(url_for('show_login'))
    
@app.route('/')
@requires_auth
def hello_world():
    return render_template('index.html')

if __name__ == '__main__':
    app.run()