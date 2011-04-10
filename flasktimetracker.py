from flask import Flask, render_template, send_from_directory, request, Response
from flask import session, escape, flash, redirect, url_for
from functools import wraps
from flaskext.wtf import Form,TextField,PasswordField
from wtforms import validators
from werkzeug import generate_password_hash, check_password_hash
import datetime
import os
from mongoengine import EmbeddedDocument, Document, DateTimeField, StringField, IntField, ListField, EmbeddedDocumentField, connect

# configuration
DEBUG = True
SECRET_KEY = "66&r+=abre8AKaprE!acR87=P?esAd"
CSRF_ENABLED = False
MONGODB_DATABASE = "testdb"

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('SETTINGS', silent=True)

class Interval(EmbeddedDocument):
    start = DateTimeField()
    stop = DateTimeField()
    
class User(Document):
    username = StringField()
    pw_hash = StringField()
    overtime = IntField()
    worktime = IntField()
    intervals = ListField(EmbeddedDocumentField(Interval))
    
    def set_pw_hash(self, password):
        self.pw_hash = generate_password_hash(password)
        
    def is_correct_password(self, password):
        return check_password_hash(self.pw_hash, password)

class LoginForm(Form):
    username = TextField("username",[validators.required()])
    password = PasswordField("password",[validators.required()])
    
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "userid" not in session:
            flash("login required.")
            return redirect(url_for('login'))
        else:
            return f(*args, **kwargs)
    return decorated

mongo = connect(app.config['MONGODB_DATABASE'])

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/login')
def login():
        return render_template('login.html', form=LoginForm())

@app.route('/logout')
def logout():
    session.pop("userid", None)
    flash("logged out successfully.")
    return redirect(url_for('login'))

@app.route('/checkLogin',  methods=['POST'])
def check_login():
    form = LoginForm(request.form) 
    if form.validate_on_submit():
        user = User.objects(username = form.username.data).first()
        if user is not None and user.is_correct_password(form.password.data):
            valid_login = True
        else:
            valid_login = False
    else:
        valid_login = False    
      
    if valid_login:
        session["userid"] = user.id
        flash("logged in successfully.")
        return redirect(url_for('hello_world'))        
    else:
        flash("user/pw invalid.")
        return render_template('login.html', form=form)
        
@app.route('/')
@requires_auth
def hello_world():
    return render_template('index.html')

if __name__ == '__main__':
    app.run()
