__author__ = 'Eleonor Bart'

from main import app

from flask import session, g, send_from_directory, request, jsonify, render_template

@app.route('/cow')
def hello_cow():
    return 'M<i>ooooo</i>'
