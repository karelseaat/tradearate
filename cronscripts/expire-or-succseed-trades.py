#!/usr/bin/env python

#the two lines bellow, hate it !
import sys
import os
dirname = "/".join(os.path.realpath(__file__).split('/')[:-1])

sys.path.append(dirname + '/..')

from config import make_session
from config import Config
from config import domain
from models import Trade
import logging
import datetime
import smtplib

from sqlalchemy import and_, or_, not_

dirname = os.getcwd()
logging.basicConfig(filename='{}/history-update.log'.format(dirname), level=logging.INFO)


def expire_or_succeed():

    dbsession = make_session()
    tradeobj = Trade()

    trades = dbsession.query(Trade).filter(Trade.accepted + datetime.timedelta(days=tradeobj.timetotrade) < datetime.datetime.now().date()).filter(or_(not_(Trade.initiator_reviewed), not_(Trade.joiner_reviewed))).all()


    for trade in trades:
        trade.failure = datetime.datetime.now()

        sender = "sixdots.soft@gmail.com"

        message_initiator = f"""\
            Subject: Trade a Rate, status change !
            To: {trade.initiator.email}
            From: {sender}

            The trade has failed !
        """

        message_joiner = f"""\
            Subject: Trade a Rate, status change !
            To: {trade.joiner.email}
            From: {sender}

            The trade has failed !
        """

        with smtplib.SMTP_SSL(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
            server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            server.sendmail("sixdots.soft@gmail.com", trade.initiator.email, message_initiator)

        with smtplib.SMTP_SSL(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
            server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            server.sendmail("sixdots.soft@gmail.com", trade.joiner.email, message_joiner)

    dbsession.commit()
    dbsession.close()


if __name__ == "__main__":
    logging.info('Start of expire trade ' + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    expire_or_succeed()
    logging.info('End of expire trade ' + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
