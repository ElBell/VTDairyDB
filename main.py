__author__ = 'Eleonor Bart'

from flask_security.core import current_user
import logging
from flask import render_template, url_for
import urllib
from flask import session, g, send_from_directory, request, jsonify, render_template
from flask import Flask
from logging import FileHandler

app = Flask(__name__)

app.config.from_object('config.TestingConfig')

from natsort import natsorted, ns
app.jinja_env.filters['natsorted'] = natsorted
BREED_VALUE = {'HO': 1, 'JE': 2, 'HJ': 3, 'HX': 4, 'JX': 5}
def breed_sort(a_list):
    return sorted(a_list, key=lambda x: BREED_VALUE.get(x, 6))
app.jinja_env.filters['breed_sort'] = breed_sort

file_handler = FileHandler('logs/run.log')
file_handler.setLevel(logging.DEBUG)
app.logger.addHandler(file_handler)

@app.before_request
def load_user():
    if current_user.is_authenticated:
        g.user = current_user
    else:
        g.user = None

import controllers