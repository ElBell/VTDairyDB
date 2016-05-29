import sys, os

from main import app
from flask_script import Manager, Server, Command, Option
from flask_security.utils import encrypt_password
from models import db, populate_db, BirthStatusData, GrowthData
from main import app
import datetime
import random
from datetime import date, datetime

class ResetDB(Command):
    """Drops all tables and recreates them"""
    def run(self, **kwargs):
        db.drop_all()
        db.create_all()

class PopulateDB(Command):
    option_list = (
        Option('--file', '-f', dest='user_data_file', default='scripts/user_data.csv'),
    )

    """Fills in predefined data into DB"""
    def run(self, user_data_file, **kwargs):
        print("Complete")
        populate_db()
def parse_float(val):
    try:
        float(val)
        return float(val)
    except ValueError:
        if val in (".", ""):
            return None
        print(val)
        raise Exception

class ProcessGrowthData(Command):
    option_list = (
        Option('--file', '-f', dest='full_filename', default='data/growthData.xlsx'),
    )
    def run(self, full_filename):
        import pandas
        data = pandas.read_excel(full_filename)
        data = data.set_index('Index')
        birth_status_data, growth_data_old, growth_data_new = data.ix[:, :5], data.ix[:, 5:157], data.ix[:, 157:]
        # print(growth_data_old.index)

        for index, row in birth_status_data.iterrows():
            cow = BirthStatusData(fid=int(index), dob=row['Birthdate'], breed=row['Brd'], bwt=row['BWt'], status=row['Status'], status_date=None if pandas.isnull(row['Date']) else row['Date'])
            db.session.add(cow)
        db.session.commit()

        growth_data_old.columns = pandas.MultiIndex.from_tuples([(c[:-1], c[-1]) for c in growth_data_old.columns])
        for row_name, row in growth_data_old.iterrows():
            row = row.where((pandas.notnull(row)), None)
            for date_name, weight_data in row.unstack().iterrows():
                weight = weight_data['W'] if type(weight_data['W']) != pandas.tslib.NaTType else None
                date = weight_data['D'] if type(weight_data['D']) != pandas.tslib.NaTType else None
                location = weight_data['L'] if type(weight_data['L']) != pandas.tslib.NaTType else None
                height = weight_data['H'] if type(weight_data['H']) != pandas.tslib.NaTType else None
                # print(row_name, weight, date, location, height)
                measurement = GrowthData(fid=int(row_name), date=date, weight=weight, height=parse_float(height) if height is not None else height, location=location)
                db.session.add(measurement)
                # print("Adding weighing "+str(row_name)+", "+date_name+":", weight_data.get('D', date_name), weight_data['L'], weight_data['W'], weight_data['H'])
        db.session.commit()

        growth_data_new.columns = pandas.MultiIndex.from_tuples([(c[:-1], c[-1]) for c in growth_data_new.columns])
        for row_name, row in growth_data_new.iterrows():
            row = row.where((pandas.notnull(row)), None)
            for date_name, weight_data in row.unstack().iterrows():
                date = datetime.strptime(date_name, '%y%m%d').date()
                weight = weight_data['W'] if type(weight_data['W']) != pandas.tslib.NaTType else None
                location = weight_data['L'] if type(weight_data['L']) != pandas.tslib.NaTType else None
                bcs = weight_data['C']
                # print(type(bcs))
                height = weight_data['H'] if type(weight_data['H']) != pandas.tslib.NaTType else None
                #print(row_name, weight, date, location, height)
                measurement = GrowthData(fid=int(row_name), bcs=parse_float(bcs) if bcs is not None else bcs, location=location, date=date, weight=weight, height=parse_float(height) if height is not None else height)
                db.session.add(measurement)
                # print("Adding weighing "+str(row_name)+", "+date_name+":", weight_data['C'], weight_data.get('D', date_name), weight_data['L'], weight_data['W'], weight_data['H'])
        db.session.commit()


class DisplayDB(Command):
    def run(self, **kwargs):
        from sqlalchemy import MetaData
        from sqlalchemy_schemadisplay3 import create_schema_graph
        connection = app.config['SQLALCHEMY_DATABASE_URI']
        filename='dbschema.png'
        graph = create_schema_graph(metadata=MetaData(connection),
            show_datatypes=False, # The image would get nasty big if we'd show the datatypes
            show_indexes=False, # ditto for indexes
            rankdir='BT', # From left to right (instead of top to bottom)
            font='Helvetica',
            concentrate=False # Don't try to join the relation lines together
            )
        graph.write_png(filename) # write out the file

manager = Manager(app)

# Server commands context
#manager.add_command("secure", Server(ssl_context=context))

# Database Commands
manager.add_command("reset_db", ResetDB())
manager.add_command("populate_db", PopulateDB())
manager.add_command("display_db", DisplayDB())
manager.add_command("process_growth_data", ProcessGrowthData())

if __name__ == "__main__":
    manager.run()
