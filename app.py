from flask import Flask, jsonify, redirect, request, url_for, render_template, session
from authlib.integrations.flask_client import OAuth
from config import make_session
from models import User, Trade, App
import psutil
import requests, json
import google_play_scraper

app = Flask(__name__,
            static_url_path='/assets',
            static_folder = "assets",
            template_folder = "dist",
            )

app.secret_key = 'random secret'
app.session = make_session()

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='246793217963-ph4ft9vem6ocs45iathatof8914o88pa.apps.googleusercontent.com',
    client_secret='pojrKKIOrDKdGsJA2ByejdN3',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    # This is only needed if using openId to fetch user info
    client_kwargs={'scope': 'openid email profile'},
)

@app.route('/login')
def login():
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/authorize')
def authorize():
    google = oauth.create_client('google')
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    user_info = resp.json()
    print(user_info)
    # do something with the token and profile
    # session['email'] = user_info['email']
    session['user'] = user_info
    return redirect('/')

@app.route("/add")
def test():

    return render_template('index.html.jinja')

def get_country_by_ip(ip):
    r = requests.get('https://api.cleantalk.org/?method_name=ip_info&ip=' + ip)
    rawjson = r.text.encode('ascii', 'ignore').decode()
    return json.loads(rawjson)['data'][ip]['country_code']

def get_app_from_store(appid):
    appobj = None
    try:
        appobj = google_play_scraper.app(appid)
    except Exception as e:
        print(e)

    return appobj

@app.route("/processadd", methods = ['POST'])
def nogietsZ():


# klont = get_country_by_ip(request.remote_addr)
    klont = get_country_by_ip("213.208.216.6")

    appid = request.form.get('appid')
    appobj = get_app_from_store(appid)

    if klont and appobj:

        user = User(2352526455556666666)
        appmodel = App(appobj['title'], appid)
        trade = Trade(user, appmodel, klont.lower())

        app.session.add(trade)
        app.session.commit()
        app.session.close()

        return redirect('/')
    else:
        redirect('/add')

@app.route("/")
def nogiets():
    data = {'message': 'no data', 'stats-cpu':psutil.cpu_percent(), 'stats-mem':psutil.virtual_memory()[2]}
    try:
        activetrades = app.session.query(Trade).all()
        data['message'] = activetrades

    except Exception as e:
        app.session.rollback()
        data['message'] = str(e)


    content = render_template('notindexa.html.jinja', data=data)

    app.session.close()

    return content

@app.route("/show")
def nogietsB():
    data = {'message': 'no data', 'stats-cpu':psutil.cpu_percent(), 'stats-mem':psutil.virtual_memory()[2]}
    tradeid = request.args.get('tradeid')

    # wat willen we zien in de join pagina
    # creator: image van google, creator nickname, creator app name en plaatje, link to creator app in store, creator language
    # acceptor image van google, acceptock nick, acceptor app name plaatje link to app in store, acceptor language

    try:
        thetrade = app.session.query(Trade).get(int(tradeid))
        data['message'] = thetrade
    except Exception as e:
        app.session.rollback()
        data['message'] = str(e)


    app.session.close()
    return render_template('notindexb.html.jinja', data=data)

@app.route("/join")
def nogietsC():
    tradeid = request.args.get('tradeid')

    return render_template('indexX.html.jinja', tradeid=tradeid)

@app.route("/processjoin", methods = ['POST'])
def nogietsW():
    klont = get_country_by_ip("213.208.216.6")

    appid = request.form.get('appid')
    tradeid = request.form.get('tradeid')
    appobj = get_app_from_store(appid)

    if klont and appobj:

        user = User(39846723983375)
        appmodel = App(appobj['title'], appid)
        trade = app.session.query(Trade).get(int(tradeid))

        trade.set_accepted()
        trade.joiner = user
        trade.joinerapp = appmodel
        trade.joinerlang = klont.lower()

        app.session.add(trade)
        app.session.commit()
        app.session.close()

        return redirect('/')
    else:
        redirect('/join')



#welke info hebben we nodig
# 1 all uitstaande trades
# 2 check de trade(s) die uitstaan waarin jij actief bent
# 3 een enkele trade op basis van zn ID

# @app.route("/alltrades")
# @jwt_required()
# def allactivetrades():
#     data = {'message': 'no data', 'stats-cpu':psutil.cpu_percent(), 'stats-mem':psutil.virtual_memory()[2]}
#
#     try:
#         activetrades = app.session.query(Trade).all()
#         data['message'] = [i.as_dict() for i in activetrades]
#     except Exception as e:
#         app.session.rollback()
#         data['message'] = str(e)
#     app.session.close()
#
#     return jsonify(data)
#
# @app.route("/yourtrades")
# @jwt_required()
# def youractivetrades():
#     userid = get_jwt_identity()
#     data = {'message': 'no data', 'stats-cpu':psutil.cpu_percent(), 'stats-mem':psutil.virtual_memory()[2]}
#     try:
#         auser = app.session.query(User).filter(User.sub == str(userid)).first()
#         data['message']['initiations'] = [i.as_dict() for i in auser.initiatortrades]
#         data['message']['joinings'] = [i.as_dict() for i in auser.joinertrades]
#     except Exception as e:
#         app.session.rollback()
#         data['message'] = str(e)
#
#     app.session.close()
#     return jsonify(data)
#
# @app.route("/atrade")
# @jwt_required()
# def onetrade():
#     userid = get_jwt_identity()
#     data = {'message': 'no data', 'stats-cpu':psutil.cpu_percent(), 'stats-mem':psutil.virtual_memory()[2]}
#
#     if 'tradeid' in request.args:
#         tradeid = request.args.get('tradeid')
#         try:
#             data['message'] = app.session.query(Trade).filter(Trade.id == tradeid).first()
#         except Exception as e:
#             app.session.rollback()
#             data['message'] = str(e)
#
#         app.session.close()
#     return jsonify(data)
#
# @app.route("/customlogin", methods = ['POST'])
# def customlogin():
#     '''
#     This login will be used bij the performance measure tool, locust
#     '''
#
#     message = {'message': 'Nope'}
#
#     if 'beest' in request.form and request.form.get('beest') == "Lollozotoeoobnenfmnbsf":
#         expires = datetime.timedelta(minutes=60)
#
#         message = {
#             'access_token': create_access_token(identity = "testusertest", expires_delta=expires),
#             'refresh_token': create_refresh_token(identity = "testusertest"),
#             'expire_time': str((datetime.datetime.now().timestamp() + expires.total_seconds()))
#         }
#
#     return jsonify(message)
#
# @app.route("/login", methods = ['GET'])
# def login():
#     '''
#     Ths login will be used by the phone application, you will login by your google kay thing !!
#     '''
#     replymesg = {'message': 'Nope'}
#
#     if 'token' in request.args:
#         token = request.args.get('token')
#         idinfo = id_token.verify_oauth2_token(token, googlerequest.Request(), GOOGLE_CLIENT_ID)
#         if idinfo and 'name' in idinfo and 'email_verified' in idinfo and 'sub' in idinfo:
#
#             expires = datetime.timedelta(minutes=60)
#             hash_object = hashlib.sha1(idinfo['sub'].encode('utf-8'))
#
#             replymesg = {
#                 'message': 'Logged in as {}'.format(idinfo['name']),
#                 'access_token': create_access_token(identity = hash_object.hexdigest(), expires_delta=expires),
#                 'refresh_token': create_refresh_token(identity = hash_object.hexdigest()),
#                 'expire_time': str((datetime.datetime.now().timestamp() + expires.total_seconds()))
#             }
#
#     return jsonify(replymesg)
#
# @app.route("/tokenrefresh")
# @jwt_required(refresh=True)
# def refresh():
#     '''
#     This will refresh the token, for a client to identify itself.
#     Not quite sure if it works since our test cycle is quite short now !
#     '''
#     expires = datetime.timedelta(minutes=30)
#
#     return {
#         'message': 'Refresh token OK !',
#         'access_token': create_access_token(identity = get_jwt_identity(), expires_delta=expires),
#         'refresh_token': None,
#         'expire_time': str((datetime.datetime.now().timestamp() + expires.total_seconds()))
#     }
