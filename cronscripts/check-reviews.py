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
from email.mime.text import MIMEText
import logging
import datetime

dirname=dirname+"/../logs"
logging.basicConfig(filename='{}/check-reviews.log'.format(dirname), level=logging.INFO)

def check_reviews():
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
                # if len(value.reviewtext) > value.minreviewlength:
                if value.user:
                    initiatorreviews.append(value.user.fullname)
                else:
                    initiatorreviews.append(value.username)

        if trade.joinerapp:
            for value in trade.joinerapp.reviews:
                # if len(value.reviewtext) > value.minreviewlength:
                if value.user:
                    joinerreviews.append(value.user.fullname)
                else:
                    joinerreviews.append(value.username)


        print(initiatorreviews, joiner)
        print(joinerreviews, initiator)

        if joiner in initiatorreviews:
            print("initiator has done review")
            trade.initiator_reviewed = True

        if initiator in joinerreviews:
            print("joiner has done review")
            trade.joiner_reviewed = True

        if trade.joiner_reviewed and trade.initiator_reviewed:
            trade.success = datetime.datetime.now()
            sender = "sixdots.soft@gmail.com"

            message_initiator = MIMEText("<p>A <a href='{}/show?tradeid={}'>trade</a> you started on Trade A Rate has suceeded</p>".format(domain, trade.id), 'html')
            message_initiator['From'] = sender
            message_initiator['To'] = trade.initiator.email
            message_initiator['Subject'] = "Trade A Rate, success !"

            message_joiner = MIMEText("<p>A <a href='{}/show?tradeid={}'>trade</a> you joined on Trade A Rate has suceeded</p>".format(domain, trade.id), 'html')
            message_joiner["From"] = sender
            message_joiner["To"] = trade.joiner.email
            message_joiner['Subject'] = "Trade A Rate, success !"

            with smtplib.SMTP_SSL(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.sendmail("sixdots.soft@gmail.com", trade.initiator.email, message_initiator.as_string())

            with smtplib.SMTP_SSL(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.sendmail("sixdots.soft@gmail.com", trade.joiner.email, message_joiner.as_string())

        dbsession.add(trade)
        dbsession.commit()
    dbsession.close()



if __name__ == "__main__":
    logging.info('Start of check reviews' + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    check_reviews()
    logging.info('End of check reviews' + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
