__author__ = 'Eleonor Bart'

from main import app
from flask import session, g, send_from_directory, request, jsonify, render_template
from flask import url_for, redirect


@app.route('/')
def homepage():
    return render_template('homepage.html')


@app.route("/site-map", methods=['GET', 'POST'])
def site_map():
    import urllib
    output = []
    for rule in app.url_map.iter_rules():

        options = {}
        for arg in rule.arguments:
            options[arg] = "[{0}]".format(arg)

        methods = ','.join(rule.methods)
        try:
            url = url_for(rule.endpoint, **options)
        except:
            url = "Unknown error"
        line = urllib.unquote("<td>{:50s}</td><td>{:20s}</td><td>{}</td>".format(rule.endpoint, methods, url))
        output.append(line)
    return "<table><tr>{}</tr></table>".format("</tr><tr>".join(sorted(output)))


#
from admin import admin
import security

import cow
import uploads
import data

