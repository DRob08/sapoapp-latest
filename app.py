import logging
import os
import ssl
import sys
from datetime import date
from datetime import datetime
from functools import wraps

import certifi
# import folium
import geopy.geocoders
import pandas as pd
import requests
from PIL import Image
from flask import Flask, render_template, flash, redirect, url_for, session, request
from flask import jsonify
from flask_googlemaps import GoogleMaps
from flask_migrate import Migrate
# from data import Articles
from flask_mysqldb import MySQL
from flask_sqlalchemy import SQLAlchemy
from geopy.geocoders import Nominatim
from passlib.hash import sha256_crypt
from sqlalchemy.engine import create_engine
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, SubmitField
# from wtforms.fields.html5 import EmailField
from wtforms.validators import Email

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'flaskappdb'
app.config['MYSQL_UNIX_SOCKET'] = '/Applications/MAMP/tmp/mysql/mysql.sock'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# you can set key as config
app.config['GOOGLEMAPS_KEY'] = "8JZ7i18MjFuM35dJHq70n3Hx4"

# you can also pass the key here if you prefer
GoogleMaps(app, key="AIzaSyAFkMCq9GY2J9N-LDOlqCpBWDM1c4QwKbs")

geopy.geocoders.options.default_user_agent = 'my_app/1'
geopy.geocoders.options.default_timeout = 7
ctx = ssl.create_default_context(cafile=certifi.where())
geopy.geocoders.options.default_ssl_context = ctx
geolocator = Nominatim(scheme='http')

API_KEY = "AIzaSyAFkMCq9GY2J9N-LDOlqCpBWDM1c4QwKbs"
RETURN_FULL_RESULTS = False

# app.config['profile-images'] = '/Users/DRob/PycharmProjects/myflaskapp/static/profile-images'
app.config['profile-images'] = '/Users/DRob/sites/content/uploads'

# init MySQL
mysql = MySQL(app)

logger = logging.getLogger("root")
logger.setLevel(logging.DEBUG)
# create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@127.0.0.1:8889/flaskappdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = 'false'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# default
engine = create_engine('mysql://root:root@127.0.0.1:8889/flaskappdb', echo=False)
connection = engine.connect()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    name = db.Column(db.String(120))
    '''last_name = db.Column(db.String(120))'''
    email = db.Column(db.String(120), index=True, unique=True)
    password = db.Column(db.String(128))
    register_date = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def __init__(self, name, last_name, email, username, password):
        self.name = name
        self.last_name = last_name
        self.email = email
        self.username = username
        self.password = password

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Articles = Articles()


@app.route('/')
def index():
    users = User.query.all()

    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


def increment_filename(filename, marker='-'):
    """
    Returns a generator that yields filenames with a counter. This counter
    is placed before the file extension, and incremented with every iteration.
    For example:
        f1 = increment_filename("myimage.jpeg")
        f1.next() # myimage-1.jpeg
        f1.next() # myimage-2.jpeg
        f1.next() # myimage-3.jpeg
    If the filename already contains a counter, then the existing counter is
    incremented on every iteration, rather than starting from 1.
    For example:
        f2 = increment_filename("myfile-3.doc")
        f2.next() # myfile-4.doc
        f2.next() # myfile-5.doc
        f2.next() # myfile-6.doc
    The default marker is an underscore, but you can use any string you like:
        f3 = increment_filename("mymovie.mp4", marker="_")
        f3.next() # mymovie_1.mp4
        f3.next() # mymovie_2.mp4
        f3.next() # mymovie_3.mp4
    Since the generator only increments an integer, it is practically unlimited
    and will never raise a StopIteration exception.
    """
    # First we split the filename into three parts:
    #
    #  1) a "base" - the part before the counter
    #  2) a "counter" - the integer which is incremented
    #  3) an "extension" - the file extension
    basename, fileext = os.path.splitext(filename)

    # Check if there's a counter in the filename already - if not, start a new
    # counter at 0.
    if marker not in basename:
        base = basename
        value = 0

    # If it looks like there might be a counter, then try to coerce it to an
    # integer to get its value. Otherwise, start with a new counter at 0.
    else:
        base, counter = basename.rsplit(marker, 1)

        try:
            value = int(counter)
        except ValueError:
            base = basename
            value = 0

    # The counter is just an integer, so we can increment it indefinitely.
    while True:
        if value == 0:
            value += 1
            return '%s%s%d%s' % (base, marker, value, fileext)
        value += 1
        break
    return '%s%s%d%s' % (base, marker, value, fileext)


def insert_profile(name, midlename, lastname, lastnamemom, dob, cedula, imgpath, phone, address, department,
                   municipality, area, employment, alias, sex, allegations, lat, lng):
    query = "INSERT INTO profiles(name,middle_name,lastname,lastname_mother,dob,cedula_id,imgpath,phone," \
            "address,department,municipality,area,work,alias,sex,allegations_details,latitude,longitude) " \
            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    args = (name, midlename, lastname, lastnamemom, dob, cedula, imgpath, phone, address, department,
            municipality, area, employment, alias, sex, allegations, lat, lng)

    try:
        # Create cursor
        cur = mysql.connection.cursor()

        #  Execute query
        #  cur.execute("INSERT INTO users(name, email, username, password) VALUES( %s, %s, %s, %s)",
        #   (name, email, username, password))
        cur.execute(query, args)

        # commit DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        return True

    # except my.DataError as e:
    #     print("DataError")
    #     print(e)
    #
    # except my.InternalError as e:
    #     print("InternalError")
    #     print(e)
    #
    # except my.IntegrityError as e:
    #     print("IntegrityError")
    #     print(e)
    #
    # except my.OperationalError as e:
    #     print("OperationalError")
    #     print(e)
    #
    # except my.NotSupportedError as e:
    #     print("NotSupportedError")
    #     print(e)
    #
    # except my.ProgrammingError as e:
    #     print("ProgrammingError")
    #     print(e)

    except:
        print("Unknown error occurred")
        return False

    finally:
        cur.close()


@app.route('/add_profile', methods=['GET', 'POST'])
def new_profile():
    if request.method == 'POST':
        name = request.form['name']
        middle_name = request.form['secondname']
        lastname = request.form['lastname']
        secondlname = request.form['secondlname']
        dob = request.form['datepicker']
        cedula = request.form['cedula']
        phone = request.form['phone']
        address = request.form['address']
        department = request.form['department']
        municipality = request.form['municipality']
        area = request.form['area']
        alias = request.form['alias']
        work = request.form['work']
        # work_address = request.form['work_address']
        allegations = request.form['delitos']
        gender = request.form['defaultExampleRadios']

        if len(area) == 0:
            full_address = municipality + ", " + department + ", Nicaragua"
        else:
            full_address = area + " " + municipality + ", " + department + ", Nicaragua"

        # Ensure, before we start, that the API key is ok/valid, and internet access is ok
        # test_result = get_google_results("London, England", API_KEY, RETURN_FULL_RESULTS)
        # if (test_result['status'] != 'OK') or (test_result['formatted_address'] != 'London, UK'):
        #     logger.warning("There was an error when testing the Google Geocoder.")
        #     raise ConnectionError('Problem with test results from Google Geocode - '
        #                           'check your API key and internet connection.')

        # location = geolocator.geocode(full_address)

        try:
            # geocode_result = get_google_results(full_address, API_KEY, return_full_response=RETURN_FULL_RESULTS)

            location = geolocator.geocode(full_address)

            if location:
                latitude, longitude = location.latitude, location.longitude
            else:
                latitude, longitude = 0.0, 0.0
                error = "No Address Found "
                render_template('add_profile.html', error=error)

        except Exception as e:
            logger.exception(e)
            logger.error("Major error with {}".format(address))
            logger.error("Skipping!")
            geocoded = True

        # if geocode_result['status'] != 'OK':
        #     logger.warning("Error geocoding {}: {}".format(address, geocode_result['status']))
        #     logger.debug("Geocoded: {}: {}".format(address, geocode_result['status']))
        #     geocoded = True

        f = request.files['profile_img']
        filename = secure_filename(f.filename)

        # format_str = '%m/%d/%Y'  # The format
        format_str = '%d/%m/%Y'  # The format
        dob_obj = datetime.strptime(dob, format_str)

        today_date = date.today()
        today_path = app.config['profile-images'] + '/' + today_date.strftime("%Y/%m/%d")

        local_host_path = 'http://127.0.0.1:8888/content/uploads/' + today_date.strftime("%Y/%m/%d")

        if not os.path.exists(today_path):
            os.makedirs(today_path)
            f.save(os.path.join(today_path, filename))
        else:
            if os.path.isfile(today_path + '/' + filename):

                while os.path.isfile(today_path + '/' + filename):
                    filename = increment_filename(filename)

                f.save(os.path.join(today_path, filename))
            else:
                f.save(os.path.join(today_path, filename))

        resize_and_crop(today_path + '/' + filename, today_path + '/' + filename, (200, 200), 'middle')

        # img_path = today_path + '/' + filename
        img_path = local_host_path + '/' + filename

        if insert_profile(name, middle_name, lastname, secondlname, dob_obj, cedula, img_path, phone, address,
                          department,
                          municipality, area, work, alias, '', allegations, latitude, longitude):

            # Create Cursor
            cur = mysql.connection.cursor()

            # Get Articles
            cur.execute("SELECT * from profiles ORDER BY id DESC LIMIT 1")

            profile = cur.fetchone()

            # Close Connection
            cur.close
            return render_template('profile.html', profile=profile)
        else:
            error = 'Error tratando de insertar nuevo perfil'

            render_template('add_profile.html', error=error)

    return render_template('add_profile.html')


def get_google_results(address, api_key=None, return_full_response=False):
    """
    Get geocode results from Google Maps Geocoding API.

    Note, that in the case of multiple google geocode reuslts, this function returns details of the FIRST result.

    @param address: String address as accurate as possible. For Example "18 Grafton Street, Dublin, Ireland"
    @param api_key: String API key if present from google.
                    If supplied, requests will use your allowance from the Google API. If not, you
                    will be limited to the free usage of 2500 requests per day.
    @param return_full_response: Boolean to indicate if you'd like to return the full response from google. This
                    is useful if you'd like additional location details for storage or parsing later.
    """
    # Set up your Geocoding url
    geocode_url = "https://maps.googleapis.com/maps/api/geocode/json?address={}".format(address) + "&sensor=false"
    # if api_key is not None:
    #     geocode_url = geocode_url + "&key={}".format(api_key)

    # Ping google for the reuslts:
    results = requests.get(geocode_url)

    # Results will be in JSON format - convert to dict using requests functionality
    results = results.json()

    # if there's no results or an error, return empty results.
    if len(results['results']) == 0:
        output = {
            "formatted_address": None,
            "latitude": None,
            "longitude": None,
            "accuracy": None,
            "google_place_id": None,
            "type": None,
            "postcode": None
        }
    else:
        answer = results['results'][0]
        output = {
            "formatted_address": answer.get('formatted_address'),
            "latitude": answer.get('geometry').get('location').get('lat'),
            "longitude": answer.get('geometry').get('location').get('lng'),
            "accuracy": answer.get('geometry').get('location_type'),
            "google_place_id": answer.get("place_id"),
            "type": ",".join(answer.get('types')),
            "postcode": ",".join([x['long_name'] for x in answer.get('address_components')
                                  if 'postal_code' in x.get('types')])
        }

    # Append some other details:
    output['input_string'] = address
    output['number_of_results'] = len(results['results'])
    output['status'] = results.get('status')
    if return_full_response is True:
        output['response'] = results

    return output


def resize_and_crop(img_path, modified_path, size, crop_type='top'):
    """
    Resize and crop an image to fit the specified size.

    args:
    img_path: path for the image to resize.
    modified_path: path to store the modified image.
    size: `(width, height)` tuple.
    crop_type: can be 'top', 'middle' or 'bottom', depending on this
    value, the image will cropped getting the 'top/left', 'middle' or
    'bottom/right' of the image to fit the size.
    raises:
    Exception: if can not open the file in img_path of there is problems
    to save the image.
    ValueError: if an invalid `crop_type` is provided.
    """
    # If height is higher we resize vertically, if not we resize horizontally
    img = Image.open(img_path)
    # Get current and desired ratio for the images
    img_ratio = img.size[0] / float(img.size[1])
    ratio = size[0] / float(size[1])
    # The image is scaled/cropped vertically or horizontally depending on the ratio
    if ratio > img_ratio:
        img = img.resize((size[0], int(round(size[0] * img.size[1] / img.size[0]))),
                         Image.ANTIALIAS)
        # Crop in the top, middle or bottom
        if crop_type == 'top':
            box = (0, 0, img.size[0], size[1])
        elif crop_type == 'middle':
            box = (0, int(round((img.size[1] - size[1]) / 2)), img.size[0],
                   int(round((img.size[1] + size[1]) / 2)))
        elif crop_type == 'bottom':
            box = (0, img.size[1] - size[1], img.size[0], img.size[1])
        else:
            raise ValueError('ERROR: invalid value for crop_type')
        img = img.crop(box)
    elif ratio < img_ratio:
        img = img.resize((int(round(size[1] * img.size[0] / img.size[1])), size[1]),
                         Image.ANTIALIAS)
        # Crop in the top, middle or bottom
        if crop_type == 'top':
            box = (0, 0, size[0], img.size[1])
        elif crop_type == 'middle':
            box = (int(round((img.size[0] - size[0]) / 2)), 0,
                   int(round((img.size[0] + size[0]) / 2)), img.size[1])
        elif crop_type == 'bottom':
            box = (img.size[0] - size[0], 0, img.size[0], img.size[1])
        else:
            raise ValueError('ERROR: invalid value for crop_type')
        img = img.crop(box)
    else:
        img = img.resize((size[0], size[1]), Image.ANTIALIAS)
    # If the scale is the same, we do not need to crop
    img.save(modified_path)


# User Sign in
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        # Get forms field
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor

        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username =%s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):

                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now Logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid Login'
                return render_template('signin.html', error=error)
            # Close Connection
            cur.close()

        else:
            error = 'Username not found'
            return render_template('signin.html', error=error)

    return render_template('signin.html')


# Check if user Logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login', 'danger')
            return redirect(url_for('login'))

    return wrap


# Articles
@app.route('/articles')
@is_logged_in
def articles():
    # Create Cursor
    cur = mysql.connection.cursor()

    # Get Articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg)

    # Close Connection
    cur.close


@app.route('/profile/<string:profile_id>/')
def profile(profile_id):
    # Create Cursor
    cur = mysql.connection.cursor()

    # Get Articles
    result = cur.execute("SELECT * FROM profiles WHERE id = %s", [profile_id])

    profile = cur.fetchone()

    # Close Connection
    cur.close

    return render_template('profile.html', profile=profile)


@app.route('/profiles', methods=['GET', 'POST'])
def show_profile():
    if request.method == 'GET':
        # Create Cursor
        cur = mysql.connection.cursor()

        # Get Articles
        result = cur.execute("SELECT * FROM profiles")
        profiles = cur.fetchall()

        # Get Areas
        result = cur.execute("SELECT DISTINCT AREA from profiles where LENGTH(area) > 0")
        areas = cur.fetchall()

        # Get Municipality
        result = cur.execute("SELECT DISTINCT municipality  from profiles where LENGTH(municipality ) > 0")
        municipalities = cur.fetchall()

        result = cur.execute("SELECT DISTINCT department from profiles where LENGTH(department) > 0")
        departments = cur.fetchall()

        # Close Connection
        cur.close

        return render_template('profiles.html', profiles=profiles, areas=areas)
    elif request.method == 'POST':
        return render_template('profiles.html')

    error = "NO PERFILES"
    return render_template('profiles.html', error=error)


# @app.route('/show_map')
# def mapview():

# creating a map in the view
    # mymap =  Map(
    #     identifier="catsmap",
    #     lat=12.335542,
    #     lng=-84.919941,
    #     zoom=9,
    #     maptype="ROADMAP",
    #     fit_markers_to_bounds=True,
    #     markers=[
    #         {
    #             'icon': 'http://127.0.0.1:8888/content/uploads/2018/09/20/sapo-face-logo-30x30.png',
    #             'lat':  12.335542,
    #             'lng':  -84.919941,
    #             'infobox': "<img src='cat1.jpg' />"
    #         },
    #         {
    #             'icon': 'http://127.0.0.1:8888/content/uploads/2018/09/20/sapo-face-logo-30x30.png',
    #             'lat': 12.335542,
    #             'lng': -86.251389,
    #             'infobox': "<img src='cat2.jpg' />"
    #         },
    #         {
    #             'icon': 'http://127.0.0.1:8888/content/uploads/2018/09/20/sapo-face-logo-30x30.png',
    #             'lat': 12.335542,
    #             'lng': -84.919941,
    #             'infobox': "<img src='cat3.jpg' />"
    #         }
    #     ]
    # )
    # sndmap = Map(
    #     identifier="sndmap",
    #     lat=37.4419,
    #     lng=-122.1419,
    #     markers=[
    #       {
    #          'icon': 'http://maps.google.com/mapfiles/ms/icons/green-dot.png',
    #          'lat': 37.4419,
    #          'lng': -122.1419,
    #          'infobox': "<b>Hello World</b>"
    #       },
    #       {
    #          'icon': 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
    #          'lat': 37.4300,
    #          'lng': -122.1400,
    #          'infobox': "<b>Hello World from other place</b>"
    #       }
    #     ]
    # )
    #
    # return render_template('show_map.html', mymap=mymap, sndmap=sndmap)
# SF_COORDINATES = (37.76, -122.45)
#
# firedata = pd.read_csv('/Users/DRob/PycharmProjects/myflaskapp/Fire_Incidents.csv')
#
# firedata = firedata[pd.notnull(firedata['Location']) & pd.notnull(firedata['Address'])]
#
# # for speed purposes
# MAX_RECORDS = 1000
#
# # create empty map zoomed in on San Francisco
# mymap = folium.Map(location=SF_COORDINATES, zoom_start=12)
#
# marker_cluster = MarkerCluster().add_to(mymap)
#
# # add a marker for every record in the filtered data, use a clustered view
# # for each in firedata[0:MAX_RECORDS].iterrows():
# #     s = each['Location']
# #     folium.Marker(
# #         [each['location']],
# #         clustered_marker=True).add_to(mymap)
#
# for i in range(0, MAX_RECORDS):
#     latlong = firedata.iloc[i]['Location']
#
#     if latlong:
#         lat, lng = map(float, latlong.strip('()').split(','))
#
#         # folium.Marker([lat, lng], popup=firedata.iloc[i]['Address']).add_to(mymap)
#         folium.Marker([lat, lng], popup=firedata.iloc[i]['Address']).add_to(marker_cluster)
#
# mymap.save('mapsf.html')
#
# return mymap.get_root().render()


# Single Article
@app.route('/article/<string:id>/')
@is_logged_in
def article(id):
    # Create Cursor
    cur = mysql.connection.cursor()

    # Get Articles
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    # Close Connection
    cur.close

    return render_template('article.html', article=article)


# Reset Form Class
class ResetPasswordRequestForm(Form):
    email = StringField('Email', validators=[validators.data_required(), Email()])
    submit = SubmitField('Request Password Reset')


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password_request():
    form = ResetPasswordRequestForm(request.form)
    if request.method == 'POST' and form.validate():
        email = form.email.data
        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE email =%s", [email])

        # user = User.query.filter_by(email=form.email.data).first()
        user = cur.fetchone()

        other_user = User.query.filter_by(email=[email]).first()

        if user:
            # send_password_reset_email(user)
            flash('Check your email for the instructions to reset your password', 'success')
        else:
            flash('No User found with that E-mail', 'danger')
            return render_template('reset_password.html',
                                   title='Reset Password', form=form)
        # flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))

    return render_template('reset_password.html',
                           title='Reset Password', form=form)


# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.length(min=1, max=50)])
    username = StringField("Username", [validators.length(min=4, max=25)])
    email = StringField("Email", validators=[
        validators.email("Please Enter valid Email Address"), validators.Length(min=6, max=35),
        validators.data_required(), Email()])
    allusers = StringField('All Users', validators=[validators.Length(min=3, max=35)],
                           render_kw={"placeholder": "users"})
    # email = EmailField("Email", [InputRequired("Please enter your email address."),
    # Email("Please enter your email address.")])

    # email = TextField('Email:', validators=[validators.required(), validators.Length(min=6, max=35)])
    password = PasswordField("Password", [
        validators.data_required(),
        validators.equal_to('confirm', message='Password do not match')
    ])
    confirm = PasswordField("Confirm Password")


# Register Form Class
class NewRegisterForm(Form):
    name = StringField('Name', [validators.length(min=1, max=50)])
    username = StringField("Username", [validators.length(min=4, max=25)])
    email = StringField(" ", validators=[
        validators.email("Check Email Address"), validators.Length(min=6, max=35),
        validators.data_required(), Email()])
    # email = EmailField("Email", [InputRequired("Please enter your email address."),
    # Email("Please enter your email address.")])

    # email = TextField('Email:', validators=[validators.required(), validators.Length(min=6, max=35)])
    password = PasswordField("Password", [
        validators.data_required(),
        validators.equal_to('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField("Confirm Password")


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)

    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username =%s", [username])

        if result > 0:
            flash('User already exist', 'danger')

            return render_template('register.html', form=form)

        # Get user by username
        email_result = cur.execute("SELECT * FROM users WHERE email =%s", [email])

        if email_result > 0:
            flash('E-mail already exist', 'danger')
            form.email.data = None
            return render_template('register.html', form=form)

        #   Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES( %s, %s, %s, %s)",
                    (name, email, username, password))

        # commit DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    form = NewRegisterForm(request.form)

    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username =%s", [username])

        if result > 0:
            flash('User already exist', 'danger')

            return render_template('new_register.html', form=form)

        # Get user by username
        email_result = cur.execute("SELECT * FROM users WHERE email =%s", [email])

        if email_result > 0:
            flash('E-mail already exist', 'danger')
            form.email.data = None
            return render_template('new_register.html', form=form)

        #   Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES( %s, %s, %s, %s)",
                    (name, email, username, password))

        # commit DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))

    if request.method == 'POST':
        username = form.username.data

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        user_result = cur.execute("SELECT * FROM users WHERE username =%s", [username])
        if user_result > 0:
            error = 'User already exist'

            return 'error_show'
        else:
            return 'no_error'

    return render_template('new_register.html', form=form)


# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get forms field
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor

        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username =%s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):

                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now Logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid Login'
                return render_template('login.html', error=error)
            # Close Connection
            cur.close()

        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')


# Check if user Logedin
"""def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login', 'danger')
            return redirect(url_for('login'))
    return wrap"""


# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now Logged out', 'success')
    return redirect(url_for('login'))


# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create Cursor
    cur = mysql.connection.cursor()

    # Get Articles
    result = cur.execute("SELECT * FROM profiles")

    profiles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', profiles=profiles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg)

    # Close Connection
    cur.close


class ArticleForm(Form):
    title = StringField('Name', [validators.length(min=1, max=200)])
    body = TextAreaField("Body", [validators.length(min=30)])


# Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))

        # Commit
        mysql.connection.commit()

        # Close Connection
        cur.close()

        flash('Article Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)


# Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create Cursor
    cur = mysql.connection.cursor()

    # Get Article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    # Get Form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("UPDATE articles SET title = %s, body = %s WHERE id = %s", (title, body, article['id']))

        # Commit
        mysql.connection.commit()

        # Close Connection
        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)


@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create Cursor
    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM articles WHERE id = %s", id)

    # Commit to DB
    mysql.connection.commit()

    # Close Connection
    cur.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))


@app.route('/countries', methods=['GET', 'POST'])
def all_users():
    # Create Cursor
    cur = mysql.connection.cursor()

    # Get Articles
    result = cur.execute("SELECT name FROM users")

    myusers = cur.fetchall()

    # Close Connection
    cur.close

    return jsonify(myusers)


@app.route('/load_municipalities', methods=['GET', 'POST'])
def load_municipalities():
    try:
        nicadata = pd.read_csv('/Users/DRob/PycharmProjects/myflaskapp/mydata.csv')

        department = request.args.get('dpt', '', type=str)

        nicadata = nicadata.loc[nicadata['Department'] == department]

        # nicadata = nicadata.iloc[:, 1]

        mylist = nicadata.iloc[:, 1].values.tolist()

        # mylist = nicadata.to_dict()

        return jsonify(mylist)

    except OSError as err:
        print("OS error: {0}".format(err))
    except ValueError:
        print("Unexpected error:", sys.exc_info()[0])
    except:
        print("Unexpected error:", sys.exc_info()[0])

    return render_template('add_profile.html')


@app.route('/filter_profiles', methods=['GET', 'POST'])
def filter_profiles():
    try:
        municipality = request.args.get('mncplty', '', type=str)
        department = request.args.get('dpt', '', type=str)
        area = request.args.get('area', '', type=str)

        where_clause = ""
        inputparam = ""

        if len(municipality) > 0 and municipality != "Municipio":
            where_clause = " WHERE municipality  = %s "
            params = "(municipality"
            inputparam = municipality

        if len(department) > 0 and department != "Departamento":
            if len(where_clause) > 0:
                where_clause = where_clause + " AND Department = %s"
                inputparam = (municipality, department)
            else:
                where_clause = " WHERE Department  = %s "
                inputparam = department

        if len(area) > 0 and area != "Barrio/Colonia":
            if len(where_clause) > 0:
                where_clause = where_clause + " AND area = %s"

                if len(department) > 0 and len(municipality) > 0:
                    inputparam = (municipality, department, area)
                elif len(department) == 0 and len(municipality) > 0:
                    inputparam = (municipality, area)
                elif len(department) > 0 and len(municipality) == 0:
                    inputparam = (department, area)
            else:
                where_clause = " WHERE area  = %s "
                inputparam = area

        # Create Cursor
        cur = mysql.connection.cursor()

        # Get Articles
        result = cur.execute("SELECT * FROM profiles " + where_clause,
                             inputparam)

        # result = cur.execute("SELECT * FROM profiles WHERE municipality = %s and area = %s and department = %s",
        #                      (municipality, area, department))

        myusers = cur.fetchall()

        # Close Connection
        cur.close

        return jsonify(myusers)

    except OSError as err:
        print("OS error: {0}".format(err))
    except ValueError:
        print("Unexpected error:", sys.exc_info()[0])
    except:
        print("Unexpected error:", sys.exc_info()[0])

    return render_template('add_profile.html')


if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True)
