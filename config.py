
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base

REVIEWLIMIT = 1000

oauthconfig = {
    'name':'google',
    'client_id':'73190520700-quq0eklkk131ulbukpcokav1khtrupo6.apps.googleusercontent.com',
    'client_secret':'PcA-dpVsAsqAzIcliLwhxZ7B',
    'access_token_url':'https://accounts.google.com/o/oauth2/token',
    'access_token_params':None,
    'authorize_url':'https://accounts.google.com/o/oauth2/auth',
    'authorize_param':None,
    'api_base_url':'https://www.googleapis.com/oauth2/v1/',
    'userinfo_endpoint':'https://openidconnect.googleapis.com/v1/userinfo',
    'client_kwargs':{'scope': 'openid email profile'}
}

CONNECTIONURI = "sqlite:///treetareet.sqlite"

def make_session():
    engine = create_engine(CONNECTIONURI, echo=False, connect_args={'check_same_thread': False})
    dbsession = scoped_session(sessionmaker(bind=engine))
    Base.metadata.create_all(engine)
    return dbsession()



# Wat komt hier in te staan:
# alle google OAuth keys, oauth urls, names etc.
# de app secret key
# de reviews liemit die nu nog op 1000 staat in app.py
