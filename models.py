__author__ = 'Eleonor Bart'

from datetime import datetime, timedelta, date as date_type
from flask_security.utils import encrypt_password
import time
import re
import pandas
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
                       cast, func, Float, desc
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
    estimate = Column(Boolean())
    def __repr__(self):
        return "<LifeData(fid={fid},eid={eid},breed={breed},dob={dob},bwt={bwt},estimate={estimate})>".format(fid=self.fid, eid=self.eid, breed=self.breed, dob=self.dob, bwt=self.bwt, estimate=self.estimate)


class StatusData(Base):
    __tablename__ = 'birth_status_data'
    fid = Column(Integer())
    status = Column(String(20))
    status_date = Column(Date())


class GrowthDataAverages(Base):
    __tablename__ = 'growth_data_averages'
    fid = Column(Integer())
    most_recent_date = Column(Date())
    last_date = Column(Date())
    lifetime_adg = Column(Integer())
    monthly_adg = Column(Integer())
    age = Column(Integer())
    monthly_height_change = Column(Integer())
    def __repr__(self):
        return "<GrowthDataAverages(fid={fid},most_recent_date={most_recent_date},last_date={last_date},lifetime_adg={lifetime_adg},monthly_adg={monthly_adg},age={age},monthly_height_change={monthly_height_change})>".format(fid=self.fid, most_recent_date=self.most_recent_date, last_date=self.last_date, lifetime_adg=self.lifetime_adg, monthly_adg=self.monthly_adg, age=self.age, monthly_height_change=self.monthly_height_change)



class GrowthData(Base):
    __tablename__ = 'growth_data'
    fid = Column(Integer())
    date = Column(Date())
    location = Column(String(20))
    weight = Column(Integer())
    height = Column(Float())
    bcs = Column(Float())
    lifetime_adg = Column(Float())
    monthly_adg = Column(Float())
    age = Column(Integer())
    monthly_height_change = Column(Float())

    @staticmethod
    def new(fid, date, location, weight, height, bcs=None):
        life = LifeData.query.filter_by(fid=fid).first()
        birthdate = life.dob
        if isinstance(birthdate, pandas.Timestamp):
            birthdate = birthdate.to_datetime().date()
        if isinstance(date, pandas.Timestamp):
            date = date.to_datetime().date()
        elif isinstance(date, datetime):
            date = date.date()
        age = (date - birthdate).days
        life_bwt = life.bwt
        if life_bwt is None:
            if life.breed == 'HO':
                life_bwt = 90
            elif life.breed == 'JE':
                life_bwt = 55
            else:
                life_bwt = 80
        lifetime_adg = (weight - life_bwt) / age
        previous = GrowthData.query.filter_by(fid=fid).order_by(desc(GrowthData.date)).first()
        if previous is not None:
            previous_date = previous.date
            if isinstance(previous_date, datetime):
                previous_date = previous_date.date()
            if previous_date != date:
                monthly_adg = (weight - previous.weight) / (date - previous_date).days
            else:
                monthly_adg = None
            if previous.height is None or height is None:
                mhg = None
            else:
                if previous_date != date:
                    height_converted = 10 * (height - previous.height)
                    mhg = height_converted / (date - previous_date).days
                else:
                    mhg = None
        else:
            monthly_adg, mhg = None, None
        gd = GrowthData(fid=fid, date=date, location=location, weight=weight,
                        height=height, bcs=bcs, lifetime_adg=lifetime_adg,
                        monthly_adg=monthly_adg, age=age, monthly_height_change=mhg)
        return gd

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