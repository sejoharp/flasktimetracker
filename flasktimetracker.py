from datetime import datetime, timedelta
from flask import Flask, render_template, send_from_directory, request, Response, \
    session, escape, flash, redirect, url_for, abort
from flaskext.wtf import Form, TextField, PasswordField, DateTimeField
from functools import wraps
from mongoengine import fields, Document, connect, ValidationError
from pymongo.objectid import ObjectId
from werkzeug import generate_password_hash, check_password_hash
from wtforms import validators
import os

# configuration
DEBUG = True
SECRET_KEY = "66&r+=abre8AKaprE!acR87=P?esAd"
CSRF_ENABLED = False
MONGODB_DATABASE = "testdb"

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('SETTINGS', silent=True)

class Interval(Document):
    start = fields.DateTimeField(required=True)
    stop = fields.DateTimeField()
    userid = fields.ObjectIdField(required=True)
    
    def duration(self):
        return (self.stop or datetime.today()) - self.start 
    
class User(Document):
    username = fields.StringField()
    pw_hash = fields.StringField()
    overtime = fields.IntField()
    worktime = fields.IntField()
    
    def set_pw_hash(self, password):
        self.pw_hash = generate_password_hash(password)
        
    def is_correct_password(self, password):
        return check_password_hash(self.pw_hash, password)

class LoginForm(Form):
    username = TextField("username",[validators.required()])
    password = PasswordField("password",[validators.required()])

class Interval_Form(Form):
    start = DateTimeField([validators.required()])
    stop = DateTimeField()
    userid = TextField()
        
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

@app.route('/login/show')
def login():
        return render_template('login.html', form=LoginForm())

@app.route('/login/disable')
def logout():
    session.pop("userid", None)
    flash("logged out successfully.")
    return redirect(url_for('login'))

@app.route('/interval/edit/<id>')
@requires_auth
def edit_interval(id):
    try:
        interval = Interval.objects().with_id(id)
    except ValidationError:
        abort(404)        
    return render_template('interval_edit.html', form=Interval_Form(obj=interval))
        
@app.route('/interval/save',  methods=['POST'])
@requires_auth
def save_interval():
    form = LoginForm(request.form) 
    if form.validate_on_submit():
        form.populate_obj(interval)
        interval.save()
        flash("interval edit successfully.")
        return redirect(url_for('index')) 
    else:
        return render_template('interval_edit.html', form=form)

@app.route('/login/check',  methods=['POST'])
def check_login():
    form = LoginForm(request.form) 
    if form.validate_on_submit():
        user = User.objects(username = form.username.data).first()
        if user is not None and user.is_correct_password(form.password.data):
            session["userid"] = user.id
            flash("logged in successfully.")
            return redirect(url_for('index'))  

    flash("user/pw invalid.")
    return render_template('login.html', form=form)
        
@app.route('/')
@requires_auth
def index():
    return render_template('index.html')

def calc_durations(intervals):
    sum = timedelta()
    if intervals:
        for interval in intervals:
            sum += interval.duration()
    return sum

def get_current_user():
    return User.objects().with_id(session["userid"])
    
if __name__ == '__main__':
    app.run()
