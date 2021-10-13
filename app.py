import json
from datetime import timedelta
import datetime as dt
import requests
from flask import Flask, redirect, request, url_for, render_template, flash
from authlib.integrations.flask_client import OAuth
from flask_login import (
    login_required,
    login_user,
    logout_user,
    current_user,
    LoginManager
)

from flask_mail import Mail, Message
from cerberus import Validator
from config import make_session, oauthconfig, REVIEWLIMIT, recaptchasecret, recapchasitekey
from models import User, Trade, App, Review, Historic
from myownscraper import get_app
from translator import PyNalator

valliappinit = Validator({
    'appid': {'required': True, 'type': 'string', 'regex': "^.*\..*\..*$"},
    'g-recaptcha-response': {'required': True}
})

alliappjoin = Validator({
    'tradeid':{'required': True, 'type': 'string'},
    'appid': {'required': True, 'type': 'string', 'regex': "^.*\..*\..*$"},
    'g-recaptcha-response': {'required': True}
})

app = Flask(
    __name__,
    static_url_path='/assets',
    static_folder = "assets",
    template_folder = "dist",
)


login_manager = LoginManager()
login_manager.setup_app(app)


app.secret_key = 'random secret223'
app.session = make_session()
app.browsersession = {}

app.config.from_object("config.Config")

oauth = OAuth(app)
oauth.register(**oauthconfig)

@app.errorhandler(401)
def unauthorized(_):
    return redirect('/login')

def local_breakdown(local):
    """Will filter out the locale language from a structure"""
    if "-" in local:
        boff = local.split("-")[1]
    else:
        boff = local
    return boff.lower()

def is_human(captcha_response):
    """ Validating recaptcha response from google server
        Returns True captcha test passed for submitted form else returns False.
    """
    payload = {'response':captcha_response, 'secret':recaptchasecret}
    response = requests.post("https://www.google.com/recaptcha/api/siteverify", payload)
    response_text = json.loads(response.text)
    return response_text['success']

def round_up(num):
    """does rounding up without importing the math module"""
    return int(-(-num // 1))

def pagination(db_object, itemnum):
    """it does the pagination for db results"""
    pagenum = 0
    data = None
    if 'pagenum' in request.args:
        pagenum = int(request.args.get('pagenum'))

    total = app.session.query(db_object).count()
    app.data['total'] = list(range(1, round_up(total/itemnum)+1))
    app.data['pagenum'] = pagenum+1, round_up(total/itemnum)
    data = app.session.query(db_object).limit(itemnum).offset(pagenum*itemnum).all()

    return data

@login_manager.user_loader
def load_user(userid):
    return app.session.query(User).filter(User.googleid == userid).first()

@app.before_request
def before_request_func():
    app.pyn = PyNalator("de")
    app.jinja_env.globals.update(trans=app.pyn.trans)

    navigation = {
        'dashboard': ('Dashboard', 'index'),
        'alltrades': ('All trades', 'overviewtrades'),
        'allapps': ('All apps', 'overviewapps'),
        'allreviews': ('All reviews', 'overviewreviews'),
        'mytrades': ('My trades', 'trades'),
        'myreviews': ('All reviews', 'overviewreviews'),
        'profile': ('My profile', 'userprofile'),
        'logout': ('Log Out', 'logout'),
        'about': ('About', '/')
    }
    app.data = {
        'pagename': 'Unknown',
        'user': None,
        'navigation': navigation,
        'recapchasitekey': recapchasitekey,
        'data': None,
        'logged-in': current_user.is_authenticated
    }

    app.data['currentnavigation'] = request.full_path[1:-1]

    if current_user.is_authenticated:
        app.data['user'] = {
            'fullname': current_user.fullname,
            'language': current_user.locale,
            'email': current_user.email,
            'picture': current_user.picture,
            'cancreate': current_user.can_create_trade()
        }

@app.route('/userprofile')
@login_required
def userprofile():
    app.data['pagename'] = 'User profile'
    app.data['data'] = current_user
    app.data['userscore'] = current_user.get_score()
    return render_template('userprofile.html', data=app.data)

@app.route('/login')
def login():
    """login that will call google oauth to you can login with your gooogle account"""
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route("/customlogin", methods = ['POST'])
def customlogin():
    """a custom login that will be used by the locust runner, for now it is a security risk"""
    if 'beest' in request.form and request.form.get('beest') == "Lollozotoeoobnenfmnbsf":
        customuser = app.session.query(User).filter(User.googleid == 666).first()

        if not customuser:
            customuser = User(666)
            customuser.fullname = "customuser"
            app.session.add(customuser)
            app.session.commit()

        login_user(customuser)
        return "success"
    return "fail"

@app.route('/logout')
@login_required
def logout():
    """here you can logout , it is not used since you login via google oauth so as soon as you are on the site you are loggedin"""
    logout_user()
    return redirect('/')

@app.route('/authorize')
def authorize():
    """part of the google oauth login"""
    google_auth = oauth.create_client('google')
    google_auth.authorize_access_token()

    resp = google_auth.get('userinfo')
    user_info = resp.json()

    if user_info and 'id' in user_info and 'verified_email' in user_info:
        user = app.session.query(User).filter(User.googleid == user_info['id']).first()

        if user:
            login_user(user)
            if (user.fullname != user_info['name'] or
            user.email != user_info['email'] or
            user.locale != local_breakdown(user_info['locale'])
            or user.email != user_info['email']):
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
    """an overview page of all trades"""
    app.data['pagename'] = 'My trades'
    app.data['data'] = current_user

    return render_template('alltrades.html', data=app.data)

# @app.route("/apps")
# @login_required
# def apps():
#     app.data['pagename'] = 'My apps'
#     app.data['data'] = current_user
#     return render_template('userapps.html', data=app.data)

@app.route("/showapp")
@login_required
def showapp():
    """detail page for one application"""
    appid = request.args.get('appid')
    appobj = app.session.query(App).filter(App.id==appid).first()
    app.data['data'] = appobj
    return render_template('oneapp.html', data=app.data)

@app.route("/usertrades")
@login_required
def usertrades():
    app.data['pagename'] = 'User profile'

    userid = request.args.get('userid')
    userobj = app.session.query(User).filter(User.id==userid).first()
    app.data['data'] = userobj

    return render_template('usertrades.html', data=app.data)

@app.route("/add")
@login_required
def add():
    """this page will show a form to add a trade"""
    app.data['pagename'] = 'Add Trade'

    if 'redirectto' in request.args:
        app.data['redirectto'] = request.args['redirectto']

    if current_user.get_score() < 0:
        flash("your trade score is not height enough to start a trade!", 'has-text-danger')
    return render_template('add.html', data=app.data)

def get_app_from_store(appid, country='us'):
    """this method / function can be removed and get_app can be called directly"""
    appobj = None
    try:
        appobj = get_app(appid, country=country)
    except Exception as exception:
        flash(str(exception), 'has-text-danger')
    return appobj

@app.route("/processadd", methods = ['POST'])
@login_required
def processadd():
    """This will process the post of a form to add a trade"""
    valliappinit.validate(dict(request.form))

    if valliappinit.errors:
        for key, val in valliappinit.errors.items():
            flash(key + ": " + val, 'has-text-danger')
        return redirect('/add')

    appid = request.form.get('appid')
    captcha_response = request.form['g-recaptcha-response']
    appobj = get_app_from_store(appid, country=current_user.locale)

    if current_user.get_score() < 0:
        flash("your trade score is not height enough to start a trade!", 'has-text-danger')
        return redirect('/overviewtrades')

    if 'rating' not in appobj or not appobj['rating']:
        flash("at the moment there is minor trouble with google playstore, try angain later !", 'has-text-danger')
        return redirect('/add')

    if appobj and int(appobj['rating']) <= REVIEWLIMIT and is_human(captcha_response):
        appmodel = app.session.query(App).filter(App.appidstring==appid).first()
        if not appmodel:
            appmodel = App(appobj['title'], appid)
        appmodel.imageurl = appobj['icon']
        trade = Trade(current_user, appmodel, current_user.locale)
        app.session.add(trade)
        app.session.commit()
        flash("added trade", 'has-text-primary')
        if 'redirectto' in request.args:
            return redirect(request.args.get('redirectto'))
        return redirect('/overviewtrades')
    else:
        flash(str("chapcha trouble, more than reviews, or of the process doent exist"), 'has-text-danger')
    return redirect('/add')

@app.route('/index')
def index():
    """the index page, a bit of a shit name, it shows the dashboard with graphs"""
    app.data['pagename'] = 'Dashboard'

    nowdate = dt.datetime.now().date()

    allstuff = (
        app
        .session
        .query(Historic)
        .filter(Historic.date >= nowdate + timedelta(days=-30) ,Historic.date <= nowdate)
        .order_by(Historic.date)
        .all()
    )
    app.data['apps'] = [ x.number for x in allstuff if 0 == x.infotype ]
    app.data['trades'] = [ x.number for x in allstuff if 1 == x.infotype ]
    app.data['reviews'] = [ x.number for x in allstuff if 2 == x.infotype ]
    app.data['labels'] = json.dumps(sorted(list({ str(x.date) for x in allstuff})))

    return render_template('index.html', data=app.data)

@app.route('/')
def mainpage():
    """This intro page will show the help for this webapp, perhaps an other name or url is needed ?"""
    app.data['pagename'] = 'Intro page'
    return render_template('mainpage.html', data=app.data)

@app.route('/overviewapps')
@login_required
def overviewapps():
    """This will show all the apps in a overview page"""
    app.data['pagename'] = 'All apps'
    try:
        app.data['data'] = pagination(App, 5)


    except Exception as exception:
        flash(str(exception), 'has-text-danger')
    return render_template('overviewapps.html', data=app.data)

@app.route('/showreview')
def showreview():
    """This will show the details about a review"""
    app.data['pagename'] = 'Reviews ?'
    reviewid = request.args.get('reviewid')
    try:
        review = app.session.query(Review).get(reviewid)
        app.data['data'] = review
    except Exception as exception:
        flash(str(exception), 'has-text-danger')
    return render_template('showreview.html', data=app.data)

@app.route('/overviewreviews')
def overviewreviews():
    """the overview page so you can see all the reviews done"""
    app.data['pagename'] = 'My reviews'
    try:

        app.data['data'] = pagination(Review, 50)
    except Exception as exception:
        flash(str(exception), 'has-text-danger')
    return render_template('overviewreviews.html', data=app.data)

@app.route('/overviewtrades')
@login_required
def overviewtrades():
    """a page that will show you a overview for all trades"""
    app.data['pagename'] = 'My trades'

    app.data['data'] = pagination(Trade, 5)

    return render_template('overview.html', data=app.data)

@app.route("/show")
@login_required
def show():
    """detail page for a single trade"""
    app.data['pagename'] = 'Trade details'
    tradeid = request.args.get('tradeid')
    googleid = current_user.googleid
    try:
        thetrade = app.session.query(Trade).get(tradeid)
        app.data['data'] = thetrade
        app.data['canaccept'] = thetrade.can_accept(googleid)
        app.data['canjoin'] = thetrade.can_join(googleid) and current_user.can_join_trade()
        app.data['canreject'] = thetrade.can_reject(googleid)
        app.data['candelete'] = thetrade.can_delete(googleid)
        app.data['canleave'] = thetrade.can_leave(googleid)
    except Exception as exception:
        flash(str(exception), 'has-text-danger')

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
            flash("rejected the trade", 'has-text-danger')
    except Exception as exception:
        app.session.rollback()
        flash(str(exception), 'has-text-danger')
    return redirect('/show?tradeid=' + tradeid)

@app.route("/accept")
@login_required
def accept():
    """here a initiator or a joiner of a trade can accept the trade, if both partys have accepted the trade is on so to call"""
    tradeid = request.args.get('tradeid')
    baseurl = request.base_url
    try:
        thetrade = app.session.query(Trade).get(int(tradeid))
        if thetrade.can_accept(current_user.googleid):
            thetrade.accept_user(current_user.googleid)
            app.session.commit()
            if thetrade.accepted:
                msg = Message(
                    'Test !',
                    body="The trade has now been accepted !",
                    sender="no-reply@{}".format(baseurl),
                    recipients=[thetrade.joiner.email]
                )

                mail = Mail(app)
                mail.send(msg)
                msg = Message(
                    'Test !',
                    body="The trade has now been accepted !",
                    sender="no-reply@{}".format(baseurl),
                    recipients=[thetrade.initiator.email]
                )
                mail = Mail(app)
                mail.send(msg)

            flash("accepted the trade",'has-text-danger')
    except Exception as exception:
        app.session.rollback()
        flash(str(exception),'has-text-danger')
    return redirect('/show?tradeid=' + tradeid)

@app.route("/delete")
@login_required
def delete():
    """this function will let the initiator of the trade delete the trade"""
    tradeid = request.args.get('tradeid')
    app.session.query(Trade).filter(Trade.id==tradeid).delete()
    app.session.commit()
    flash("trade removed !",'has-text-primary')
    return redirect('/overviewtrades')

@app.route("/join")
@login_required
def join():
    """here someone can join a trade by filling in a form with something to review, an app"""
    app.data['pagename'] = 'Join Trade'
    tradeid = request.args.get('tradeid')

    if current_user.get_score() < 0:
        flash("your trade score is not height enough to join a trade!", 'has-text-danger')

    return render_template('join.html', tradeid=tradeid, data=app.data)

@app.route("/processjoin", methods = ['POST'])
@login_required
def processjoin():
    """here we will process the join form post so you can join a trade"""
    alliappjoin.validate(dict(request.form))

    tradeid = request.form.get('tradeid')

    if not tradeid:
        return redirect('/')

    if alliappjoin.errors:
        for key, val in alliappjoin.errors.items():
            flash(key + ": " + val[0], 'has-text-danger')
        return redirect('/join?tradeid={}'.format(tradeid))

    if current_user.get_score() < 0:
        flash("your trade score is not height enough to join a trade!", 'has-text-danger')
        return redirect('/overviewtrades')

    appid = request.form.get('appid')
    captcha_response = request.form['g-recaptcha-response']

    appobjjoiner = get_app_from_store(appid, country=current_user.locale)

    if appobjjoiner and int(appobjjoiner['rating']) <= REVIEWLIMIT and is_human(captcha_response):
        joinerappmodel = app.session.query(App).filter(App.appidstring==appid).first()
        if not joinerappmodel:
            joinerappmodel = App(appobjjoiner['title'], appid)
            joinerappmodel.imageurl = appobjjoiner['icon']
        trade = app.session.query(Trade).get(int(tradeid))

        trade.joiner = current_user
        trade.joinerapp = joinerappmodel
        trade.joinerlang = current_user.locale
        app.session.add(trade)
        app.session.commit()
        flash("joined the trade", 'has-text-primary')
        return redirect('/overviewtrades')
    else:
        flash(str("chapcha trouble, more than reviews, or of the process doent exist"), 'has-text-danger')

    return redirect('/join')

@app.route("/leave")
@login_required
def leave():
    """here a trade joiner can leave a trade"""
    tradeid = request.args.get('tradeid')
    thetrade = app.session.query(Trade).get(int(tradeid))
    try:
        if thetrade.can_leave(current_user.googleid):
            thetrade.joiner = None
            thetrade.joinerapp = None
            thetrade.joiner_accepted = False
            thetrade.joiner_accepted = False
            thetrade.initiator_accepted = False
            app.session.commit()
            flash("left the trade", 'has-text-primary')
    except Exception as exception:
        flash(str(exception), 'has-text-danger')
    return redirect('/overviewtrades')
