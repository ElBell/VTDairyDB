__author__ = 'Eleonor Bart'

from main import app
from flask import session, g, send_from_directory, request, jsonify, render_template, flash
import os
from werkzeug import secure_filename
import pandas
from models import LifeData, db, GrowthData, StatusData
from dateutil import parser
import datetime


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
                for index, row in data.iterrows():
                    life = LifeData.query.filter_by(fid=row['FID']).first()
                    if life is None:
                        print "adding to", row['FID']
                        life = LifeData(fid=row['FID'], eid=row['EID'], breed=row['Breed'], dob=row['DOB'], bwt=row['Birth Weight (kg)'], estimate=True if type(row['Est BW']) is unicode else False)
                        db.session.add(life)
                    else:
                        life.dob = row['DOB']
                        life.breed = row['Breed']
                        life.eid = row['EID']
                        life.bwt = row['Birth Weight (kg)']
                        life.estimate = True if type(row['Est BW']) is unicode else False
                    growth = GrowthData(fid=row['FID'], weight=row['Weight (kg)'], location=row['Group'], date=datetime.date.today(), height=row['Height (cm)'] if type(row['Height (cm)']) is float or type(row['Height (cm)']) is int else None)
                    db.session.add(growth)
                db.session.commit()
                app.logger.info(data)
                flash("Your file was saved!")

    return render_template('uploads.html')



