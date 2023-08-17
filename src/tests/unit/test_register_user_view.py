import unittest
import sys
import os
from flask import url_for
from flask_testing import TestCase
from flask_wtf.csrf import CSRFProtect
sys.path.append('../')
sys.path.append('./')


from app import app, db
from app.forms import LoginForm

SECRET_KEY = 'secret'

class TestRegisterUserView(TestCase):

    def create_app(self):
        app.config['TESTING'] = True
        return app
 
    def create_test_database_struture(self):
        # putting this assertion here to stop me from wiping the non-test database
        SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
        assert SQLALCHEMY_DATABASE_URI.split('/')[3].startswith('test') # Need to be certain you are dropping the testing database and not a production database...
        db.drop_all()
        db.create_all()

    def test_register_user(self):
        self.create_test_database_struture()
        self.csrf = CSRFProtect(app)
        form = LoginForm(username='testuser', email='test@example.com', password='testpass', password2='testpass')
        response = self.client.post(url_for('register'), data=form_data, follow_redirects=True)
        self.assertEqual(response.status_code, 302)
        self.assertIn(b'Congratulations, you are now a registered user!', response.data)

if __name__ == '__main__':
    unittest.main()