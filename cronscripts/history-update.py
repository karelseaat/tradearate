#!/usr/bin/env python

#the two lines bellow, hate it !
import sys
import os
dirname = "/".join(os.path.realpath(__file__).split('/')[:-1])

from config import make_session
from models import Trade, App, Review, Historic
import logging
import datetime

logging.basicConfig(filename='{}/history-update.log'.format(dirname), level=logging.INFO)

logging.info('Start of history update ' + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))

dbsession = make_session()

try:
    tradenum = dbsession.query(Trade).count()
    appnum = dbsession.query(App).count()
    reviewnum = dbsession.query(Review).count()
    logging.info("counts: {} {} {}".format(tradenum, appnum, reviewnum))
except error:
   logging.info("An error occured while counting objects: {}".format(error))

try:
    historyapp = Historic(infotype=0, number=appnum)
    historytrade = Historic(infotype=1, number=tradenum)
    historyreview = Historic(infotype=2, number=reviewnum)
    logging.info("history objects made !")
except error:
   logging.info("An error occured where adding to history: {}".format(error))

try:
    dbsession.add(historytrade)
    dbsession.add(historyapp)
    dbsession.add(historyreview)
    dbsession.commit()
    logging.info("All inserted into the db !")
except error:
   logging.info("An error occured while sending the whole shabang to the db: {}".format(error))

logging.info('End of history update ' + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
