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
from config import make_session, oauthconfig, REVIEWLIMIT, recaptchasecret, recapchasitekey, domain
from flask import session as browsersession
from models import User, Trade, App, Review, Historic
from lib.myownscraper import get_app
from lib.translator import PyNalator
import os

valliappinit = Validator({
    'appid': {'required': True, 'type': 'string', 'regex': "^.*\..*\..*$"},
    'g-recaptcha-response': {'required': True}
})

alliappjoin = Validator({
    'tradeid':{'required': True, 'type': 'string'},
    'appid': {'required': True, 'type': 'string', 'regex': "^.*\..*\..*$"},
    'g-recaptcha-response': {'required': True}
})

vallcontact = Validator({
    'subject':{'required': True, 'type': 'string'},
    'message':{'required': True, 'type': 'string'},
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


app.config.from_object("config.Config")

oauth = OAuth(app)
oauth.register(**oauthconfig)

@app.errorhandler(401)
def unauthorized(_):
    browsersession['redirect'] = request.path
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
    if 'pagenum' in request.args and request.args.get('pagenum').isnumeric():
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
    if isinstance(current_user, User) and current_user.locale:
        app.pyn = PyNalator(localename=current_user.locale, subdir="translations")
    else:
        app.pyn = PyNalator(subdir="translations")

    app.jinja_env.globals.update(trans=app.pyn.trans)

    navigation = {
        'dashboard': ('Dashboard', 'index'),
        'alltrades': ('All trades', 'overviewtrades'),
        'allapps': ('All apps', 'overviewapps'),
        'allreviews': ('All reviews', 'overviewreviews'),
        'mytrades': ('My trades', 'trades'),
        'myreviews': ('All reviews', 'overviewreviews'),
        'profile': ('My profile', 'userprofile'),
        'about': ('About', '/'),
        'contact': ('Contact', 'contact')
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
            'cancreate': current_user.can_create_trade(),
            'score': current_user.get_score(),
            'pending':  current_user.all_pending()
        }

@app.route('/userprofile')
@login_required
def userprofile():
    app.data['pagename'] = 'User profile'
    app.data['data'] = current_user
    app.data['userscore'] = current_user.get_score()
    result = render_template('userprofile.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result


@app.route('/login')
def login():
    """login that will call google oauth to you can login with your gooogle account"""
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    result = google.authorize_redirect(redirect_uri)
    app.session.close()
    app.pyn.close()
    return result

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
        app.session.close()
        app.pyn.close()
        return "success"

    app.session.close()
    app.pyn.close()
    return "fail"

@app.route('/logout')
@login_required
def logout():
    """here you can logout , it is not used since you login via google oauth so as soon as you are on the site you are loggedin"""
    logout_user()
    app.session.close()
    app.pyn.close()
    return redirect('/')

@app.route('/contact')
@login_required
def contact():
    """Showin a contact form !"""
    app.data['pagename'] = 'Contact'
    result = render_template('contact.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result

@app.route('/processcontact', methods = ['POST'])
@login_required
def processcontact():
    vallcontact.validate(dict(request.form))

    message = request.form.get('message')
    subject = request.form.get('subject')

    if not message:
        flash("no message ?!", 'has-text-danger')
        app.session.close()
        app.pyn.close()
        return redirect('/')

    if vallcontact.errors:
        for key, val in vallcontact.errors.items():
            flash(key + ": " + val[0], 'has-text-danger')

        app.session.close()
        app.pyn.close()
        return redirect('/')

    mail = Mail(app)

    msg = Message(
        "Trade a rate contact form !, {}".format(subject),
        sender = 'sixdots.soft@gmail.com',
        body="name: {}\nemail: {}\nmessage: {}".format(current_user.fullname, current_user.email, message),
        recipients=['sixdots.soft@gmail.com']
    )

    mail.send(msg)

    app.session.close()
    app.pyn.close()
    flash("Message send !", 'has-text-primary')
    return redirect('/overviewtrades')

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

    app.session.close()
    # app.pyn.close()
    return redirect(browsersession['redirect'])

@app.route("/trades")
@login_required
def trades():
    """an overview page of all trades"""
    app.data['pagename'] = 'My trades'
    app.data['data'] = current_user

    result = render_template('alltrades.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result


@app.route("/showapp")
@login_required
def showapp():
    """detail page for one application"""
    app.data['pagename'] = 'App details'
    appid = request.args.get('appid')
    if not appid or not appid.isnumeric():
        flash('Should be a number', 'has-text-danger')
        return redirect('/overviewtrades')

    appobj = app.session.query(App).filter(App.id==appid).first()

    if not appobj:
        flash('app not found', 'has-text-danger')
        return redirect('/overviewtrades')

    app.data['data'] = appobj
    result = render_template('oneapp.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result

@app.route("/usertrades")
@login_required
def usertrades():
    app.data['pagename'] = 'User profile'
    userid = request.args.get('userid')
    if not userid or not userid.isnumeric():
        flash('Should be a number', 'has-text-danger')
        return redirect('/overviewtrades')

    userobj = app.session.query(User).filter(User.id==userid).first()
    if not userobj:
        flash('app not found', 'has-text-danger')
        return redirect('/overviewtrades')

    app.data['data'] = userobj

    result = render_template('usertrades.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result

@app.route("/add")
@login_required
def add():
    """this page will show a form to add a trade"""
    app.data['pagename'] = 'Add Trade'

    if 'redirectto' in request.args:
        app.data['redirectto'] = request.args['redirectto']

    if current_user.get_score() < 0:
        flash("your trade score is not height enough to start a trade!", 'has-text-danger')
    result = render_template('add.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result

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

    if not appobj:
        app.session.close()
        app.pyn.close()
        flash('app not found', 'has-text-danger')
        return redirect('/overviewtrades')

    if current_user.get_score() < 0:
        flash("your trade score is not height enough to start a trade!", 'has-text-danger')
        app.session.close()
        app.pyn.close()
        return redirect('/showtrade')

    if 'rating' not in appobj or not appobj['rating']:
        flash("at the moment there is minor trouble with google playstore, try angain later !", 'has-text-danger')
        app.session.close()
        app.pyn.close()
        return redirect('/add')

    if appobj and int(appobj['rating']) <= REVIEWLIMIT and is_human(captcha_response):
        appmodel = app.session.query(App).filter(App.appidstring==appid).first()
        if not appmodel:
            appmodel = App(appobj['title'], appid)
        appmodel.imageurl = appobj['icon']
        appmodel.paid = appobj['price'] > 0
        trade = Trade(current_user, appmodel, current_user.locale)
        app.session.add(trade)
        app.session.commit()
        tradeid = trade.id
        flash("added trade", 'has-text-primary')
        if 'redirectto' in request.args:
            app.session.close()
            app.pyn.close()
            return redirect(request.args.get('redirectto'))

        app.session.close()
        app.pyn.close()

        return redirect('/show?tradeid={}'.format(tradeid))
    else:
        flash(str("chapcha trouble, more than reviews, or of the process doent exist"), 'has-text-danger')

    app.session.close()
    app.pyn.close()
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

    result =  render_template('index.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result

@app.route('/')
def mainpage():
    """This intro page will show the help for this webapp, perhaps an other name or url is needed ?"""
    app.data['pagename'] = 'Intro page'
    result = render_template('mainpage.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result

@app.route('/overviewapps')
@login_required
def overviewapps():
    """This will show all the apps in a overview page"""
    app.data['pagename'] = 'All apps'
    try:
        app.data['data'] = pagination(App, 5)

    except Exception as exception:
        flash(str(exception), 'has-text-danger')

    result = render_template('overviewapps.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result

@app.route('/showreview')
@login_required
def showreview():
    """This will show the details about a review"""
    app.data['pagename'] = 'Reviews ?'
    reviewid = request.args.get('reviewid')
    try:
        review = app.session.query(Review).get(reviewid)
        if not review:
            app.session.close()
            app.pyn.close()
            flash('review not found', 'has-text-danger')
            return redirect('/overviewtrades')
        app.data['data'] = review
    except Exception as exception:
        flash(str(exception), 'has-text-danger')
    result = render_template('showreview.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result

@app.route('/overviewreviews')
@login_required
def overviewreviews():
    """the overview page so you can see all the reviews done"""
    app.data['pagename'] = 'All reviews'
    try:

        app.data['data'] = pagination(Review, 50)
    except Exception as exception:
        flash(str(exception), 'has-text-danger')
    result = render_template('overviewreviews.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result

@app.route('/overviewtrades')
@login_required
def overviewtrades():
    """a page that will show you a overview for all trades"""
    app.data['pagename'] = 'My trades'
    app.data['data'] = pagination(Trade, 5)

    app.data['sometest'] = current_user.all_pending()

    result = render_template('overview.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result

@app.route("/show")
@login_required
def show():
    """detail page for a single trade"""
    app.data['pagename'] = 'Trade details'
    tradeid = request.args.get('tradeid')

    if not tradeid or not tradeid.isnumeric():
        flash('Should be a number', 'has-text-danger')
        return redirect('/overviewtrades')

    googleid = current_user.googleid
    try:
        thetrade = app.session.query(Trade).get(tradeid)
        if not thetrade:
            flash('No trade found', 'has-text-danger')
            return redirect('/overviewtrades')

        app.data['data'] = thetrade
        app.data['canaccept'] = thetrade.can_accept(googleid)
        app.data['canjoin'] = thetrade.can_join(googleid) and current_user.can_join_trade()
        app.data['canreject'] = thetrade.can_reject(googleid)
        app.data['candelete'] = thetrade.can_delete(googleid)
        app.data['canleave'] = thetrade.can_leave(googleid)
    except Exception as exception:
        flash(str(exception), 'has-text-danger')

    result = render_template('showtrade.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result

@app.route("/reject")
@login_required
def reject():
    tradeid = request.args.get('tradeid')
    if not tradeid or not tradeid.isnumeric():
        flash('Should be a number', 'has-text-danger')
        return redirect('/overviewtrades')

    try:
        thetrade = app.session.query(Trade).get(int(tradeid))

        if not thetrade:
            app.session.close()
            app.pyn.close()
            flash('review not found', 'has-text-danger')
            return redirect('/overviewtrades')

        if thetrade.can_reject(current_user.googleid):
            thetrade.reject_user(current_user.googleid)
            app.session.commit()
            flash("rejected the trade", 'has-text-danger')
    except Exception as exception:
        app.session.rollback()
        flash(str(exception), 'has-text-danger')
    result = redirect('/show?tradeid=' + tradeid)
    app.session.close()
    app.pyn.close()
    return result

@app.route("/accept")
@login_required
def accept():
    """here a initiator or a joiner of a trade can accept the trade, if both partys have accepted the trade is on so to call"""
    tradeid = request.args.get('tradeid')
    if not tradeid or not tradeid.isnumeric():
        flash('Should be a number', 'has-text-danger')
        return redirect('/overviewtrades')

    try:
        thetrade = app.session.query(Trade).get(int(tradeid))

        if not thetrade:
            app.session.close()
            app.pyn.close()
            flash('trade not found', 'has-text-danger')
            return redirect('/overviewtrades')

        if thetrade.can_accept(current_user.googleid):
            thetrade.accept_user(current_user.googleid)
            app.session.commit()
            if thetrade.accepted:
                msg = Message(
                    'One of your app trades has been accepted',
                    html= """
                        <p>The trade has now been accepted !</p>
                        <p>The system will now start to look for your review.</p>
                        <p>Go to your <a href='{}/show?tradeid={}'>trade</a> to view the details and do a review of the counter app.</p>
                    """.format(domain, thetrade.id),
                    sender="sixdots.soft@gmail.com",
                    recipients=[thetrade.joiner.email]
                )

                mail = Mail(app)
                mail.send(msg)

                msg = Message(
                    'One of your app trades has been accepted',
                    html= """
                        <p>The trade has now been accepted !</p>
                        <p>The system will now start to look for your review.</p>
                        <p>Go to your <a href='{}/show?tradeid={}'>trade</a> to view the details and do a review of the counter app.</p>
                    """.format(domain, thetrade.id),
                    sender="sixdots.soft@gmail.com",
                    recipients=[thetrade.initiator.email]
                )
                mail = Mail(app)
                mail.send(msg)

            flash("accepted the trade",'has-text-primary')
    except Exception as exception:
        app.session.rollback()
        flash(str(exception),'has-text-danger')

    app.session.close()
    app.pyn.close()
    return redirect('/show?tradeid=' + tradeid)


@app.route("/delete")
@login_required
def delete():
    """this function will let the initiator of the trade delete the trade"""
    tradeid = request.args.get('tradeid')
    if not tradeid or not tradeid.isnumeric():
        flash('Should be a number', 'has-text-danger')
        return redirect('/overviewtrades')
    app.session.query(Trade).filter(Trade.id==tradeid).delete()
    app.session.commit()
    flash("trade removed !",'has-text-primary')
    app.session.close()
    app.pyn.close()
    return redirect('/overviewtrades')

@app.route("/join")
@login_required
def join():
    """here someone can join a trade by filling in a form with something to review, an app"""
    app.data['pagename'] = 'Join Trade'
    tradeid = request.args.get('tradeid')
    if not tradeid or not tradeid.isnumeric():
        flash('Should be a number', 'has-text-danger')
        return redirect('/overviewtrades')

    if current_user.get_score() < 0:
        flash("your trade score is not height enough to join a trade!", 'has-text-danger')

    result = render_template('join.html', tradeid=tradeid, data=app.data)
    app.session.close()
    app.pyn.close()
    return result

@app.route("/processjoin", methods = ['POST'])
@login_required
def processjoin():
    """here we will process the join form post so you can join a trade"""
    alliappjoin.validate(dict(request.form))

    tradeid = request.form.get('tradeid')

    if not tradeid or not tradeid.isnumeric():
        flash('Should be a number', 'has-text-danger')
        app.session.close()
        app.pyn.close()
        return redirect('/')


    if alliappjoin.errors:
        for key, val in alliappjoin.errors.items():
            flash(key + ": " + val[0], 'has-text-danger')
        app.session.close()
        app.pyn.close()
        return redirect('/join?tradeid={}'.format(tradeid))

    if current_user.get_score() < 0:
        flash("your trade score is not height enough to join a trade!", 'has-text-danger')
        app.session.close()
        app.pyn.close()
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

        if not trade.can_join(current_user.id):
            flash("trade is already joind you sly dog !", 'has-text-danger')
            app.session.close()
            app.pyn.close()
            return redirect('/overviewtrades')

        trade.joiner = current_user
        trade.joinerapp = joinerappmodel
        trade.joinerlang = current_user.locale
        trade.joined = dt.datetime.now()
        app.session.add(trade)

        if trade.joinerapp == trade.initiatorapp:
            flash("cant join with same app as initiator app !", 'has-text-danger')
            app.session.close()
            app.pyn.close()
            return redirect('/overviewtrades')

        app.session.commit()
        tradeid = trade.id
        flash("joined the trade", 'has-text-primary')
        app.session.close()
        app.pyn.close()
        return redirect('/show?tradeid={}'.format(tradeid))
    else:
        flash(str("chapcha trouble, more than reviews, or of the process doent exist"), 'has-text-danger')

    app.session.close()
    app.pyn.close()
    return redirect('/join')

@app.route("/leave")
@login_required
def leave():
    """here a trade joiner can leave a trade"""
    tradeid = request.args.get('tradeid')
    if not tradeid or not tradeid.isnumeric():
        flash('Should be a number', 'has-text-danger')
        return redirect('/overviewtrades')
    thetrade = app.session.query(Trade).get(int(tradeid))
    try:
        if thetrade and thetrade.can_leave(current_user.googleid):
            thetrade.joiner = None
            thetrade.joined = None
            thetrade.joinerapp = None
            thetrade.joiner_accepted = False
            thetrade.joiner_accepted = False
            thetrade.initiator_accepted = False
            app.session.commit()
            flash("left the trade", 'has-text-primary')
        else:
            flash("cant leave since trade does not exist or trade has to be concluded", 'has-text-danger')
            app.session.close()
            app.pyn.close()
            return redirect('/overviewtrades')
    except Exception as exception:
        flash(str(exception), 'has-text-danger')

    app.session.close()
    app.pyn.close()
    return redirect('/overviewtrades')

@app.after_request
def set_response_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
