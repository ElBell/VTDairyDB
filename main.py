__author__ = 'Eleonor Bart'

import logging

from flask import render_template

from flask import Flask

app = Flask(__name__)

app.config.from_object('config.TestingConfig')

import controllers

@app.route('/')
def homepage():
    return render_template('homepage.html')

if __name__ == '__main__':
    app.run(debug=True)
