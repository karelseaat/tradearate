#!/usr/bin/env python

from config import make_session
from models import User, Trade, App, Review
import google_play_scraper
import pprint
import time
import smtplib
import logging
import datetime
logging.basicConfig(filename='check-reviews.log', level=logging.INFO)

logging.info('Start of check reviews' + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))

dbsession = make_session()

trades = dbsession.query(Trade).filter(Trade.accepted).filter(Trade.success==None).filter(Trade.failure==None).all()
siteurl = "trade.six-dots.app"
port = 465
smtp_server = "smtp.gmail.com"
login = "sixdots.soft@gmail.com"
password = "oqmhnpocsnigsvrx"

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


    if joiner in joinerreviews and initiator in initiatorreviews and trade.joiner_reviewed and trade.initiator_reviewed:

        sender = "no-reply@{}".format(siteurl)

        message_initiator = f"""\
            Subject: Trade a Rate, status change !
            To: {trade.initiator.email}
            From: {sender}

            The trade is succesfull !
        """

        message_joiner = f"""\
            Subject: Trade a Rate, status change !
            To: {trade.joiner.email}
            From: {sender}

            The trade is succesfull !
        """

        with smtplib.SMTP(smtp_server, port) as server:
            server.login(login, password)
            server.sendmail("no-reply@{}".format(siteurl), trade.initiator.email, message_initiator)

        with smtplib.SMTP(smtp_server, port) as server:
            server.login(login, password)
            server.sendmail("no-reply@{}".format(siteurl), trade.joiner.email, message_joiner)


    dbsession.add(trade)
    dbsession.commit()

dbsession.close()

logging.info('End of check reviews' + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
