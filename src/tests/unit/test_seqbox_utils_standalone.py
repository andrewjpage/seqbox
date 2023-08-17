import sys
from flask_testing import TestCase
import datetime
import pandas as pd

sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')

from app import app, db
from seqbox_utils import replace_with_none, convert_to_datetime_dict, convert_to_datetime_df, check_plate_ids

# Test methods that are standalone and dont need complex external libraries or inputs
class TestUtilsStandalone(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app
    
    def test_replace_with_none(self):
        # Test that empty strings are replaced with None
        test_dict = {'a': '', 'b': 'foo', 'c': ''}
        expected_dict = {'a': None, 'b': 'foo', 'c': None}
        self.assertEqual(replace_with_none(test_dict), expected_dict)
        
        # Test that non-empty strings are not replaced
        test_dict = {'a': 'bar', 'b': 'baz'}
        expected_dict = {'a': 'bar', 'b': 'baz'}
        self.assertEqual(replace_with_none(test_dict), expected_dict)
        
    def test_convert_to_datetime_dict(self):
        # Test that date strings are converted to datetime objects
        test_dict = {'a': '12/05/2021', 'b': 'foo', 'c_date': '01/01/2020'}
        expected_dict = {'a': '12/05/2021', 'b': 'foo', 'c_date': datetime.datetime(2020, 1, 1)}
        self.assertEqual(convert_to_datetime_dict(test_dict), expected_dict)
        
    def test_convert_nondate_to_datetime_dict(self):
        # Test that non-date strings are not converted
        test_dict = {'a': 'bar', 'b': 'baz'}
        expected_dict = {'a': 'bar', 'b': 'baz'}
        self.assertEqual(convert_to_datetime_dict(test_dict), expected_dict)

    def test_convert_to_datetime_df(self):
        expected_output = pd.DataFrame({'date1': [datetime.datetime(2022, 1, 1, 0, 0), None, datetime.datetime(2022, 3, 3, 0, 0)], 'col2': ['value1', 'value2', 'value3']})
        test_df = pd.DataFrame({'date1': ['01/01/2022', '', '03/03/2022'], 'col2': ['value1', 'value2', 'value3']})
        self.assertTrue(expected_output.equals(convert_to_datetime_df(test_df)))
