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
from sqlalchemy import func

class GrowthSearchForm(Form):
    animal = StringField("Animal ID")
    #breed = SelectField("(optional) Breed:", choices=[('ho', 'HO'), ('je', 'JE'), ('hj', 'HJ'), ('hx', 'HX'), ('jx', 'JX')])
    #group = SelectField("Group", choices=[('24', '24'), ('27', '27')])
    date = SelectField("Weigh Day:")
    submit = SubmitField("Submit")

def generate_monthly_report(date):
    current_date = datetime.strptime(date, '%Y-%m-%d').date()
    db.session.query(GrowthData).first()
    last_date = db.session.query(GrowthData.date).filter(GrowthData.date < current_date).order_by('date desc').first()
    if last_date is None:
        last_date = current_date
    else:
        last_date = last_date[0]
    previous_data = {t.fid: t for t in db.session.query(GrowthData).filter_by(date=last_date).all()}
    birth_weights = {t.fid: t for t in db.session.query(LifeData).all()}
    current_data = db.session.query(GrowthData).filter_by(date=current_date).all()
    for animal in current_data:
        averages = GrowthData.query.filter_by(fid=animal.fid).first()
        if averages is None:
            averages = GrowthData(fid=int(animal.fid))
            db.session.add(averages)
        if animal.fid in previous_data:
            if type(animal.weight) is int or type(animal.weight) is float:
                if type(previous_data[animal.fid].weight) is int or type(previous_data[animal.fid].weight) is float:
                    changed_weight = float(animal.weight - previous_data[animal.fid].weight)
                    days_since_last_weigh = (animal.date - previous_data[animal.fid].date).days
                    averages.monthly_adg = changed_weight/days_since_last_weigh if days_since_last_weigh != 0 else None
                else:
                    averages.monthly_adg = None
            else:
                averages.monthly_adg = None

            if type(animal.height) is int or type(animal.height) is float:
                if type(previous_data[animal.fid].height) is int or type(previous_data[animal.fid].height) is float:
                    changed_height = float(animal.height - previous_data[animal.fid].height)
                    changed_height_in_mm = changed_height * 10
                    days_since_last_weigh = (animal.date - previous_data[animal.fid].date).days
                    averages.monthly_height_change = changed_height_in_mm/days_since_last_weigh if days_since_last_weigh != 0 else None
                else:
                    averages.monthly_height_change = None
            else:
                averages.monthly_height_change = None
        else:
            averages.monthly_adg = None
            averages.monthly_height_change = None

        if animal.fid in birth_weights:
            if type(animal.weight) is int or type(animal.weight) is float:
                if type(birth_weights[animal.fid].bwt) is int or type(birth_weights[animal.fid].bwt) is float:
                    lifetime_changed_weight = float(animal.weight - birth_weights[animal.fid].bwt)
                    averages.age = float((animal.date - birth_weights[animal.fid].dob).days)
                    averages.lifetime_adg = lifetime_changed_weight/averages.age if averages.age != 0 else None

    db.session.commit()

    total_data = db.session.query(GrowthData, LifeData).filter(GrowthData.date == date, GrowthData.fid == LifeData.fid).all()

    tables = (db.session.query(GrowthData, LifeData,
                               LifeData.breed.label('breed'),
                               GrowthData.location.label('location'),
                               func.avg(GrowthData.weight).label('average_weight'),
                               func.avg(GrowthData.height).label('average_height'),
                               func.avg(GrowthData.age).label('average_age'),
                               func.avg(GrowthData.lifetime_adg).label('average_lifetime_adg'),
                               func.avg(GrowthData.monthly_adg).label('average_monthly_adg'),
                               func.avg(GrowthData.monthly_height_change).label('average_monthly_height_change'),
                               func.count(GrowthData.fid).label('n'))
                               .filter(GrowthData.date == current_date,
                                       GrowthData.fid == LifeData.fid,))

    inside_data = {(t.breed, t.location): t for t in tables.group_by(LifeData.breed, GrowthData.location).all()}
    subtotal_breed = {t.breed: t for t in tables.group_by(LifeData.breed).all()}
    subtotal_location = {t.location: t for t in tables.group_by(GrowthData.location).all()}
    grand_total = tables.one()

    return total_data, inside_data, subtotal_breed, subtotal_location, grand_total


def generate_individual_report():
    for animal in db.session.query(LifeData, GrowthData).outerjoin(GrowthData, LifeData.fid == GrowthData.fid).order_by('date, life_data.fid desc').all():
        if animal[1] is not None:
            print animal[1].fid, animal[1].date


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
    #if request.method == 'POST':
    total_data = generate_individual_report()
    return render_template('growth_data_individual_reports.html', total_data=total_data)


@app.route('/total_growth_data', methods=['GET'])
def total_growth_data():
    #total_data = db.session.query(GrowthData, LifeData, StatusData).filter(GrowthData.fid == LifeData.fid == StatusData.fid).all()
    life_data_table = LifeData.query.all()
    growth_data_table = GrowthData.query.all()

    return render_template('total_growth_data.html', current_table=growth_data_table)


