import sys, os

from main import app
from flask_script import Manager, Server, Command, Option
from flask_security.utils import encrypt_password
from models import db
from main import app
import datetime
import random

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
        from models import Role, User

        print("Adding Admin")
        admin = User(first_name='Eleonor', last_name='Bart',
                     password=encrypt_password('dairy5'),
                     confirmed_at=datetime.datetime.now(),
                     active= True,
                     email='eleonorc@vt.edu')
        db.session.add(admin)
        db.session.flush()
        db.session.add(Role(name='admin', user_id=admin.id))

        print("Adding some students for color")
        for user in ('Dan Tilden', 'Anamary Leal', 'Cory Bart'):
            first, last = user.split()
            email = '{}{}@vt.edu'.format(first[0].lower(), last.lower())
            db.session.add(User(first_name=first, last_name=last, email=email))


        db.session.commit()
        print("Complete")


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

if __name__ == "__main__":
    manager.run()
