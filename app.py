import json
from datetime import timedelta
import datetime as dt
import time
import requests
from flask import Flask, redirect, request, url_for, render_template, flash, Response, session as browsersession
from authlib.integrations.flask_client import OAuth
from flask_login import (login_required, login_user, logout_user, current_user, LoginManager)

from flask_mail import Mail, Message
from cerberus import Validator

from flask_cachecontrol import (FlaskCacheControl, cache_for, dont_cache)
from config import make_session, oauthconfig, REVIEWLIMIT, recaptchasecret, recapchasitekey, domain
from models import User, Trade, App, Review, Historic
from lib.myownscraper import get_app, get_app_alt
from lib.filtersort import FilterSort
from lib.translator import PyNalator


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


flask_cache_control = FlaskCacheControl()
flask_cache_control.init_app(app)

oauth = OAuth(app)
oauth.register(**oauthconfig)

@app.errorhandler(401)
def unauthorized(_):
    """the error handler for unauthorised"""
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

def nongetpagination(db_object, itemnum):
    """it does the pagination for db results"""
    pagenum = 0

    if 'pagenum' in request.args and request.args.get('pagenum').isnumeric():
        pagenum = int(request.args.get('pagenum'))

    total = db_object.count()
    app.data['total'] = list(range(1, round_up(total/itemnum)+1))
    app.data['pagenum'] = pagenum+1, round_up(total/itemnum)
    return db_object.limit(itemnum).offset(pagenum*itemnum)

@login_manager.user_loader
def load_user(userid):
    """we need this for authentication"""
    return app.session.query(User).filter(User.googleid == userid).first()

@app.route('/process_index.svg', methods=('GET', 'HEAD'))
@cache_for(hours=12)
def index_svg():
    """a dynamic svg fancy hu"""
    xml = render_template('indexsvg.svg', color="#f00")
    return Response(xml, mimetype='image/svg+xml')

@app.route('/process_help.svg', methods=('GET', 'HEAD'))
@cache_for(hours=12)
def help_svg():
    """another dynamic svg for the help page"""
    xml = render_template('helpsvg.svg', color="#f00")
    return Response(xml, mimetype='image/svg+xml')

@app.before_request
def before_request_func():
    """do this before any request"""
    if isinstance(current_user, User) and current_user.locale:
        app.pyn = PyNalator(localename=current_user.locale, subdir="translations")
    else:
        app.pyn = PyNalator(subdir="translations")

    app.jinja_env.globals.update(trans=app.pyn.trans)

    navigation = {
        'dashboard': ('Dashboard', 'dashboard'),
        'alltrades': ('All trades', 'overviewtrades'),
        'allapps': ('All apps', 'overviewapps'),
        'allreviews': ('All reviews', 'overviewreviews'),
        'mytrades': ('My trades', 'trades'),
        'myreviews': ('All reviews', 'overviewreviews'),
        'profile': ('My profile', 'userprofile'),
        'about': ('help', '/help'),
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
@cache_for(hours=12)
@login_required
def userprofile():
    """ this will show a users profile"""
    app.data['pagename'] = 'User profile'
    app.data['data'] = current_user
    app.data['userscore'] = current_user.get_score()
    result = render_template('userprofile.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result


@app.route('/login')
@dont_cache()
def login():
    """login that will call google oauth to you can login with your gooogle account"""
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    result = google.authorize_redirect(redirect_uri)
    app.session.close()
    app.pyn.close()
    return result

@app.route("/customlogin", methods = ['POST'])
@dont_cache()
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
@dont_cache()
@login_required
def logout():
    """here you can logout , it is not used since you login via google oauth so as soon as you are on the site you are loggedin"""
    logout_user()
    app.session.close()
    app.pyn.close()
    return redirect('/')

@app.route('/contact')
@cache_for(hours=12)
@login_required
def contact():
    """Showin a contact form !"""
    app.data['pagename'] = 'Contact'
    result = render_template('contact.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result

@app.route('/processcontact', methods = ['POST'])
@dont_cache()
@login_required
def processcontact():
    """this will prcess a contact form"""
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
        f"Trade a rate contact form !, {subject}",
        sender = 'sixdots.soft@gmail.com',
        body= f"name: {current_user.fullname}\nemail: {current_user.email}\nmessage: {message}",
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
@dont_cache()
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
@dont_cache()
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
@dont_cache()
@login_required
def usertrades():
    """this will show all trades of the current user"""
    app.data['pagename'] = 'User Trades'
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
@cache_for(hours=12)
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
        appobj = get_app_alt(appid, country=country)
    except Exception as exception:
        flash(str(exception), 'has-text-danger')
    return appobj

@app.route("/processadd", methods = ['POST'])
@dont_cache()
@login_required
def processadd():
    """This will process the post of a form to add a trade"""
    valliappinit.validate(dict(request.form))

    if valliappinit.errors:
        for key, val in valliappinit.errors.items():
            flash(f"{key}: {val}", 'has-text-danger')
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

    if 'ratings' not in appobj or not appobj['ratings']:
        flash("at the moment there is minor trouble with google playstore, try angain later !", 'has-text-danger')
        app.session.close()
        app.pyn.close()
        return redirect('/add')

    if appobj and int(appobj['ratings']) <= REVIEWLIMIT and is_human(captcha_response):
        appmodel = app.session.query(App).filter(App.appidstring==appid).first()
        if not appmodel:
            appmodel = App(appobj['title'], appid)
        appmodel.imageurl = appobj['icon']
        appmodel.paid = not appobj['free']
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

    flash(str("chapcha trouble, more than reviews, or of the process doent exist"), 'has-text-danger')
    app.session.close()
    app.pyn.close()
    return redirect('/add')

@app.route('/dashboard')
@cache_for(hours=6)
def dashboard():
    """the dashboard page, a bit of a shit name, it shows the dashboard with graphs"""
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
    app.data['apps'] = [ x.number for x in allstuff if  x.infotype == 0]
    app.data['trades'] = [ x.number for x in allstuff if x.infotype == 1]
    app.data['reviews'] = [ x.number for x in allstuff if  x.infotype == 2]
    app.data['labels'] = json.dumps(sorted(list({ str(x.date) for x in allstuff})))

    result =  render_template('dashboard.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result

@app.route('/')
@cache_for(hours=12)
def index():

    app.data['pagename'] = 'About'
    result = render_template('index.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result


@app.route('/help')
@cache_for(hours=12)
def helppage():
    """This intro page will show the help for this webapp, perhaps an other name or url is needed ?"""
    app.data['pagename'] = 'Help page'
    result = render_template('helppage.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result

@app.route('/overviewapps')
@cache_for(hours=3)
@login_required
def overviewapps():
    """This will show all the apps in a overview page"""
    app.data['pagename'] = 'All apps'
    try:
        filtersort = FilterSort()
        sortlist = filtersort.make_sort({'name': App.name, 'payed': App.paid})
        app.data['sorts'] = filtersort.generate_next_sort(['name', 'payed'])
        app.data['cursort'] = filtersort.generate_current_sort(['name', 'payed'])

        apps = app.session.query(App)
        for sort in sortlist:
            apps = apps.order_by(sort())

        apps = nongetpagination(apps, 5).all()

        app.data['data'] = apps

    except Exception as exception:
        print(str(exception))
        flash(str(exception), 'has-text-danger')

    result = render_template('overviewapps.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result

@app.route('/showreview')
@dont_cache()
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
@cache_for(hours=6)
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
@dont_cache()
@login_required
def overviewtrades():
    """a page that will show you a overview for all trades"""
    app.data['pagename'] = 'All trades'


    alltrades = app.session.query(Trade).filter(Trade.accepted == None).filter(Trade.success == None)

    app.data['data'] = nongetpagination(alltrades, 5).all()

    result = render_template('overview.html', data=app.data)
    app.session.close()
    app.pyn.close()
    return result

@app.route("/show")
@dont_cache()
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
@dont_cache()
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
@dont_cache()
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
                    html= f"""
                        <p>The trade has now been accepted !</p>
                        <p>The system will now start to look for your review.</p>
                        <p>Go to your <a href='{domain}/show?tradeid={thetrade.id}'>trade</a> to view the details and do a review of the counter app.</p>
                        <p>Or go to the playstore directly <a href='{thetrade.initiatorapp.get_url()}'>directly</a> to do a download and review!</p>
                    """,
                    sender="sixdots.soft@gmail.com",
                    recipients=[thetrade.joiner.email]
                )

                mail = Mail(app)
                mail.send(msg)

                msg = Message(
                    'One of your app trades has been accepted',
                    html= f"""
                        <p>The trade has now been accepted !</p>
                        <p>The system will now start to look for your review.</p>
                        <p>Go to your <a href='{domain}/show?tradeid={thetrade.id}'>trade</a> to view the details and do a review of the counter app.</p>
                        <p>Or go to the playstore directly <a href='{thetrade.joinerapp.get_url()}'>directly</a> to do a download and review!</p>
                    """,
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
@dont_cache()
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
    time.sleep(1)
    return redirect('/overviewtrades', 303)

@app.route("/join")
@cache_for(hours=12)
@dont_cache()
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
@dont_cache()
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

    if appobjjoiner and int(appobjjoiner['ratings']) <= REVIEWLIMIT and is_human(captcha_response):
        joinerappmodel = app.session.query(App).filter(App.appidstring==appid).first()
        if not joinerappmodel:
            joinerappmodel = App(appobjjoiner['title'], appid)
            joinerappmodel.imageurl = appobjjoiner['icon']
            joinerappmodel.paid = not appobjjoiner['free']
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
        trade.tradestatus = 1
        app.session.add(trade)

        if trade.joinerapp == trade.initiatorapp:
            flash("cant join with same app as initiator app !", 'has-text-danger')
            app.session.close()
            app.pyn.close()
            return redirect('/overviewtrades')

        msg = Message(
            'One of your app trades has been joined!',
            html= f"""
                <p>Go to your <a href='{domain}/show?tradeid={trade.id}'>trade</a> to view the details and decide if you want to accept the trade !</p>
            """,
            sender="sixdots.soft@gmail.com",
            recipients=[trade.initiator.email]
        )

        mail = Mail(app)
        mail.send(msg)

        msg = Message(
            'You have joined a app trade!',
            html= f"""
                <p>Go to the <a href='{domain}/show?tradeid={trade.id}'>trade</a> to view the details and decide if you want to accept the trade !</p>
            """,
            sender="sixdots.soft@gmail.com",
            recipients=[trade.joiner.email]
        )

        mail = Mail(app)
        mail.send(msg)

        app.session.commit()
        tradeid = trade.id
        flash("joined the trade", 'has-text-primary')
        app.session.close()
        app.pyn.close()
        return redirect('/show?tradeid={}'.format(tradeid))

    flash(str("chapcha trouble, more than reviews, or of the process doent exist"), 'has-text-danger')
    app.session.close()
    app.pyn.close()
    return redirect('/join')

@app.route("/leave")
@dont_cache()
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
            thetrade.tradestatus = 0
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
