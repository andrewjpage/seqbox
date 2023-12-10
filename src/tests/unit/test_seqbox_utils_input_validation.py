import sys
from flask_testing import TestCase
import pandas as pd

sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')

from app import app, db
from scripts.utils.check import check_plate_ids

# Test methods that are standalone and dont need complex external libraries or inputs
class TestUtilsStandaloneInputValidation(TestCase):

    def create_app(self):
        app.config['TESTING'] = True
        return app
    
    def test_check_plate_ids(self):
        data = [{'elution_plate_id': 'plate1', 'submitter_plate_id': 'plate1'}, {'elution_plate_id': 'plate1', 'submitter_plate_id': 'plate1'}, {'elution_plate_id': 'plate1', 'submitter_plate_id': 'plate1'}]
        self.assertTrue(check_plate_ids(data, 'elution_plate_id'))
        self.assertTrue(check_plate_ids(data, 'submitter_plate_id'))
    
    # a warning should be triggered if there are
    def test_check_plate_ids_multiple(self):
        data = [{'elution_plate_id': 'plate1', 'submitter_plate_id': 'plate2'}, {'elution_plate_id': 'plate1', 'submitter_plate_id': 'plate3'}, {'elution_plate_id': 'plate4', 'submitter_plate_id': 'plate5'}]
        self.assertFalse(check_plate_ids(data, 'elution_plate_id'))
        self.assertFalse(check_plate_ids(data, 'submitter_plate_id'))
