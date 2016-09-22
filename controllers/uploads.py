__author__ = 'Eleonor Bart'

from main import app
from flask import session, g, send_from_directory, request, jsonify, render_template, flash
import os
from werkzeug import secure_filename
import pandas
from models import LifeData, db, GrowthData, StatusData, GrowthDataAverages, set_estimated_life_data

from dateutil import parser
import datetime
from sqlalchemy import desc
import numpy as np
from helpers import login_required


def calculate_growth_averages(date):
    fids = db.session.query(GrowthData).filter_by(date=date).all()
    for fid in fids:
        fid_data = db.session.query(GrowthData).filter(GrowthData.fid == fid.fid,
                                                       GrowthData.date >= date).order_by(desc(GrowthData.date)).all()
        today = fid_data[0]
        growth_averages = GrowthDataAverages.query.filter_by(fid=int(fid.fid)).first()
        life_data = LifeData.query.filter_by(fid=int(fid.fid)).first()
        if len(fid_data) > 1:
            previous = fid_data[1]
            time_dif = today.date - previous.date
            time_dif = time_dif.days
            if today.weight is not None and previous.weight is not None:
                monthly_weight_dif = float(today.weight - previous.weight)
            else:
                monthly_weight_dif = None
            if time_dif is not 0:
                if monthly_weight_dif is not 0 and monthly_weight_dif is not None:
                    monthly_adg = float(monthly_weight_dif/time_dif)
                else:
                    monthly_adg = None
            else:
                monthly_adg = None
            if previous.height is not None and today.height is not None and time_dif is not 0:
                monthly_height_dif = float(today.height - previous.height)
                monthly_height_change = float(monthly_height_dif/time_dif)
            else:
                monthly_height_change = None
            if today.date is not None and life_data.dob is not None:
                age = today.date - life_data.dob
                age = age.days
            else:
                age = None
            if today.weight is not None and life_data.bwt is not None:
                lifetime_weight_dif = float(today.weight - life_data.bwt)
                lifetime_adg = float(lifetime_weight_dif/age)
            else:
                lifetime_adg = None
            if growth_averages is None:
                growth_averages = GrowthDataAverages(fid=int(fid.fid), most_recent_date=today.date, monthly_adg=monthly_adg, age=age, lifetime_adg=lifetime_adg, monthly_height_change=monthly_height_change)
                db.session.add(growth_averages)
            else:
                growth_averages.most_recent_date = today.date
                growth_averages.monthly_adg = monthly_adg
                growth_averages.age = age
                growth_averages.lifetime_adg = lifetime_adg
                growth_averages.monthly_height_change = monthly_height_change
        else:
            time_dif = 0
    db.session.commit()


def read_pandas_file(filename):
    if filename.endswith('.csv'):
        data = pandas.read_csv(filename)
    elif filename.endswith('.xlsx'):
        data = pandas.read_excel(filename)
    else:
        raise Exception("Unknown filetype")
    return data


@app.route('/uploads', methods=['GET', 'POST'])
@login_required
def uploads():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            if request.form['type'] == 'life_data':
                filename = secure_filename(file.filename)
                full_filename = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(full_filename)
                data = read_pandas_file(full_filename)

                flash("Your file was saved!")
                for index, row in data.iterrows():
                    if 'FID' in data:
                        life = LifeData.query.filter_by(fid=row['FID']).first()
                    if 'Index' in data:
                        life = LifeData.query.filter_by(fid=row['Index']).first()
                    # life = LifeData.query.filter_by(fid=row['FID']).first()
                    if life is None:
                        breed = row.get('Breed', 'Unknown')
                        eid = row.get('EID', None)
                        bwt = row.get('Birth Weight', None)
                        estimate = bwt is None
                        dob = row.get('DOB', None)
                        if dob is not None:
                            if isinstance(dob, pandas.Timestamp):
                                dob = dob.to_datetime().date()
                            else:
                                dob = datetime.datetime.strptime(dob, '%m/%d/%Y').date()
                        if 'FID' in data:
                            fid=row['FID']
                        if 'Index' in data:
                            fid=row['Index']
                        life = LifeData(fid=fid, eid=eid, breed=breed, dob=dob, bwt=bwt, estimate=estimate)

                        db.session.add(life)

                    else:
                        if 'DOB' in data:
                            dob = row['DOB']
                            if isinstance(dob, pandas.Timestamp):
                                dob = dob.to_datetime().date()
                            else:
                                dob = datetime.datetime.strptime(dob, '%m/%d/%Y').date()
                            life.dob = dob
                        if 'Breed' in data:
                            life.breed = row['Breed']
                        if 'EID' in data:
                            life.eid = row['EID']
                        if 'Birth Weight' in data:
                            life.bwt = row['Birth Weight']
                        if 'Est BW' in data:
                            life.estimate = True if type(row['Est BW']) is unicode else False
                    if life.bwt is None or np.isnan(life.bwt) or life.estimate:
                        if life.breed == "JE":
                            life.bwt = 24.94758035
                            life.estimate = True
                        elif life.breed == "HO":
                            life.bwt = 40.8233133
                            life.estimate = True
                        else:
                            life.bwt = 30
                            life.estimate = True
                        # Add won't happen without commit
                db.session.commit()

            elif request.form['type'] == 'growth_data':
                filename = secure_filename(file.filename)
                full_filename = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(full_filename)
                if full_filename.endswith('.xlsx'):
                    data = pandas.read_excel(full_filename)
                if full_filename.endswith('.csv'):
                    data = pandas.read_csv(full_filename)
                date_list = []
                everything = set()
                for index, row in data.iterrows():
                    if 'FID' in data:
                        life = LifeData.query.filter_by(fid=row['FID']).first()
                    if 'Index' in data:
                        life = LifeData.query.filter_by(fid=row['Index']).first()
                    if life is None:
                        eid = None
                        dob = None
                        breed = 'Unknown'
                        bwt = None
                        estimate = True
                        if "Breed" in row:
                            breed = row['Breed']
                        if 'Birth Weight' in data:
                            bwt = row['Birth Weight']
                            estimate = False
                        if 'EID' in data:
                            eid = row['EID']
                        if 'DOB' in data:
                            dob = parse_date(row['DOB'])
                        life = LifeData(fid=row['FID'], eid=eid, breed=breed, dob=dob, bwt=bwt, estimate=estimate)

                        db.session.add(life)
                    else:
                        if 'DOB' in data:
                            dob = parse_date(row['DOB'])
                            life.dob = dob
                        if 'Breed' in data:
                            life.breed = row['Breed']
                        if 'EID' in data:
                            life.eid = row['EID']
                        if 'Birth Weight' in data:
                            life.bwt = row['Birth Weight']
                        if 'Est BW' in data:
                            life.estimate = True if type(row['Est BW']) is unicode else False
                    # SHOULD THIS BE HERE??????????????????????????????????????????????????????????????????????????????
                    set_estimated_life_data(life)

                    weight = None
                    location = None
                    date = None
                    height = None
                    if 'Weight' in data:
                        weight = parse_float_field(row['Weight'])
                    if 'Group' in data:
                        location = row['Group']
                    if 'Date' in data:
                        date = parse_date(row['Date'])
                    if 'Height' in data:
                        #height = row['Height'] if type(row['Height']) is float or type(row['Height']) is int else None
                        height = parse_float_field(row['Height'])
                    growth = GrowthData.new(fid=row['FID'], weight=weight, location=location, date=date, height=height)
                    db.session.add(growth)
                    date = None
                    if 'Date' in data:
                        date = row['Date']
                    if date not in date_list:
                        date_list.append(date)
                db.session.commit()
                #app.logger.info(data)
                flash("Your file was saved! Please be patient while ADGs are calculated")

                #for date in date_list:
                #    calculate_growth_averages(date)

                flash("All done!")



    return render_template('uploads.html')


def parse_date(date):
    if isinstance(date, pandas.Timestamp):
        return date.to_datetime().date()
    else:
        return datetime.datetime.strptime(date, '%m/%d/%Y')


def parse_float_field(a_value):
    try:
        float(a_value)
    except ValueError:
        return None
    return float(a_value)

