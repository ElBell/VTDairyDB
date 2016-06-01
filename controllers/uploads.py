__author__ = 'Eleonor Bart'

from main import app
from flask import session, g, send_from_directory, request, jsonify, render_template, flash
import os
from werkzeug import secure_filename
import pandas
from models import LifeData, db, GrowthData, StatusData
from dateutil import parser


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
                birth_status_data, growth_data = data.ix[:, :5], data.ix[:, :1] + data.ix[:, 5:]
                data = data.set_index('Index')
                for index, row in birth_status_data.iterrows():
                    cow = BirthStatusData(fid=row['Index'], dob=row['Birthdate'], breed=row['Brd'], bwt=row['BWt'], status=row['Status'], status_date=row['Date'])
                    db.session.add(cow)
                data.columns = pandas.MultiIndex.from_tuples([(c[:-1], c[-1]) for c in data.columns])
                print(growth_data.head())
                for row_name, row in growth_data.iterrows():
                    print(row)
                    for date_name, weight_data in row.unstack().iterrows():
                        print("Adding weighing "+str(row_name)+", "+date_name+":", weight_data.get('D', date_name), weight_data['L'], weight_data['W'], weight_data['H'])
                app.logger.info(data)

    return render_template('uploads.html')

