from datetime import datetime, timedelta, date
from flask import Flask, render_template, send_from_directory, request, Response, \
    session, escape, flash, redirect, url_for, abort
from flaskext.wtf import Form, TextField, PasswordField, DateTimeField, HiddenField
from functools import wraps
from mongoengine import fields, Document, connect, ValidationError
from pymongo.objectid import ObjectId
from werkzeug import generate_password_hash, check_password_hash
from wtforms import validators
import os
from mongoengine.queryset import queryset_manager, Q
# configuration
DEBUG = True
SECRET_KEY = "66&r+=abre8AKaprE!acR87=P?esAd"
CSRF_ENABLED = False
MONGODB_DATABASE = "testdb"

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('SETTINGS', silent=True)

@app.template_filter('datetime')
def datetime_filter(dt):
    try:
        if is_today(dt):
            return dt.strftime("%H:%M:%S")
        else:
            return dt.strftime("%d.%m.%Y %H:%M:%S")
    except:
        return ""

@app.template_filter('timedelta')
def timedelta_filter(td):

    total_seconds = td.days * 24 * 60 * 60 + td.seconds

    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    hours = "00" if hours == 0 else str(hours)
    minutes = "00" if minutes == 0 else str(minutes)
    seconds = "00" if seconds == 0 else str(seconds)
    return hours + ":" + minutes + ":" + seconds
           

    
class Interval(Document):
    start = fields.DateTimeField(required=True)
    stop = fields.DateTimeField()
    userid = fields.ObjectIdField(required=True)
    
    def duration(self):
        return (self.stop or datetime.today()) - self.start 
    
    @staticmethod
    def get_last_from_user(userid):
        return Interval.objects(userid=userid).order_by("-start").first()
    
    @staticmethod
    def get_from_today(userid):
        date = datetime.today().replace(second=0, minute=0, hour=0, microsecond=0)
        return Interval.objects(userid=userid, start__gte=date)
    
    @staticmethod
    def get_by_id(id):
        return Interval.objects().with_id(id)
    
class User(Document):
    username = fields.StringField()
    pw_hash = fields.StringField()
    overtime = fields.IntField()
    worktime = fields.IntField()
    
    def set_pw_hash(self, password):
        self.pw_hash = generate_password_hash(password)
        
    def is_correct_password(self, password):
        return check_password_hash(self.pw_hash, password)
    
    @staticmethod
    def get_user_by_id(userid):
        return User.objects().with_id(userid)
        
    @staticmethod
    def get_user_by_name(name):
        return User.objects(username = name).first()

class Login_Form(Form):
    username = TextField("username",[validators.required()])
    password = PasswordField("password",[validators.required()])

class Interval_Form(Form):
    stop = DateTimeField("stop", [validators.optional()])
    start = DateTimeField("start", [validators.required()])
    id = HiddenField([validators.required()])
        
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
        return render_template('login.html', form=Login_Form())

@app.route('/login/disable')
def logout():
    session.pop("userid", None)
    flash("logged out successfully.")
    return redirect(url_for('login'))

@app.route('/interval/edit/<id>')
@requires_auth
def edit_interval(id):
    try:
        interval = Interval.get_by_id(id)
    except ValidationError:
        abort(404)        
    return render_template('interval_edit.html', form=Interval_Form(obj=interval))
        
@app.route('/interval/save',  methods=['POST'])
@requires_auth
def save_interval():
    form = Interval_Form(request.form) 
    if form.validate_on_submit():
        interval = Interval.get_by_id(form.id.data)
        form.populate_obj(interval)
        interval.userid = get_current_user().id
        interval.save()
        flash("interval edit successfully.")
        return redirect(url_for('index')) 
    else:
        return render_template('interval_edit.html', form=form)

@app.route('/login/check',  methods=['POST'])
def check_login():
    form = Login_Form(request.form) 
    if form.validate_on_submit():
        user = User.get_user_by_name(form.username.data);
        if user is not None and user.is_correct_password(form.password.data):
            session["userid"] = user.id
            flash("logged in successfully.")
            return redirect(url_for('index'))  

    flash("user/pw invalid.")
    return render_template('login.html', form=form)
        
@app.route('/')
@requires_auth
def index():
    return render_template('index.html', 
                           intervals=Interval.get_from_today(get_current_userid()),
                           is_working = is_user_working())

@app.route('/interval/change',  methods=['POST'])
@requires_auth
def change_state():
    interval = Interval.get_last_from_user(get_current_userid())
    if interval and interval.stop is None:
        interval.stop = datetime.now()
        interval.save()
    else:
        interval = Interval()
        interval.start = datetime.now()
        interval.userid = get_current_userid()
        interval.save()
    return redirect(url_for('index'))  

def calc_durations(intervals):
    sum = timedelta()
    if intervals:
        for interval in intervals:
            sum += interval.duration()
    return sum

def is_user_working():
    interval = Interval.get_last_from_user(get_current_userid())
    return True if interval and interval.stop is None else False

def get_current_user():
    return User.get_user_by_id(get_current_userid())

def get_current_userid():
    return session["userid"];

def is_today(value):
    return True if value.date() == date.today() else False
 
if __name__ == '__main__':
    app.run()
