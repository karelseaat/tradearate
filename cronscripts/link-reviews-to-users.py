#!/usr/bin/env python

import sys
import os

dirname = "/".join(os.path.realpath(__file__).split('/')[:-1])
sys.path.append(dirname + '/..')

from config import make_session
from models import User, Review
import datetime

def link_reviews_to_users():
    dbsession = make_session()
    users = dbsession.query(User).all()

    reviews = dbsession.query(Review).filter(Review.added > datetime.datetime.now().date() - datetime.timedelta(days=2)).all()

    reviewnames = {trade.username:trade for trade in reviews}

    for user in users:
        if user.fullname in reviewnames:
            tochange = reviewnames[user.fullname]
            tochange.username = ""
            tochange.userimageurl = ""
            tochange.user  = user
            dbsession.add(tochange)
            print("found one !")

    dbsession.commit()
    dbsession.close()

if __name__ == "__main__":
    link_reviews_to_users()
