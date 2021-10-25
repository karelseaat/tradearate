import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, String, Integer, Boolean, Date
from sqlalchemy_utils import get_hybrid_properties


Base = declarative_base()
metadata = Base.metadata

class DictSerializableMixin(Base):
    __abstract__ = True

    def _asdict(self):
        """will return a query and its props in dict form"""
        result = {}

        for key in self.__mapper__.c.keys() + list(get_hybrid_properties(self).keys()):
            result[key] = getattr(self, key)
        return result

    def _asattrs(self, adict, afilter):
        """will return a query and its props as attrs ?"""
        for key, val in adict.items():
            if hasattr(self, key) and key in afilter:
                setattr(self, key, val)

class User(DictSerializableMixin):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    fullname = Column(String(64))
    picture = Column(String(256))
    email = Column(String(256))
    locale = Column(String(3))
    googleid = Column(String(256), nullable=False)

    def __init__(self, googleid):
        self.googleid = googleid

    def is_active(self):
        """user is alwais active"""
        return True

    def get_id(self):
        """it is needed for login functionality, yes it will return the id"""
        return self.googleid

    def is_authenticated(self):
        """yes"""
        return True

    def is_anonymous(self):
        """never"""
        return False

    def can_create_trade(self):
        """if your score is height enough you can, chine eat your heart out"""
        return (self.get_score() - len(self.all_pending()) * 10) >= 0

    def can_join_trade(self):
        """if your score is height enough you can, chine eat your heart out"""
        return (self.get_score() - len(self.all_pending()) * 10)  >= 0

    def all_trade_fails(self):
        """will give you all the trades that you failed"""
        joiners = [x for x in self.joinertrades if x.failure and x.joiner_reviewed ]
        initiators = [x for x in self.initiatortrades  if x.failure and x.initiator_reviewed ]
        return set(joiners + initiators)

    def all_trade_successes(self):
        """will give you all the trades that you you sucseeded"""
        return [x for x in set(self.initiatortrades + self.joinertrades) if x.success]

    def get_score(self):
        """will calculate you trade score based on you sucseeded and failed trades"""
        return (
            len(self.all_trade_successes())
            -
            (len(self.all_trade_fails())*10)
        )

    def all_pending(self):
        """will give you all your pending trades"""
        return [x for x in set(self.initiatortrades + self.joinertrades) if not x.success and not x.failure]


    def all_apps(self):
        return [x.initiatorapp for x in self.initiatortrades] + [x.joinerapp for x in self.joinertrades]

class Trade(DictSerializableMixin):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True)

    initiator_id = Column(ForeignKey('users.id'), index=True)
    joiner_id = Column(ForeignKey('users.id'), index=True)

    initiator = relationship(
        'User',
        backref='initiatortrades',
        foreign_keys='Trade.initiator_id'
    )

    joiner = relationship(
        'User',
        backref='joinertrades',
        foreign_keys='Trade.joiner_id'
    )

    initiatorapp_id = Column(ForeignKey('apps.id'), index=True)
    joinerapp_id = Column(ForeignKey('apps.id'), index=True)

    initiatorapp = relationship(
        'App',
        backref='initiatortrades',
        foreign_keys='Trade.initiatorapp_id'
    )

    joinerapp = relationship(
        'App',
        backref='joinertrades',
        foreign_keys='Trade.joinerapp_id'
    )

    initiatorlang = Column(String(4), default="unk")
    joinerlang = Column(String(4), default="unk")

    initiator_accepted = Column(Boolean, default=False)
    joiner_accepted = Column(Boolean, default=False)

    initiator_reviewed = Column(Boolean, default=False)
    joiner_reviewed = Column(Boolean, default=False)

    initiated = Column(Date, default=datetime.datetime.utcnow)
    accepted = Column(Date, nullable=True)
    success = Column(Date, nullable=True)
    failure = Column(Date, nullable=True)
    joined = Column(Date, nullable=True)

    timetotrade = 7

    def __init__(self, initiator=None, initiatorapp=None, initiatorlang=None):
        if initiator:
            self.initiator = initiator
        if initiatorapp:
            self.initiatorapp = initiatorapp
        if initiatorlang:
            self.initiatorlang = initiatorlang


    def status(self):
        """will return the status of a trade"""
        if self.failure:
            return "failure"
        elif self.success:
            return "success"
        elif self.joined:
            return "joined"
        elif self.accepted:
            return "accepted"
        else:
            return "initiated"

    def trade_days_left(self):
        """ will return the nr of days left for a trade, counted from the moment a trade was accepted"""
        if self.accepted:
            curr_date = (
                datetime.datetime.now()
                +
                datetime.timedelta(days=self.timetotrade)
            )
            return (curr_date.date() - self.accepted).days - self.timetotrade
        return self.timetotrade

    def age(self):
        """will return the age of a trade, since its initiation"""
        curr_date = datetime.datetime.now()
        return (curr_date.date() - self.initiated).days

    def accept_age(self):
        """the time that has passed since a trade was accepted"""
        if self.accepted:
            curr_date = datetime.datetime.now()
            return (curr_date.date() - self.accepted).days
        return 0


    def can_join(self, usergoogleid):
        """will give you a true if you can join a trade"""
        return not self.joiner and self.initiator.googleid is not usergoogleid

    def can_reject(self, usergoogleid):
        """will give a true if you can reject a trade"""
        if self.joiner and self.joiner.googleid is usergoogleid and self.joiner_accepted and not self.accepted:
            return True
        elif self.initiator and self.initiator.googleid is usergoogleid and self.initiator_accepted and not self.accepted:
            return True
        return False

    def can_accept(self, usergoogleid):
        """will give you a true if you can accept a trade"""
        return (self.joiner and self.initiator) and ((self.joiner.googleid is usergoogleid and not self.joiner_accepted) or (self.initiator.googleid is usergoogleid and not self.initiator_accepted and not self.accepted))

    def can_delete(self, usergoogleid):
        """will return true if a initiator of a trade can delete that trade"""
        return (self.initiator and self.initiator.googleid == usergoogleid) and not self.accepted

    def can_leave(self, usergoogleid):
        """will return true if a joiner of a trade can leave the trade"""
        return (self.joiner and self.joiner.googleid == usergoogleid) and not self.accepted

    def reject_user(self, usergoogleid):
        """will reject a trade, this trade, perhaps this can be done better, why need userid ?"""
        if self.initiator_accepted and self.initiator.googleid == usergoogleid:
            self.initiator_accepted = False
        if self.joiner_accepted and self.joiner.googleid == usergoogleid:
            self.joiner_accepted = False

    def accept_user(self, usergoogleid):
        """will accept a trade, this trade, perhaps this can be done better, why need userid ?"""
        if self.initiator.googleid == usergoogleid:
            self.initiator_accepted = True
        if self.joiner.googleid == usergoogleid:
            self.joiner_accepted = True

        if self.initiator_accepted and self.joiner_accepted:
            self.accepted = datetime.datetime.now().date()

    def all_apps_in_trade(self):
        """ get all apps in a trade, that are at most two appps"""
        allapps = [self.initiatorapp, self.joinerapp]
        return [x for x in allapps if x]

    def all_users_in_trade(self):
        """get all users in a trade, at most two users"""
        allusers = [self.initiator, self.joiner]
        return [x for x in allusers if x]

class App(DictSerializableMixin):
    __tablename__ = 'apps'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    appidstring = Column(String(64), nullable=False)
    continuation_token = Column(String(512))
    reviews = relationship('Review', back_populates="app")
    paid = Column(Boolean, default=False)
    imageurl = Column(String(256))

    def __init__(self, name, idstring):
        self.name = name
        self.appidstring = idstring

    def get_url(self):
        return "https://play.google.com/store/apps/details?id=" + self.appidstring

    def all_trades(self):
        return  self.initiatortrades + self.joinertrades

    def all_users(self):
        prelist = [x.initiator for x in self.all_trades()] + [x.joiner for x in self.all_trades()]
        return [x for x in prelist if x]


class Review(DictSerializableMixin):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True)
    google_id = Column(String(128), nullable=True)
    reviewtime = Column(Date, nullable=True)
    app_id = Column(ForeignKey('apps.id'), index=True)
    app = relationship('App', back_populates="reviews")
    locale = Column(String(3))
    reviewtext = Column(String(4096), nullable=True)
    reviewrating = Column(Integer)
    reviewappversion = Column(String(16), nullable=True)
    username = Column(String(64), nullable=True)

    minreviewlength = 50

class Historic(DictSerializableMixin):
    __tablename__ = 'historic'
    id = Column(Integer, primary_key=True)
    infotype = Column(Integer)
    date = Column(Date, default=datetime.datetime.utcnow)
    number = Column(Integer)
