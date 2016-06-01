import sys, os

from main import app
from flask_script import Manager, Server, Command, Option
from flask_security.utils import encrypt_password
from models import db, populate_db, StatusData, GrowthData, LifeData
from main import app
import random
from datetime import date, datetime
import pandas
from tqdm import tqdm
from dateutil import parser


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

class ProcessLifeData(Command):
    option_list = (
        Option('--file', '-f', dest='full_filename', default='data/lifeData.csv'),
    )
    def run(self, full_filename):
        data = pandas.read_csv(full_filename)
        data = data.dropna()
        # Removes the first two rows of not data
        data = data.ix[4:]
        # Labels the columns as follows (so columns MUST BE IN THIS ORDER)
        data.columns = ['FID', 'EID', 'Breed', 'DOB']
        #app.logger.info(data)

        for index, row in data.iterrows():
            life = LifeData.query.filter_by(fid=row['FID']).first()
            if life is None:
                life = LifeData(fid=row['FID'], eid=row['EID'], breed=row['Breed'], dob=parser.parse(row['DOB']))
                db.session.add(life)
            else:
                life.dob=parser.parse(row['DOB'])
                life.breed=row['Breed']
                life.eid=row['EID']
        # Add won't happen without commit
        db.session.commit()

class ProcessGrowthData(Command):
    option_list = (
        Option('--file', '-f', dest='full_filename', default='data/growthData.xlsx'),
    )
    def run(self, full_filename):
        data = pandas.read_excel(full_filename)
        data = data.set_index('Index')
        status_data, growth_data_old, growth_data_new = data.ix[:, :6], data.ix[:, 6:158], data.ix[:, 158:]
        # print(growth_data_old.index)

        for index, row in tqdm(status_data.iterrows()):
            status = StatusData(fid=int(index), status=row['Status'], status_date=None if pandas.isnull(row['Date']) else row['Date'])
            db.session.add(status)
            life = LifeData.query.filter_by(fid=int(index)).first()
            if life is None:
                life = LifeData(fid=int(index), bwt=row['BWt'], dob=row['Birthdate'], breed=row['Brd'], estimate=True if type(row['Estimate']) is unicode else False)
                db.session.add(life)
            else:
                life.bwt = row['BWt']
                life.dob = row['Birthdate']
                life.breed = row['Brd']
                life.estimate = True if type(row['Estimate']) is unicode else False

        db.session.commit()

        growth_data_old.columns = pandas.MultiIndex.from_tuples([(c[:-1], c[-1]) for c in growth_data_old.columns])
        for row_name, row in tqdm(growth_data_old.iterrows()):
            row = row.where((pandas.notnull(row)), None)
            for date_name, weight_data in row.unstack().iterrows():
                weight = weight_data['W'] if type(weight_data['W']) != pandas.tslib.NaTType else None
                date = weight_data['D'] if type(weight_data['D']) != pandas.tslib.NaTType else None
                location = weight_data['L'] if type(weight_data['L']) != pandas.tslib.NaTType else None
                height = weight_data['H'] if type(weight_data['H']) != pandas.tslib.NaTType else None
                # print(row_name, weight, date, location, height)
                if weight is None:
                    continue

                measurement = GrowthData(fid=int(row_name), date=date, weight=weight, height=parse_float(height) if height is not None else height, location=location)
                db.session.add(measurement)
                # print("Adding weighing "+str(row_name)+", "+date_name+":", weight_data.get('D', date_name), weight_data['L'], weight_data['W'], weight_data['H'])
        db.session.commit()

        growth_data_new.columns = pandas.MultiIndex.from_tuples([(c[:-1], c[-1]) for c in growth_data_new.columns])
        for row_name, row in tqdm(growth_data_new.iterrows()):
            row = row.where((pandas.notnull(row)), None)
            for date_name, weight_data in row.unstack().iterrows():
                date = datetime.strptime(date_name, '%y%m%d').date()
                weight = weight_data['W'] if type(weight_data['W']) != pandas.tslib.NaTType else None
                location = weight_data['L'] if type(weight_data['L']) != pandas.tslib.NaTType else None
                bcs = weight_data['C']
                # print(type(bcs))
                height = weight_data['H'] if type(weight_data['H']) != pandas.tslib.NaTType else None
                #print(row_name, weight, date, location, height)
                if weight is None:
                    continue
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
            show_datatypes=False,  # The image would get nasty big if we'd show the datatypes
            show_indexes=False,  # ditto for indexes
            rankdir='BT',  # From left to right (instead of top to bottom)
            font='Helvetica',
            concentrate=False  # Don't try to join the relation lines together
            )
        graph.write_png(filename)  # write out the file

manager = Manager(app)

# Server commands context
#manager.add_command("secure", Server(ssl_context=context))

# Database Commands
manager.add_command("reset_db", ResetDB())
manager.add_command("populate_db", PopulateDB())
manager.add_command("display_db", DisplayDB())
manager.add_command("process_growth_data", ProcessGrowthData())
manager.add_command("process_life_data", ProcessLifeData())

if __name__ == "__main__":
    manager.run()
