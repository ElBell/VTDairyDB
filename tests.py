__author__ = 'Eleonor Bart'
#NEVER RUN ON SERVER


import os
from main import app
from models import db, populate_db, LifeData
import unittest
import tempfile
from flask_security import current_user

class VTDairyDBTestCase(unittest.TestCase):

    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///unittest.db'
        app.config['TESTING'] = True
        self.app = app.test_client()
        with app.app_context():
            db.drop_all()
            db.create_all()
            populate_db()

    def tearDown(self):
        """
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])
        """

    def login(self, email, password):
        return self.app.post('/login', data=dict(
            email=email,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    """
    def test_login_logout(self):
        with app.app_context():
            self.login('eleonorc@vt.edu', 'dairy5')
            self.assertEqual(current_user.email, 'eleonorc@vt.edu')
            rv = self.logout()
            assert 'You were logged out' in rv.data
            rv = self.login('adminx', 'dairy5')
            assert 'Invalid username' in rv.data
            rv = self.login('eleonorc@vt.edu', 'defaultx')
            assert 'Invalid password' in rv.data
    """

    def test_upload(self):
        with open('data/lifeData.csv', 'rb') as life_data_file:
            raw_data = life_data_file.read()
        self.app.post('/uploads', data=dict(
            file=('data/lifeData.csv', raw_data)
            ), follow_redirects=True)
        currentTable = LifeData.query.all()
        self.assertTrue(currentTable)

if __name__ == '__main__':
    unittest.main()
