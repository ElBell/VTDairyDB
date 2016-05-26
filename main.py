__author__ = 'Eleonor Bart'

from flask_security.core import current_user
import logging
from flask import render_template, url_for
import urllib
from flask import session, g, send_from_directory, request, jsonify, render_template
from flask import Flask

app = Flask(__name__)

app.config.from_object('config.TestingConfig')


@app.before_request
def load_user():
    if current_user.is_authenticated:
        g.user = current_user
    else:
        g.user = None

import controllers