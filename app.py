from flask import Flask, jsonify, redirect, request, url_for, render_template, session
from authlib.integrations.flask_client import OAuth
from config import make_session
from models import User, Trade, App
import psutil
import requests, json
import google_play_scraper
from flask_login import (UserMixin, login_required, login_user, logout_user, current_user, LoginManager)
# todo:
# checkout of een app al 1000 reviews heeft zo jah dan kun je bij ons niet traden ! (done)
# bij een join een check doen of de joiner de initiator app kan downloaden en de initiator de joiner app kan downloaden, kijkenn of de apps op de store staan onder de country code van elkaar (ik denk done)
# ff de main page css fixen (pause tot nietuwe css framework ?)
# bezig met de your tades pagina (done)
# bezig met de trades wan welke user dan ook pagina ! (done)
# de intro pagina waarin we uitleggen op welke site je bent en wat dit doet ! (done)
# maak het zo dat als je niet ingelogd bent je eerst naar de google login wordt gestuurd. (done)
# kan ik een functie aanroepen aan het einde van iedere call om de sessie te sluiten ? (done)
# er moet een functie komen die voor iedere pagina wordt aangeroepen en alle data laad die altijd nodig is: (done)
# pagenaam, ingelogd of niet, logo, etc
# ff checken of we een ding als memcahce of reddis nodig hebben voor het cachen van languages store calls, etc ? (done)
# voor nu gewoon dickcache gebruiken met een een uur limiet voor development later wellicht een dag limiet !
# weghalen van menu als je niet bent ingelogd. (done)
# invullen van footer met wat nuttige info (done)
# zoals: privacy license, About, mogelijk gemaakt door (link to out page, copyright 2021 sixdots, cookie statement1)
# ik heb een page nodig met de user info van de user zelf. (done)
# Voor de user trades en your trade de teller van joiend trades en initiated trades instellen (done)
# wil ik voor extra user information deze info uit de db halen(in dat geval db van user uitbrijden) of wil ik het van google halen ? of wil ik het zo maken dat de user zelf info kan invullen !? (somewhat done)

# Aanpassen van een gebruiker die inlogt als zijn gegevens van google verandert lijken te zijn ! (todo)
# Het score deel moet ook nog gemaakt worden, so lets do that ! (todo)
# de knoppen voor: Join, Accept, Reject, Delete, Leave moeten niet gdisabled worden maar gewoon verdwijnen (todo)
# het logo moet er natuurlijk nog in ! (todo)
# De knoppen moeten ook nog even goed worden getest(als in staan ze er wanneer dat nodig is en dus test de progressie van state van de trade !) (todo)
# de links naar de gebruiker moeten naam en plaatje innemen ! (todo)
## even kijken of er nog meer dingen zijn onter te verdelen zijn in partials ! (todo)
# de leave knop werkt nog niet ff hier mee bezig ! (todo)

# wellicht voor later, dat een gebruiker custom data bij zn account kan zetten (geen id wat)
# de data in de db is niet heel byzonder en we hebben deze data nodig om alle data in de db te linken maar moet een gebruiker zn account niet kunnen verwijderen ?
# kijken waar we magic numbers hebben en deze in een config zetten !
# er moet een crontab script worden gemaakt dat de volgende doengen doet:
# - kijken of er van alle apps wat een trade op staat de grbruikers als een rating hebben gegeven !
# - ophalen van alle ratings voor een app en deze in de ratings zetten die aan een app hangen
#gezien de licentie geen commerciele werken toestaat moet het css framework volgens mij verandert worden !
# er moet nog een robot checker in gezien er anders robots op de site komen wat nogal kut is, we willen niet dat iemand onze site inzet en wat eigen marketing om groter te worden dan ons terwijk ons dat cpu kost en dan onze concurent zijn !
# er moet een mailer komen naar het email address van initiator en van joiner om de veranderde staat van een treet aan te geven, als bijde accept een seintje dat het aan is als er gejoined word ook ff en als een treet gelukt is !
# ok we gaan deze doen: https://github.com/creativetimofficial/material-dashboard
# is geinstaleerdin dir: ~/flask-material-dashboard
# ok voor je eigen profile moet je dus de info uit de sessie halen maar voor andere users moet de info uit de database worden gehaald.
#bij een login moet de data in de database voor deze users worden upgedate.
# dus ook de email voor een user in de db, locate niet in user db niet nodig, wel in session
#grofweg haal het altijd uit de db doe een update van userinfo in de db met de data die van google komt bij login !
# mild probleem dat oogle en google store niet wilt dat je naar hun site linkt qua plaatjes, moet op te lossen zijn door ze te downloaden.

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


@app.errorhandler(401)
def unauthorized(e):
    return redirect('/login')


@login_manager.user_loader
def load_user(userid):
    return app.session.query(User).filter(User.googleid == userid).first()
    # return user

@app.before_request
def before_request_func():
    app.data = {'message': [], 'logged-in': current_user.is_authenticated, 'stats-cpu':psutil.cpu_percent(), 'stats-mem':psutil.virtual_memory()[2]}
    current_user
    if current_user.is_authenticated:
        app.data['user'] = {'fullname': current_user.fullname, 'language': current_user.locale, 'email': current_user.email, 'picture': current_user.picture}

@app.route('/userprofile')
@login_required
def userprofile():
    app.data['message'] = current_user

    return render_template('userprofile.html.jinja', data=app.data)

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
            newuser.email = user_info['email']
            newuser.locale = user_info['locale'].split("-")[1].lower()
            app.session.add(newuser)
            app.session.commit()
            login_user(newuser)

    return redirect('/overview')

@app.route("/trades")
@login_required
def tradesbyuser():

    app.data['message'] = current_user
    return render_template('userlisttrades.html.jinja', data=app.data)

@app.route("/usertrades")
@login_required
def usertrades():
    userid = request.args.get('userid')
    userobj = app.session.query(User).filter(User.id==userid).first()

    app.data['message'] = userobj

    return render_template('userlisttrades.html.jinja', data=app.data)

@app.route("/add")
@login_required
def test():
    return render_template('index.html.jinja', data=app.data)


def get_app_from_store(appid, country='us'):
    appobj = None
    try:
        appobj = google_play_scraper.app(appid, country=country)
    except Exception as e:
        print(e)

    return appobj

@app.route("/processadd", methods = ['POST'])
@login_required
def nogietsZ():

    appid = request.form.get('appid')
    appobj = get_app_from_store(appid, country=current_user.locale)

    if appobj and int(appobj['reviews']) <= 1000 :

        appmodel = App(appobj['title'], appid)
        appmodel.imageurl = appobj['icon']
        trade = Trade(current_user, appmodel, current_user.locale)

        app.session.add(trade)
        app.session.commit()

        return redirect('/overview')
    else:
        return redirect('/add')

@app.route('/')
def mainpage():
    return render_template('mainpage.html.jinja', data=app.data)


@app.route('/overview')
@login_required
def nogiets():
    try:
        activetrades = app.session.query(Trade).all()
        app.data['message'] = activetrades

    except Exception as e:
        app.session.rollback()
        app.data['message'] = str(e)
    return render_template('notindexa.html.jinja', data=app.data)


@app.route("/show")
@login_required
def nogietsB():
    tradeid = request.args.get('tradeid')

    googleid = current_user.googleid

    try:
        thetrade = app.session.query(Trade).get(tradeid)
        app.data['message'] = thetrade
        app.data['canaccept'] = thetrade.can_accept(googleid)
        app.data['canjoin'] = thetrade.can_join(googleid)
        app.data['canreject'] = thetrade.can_reject(googleid)
        app.data['candelete'] = thetrade.can_delete(googleid)
        app.data['canleave'] = thetrade.can_leave(googleid)

    except Exception as e:
        app.session.rollback()
        app.data['message'] = str(e)
        print("error", e)

    return render_template('notindexb.html.jinja', data=app.data)

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
        app.data['message'] = str(e)

    return redirect('/show?tradeid=' + tradeid)

@app.route("/delete")
@login_required
def deleteit():
    tradeid = request.args.get('tradeid')
    app.session.query(Trade).filter(Trade.id==tradeid).delete()
    app.session.commit()

    return redirect('/overview')

@app.route("/join")
@login_required
def nogietsC():
    tradeid = request.args.get('tradeid')
    return render_template('indexX.html.jinja', tradeid=tradeid, data=app.data)

@app.route("/processjoin", methods = ['POST'])
@login_required
def nogietsW():

    appid = request.form.get('appid')
    tradeid = request.form.get('tradeid')
    appobjjoiner = get_app_from_store(appid, country=current_user.locale)

    if appobjjoiner and int(appobjjoiner['reviews']) <= 1000 :

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

            return redirect('/overview')
        else:
            print('some kind of error that the initiator cant review this app since country code !')
    else:
        return redirect('/join')

@app.after_request
def after_request_callback( response ):
    app.session.close()
    return response
