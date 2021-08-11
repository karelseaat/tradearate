import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, String, Integer, Float, Boolean, Date
from sqlalchemy_utils import get_hybrid_properties
from sqlalchemy.dialects.mysql import DOUBLE


Base = declarative_base()
metadata = Base.metadata

class DictSerializableMixin(Base):
    __abstract__ = True

    def _asdict(self):
        result = dict()

        for key in self.__mapper__.c.keys() + list(get_hybrid_properties(self).keys()):
            result[key] = getattr(self, key)
        return result

    def _asattrs(self, adict, afilter):
        for key, val in adict.items():
            if hasattr(self, key) and key in afilter:
                setattr(self, key, val)

class User(DictSerializableMixin):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    fullname = Column(String(64))
    picture = Column(String(256))
    reviews = relationship('Review', back_populates="user")
    googleid = Column(Integer, nullable=False)

    def __init__(self, googleid):
        self.googleid = googleid

class Trade(DictSerializableMixin):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True)

    initiator_id = Column(ForeignKey('users.id'), index=True)
    joiner_id = Column(ForeignKey('users.id'), index=True)

    initiator = relationship('User', backref='initiatortrades', foreign_keys='Trade.initiator_id')
    joiner = relationship('User', backref='joinertrades', foreign_keys='Trade.joiner_id')

    initiatorapp_id = Column(ForeignKey('apps.id'), index=True)
    joinerapp_id = Column(ForeignKey('apps.id'), index=True)

    initiatorapp = relationship('App', backref='initiatortrades', foreign_keys='Trade.initiatorapp_id')
    joinerapp = relationship('App', backref='joinertrades', foreign_keys='Trade.joinerapp_id')

    initiatorlang = Column(String(4), default="unk")
    joinerlang = Column(String(4), default="unk")

    initiated = Column(Date, default=datetime.datetime.utcnow)
    initiator_accepted = Column(Boolean, default=False)
    joiner_accepted = Column(Boolean, default=False)
    accepted = Column(Date, nullable=True)
    success = Column(Date, nullable=True)
    failure = Column(Date, nullable=True)


    def __init__(self, initiator=None, initiatorapp=None, initiatorlang=None):
        if initiator:
            self.initiator = initiator

        if initiatorapp:
            self.initiatorapp = initiatorapp

        if initiatorlang:
            self.initiatorlang = initiatorlang

    def status(self):
        if self.failure:
            return "failure"
        elif self.success:
            return "success"
        elif self.accepted:
            return "accepted"
        else:
            return "initiated"

    def set_accepted(self):
        self.accepted = datetime.datetime.now().date()

    def trade_days_left(self):
        if self.accepted:
            currDate = datetime.datetime.now() + datetime.timedelta(days=10)
            return (currDate.date() - self.accepted).days
        return 0

    def age(self):
        currDate = datetime.datetime.now()
        return (currDate.date() - self.initiated).days

    def accept_age(self):
        if self.accepted:
            currDate = datetime.datetime.now()
            return (currDate.date() - self.accepted).days
        return 0

    def canjoin(self):
        return not (self.success or self.failure or self.accepted)

    def can_accept(self, usergoogleid):
        return (self.initiator.googleid == usergoogleid or self.joiner.googleid == usergoogleid) and not self.accepted

    def accept_user(self, usergoogleid):
        if self.initiator.googleid == usergoogleid:
            self.initiator_accepted = True
        elif self.joiner.googleid == usergoogleid:
            self.joiner_accepted = True

        if self.initiator_accepted and self.joiner_accepted:
            self.accepted = True

class App(DictSerializableMixin):
    __tablename__ = 'apps'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    appidstring = Column(String(64), nullable=False)
    reviews = relationship('Review', back_populates="app")
    imageurl = Column(String(256))

    def __init__(self, name, idstring):
        self.name = name
        self.appidstring = idstring

    def get_url(self):
        return "https://play.google.com/store/apps/details?id=" + self.appidstring


class Review(DictSerializableMixin):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True)
    app_id = Column(ForeignKey('apps.id'), index=True)
    app = relationship('App', back_populates="reviews")
    reviewtext = Column(String(64), nullable=True)
    reviewrating = Column(Integer)

    user_id = Column(ForeignKey('users.id'), index=True)
    user = relationship('User', back_populates="reviews")
