#!/usr/bin/env python

import sys
sys.path.append('..')

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
    realpath = "/"+"/".join(CONNECTIONURI.split('/')[5:])
    if os.path.exists(realpath):
        os.remove(realpath)
    else:
        print("path does not exist !")

session = make_session()


session.commit()
session.close()


session = make_session()

session.commit()
session.close()
