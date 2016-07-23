__author__ = 'Eleonor Bart'

from main import app
from flask import session, g, send_from_directory, request, jsonify, render_template, flash
import os
import pandas
from models import LifeData, db
from dateutil import parser
from helpers import login_required


@app.route('/life_data', methods=['GET'])
@login_required
def life_data():
    life_data_table = LifeData.query.all()

    return render_template('life_data.html', current_table=life_data_table)
