__author__ = 'Eleonor Bart'

from models import db, User, Role
from main import app

from flask_security import SQLAlchemyUserDatastore, Security
from flask_security.forms import ConfirmRegisterForm

from wtforms import StringField, validators

class ExtendedConfirmRegisterForm(ConfirmRegisterForm):
    first_name = StringField('First Name', [validators.DataRequired()])
    last_name = StringField('Last Name', [validators.DataRequired()])

# User registration, etc.
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore, confirm_register_form=ExtendedConfirmRegisterForm)