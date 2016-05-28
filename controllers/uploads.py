__author__ = 'Eleonor Bart'

from main import app
from flask import session, g, send_from_directory, request, jsonify, render_template, flash
import os
from werkzeug import secure_filename
import pandas
from models import LifeData, db
from dateutil import parser



@app.route('/uploads', methods=['GET', 'POST'])
def uploads():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            full_filename = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(full_filename)
            data = pandas.read_csv(full_filename)
            data = data.dropna()
            #Removes the first two rows of not data
            data = data.ix[4:]
            #Labels the columns as follows (so columns MUST BE IN THIS ORDER)
            data.columns = ['FID', 'EID', 'Breed', 'DOB']
            app.logger.info(data)
            flash("Your file was saved!")

            for index, row in data.iterrows():
                cow = LifeData(fid=row['FID'], eid=row['EID'], breed=row['Breed'], dob=parser.parse(row['DOB']))
                db.session.add(cow)
            #Add won't happen without commit
            db.session.commit()

    return render_template('uploads.html')

