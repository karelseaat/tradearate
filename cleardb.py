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


session.commit()
session.close()


session = make_session()

session.commit()
session.close()
