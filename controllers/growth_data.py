__author__ = 'Eleonor Bart'

from main import app
from flask import session, g, send_from_directory, request, jsonify, render_template, flash
import os
import pandas
from models import GrowthData, db, BirthStatusData
from dateutil import parser


@app.route('/growth_data', methods=['GET'])
def growth_data():
    growth_data_table = GrowthData.query.all()
    birth_status_data_table = BirthStatusData.query.all()
    # total_growth_data =
    return render_template('growth_data.html', current_table=growth_data_table)
