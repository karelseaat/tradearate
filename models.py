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
    nickname = Column(String(64), nullable=False)
    trades = relationship('Trade', back_populates="user")
    initiatortrades = relationship('Trade', back_populates="initiator")
    joinertrades = relationship('Trade', back_populates="joiner")

class Trade(DictSerializableMixin):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True)

    initiator = relationship('User', back_populates="initiatortrades")
    joiner = relationship('User', back_populates="joinertrades")

    initiator_id = Column(ForeignKey('users.id'), index=True)
    joiner_id = Column(ForeignKey('users.id'), index=True)

    initiatorapp = relationship('App', back_populates="initiatortrades")
    joinerapp = relationship('App', back_populates="joinertrades")

    initiatorapp_id = Column(ForeignKey('apps.id'), index=True)
    joinerapp_id = Column(ForeignKey('apps.id'), index=True)

    initiated = Column(Date, default=datetime.datetime.utcnow)
    accepted = Column(Date, default=datetime.datetime.utcnow)
    success = Column(Date, default=datetime.datetime.utcnow)
    failure = Column(Date, default=datetime.datetime.utcnow)

class App(DictSerializableMixin):
    __tablename__ = 'apps'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    appidstring = Column(String(64), nullable=False)
    initiatortrades = relationship('Trade', back_populates="initiatorapp")
    joinertrades = relationship('Trade', back_populates="joinerapp")

class Reviews(DictSerializableMixin):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True)
