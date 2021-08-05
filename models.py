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
    reviews = relationship('Review', back_populates="user")
    googleid = Column(Integer, nullable=False)

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
    accepted = Column(Date, nullable=True)
    success = Column(Date, nullable=True)
    failure = Column(Date, nullable=True)

    def status(self):
        if self.failure:
            return "failure"
        elif self.success:
            return "success"
        elif self.accepted:
            return "accepted"
        else:
            return "initiated"

    def age(self):
        currDate = datetime.datetime.now()
        return (currDate.date() - self.initiated).days

    def canjoin(self):
        return not (self.success or self.failure or self.accepted)

class App(DictSerializableMixin):
    __tablename__ = 'apps'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    appidstring = Column(String(64), nullable=False)
    reviews = relationship('Review', back_populates="app")


class Review(DictSerializableMixin):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True)
    app_id = Column(ForeignKey('apps.id'), index=True)
    app = relationship('App', back_populates="reviews")
    reviewtext = Column(String(64), nullable=True)
    reviewrating = Column(Integer)

    user_id = Column(ForeignKey('users.id'), index=True)
    user = relationship('User', back_populates="reviews")
