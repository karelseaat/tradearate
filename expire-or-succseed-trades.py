#!/usr/bin/env python

from config import make_session
from models import Trade
import logging
import datetime
import os
from sqlalchemy import and_, or_, not_

dirname = os.getcwd()
logging.basicConfig(filename='{}/history-update.log'.format(dirname), level=logging.INFO)
logging.info('Start of expire trade ' + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))

dbsession = make_session()
tradeobj = Trade()


# suctrades = dbsession.query(Trade).filter(and_(Trade.initiator_reviewed, Trade.joiner_reviewed)).all()
# for trade in suctrades:
#     trade.success = datetime.datetime.now()
#
# dbsession.commit()

trades = dbsession.query(Trade).filter(Trade.accepted + datetime.timedelta(days=tradeobj.timetotrade) < datetime.datetime.now().date()).filter(and_(not_(Trade.initiator_reviewed), not_(Trade.joiner_reviewed))).all()

for trade in trades:
    trade.failure = datetime.datetime.now()

dbsession.commit()
dbsession.close()
logging.info('End of expire trade ' + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
