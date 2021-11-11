#!/usr/bin/env python

#the two lines bellow, hate it !
import sys
import os
dirname = "/".join(os.path.realpath(__file__).split('/')[:-1])

sys.path.append(dirname + '/..')

# This script will go trough the db and will get all apps of trades that are active.
#It will also get all the languages of the user associated with the trade.
# aftwe that it will ask the google play store api what all the reviews are of that app

from config import make_session
from models import User, Trade, App, Review
import google_play_scraper
import time

from google_play_scraper.features.reviews import _ContinuationToken
import logging
import datetime
logging.basicConfig(filename='get-reviews.log', level=logging.INFO)

def serialise_token(token):
    if not token.token:
        token.token = ""
    return ",".join([token.token, token.lang, token.country, str(token.count)])

def deserialise_token(serialised):
    splitted = serialised.split(',')
    return _ContinuationToken(splitted[0], splitted[1], splitted[2], None, int(splitted[3]), None)

def feedreviews(app, langs, numofrespercall):
    count = numofrespercall
    resultcount = numofrespercall

    if app.continuation_token:
        continuation_token = deserialise_token(app.continuation_token)
    else:
        continuation_token = None

    for lang in langs:

        while resultcount == count:

            result, continuation_token = google_play_scraper.reviews(
                app.appidstring,
                lang=lang,
                count=count,
                continuation_token=continuation_token
            )

            resultcount = len(result)


            for x in result:
                if 'content' in x and 'at' in x and 'score' in x and 'userName' in x:
                    try:
                        auser = dbsession.query(User).filter(User.fullname==x['userName']).first()
                        aitem = dbsession.query(Review).filter(Review.google_id==x['reviewId']).first()
                        if not aitem:
                            aitem = Review()
                            aitem.reviewtext = x['content']
                            aitem.reviewtime = x['at']
                            aitem.reviewrating = x['score']
                            aitem.locale = lang
                            aitem.app = app
                            aitem.google_id = x['reviewId']
                            if auser:
                                aitem.user = auser
                            else:
                                aitem.username = x['userName']
                                aitem.userimageurl = x['userImage']
                        dbsession.add(aitem)

                    except Exception as e:
                        print(e)

            if continuation_token.token:
                app.continuation_token = serialise_token(continuation_token)
                dbsession.add(app)
            dbsession.commit()

            time.sleep(5)


def get_reviews():
    dbsession = make_session()

    allapps = []
    trades = dbsession.query(Trade).filter(Trade.accepted).filter(Trade.success==None).filter(Trade.failure==None).all()

    for value in trades:
        for app in value.all_apps_in_trade():
            allapps.append(app)

    for value in allapps:
        allusers = []
        for auser in value.all_users():
            allusers.append(auser)

        listoflangs = list(set([x.locale for x in set(allusers) if x.locale]))
        feedreviews(value, listoflangs, 100)

    dbsession.close()


if __name__ == "__main__":
    logging.info('Start of get reviews' + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    get_reviews()
    logging.info('End of get reviews' + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
