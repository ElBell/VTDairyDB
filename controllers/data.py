__author__ = 'Eleonor Bart'

from main import app
from flask import session, g, send_from_directory, request, jsonify, render_template, flash
import os
import pandas
from models import LifeData, db
from dateutil import parser


@app.route('/data', methods=['GET'])
def data():
    life_data_table = LifeData.query.all()

    return render_template('data.html', current_table=life_data_table)
