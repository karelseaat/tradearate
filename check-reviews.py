#!/usr/bin/python3

from config import make_session
from models import User, Trade, App, Review
import google_play_scraper
import pprint
import time


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

    dbsession.add(trade)
    dbsession.commit()

dbsession.close()
