#!/usr/bin/env python

#the two lines bellow, hate it !
import sys
import os
dirname = os.getcwd()

sys.path.append(dirname + '/..')

from config import make_session
from config import Config
form config import domain
from models import Trade
import logging
import datetime
import smtplib

from sqlalchemy import and_, or_, not_

dirname = os.getcwd()
logging.basicConfig(filename='{}/history-update.log'.format(dirname), level=logging.INFO)
logging.info('Start of expire trade ' + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))

dbsession = make_session()
tradeobj = Trade()

trades = dbsession.query(Trade).filter(Trade.accepted + datetime.timedelta(days=tradeobj.timetotrade) < datetime.datetime.now().date()).filter(and_(not_(Trade.initiator_reviewed), not_(Trade.joiner_reviewed))).all()



for trade in trades:
    trade.failure = datetime.datetime.now()

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

    with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
        server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
        server.sendmail("no-reply@{}".format(domain), trade.initiator.email, message_initiator)

    with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
        server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
        server.sendmail("no-reply@{}".format(domain), trade.joiner.email, message_joiner)

dbsession.commit()
dbsession.close()
logging.info('End of expire trade ' + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
