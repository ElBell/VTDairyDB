__author__ = 'Eleonor Bart'

from main import app
from flask import session, g, send_from_directory, request, jsonify, render_template, flash
import os
from werkzeug import secure_filename
import pandas



@app.route('/upload', methods=['GET', 'POST'])
def uploads():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            full_filename = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(full_filename)
            data = pandas.read_csv(full_filename)
            data.dropna()
            flash("Your file was saved!")
    return render_template('uploads.html')

