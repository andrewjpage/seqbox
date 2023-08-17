import sys
from flask_testing import TestCase
import pandas as pd

sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')

from app import app, db
from seqbox_utils import check_plate_ids

# Test methods that are standalone and dont need complex external libraries or inputs
class TestUtilsStandaloneInputValidation(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app
    
    def test_check_plate_ids(self):
        with self.assertWarns(None) as cm:
            # Run the code here
            data = [{'elution_plate_id': 'plate1', 'submitter_plate_id': 'plate1'}, {'elution_plate_id': 'plate1', 'submitter_plate_id': 'plate1'}, {'elution_plate_id': 'plate1', 'submitter_plate_id': 'plate1'}]
            check_plate_ids(data, 'elution_plate_id')
            check_plate_ids(data, 'submitter_plate_id')
        self.assertEqual(len(cm.warnings), 0)
    
    # a warning should be triggered if there are
    def test_check_plate_ids_multiple(self):
        data = [{'elution_plate_id': 'plate1', 'submitter_plate_id': 'plate2'}, {'elution_plate_id': 'plate1', 'submitter_plate_id': 'plate3'}, {'elution_plate_id': 'plate4', 'submitter_plate_id': 'plate5'}]
        with self.assertWarns(UserWarning):
            check_plate_ids(data, 'elution_plate_id')
            check_plate_ids(data, 'submitter_plate_id')