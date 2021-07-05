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


if CONNECTIONURI and 'sqlite:///' in CONNECTIONURI and os.path.exists(CONNECTIONURI):
    os.remove(CONNECTIONURI)

session = make_session()

def random_message(message):
    faker = Faker()

    message.latitude = round(random.uniform(52.214, 52.220), 5)
    message.longitude = round(random.uniform(6.875, 6.881), 5)

    message.place_date = faker.date_time_this_month()
    message.text = faker.text()
    message.readlimit = faker.random_int(0, 50)
    message.color = "#{}".format(str(hex(random.randint(1118481, 16777216)))[2:].upper())
    message.daysvisible = faker.random_int(0, 50)

    return message

def random_user(user):
    faker = Faker()
    user.sub = str(faker.random_int())
    return user

session.query(Message).delete()
session.query(User).delete()

session.commit()
session.close()


session = make_session()

for _ in range(10):
    auser = random_user(User())
    for _ in range(50):
        amessage = random_message(Message())
        auser.messages.append(amessage)
    session.add(auser)


session.commit()
session.close()
