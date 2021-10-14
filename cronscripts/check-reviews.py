#!/usr/bin/env python

#the two lines bellow, hate it !
import sys
import os
dirname = "/".join(os.path.realpath(__file__).split('/')[:-1])

sys.path.append(dirname + '/..')

from config import make_session
from config import Config
from config import domain
from models import User, Trade, App, Review
import google_play_scraper
import time
import smtplib
import logging
import datetime
logging.basicConfig(filename='check-reviews.log', level=logging.INFO)

logging.info('Start of check reviews' + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))

dbsession = make_session()

trades = dbsession.query(Trade).filter(Trade.accepted).filter(Trade.success==None).filter(Trade.failure==None).all()

for trade in trades:

    initiator = ""
    joiner = ""

    initiatorreviews = []
    joinerreviews = []

    if trade.initiator:
        initiator = trade.initiator.fullname

    if trade.joiner:
        joiner = trade.joiner.fullname


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

        trade.success = datetime.datetime.now()

        sender = "no-reply@{}".format(domain)

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

        with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
            server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            server.sendmail("no-reply@{}".format(domain), trade.initiator.email, message_initiator)

        with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
            server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            server.sendmail("no-reply@{}".format(domain), trade.joiner.email, message_joiner)


    dbsession.add(trade)
    dbsession.commit()

dbsession.close()

logging.info('End of check reviews' + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
