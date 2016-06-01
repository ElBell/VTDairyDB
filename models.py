__author__ = 'Eleonor Bart'

from datetime import datetime, timedelta
from flask_security.utils import encrypt_password
import time
import re
import os
import json
from pprint import pprint
import logging

from main import app

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from flask_security import UserMixin, RoleMixin, login_required
from sqlalchemy import event, Integer, Date, ForeignKey, Column, Table,\
                       String, Boolean, DateTime, Text, ForeignKeyConstraint,\
                       cast, func, Float
from sqlalchemy.ext.declarative import declared_attr

db = SQLAlchemy(app)
Model = db.Model
relationship = db.relationship
backref = db.backref


def ensure_dirs(path):
    try:
        os.makedirs(path)
    except OSError, e:
        if not os.path.isdir(path):
            app.logger.warning(e.args + (path, ) )


class Base(Model):
    __abstract__  = True
    def __repr__(self):
        return str(self)

    id = Column(Integer(), primary_key=True)
    date_created  = Column(DateTime, default=func.current_timestamp())
    date_modified = Column(DateTime, default=func.current_timestamp(),
                                     onupdate=func.current_timestamp())


class User(Base, UserMixin):
    # General user properties
    __tablename__ = 'user'
    first_name = Column(String(255))
    last_name = Column(String(255))
    email = Column(String(255))
    password = Column(String(255))
    active = Column(Boolean())
    confirmed_at = Column(DateTime())

    # Foreign key relationships
    roles = relationship("Role", backref='user', lazy='dynamic')

    def __str__(self):
        return '<User {} ({})>'.format(self.id, self.email)

    def name(self):
        return ' '.join((self.first_name, self.last_name))

    def is_admin(self):
        return 'admin' in {role.name.lower() for role in self.roles}

class Role(Base, RoleMixin):
    __tablename__ = 'role'
    name = Column(String(80))
    user_id = Column(Integer(), ForeignKey('user.id'))

    def __str__(self):
        return '<User {} is {}>'.format(self.user_id, self.name)

#Begin models for animal data ----------------------------------------------------------------------------
class LifeData(Base):
    __tablename__ = 'life_data'
    fid = Column(Integer())
    eid = Column(Integer())
    breed = Column(String(20))
    dob = Column(Date())
    bwt = Column(Integer())
    estimate = Boolean()


class StatusData(Base):
    __tablename__ = 'birth_status_data'
    fid = Column(Integer())
    status = Column(String(20))
    status_date = Column(Date())


class GrowthData(Base):
    __tablename__ = 'growth_data'
    fid = Column(Integer())
    date = Column(Date())
    location = Column(String(20))
    weight = Column(Integer())
    height = Column(Float())
    bcs = Column(Float())
    lifetime_adg = Column(Integer())
    monthly_adg = Column(Integer())
    age = Column(Integer())
    monthly_height_change = Column(Integer())


def populate_db():
    admin = User(first_name='Eleonor', last_name='Bart',
                 password=encrypt_password('dairy5'),
                 confirmed_at=datetime.now(),
                 active= True,
                 email='eleonorc@vt.edu')
    db.session.add(admin)
    db.session.flush()
    db.session.add(Role(name='admin', user_id=admin.id))

    for user in ('Dan Tilden', 'Anamary Leal', 'Cory Bart'):
        first, last = user.split()
        email = '{}{}@vt.edu'.format(first[0].lower(), last.lower())
        db.session.add(User(first_name=first, last_name=last, email=email))


    db.session.commit()