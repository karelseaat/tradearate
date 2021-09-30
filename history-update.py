#!/usr/bin/env python

from config import make_session
from models import Trade, App, Review, Historic


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
