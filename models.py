import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, String, Integer, Float, Boolean, Date
from sqlalchemy_utils import get_hybrid_properties
from sqlalchemy.dialects.mysql import DOUBLE


Base = declarative_base()
metadata = Base.metadata
