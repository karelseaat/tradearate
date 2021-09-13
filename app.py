import json
import requests
from flask import Flask, redirect, request, url_for, render_template
from authlib.integrations.flask_client import OAuth
import google_play_scraper
from flask_login import (
    UserMixin,
    login_required,
    login_user,
    logout_user,
    current_user,
    LoginManager
)
from config import make_session, oauthconfig, REVIEWLIMIT
from models import User, Trade, App, Review
import logging


app = Flask(
    __name__,
    static_url_path='/assets',
    static_folder = "assets",
    template_folder = "dist",
)

logging.basicConfig(filename='example.log', level=logging.DEBUG)

login_manager = LoginManager()
login_manager.setup_app(app)

app.secret_key = 'random secret'
app.session = make_session()
app.browsersession = {}

oauth = OAuth(app)
oauth.register(**oauthconfig)


@app.errorhandler(401)
def unauthorized(error):
    return redirect('/login')

def local_breakdown(local):
    if "-" in local:
        boff = local.split("-")[1]
    else:
        boff = local
    return boff.lower()

def is_human(captcha_response):
    """ Validating recaptcha response from google server
        Returns True captcha test passed for submitted form else returns False.
    """
    secret = "6Ld8rjMcAAAAAPDQI6igBibm24JIwHABlL5uw2RX"
    payload = {'response':captcha_response, 'secret':secret}
    response = requests.post("https://www.google.com/recaptcha/api/siteverify", payload)
    response_text = json.loads(response.text)
    print(response_text)
    return response_text['success']

@login_manager.user_loader
def load_user(userid):
    return app.session.query(User).filter(User.googleid == userid).first()


@app.before_request
def before_request_func():
    navigation = {'dashboard': ('Dashboard', 'index'), 'alltrades': ('All trades', 'overviewtrades'), 'allapps': ('All apps', 'overviewapps'), 'allreviews': ('All reviews', 'overviewreviews'), 'mytrades': ('My trades', 'trades'), 'myapps': ('My apps', 'apps'), 'myreviews': ('My reviews', 'overviewreviews'), 'profile': ('My profile', 'userprofile'), 'messages': ('Messages', ''), 'logout': ('Log Out', 'logout'), 'about': ('About', '/')}
    app.data = {'pagename': 'Unknown', 'user': None, 'messages': [], 'navigation': navigation, 'data': None, 'logged-in': current_user.is_authenticated}

    if current_user.is_authenticated:
        app.data['user'] = {'fullname': current_user.fullname, 'language': current_user.locale, 'email': current_user.email, 'picture': current_user.picture}

@app.route('/userprofile')
@login_required
def userprofile():
    app.data['pagename'] = 'User profile'
    app.data['data'] = current_user
    return render_template('userprofile.html', data=app.data)

@app.route('/login')
def login():
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/authorize')
def authorize():
    google_auth = oauth.create_client('google')
    test = google_auth.authorize_access_token()

    logging.debug(str(test))


    resp = google_auth.get('userinfo')
    user_info = resp.json()

    logging.debug(str(user_info))

    if user_info and 'id' in user_info and 'verified_email' in user_info:
        user = app.session.query(User).filter(User.googleid == user_info['id']).first()

        if user:
            login_user(user)
            if user.fullname != user_info['name'] or user.email != user_info['email'] or user.locale != user_info['locale'].split("-")[1].lower() or user.email != user_info['email']:
                user.fullname = user_info['name']
                user.email = user_info['email']
                user.locale = local_breakdown(user_info['locale'])
                app.session.commit()
        else:
            newuser = User(user_info['id'])
            newuser.fullname = user_info['name']
            newuser.picture = user_info['picture']
            newuser.email = user_info['email']
            newuser.locale = local_breakdown(user_info['locale'])
            app.session.add(newuser)
            app.session.commit()
            login_user(newuser)

    return redirect('/overviewtrades')

@app.route("/trades")
@login_required
def trades():
    app.data['pagename'] = 'My trades'
    app.data['data'] = current_user
    return render_template('alltrades.html', data=app.data)

@app.route("/apps")
@login_required
def apps():
    app.data['pagename'] = 'My apps'
    app.data['data'] = current_user
    return render_template('userapps.html', data=app.data)

@app.route("/showapp")
@login_required
def showapp():
    appid = request.args.get('appid')
    appobj = app.session.query(App).filter(App.id==appid).first()
    app.data['data'] = appobj
    return render_template('oneapp.html', data=app.data)

@app.route("/usertrades")
@login_required
def usertrades():
    userid = request.args.get('userid')
    userobj = app.session.query(User).filter(User.id==userid).first()
    app.data['data'] = userobj
    return render_template('usertrades.html', data=app.data)

@app.route("/add")
@login_required
def add():
    app.data['pagename'] = 'Add Trade'
    return render_template('add.html', data=app.data)

def get_app_from_store(appid, country='us'):
    appobj = None
    try:
        appobj = google_play_scraper.app(appid, country=country)
    except Exception as exception:
        print(exception)
    return appobj

@app.route("/processadd", methods = ['POST'])
@login_required
def processadd():
    appid = request.form.get('appid')
    captcha_response = request.form['g-recaptcha-response']
    appobj = get_app_from_store(appid, country=current_user.locale)
    # print(bool(appobj), int(appobj['reviews']) <= REVIEWLIMIT, is_human(captcha_response))

    if appobj and int(appobj['reviews']) <= REVIEWLIMIT and is_human(captcha_response):
        appmodel = app.session.query(App).filter(App.appidstring==appid).first()
        if not appmodel:
            appmodel = App(appobj['title'], appid)
        appmodel.imageurl = appobj['icon']
        trade = Trade(current_user, appmodel, current_user.locale)
        app.session.add(trade)
        app.session.commit()
        return redirect('/overviewtrades')
    return redirect('/add')

@app.route('/index')
def index():
    app.data['pagename'] = 'Dashboard'
    return render_template('index.html', data=app.data)

@app.route('/')
def mainpage():
    app.data['pagename'] = 'Intro page'
    return render_template('mainpage.html', data=app.data)

@app.route('/overviewapps')
@login_required
def overviewapps():
    app.data['pagename'] = 'All apps'
    try:
        activetrades = app.session.query(App).all()
        app.data['data'] = activetrades
    except Exception as exception:
        app.data['messages'].append(str(exception))
    return render_template('overviewapps.html', data=app.data)

@app.route('/showreview')
def showreview():
    app.data['pagename'] = 'Reviews ?'
    reviewid = request.args.get('reviewid')
    try:
        review = app.session.query(Review).get(reviewid)
        app.data['data'] = review
    except Exception as exception:
        app.data['messages'].append(str(exception))
    return render_template('showreview.html', data=app.data)

@app.route('/overviewreviews')
def overviewreviews():
    app.data['pagename'] = 'My reviews'
    try:
        activereviews = app.session.query(Review).all()
        for review in activereviews:
            if review.app:
                print(review.app.name)

        app.data['data'] = activereviews
    except Exception as exception:
        app.data['messages'].append(str(exception))
    return render_template('overviewreviews.html', data=app.data)

@app.route('/overviewtrades')
@login_required
def overviewtrades():
    app.data['pagename'] = 'My trades'
    try:
        activetrades = app.session.query(Trade).all()
        app.data['data'] = activetrades
    except Exception as exception:
        app.data['messages'].append(str(exception))
    return render_template('overview.html', data=app.data)

@app.route("/show")
@login_required
def show():
    app.data['pagename'] = 'Trade details ?'
    tradeid = request.args.get('tradeid')
    googleid = current_user.googleid
    try:
        thetrade = app.session.query(Trade).get(tradeid)
        app.data['data'] = thetrade
        app.data['canaccept'] = thetrade.can_accept(googleid)
        app.data['canjoin'] = thetrade.can_join(googleid)
        app.data['canreject'] = thetrade.can_reject(googleid)
        app.data['candelete'] = thetrade.can_delete(googleid)
        app.data['canleave'] = thetrade.can_leave(googleid)
    except Exception as exception:
        app.data['messages'].append(str(exception))
    return render_template('showtrade.html', data=app.data)

@app.route("/reject")
@login_required
def reject():
    tradeid = request.args.get('tradeid')
    try:
        thetrade = app.session.query(Trade).get(int(tradeid))
        if thetrade.can_reject(current_user.googleid):
            thetrade.reject_user(current_user.googleid)
            app.session.commit()
    except Exception as exception:
        app.session.rollback()
        app.data['messages'].append(str(exception))
    return redirect('/show?tradeid=' + tradeid)

@app.route("/accept")
@login_required
def accept():
    tradeid = request.args.get('tradeid')
    try:
        thetrade = app.session.query(Trade).get(int(tradeid))
        if thetrade.can_accept(current_user.googleid):
            thetrade.accept_user(current_user.googleid)
            app.session.commit()
    except Exception as exception:
        app.session.rollback()
        app.data['messages'].append(str(exception))
    return redirect('/show?tradeid=' + tradeid)

@app.route("/delete")
@login_required
def delete():
    tradeid = request.args.get('tradeid')
    app.session.query(Trade).filter(Trade.id==tradeid).delete()
    app.session.commit()
    return redirect('/overviewtrades')

@app.route("/join")
@login_required
def join():
    app.data['pagename'] = 'Join a trade ?'
    tradeid = request.args.get('tradeid')
    return render_template('join.html', tradeid=tradeid, data=app.data)

@app.route("/processjoin", methods = ['POST'])
@login_required
def processjoin():
    appid = request.form.get('appid')
    captcha_response = request.form['g-recaptcha-response']
    tradeid = request.form.get('tradeid')
    appobjjoiner = get_app_from_store(appid, country=current_user.locale)

    # print(bool(appobj), int(appobj['reviews']) <= REVIEWLIMIT, is_human(captcha_response))

    if appobjjoiner and int(appobjjoiner['reviews']) <= REVIEWLIMIT and is_human(captcha_response):
        joinerappmodel = App(appobjjoiner['title'], appid)
        joinerappmodel.imageurl = appobjjoiner['icon']
        trade = app.session.query(Trade).get(int(tradeid))
        initiatorabletoreview = get_app_from_store(trade.initiatorapp.appidstring, country=current_user.locale)
        if initiatorabletoreview:
            trade.joiner = current_user
            trade.joinerapp = joinerappmodel
            trade.joinerlang = current_user.locale
            app.session.add(trade)
            app.session.commit()
            return redirect('/overviewtrades')
    return redirect('/join')

@app.route("/leave")
@login_required
def leave():
    tradeid = request.form.get('tradeid')
    thetrade = app.session.query(Trade).get(int(tradeid))
    try:
        if thetrade.can_leave(current_user.googleid):
            thetrade.joiner = None
            app.session.commit()
    except Exception as exception:
        app.data['messages'].append(str(exception))
    return redirect('/overviewtrades')
