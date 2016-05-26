__author__ = 'Eleonor Bart'

import os
import json

try:
    with open('secrets.json', 'r') as secret_file:
        secrets = json.load(secret_file)

except IOError:
    print("No secrets file found. Using insecure defaults.")
    secrets = {}

class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    WTF_CSRF_ENABLED = True
    SITE_NAME = 'VTDairyDB'
    SYS_ADMINS = ['eleonorc@vt.edu']
    ROOT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
    STATIC_DIRECTORY = os.path.join(ROOT_DIRECTORY, 'static')
    UPLOAD_FOLDER = os.path.join(ROOT_DIRECTORY, 'uploads')

    #secret key for flask authentification
    SECRET_KEY = secrets.get('FLASK_SECRET_KEY', 'flask-secret-key')

    #config for GMAIL
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'eleonorc@vt.edu'
    DEFAULT_MAIL_SENDER = 'BlockPy Admin'

    SECURITY_CONFIRMABLE = True
    SECURITY_REGISTERABLE = True
    SECURITY_RECOVERABLE = True
    SECURITY_CHANGEABLE = True
    SECURITY_PASSWORD_HASH='bcrypt'
    SECURITY_PASSWORD_SALT=secrets.get('SECURITY_PASSWORD_SALT')
    SECURITY_DEFAULT_REMEMBER_ME = True

    SQLALCHEMY_TRACK_MODIFICATIONS = False

class ProductionConfig(Config):
    DEBUG = False
    PORT = 5000
    #SITE_ROOT_URL = 'kine.vbi.vt.edu'
    SQLALCHEMY_DATABASE_URI = 'mysql://compthink:runestone@127.0.0.1/blockpy'

class TestingConfig(Config):
    DEBUG = True
    PORT = 5000
    HOST = 'localhost'
    SITE_ROOT_URL = 'localhost:5000'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'