#!/usr/bin/env python

from config import make_session
from models import Trade, App, Review, Historic
import logging
import datetime

logging.basicConfig(filename='history-update.log', level=logging.INFO)

logging.info('Start of history update ' + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))

dbsession = make_session()

tradenum = dbsession.query(Trade).count()
appnum = dbsession.query(App).count()
reviewnum = dbsession.query(Review).count()

historyapp = Historic(infotype=0, number=appnum)
historytrade = Historic(infotype=1, number=tradenum)
historyreview = Historic(infotype=2, number=reviewnum)


dbsession.add(historytrade)
dbsession.add(historyapp)
dbsession.add(historyreview)
dbsession.commit()

logging.info('End of history update ' + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
