#!/usr/bin/env python
import random
import os
import sqlalchemy
from sqlalchemy import create_engine
from faker import Faker
from sqlalchemy.orm import sessionmaker
from models import *
import random

from config import make_session, CONNECTIONURI


if CONNECTIONURI and 'sqlite:///' in CONNECTIONURI:
    if os.path.exists(CONNECTIONURI.split('/')[-1]):
        os.remove(CONNECTIONURI.split('/')[-1])

session = make_session()

def random_trade(trade):
    faker = Faker()


    trade.initiator_accepted = bool(faker.random_int(0, 1))
    trade.joiner_accepted = bool(faker.random_int(0, 1))

    # if bool(faker.random_int(0, 1)):
    #     trade.set_accepted()

    return trade

def random_user(user):
    faker = Faker()
    initiateduser = user(faker.random_int(0, 100000))
    initiateduser.fullname = faker.name()
    initiateduser.picture = faker.name()
    return initiateduser

def random_app(app):
    faker = Faker()
    app.name = faker.name()
    app.appidstring = faker.name()
    return app

def random_review(review):
    faker = Faker()
    review.reviewtext = faker.name()
    review.reviewrating = faker.random_int(0, 10)
    return review

# session.query(Message).delete()
session.query(User).delete()

session.commit()
session.close()


session = make_session()

faker = Faker()

for _ in range(10):
    atrade = random_trade(Trade())

    atrade.initiator = random_user(User)


    appa = App("test", "nogtest")
    appb = App("niettest", "Klont")

    for _ in range(10):

        reviewa = Review()
        reviewb = Review()

        appa.reviews.append(random_review(reviewa))

        appb.reviews.append(random_review(reviewb))
        reviewa.user = atrade.initiator
        #
        reviewb.user = atrade.joiner

    atrade.initiatorapp = random_app(appa)
    if bool(faker.random_int(0, 1)):
        atrade.joinerapp = random_app(appb)
        atrade.joiner = random_user(User)

    session.add(atrade)

session.commit()
session.close()
