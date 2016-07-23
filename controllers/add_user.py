__author__ = 'Eleonor Bart'

from main import app
import datetime
from flask import session, g, send_from_directory, request, jsonify, render_template, flash
import os
import pandas
from models import LifeData, db, User, Role
from dateutil import parser
from helpers import login_required, admin_required
from wtforms import Form, BooleanField, StringField, PasswordField, validators


class AddUserForm(Form):
    first_name = StringField('First Name')
    last_name = StringField('Last Name')
    email = StringField('Email Address')
    password = PasswordField('New Password')
    admin = BooleanField('Admin?')

@app.route('/add_user', methods=['GET', "POST"])
@admin_required
def add_user():
    form = AddUserForm(request.form)
    if request.method == "POST":
        user = User(first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    email=form.email.data,
                    active=True,
                    confirmed_at = datetime.datetime.now(),
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        if form.admin.data:
            role = Role(name='admin', user_id=user.id)
            db.session.add(role)
            db.session.commit()
        flash('Added new user: '+form.first_name.data)
    return render_template('add_user.html', form=form)