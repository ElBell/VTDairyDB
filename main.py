__author__ = 'Eleonor Bart'

import logging

from flask import render_template, url_for
import urllib

from flask import Flask

app = Flask(__name__)

app.config.from_object('config.TestingConfig')
    
import controllers