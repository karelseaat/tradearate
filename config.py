
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base


# Configuration
GOOGLE_CLIENT_ID = "565487004572-na6f5e5cpqe77bjr69ne3gnuqdad9hmr.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "_uB_CVhw1Ax3q9vlqrs6oiXm"
SECRET_KEY = "blaat123"
GOOGLE_DISCOVERY_URL = ("https://accounts.google.com/.well-known/openid-configuration")

CONNECTIONURI = "sqlite:///treetareet.sqlite"

def make_session():
    engine = create_engine(CONNECTIONURI, echo=False)
    dbsession = scoped_session(sessionmaker(bind=engine))
    Base.metadata.create_all(engine)
    return dbsession()
