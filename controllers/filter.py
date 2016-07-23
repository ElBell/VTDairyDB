__author__ = 'Eleonor Bart'

from main import app
from flask import session, g, send_from_directory, request, jsonify, render_template, flash
import os
from werkzeug import secure_filename
import pandas
from models import LifeData, db, GrowthData, StatusData
from dateutil import parser
import datetime
from helpers import login_required


@app.route('/filter', methods=['GET', 'POST'])
@login_required
def filter():
    filtered_data = []
    if request.method == 'POST':
        file = request.files['file']
        if file:
            if request.form['type'] == 'life_data':
                filename = secure_filename(file.filename)
                full_filename = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(full_filename)
                data = pandas.read_csv(full_filename)
                data = data.dropna()
                fids = map(int, data['FID'])
                filtered_data = db.session.query(LifeData).filter(LifeData.fid.in_(fids)).all()
    return render_template('filter.html', filtered_data=filtered_data)
