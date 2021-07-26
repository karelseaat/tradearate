from flask import Flask, jsonify, redirect, request, url_for, render_template

from flask_jwt_extended import JWTManager
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required ,get_jwt_identity
from oauthlib.oauth2 import WebApplicationClient
import requests
import datetime
from models import User, Trade, App
from config import make_session, GOOGLE_DISCOVERY_URL, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SECRET_KEY
from logging.handlers import RotatingFileHandler
from google.oauth2 import id_token
from google.auth.transport import requests as googlerequest
import psutil



app = Flask(__name__,
            static_url_path='/assets',
            static_folder = "assets",
            template_folder = "dist")
app.session = make_session()
app.secret_key = SECRET_KEY
app.config["JWT_SECRET_KEY"] = SECRET_KEY


jwt = JWTManager(app)
client = WebApplicationClient(GOOGLE_CLIENT_ID)

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

@app.route("/")
def test():
    return render_template('index.html.jinja')

@app.route("/A")
def nogiets():
    return render_template('notindexa.html.jinja')

@app.route("/B")
def nogietsB():
    return render_template('notindexb.html.jinja')



#welke info hebben we nodig
# 1 all uitstaande trades
# 2 check de trade(s) die uitstaan waarin jij actief bent
# 3 een enkele trade op basis van zn ID

@app.route("/alltrades")
@jwt_required()
def allactivetrades():
    data = {'message': 'no data', 'stats-cpu':psutil.cpu_percent(), 'stats-mem':psutil.virtual_memory()[2]}

    try:
        activetrades = app.session.query(Trade).all()
        data['message'] = [i.as_dict() for i in activetrades]
    except Exception as e:
        app.session.rollback()
        data['message'] = str(e)
    app.session.close()

    return jsonify(data)

@app.route("/yourtrades")
@jwt_required()
def youractivetrades():
    userid = get_jwt_identity()
    data = {'message': 'no data', 'stats-cpu':psutil.cpu_percent(), 'stats-mem':psutil.virtual_memory()[2]}
    try:
        auser = app.session.query(User).filter(User.sub == str(userid)).first()
        data['message']['initiations'] = [i.as_dict() for i in auser.initiatortrades]
        data['message']['joinings'] = [i.as_dict() for i in auser.joinertrades]
    except Exception as e:
        app.session.rollback()
        data['message'] = str(e)

    app.session.close()
    return jsonify(data)

@app.route("/atrade")
@jwt_required()
def onetrade():
    userid = get_jwt_identity()
    data = {'message': 'no data', 'stats-cpu':psutil.cpu_percent(), 'stats-mem':psutil.virtual_memory()[2]}

    if 'tradeid' in request.args:
        tradeid = request.args.get('tradeid')
        try:
            data['message'] = app.session.query(Trade).filter(Trade.id == tradeid).first()
        except Exception as e:
            app.session.rollback()
            data['message'] = str(e)

        app.session.close()
    return jsonify(data)

@app.route("/customlogin", methods = ['POST'])
def customlogin():
    '''
    This login will be used bij the performance measure tool, locust
    '''

    message = {'message': 'Nope'}

    if 'beest' in request.form and request.form.get('beest') == "Lollozotoeoobnenfmnbsf":
        expires = datetime.timedelta(minutes=60)

        message = {
            'access_token': create_access_token(identity = "testusertest", expires_delta=expires),
            'refresh_token': create_refresh_token(identity = "testusertest"),
            'expire_time': str((datetime.datetime.now().timestamp() + expires.total_seconds()))
        }

    return jsonify(message)

@app.route("/login", methods = ['GET'])
def login():
    '''
    Ths login will be used by the phone application, you will login by your google kay thing !!
    '''
    replymesg = {'message': 'Nope'}

    if 'token' in request.args:
        token = request.args.get('token')
        idinfo = id_token.verify_oauth2_token(token, googlerequest.Request(), GOOGLE_CLIENT_ID)
        if idinfo and 'name' in idinfo and 'email_verified' in idinfo and 'sub' in idinfo:

            expires = datetime.timedelta(minutes=60)
            hash_object = hashlib.sha1(idinfo['sub'].encode('utf-8'))

            replymesg = {
                'message': 'Logged in as {}'.format(idinfo['name']),
                'access_token': create_access_token(identity = hash_object.hexdigest(), expires_delta=expires),
                'refresh_token': create_refresh_token(identity = hash_object.hexdigest()),
                'expire_time': str((datetime.datetime.now().timestamp() + expires.total_seconds()))
            }

    return jsonify(replymesg)

@app.route("/tokenrefresh")
@jwt_required(refresh=True)
def refresh():
    '''
    This will refresh the token, for a client to identify itself.
    Not quite sure if it works since our test cycle is quite short now !
    '''
    expires = datetime.timedelta(minutes=30)

    return {
        'message': 'Refresh token OK !',
        'access_token': create_access_token(identity = get_jwt_identity(), expires_delta=expires),
        'refresh_token': None,
        'expire_time': str((datetime.datetime.now().timestamp() + expires.total_seconds()))
    }
