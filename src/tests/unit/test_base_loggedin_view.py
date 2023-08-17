import unittest
import sys
from flask import url_for
from flask_testing import TestCase
sys.path.append('../')
sys.path.append('./')

from app import app, db

class TestBaseLoggedinView(TestCase):

    def create_app(self):
        app.config['TESTING'] = True
        return app

    def log_user_in(self):
        # Create a mock user
        user = User(...) 
  
        # Log the user in  
        self.login_user(user) 
        return self


if __name__ == '__main__':
    unittest.main()