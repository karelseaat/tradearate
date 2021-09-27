#!/usr/bin/env python

from config import make_session
from models import User, Trade, App, Review
import google_play_scraper
import pprint
import time
from flask_mail import Mail, Message

dbsession = make_session()

trades = dbsession.query(Trade).filter(Trade.accepted).filter(Trade.success==None).filter(Trade.failure==None).all()
siteurl = "trade.six-dots.app"

for trade in trades:

    initiator = ""
    joiner = ""

    initiatorreviews = []
    joinerreviews = []

    if trade.initiator:
        initiator = trade.initiator.fullname

    if trade.joiner:
        joiner = trade.joiner.fullname

    # er moet hier nog een check komen of de trade over datum is zo jah zet de trade of failed en stuur een mail dat de trade gefailed is naar bij de parijen
    # daarnaast moeten er nog minpunten worden eggeven voor deze trade !

    if trade.initiatorapp:
        for value in trade.initiatorapp.reviews:
            initiatorreviews.append(value.username)

    if trade.joinerapp:
        for value in trade.joinerapp.reviews:
            joinerreviews.append(value.username)


    if initiator in initiatorreviews:
        print("initiator has done review")
        trade.initiator_reviewed = True

    if joiner in joinerreviews:
        print("joiner has done review")
        trade.joiner_reviewed = True

# het email deel moet nog anders want dit deel van het prog heeft geen flask.
# https://mailtrap.io/blog/sending-emails-in-python-tutorial-with-code-examples/

    if joiner in joinerreviews and initiator in initiatorreviews and trade.joiner_reviewed and trade.initiator_reviewed:
        msg = Message('Test !', body="The trade is succesfull !", sender="no-reply@{}".format(siteurl), recipients=[trade.initiator.email])
        mail = Mail(app)
        mail.send(msg)
        msg = Message('Test !', body="The trade is succesfull !", sender="no-reply@{}".format(siteurl), recipients=[trade.joiner.email])
        mail = Mail(app)
        mail.send(msg)

    dbsession.add(trade)
    dbsession.commit()

dbsession.close()
