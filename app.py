from flask import Flask, jsonify, redirect, request, url_for, render_template, session
from authlib.integrations.flask_client import OAuth
from config import make_session
from models import User, Trade, App
import psutil
import requests, json
import google_play_scraper
from flask_login import (UserMixin, login_required, login_user, logout_user, current_user, LoginManager)

#todo checkout of een app al 1000 reviews heeft zo jah dan kun je bij ons niet traden !

app = Flask(__name__,
            static_url_path='/assets',
            static_folder = "assets",
            template_folder = "dist",
            )

login_manager = LoginManager()
login_manager.setup_app(app)

app.secret_key = 'random secret'
app.session = make_session()
app.browsersession = {}

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

@login_manager.user_loader
def load_user(userid):
    user = app.session.query(User).filter(User.googleid == userid).first()
    # app.session.close() dont close the db session here since i will be needed later on !
    return user

@app.route('/login')
def login():
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    app.session.close()
    return google.authorize_redirect(redirect_uri)

@app.route('/logout')
def logout():
    logout_user()
    app.session.close()
    return redirect('/')


@app.route('/authorize')
def authorize():
    google = oauth.create_client('google')
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    user_info = resp.json()
    if user_info and 'id' in user_info and 'verified_email' in user_info:
        user = app.session.query(User).filter(User.googleid == user_info['id']).first()

        if user:
            login_user(user)
        else:
            newuser = User(user_info['id'])
            newuser.fullname = user_info['name']
            newuser.picture = user_info['picture']
            app.session.add(newuser)
            app.session.commit()
            login_user(newuser)

    app.session.close()
    return redirect('/')

@app.route("/trades")
def tradesbyuser():
    data = {'message': [], 'stats-cpu':psutil.cpu_percent(), 'stats-mem':psutil.virtual_memory()[2]}
    if app.browsersession and 'user' in app.browsersession and 'id' in app.browsersession['user']:
        data['message'] = app.session.query(User).filter(User.googleid == app.browsersession['user']['id']).first()
        # print(data)

    content =  render_template('userlisttrades.html.jinja', data=data)
    app.session.close()
    return content

@app.route("/add")
def test():
    app.session.close()
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

        appmodel = App(appobj['title'], appid)
        appmodel.imageurl = appobj['icon']
        trade = Trade(current_user, appmodel, klont.lower())

        app.session.add(trade)
        app.session.commit()
        app.session.close()

        return redirect('/')
    else:
        app.session.close()
        return redirect('/add')

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
@login_required
def nogietsB():
    data = {'message': 'no data', 'stats-cpu':psutil.cpu_percent(), 'stats-mem':psutil.virtual_memory()[2]}
    tradeid = request.args.get('tradeid')

    googleid = current_user.googleid

    try:
        thetrade = app.session.query(Trade).get(tradeid)
        data['message'] = thetrade
        data['canaccept'] = thetrade.can_accept(googleid)
        data['canjoin'] = thetrade.can_join(googleid)
        data['canreject'] = thetrade.can_reject(googleid)
        data['candelete'] = thetrade.can_delete(googleid)
        data['canleave'] = thetrade.can_leave(googleid)

    except Exception as e:
        app.session.rollback()
        data['message'] = str(e)
        print("error", e)

    content =  render_template('notindexb.html.jinja', data=data)
    app.session.close()
    return content

@app.route("/accept")
@login_required
def accept():
    tradeid = request.args.get('tradeid')

    try:
        thetrade = app.session.query(Trade).get(int(tradeid))
        if thetrade.can_accept(current_user.googleid):
            thetrade.accept_user(current_user.googleid)
            app.session.commit()
    except Exception as e:
        app.session.rollback()
        data['message'] = str(e)

    content = redirect('/show?tradeid=' + tradeid)
    app.session.close()
    return content

@app.route("/delete")
def deleteit():
    tradeid = request.args.get('tradeid')
    app.session.query(Trade).filter(Trade.id==tradeid).delete()
    app.session.commit()
    app.session.close()
    return redirect('/')

@app.route("/join")
def nogietsC():
    tradeid = request.args.get('tradeid')
    app.session.close()
    return render_template('indexX.html.jinja', tradeid=tradeid)

@app.route("/processjoin", methods = ['POST'])
def nogietsW():
    klont = get_country_by_ip("213.208.216.6")

    appid = request.form.get('appid')
    tradeid = request.form.get('tradeid')
    appobj = get_app_from_store(appid)

    if klont and appobj:

        appmodel = App(appobj['title'], appid)
        appmodel.imageurl = appobj['icon']
        trade = app.session.query(Trade).get(int(tradeid))

        trade.joiner = current_user
        trade.joinerapp = appmodel
        trade.joinerlang = klont.lower()

        app.session.add(trade)
        app.session.commit()
        app.session.close()

        return redirect('/')
    else:
        app.session.close()
        return redirect('/join')
