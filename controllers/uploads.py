__author__ = 'Eleonor Bart'

from main import app
from flask import session, g, send_from_directory, request, jsonify, render_template, flash
import os
from werkzeug import secure_filename
import pandas
from models import LifeData, db, GrowthData, StatusData, GrowthDataAverages
from dateutil import parser
import datetime
from sqlalchemy import desc
import numpy as np


def calculate_growth_averages(date):
    fids = db.session.query(GrowthData).filter_by(date=date).all()
    for fid in fids:
        fid_data = db.session.query(GrowthData).filter(GrowthData.fid == fid.fid).order_by(desc(GrowthData.date)).all()
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


@app.route('/uploads', methods=['GET', 'POST'])
def uploads():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            if request.form['type'] == 'life_data':
                filename = secure_filename(file.filename)
                full_filename = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(full_filename)
                data = pandas.read_csv(full_filename)
                data = data.dropna()
                # Removes the first two rows of not data
                data = data.ix[4:]
                # Labels the columns as follows (so columns MUST BE IN THIS ORDER)
                data.columns = ['FID', 'EID', 'Breed', 'DOB']
                app.logger.info(data)
                flash("Your file was saved!")

                for index, row in data.iterrows():
                    cow = LifeData(fid=row['FID'], eid=row['EID'], breed=row['Breed'], dob=parser.parse(row['DOB']))
                    db.session.add(cow)
                # Add won't happen without commit
                db.session.commit()

            elif request.form['type'] == 'growth_data':
                filename = secure_filename(file.filename)
                full_filename = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(full_filename)
                data = pandas.read_excel(full_filename)
                date_list = []
                everything = set()
                for index, row in data.iterrows():
                    life = LifeData.query.filter_by(fid=row['FID']).first()
                    if life is None:
                        life = LifeData(fid=row['FID'], eid=row['EID'], breed=row['Breed'], dob=row['DOB'], bwt=row['Birth Weight (kg)'], estimate=True if type(row['Est BW']) is unicode else False)
                        db.session.add(life)
                    else:
                        life.dob = row['DOB']
                        life.breed = row['Breed']
                        life.eid = row['EID']
                        life.bwt = row['Birth Weight (kg)']
                        life.estimate = True if type(row['Est BW']) is unicode else False
                    everything.add(life.bwt)
                    if life.bwt is None or np.isnan(life.bwt):
                        print life.breed
                        if life.breed == "JE":
                            life.bwt = 24.94758035
                            life.estimate = True
                        elif life.breed == "HO":
                            life.bwt = 40.8233133
                            life.estimate = True
                        else:
                            life.bwt = 10
                            life.estimate = True
                    growth = GrowthData(fid=row['FID'], weight=row['Weight (kg)'], location=row['Group'], date=row['Date'], height=row['Height (cm)'] if type(row['Height (cm)']) is float or type(row['Height (cm)']) is int else None)
                    db.session.add(growth)
                    date = row['Date']
                    if date not in date_list:
                        date_list.append(date)
                db.session.commit()
                print(everything)
                #app.logger.info(data)
                flash("Your file was saved! Please be patient while ADGs are calculated")

                for date in date_list:
                    calculate_growth_averages(date)

                flash("All done!")



    return render_template('uploads.html')



