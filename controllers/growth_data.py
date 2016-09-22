__author__ = 'Eleonor Bart'

from main import app
from flask import session, g, send_from_directory, request, jsonify, render_template, flash
import os
import pandas
from models import GrowthData, db, StatusData, LifeData, GrowthDataAverages
from dateutil import parser
from flask_wtf import Form
from wtforms import StringField, IntegerField, TextAreaField, SubmitField, RadioField, SelectField, validators, ValidationError
from datetime import date, datetime
from sqlalchemy import func, desc
from helpers import login_required


class GrowthSearchForm(Form):
    animal = StringField("Animal ID")
    #breed = SelectField("(optional) Breed:", choices=[('ho', 'HO'), ('je', 'JE'), ('hj', 'HJ'), ('hx', 'HX'), ('jx', 'JX')])
    #group = SelectField("Group", choices=[('24', '24'), ('27', '27')])
    date = SelectField("Weigh Day:")
    submit = SubmitField("Submit")


def generate_monthly_report(date):
    current_date = datetime.strptime(date, '%Y-%m-%d').date()
    last_date = db.session.query(GrowthData.date).filter(GrowthData.date < current_date).order_by('date desc').first()[0]
    previous_data = dict([(t.fid, t) for t in db.session.query(GrowthData).filter_by(date=last_date).all()])

    total_data = db.session.query(GrowthData, LifeData).filter(GrowthData.date == date, GrowthData.fid == LifeData.fid).all()

    tables = (db.session.query(GrowthData, LifeData,
                               LifeData.breed.label('breed'),
                               GrowthData.location.label('location'),
                               (func.avg(GrowthData.weight)*2.205).label('average_weight'),
                               (func.avg(GrowthData.height)*.394).label('average_height'),
                               (func.avg(GrowthData.age)).label('average_age'),
                               (func.avg(GrowthData.lifetime_adg)*2.205).label('average_lifetime_adg'),
                               (func.avg(GrowthData.monthly_adg)*2.205).label('average_monthly_adg'),
                               (func.avg(GrowthData.monthly_height_change)*.0394).label('average_monthly_height_change'),
                               func.count(GrowthData.fid).label('n'))
                               .filter(GrowthData.date == current_date,
                                       GrowthData.fid == LifeData.fid,
                                       GrowthData.location != '.'))

    inside_data = dict([((t.breed, t.location), t) for t in tables.group_by(LifeData.breed, GrowthData.location).all()])
    subtotal_breed = dict([(t.breed, t) for t in tables.group_by(LifeData.breed).all()])
    subtotal_location = dict([(t.location, t) for t in tables.group_by(GrowthData.location).all()])
    grand_total = tables.one()

    return total_data, inside_data, subtotal_breed, subtotal_location, grand_total


def generate_individual_report():
    #total_data = db.session.query(LifeData, GrowthDataAverages).outerjoin(GrowthDataAverages, LifeData.fid == GrowthData.fid).all()
    return total_data

@app.route('/growth_data_monthly_reports', methods=['GET', 'POST'])
@login_required
def growth_data_monthly_reports():
    available_dates = db.session.query(GrowthData.date).order_by("date desc").distinct()
    list_dates = [(date[0], date[0]) for date in available_dates]
    growth_search_form = GrowthSearchForm(request.form, date=request.form.get('date', list_dates[0][0]))
    growth_search_form.date.choices = list_dates
    total_data, inside_data, subtotal_breed, subtotal_location, grand_total = [], {}, {}, {}, None
    if request.method == 'POST':
        total_data, inside_data, subtotal_breed, subtotal_location, grand_total = generate_monthly_report(growth_search_form.date.data)
    return render_template('growth_data_monthly_reports.html', growth_search_form=growth_search_form, total_data=total_data,
                           inside_data=inside_data,
                           date = datetime.now().strftime("%m-%d-%Y"),
                           subtotal_breed=subtotal_breed, subtotal_location=subtotal_location, grand_total=grand_total)


@app.route('/growth_data_individual_reports', methods=['GET', 'POST'])
@login_required
def growth_data_individual_reports():
    fids = db.session.query(GrowthData.fid).distinct()
    total_data = [db.session.query(GrowthData).filter(GrowthData.fid == fid.fid).order_by(desc(GrowthData.date)).first()
                  for fid in fids]
    '''
    total_data = GrowthData.query(GrowthData.fid,
                                  GrowthData.date, GrowthData.lifetime_adg,
                                  GrowthData.monthly_adg, GrowthData.age,
                                  GrowthData.monthly_height_change).order_by("date desc").first()
    print total_data
    '''
    return render_template('growth_data_individual_reports.html', total_data=total_data)


