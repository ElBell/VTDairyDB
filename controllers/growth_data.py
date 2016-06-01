__author__ = 'Eleonor Bart'

from main import app
from flask import session, g, send_from_directory, request, jsonify, render_template, flash
import os
import pandas
from models import GrowthData, db, StatusData, LifeData
from dateutil import parser
from flask_wtf import Form
from wtforms import StringField, IntegerField, TextAreaField, SubmitField, RadioField, SelectField, validators, ValidationError
from datetime import date, datetime
from sqlalchemy import func

class GrowthSearchForm(Form):
    animal = StringField("Animal ID")
    #breed = SelectField("(optional) Breed:", choices=[('ho', 'HO'), ('je', 'JE'), ('hj', 'HJ'), ('hx', 'HX'), ('jx', 'JX')])
    #group = SelectField("Group", choices=[('24', '24'), ('27', '27')])
    date = SelectField("Weigh Day:")
    submit = SubmitField("Submit")

def generate_monthly_report(date):
    date = datetime.strptime(date, '%Y-%m-%d').date()
    total_data = db.session.query(GrowthData, LifeData).filter(GrowthData.date == date, GrowthData.fid == LifeData.fid).all()

    tables = (db.session.query(GrowthData, LifeData,
                               LifeData.breed.label('breed'),
                               GrowthData.location.label('location'),
                               func.avg(GrowthData.weight).label('average_weight'),
                               func.avg(GrowthData.height).label('average_height'),
                               func.count(GrowthData.fid).label('n'),
                               func.avg(GrowthData.date - LifeData.dob).label('average_age'))
                               .filter(GrowthData.date == date,
                                       GrowthData.fid == LifeData.fid))
    inside_data = {(t.breed, t.location): t for t in tables.group_by(LifeData.breed, GrowthData.location).all()}
    subtotal_breed = {t.breed: t for t in tables.group_by(LifeData.breed).all()}
    subtotal_location = {t.location: t for t in tables.group_by(GrowthData.location).all()}
    grand_total = tables.one()

    return total_data, inside_data, subtotal_breed, subtotal_location, grand_total



@app.route('/growth_data_monthly_reports', methods=['GET', 'POST'])
def growth_data_monthly_reports():
    available_dates = db.session.query(GrowthData.date).order_by("date desc").distinct()
    list_dates = [(date[0], date[0]) for date in available_dates]
    growth_search_form = GrowthSearchForm(request.form, date=request.form.get('date', list_dates[0][0]))
    growth_search_form.date.choices = list_dates
    #print growth_search_form.date.data
    total_data, inside_data, subtotal_breed, subtotal_location, grand_total = [], {}, {}, {}, None
    if request.method == 'POST':
        total_data, inside_data, subtotal_breed, subtotal_location, grand_total = generate_monthly_report(growth_search_form.date.data)
    return render_template('growth_data_monthly_reports.html', growth_search_form=growth_search_form, total_data=total_data,
                           inside_data=inside_data,
                           subtotal_breed=subtotal_breed, subtotal_location=subtotal_location, grand_total=grand_total)


@app.route('/growth_data_individual_reports', methods=['GET', 'POST'])
def growth_data_individual_reports():
    return render_template('growth_data_individual_reports.html')


@app.route('/total_growth_data', methods=['GET'])
def total_growth_data():
    total_data = db.session.query(GrowthData, LifeData, StatusData).filter(GrowthData.fid == LifeData.fid == StatusData.fid).all()

    return render_template('total_growth_data.html', current_table=total_data)


