#!/usr/bin/env python

from config import make_session
from models import Trade, App, Review, Historic
import logging
import datetime
import os

dirname = os.path.dirname(__file__)
# print(dirname)

logging.basicConfig(filename='{}/history-update.log'.format(dirname), level=logging.INFO)

logging.info('Start of history update ' + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))

dbsession = make_session()

try:
    tradenum = dbsession.query(Trade).count()
    appnum = dbsession.query(App).count()
    reviewnum = dbsession.query(Review).count()
except error:
   print("An error occured while counting objects", error)

try:
    historyapp = Historic(infotype=0, number=appnum)
    historytrade = Historic(infotype=1, number=tradenum)
    historyreview = Historic(infotype=2, number=reviewnum)
except error:
   print("An error occured where adding to history", error)

try:
    dbsession.add(historytrade)
    dbsession.add(historyapp)
    dbsession.add(historyreview)
    dbsession.commit()
except error:
   print("An error occured while sending the whole shabang to the db", error)

logging.info('End of history update ' + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
