import sys
import os
from flask_testing import TestCase
import pandas as pd
import datetime

sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')

from app import app
from app.models import Project, SampleSource
from scripts.utils.generic import read_in_csv, read_in_excel, read_in_as_dict

test_modules_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(test_modules_dir, 'data','utils_file_parsing')

# Test methods that test file parsing
class TestUtilsFileParsing(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app
        
    def test_read_in_csv_valid(self):
        expected_output = [{'date1': datetime.datetime(2022, 1, 1, 0, 0), 'col2': 'value1'}, {'date1': None, 'col2': 'value2'}, {'date1': datetime.datetime(2022, 3, 3, 0, 0), 'col2': 'value3'}]
        self.assertEqual(read_in_csv(os.path.join(data_dir,'test_valid.csv')), expected_output)
    
    def test_read_in_csv_no_header(self):
        expected_output = [{'date1': datetime.datetime(2022, 1, 1, 0, 0), 'col2': 'value1'}, {'date1': None, 'col2': 'value2'}, {'date1': datetime.datetime(2022, 3, 3, 0, 0), 'col2': 'value3'}]
        self.assertEqual(read_in_csv(os.path.join(data_dir,'test_noheader.csv')), expected_output)
        
    def test_read_in_csv_blank_lines(self):
        expected_output = [{'date1': datetime.datetime(2022, 1, 1, 0, 0), 'col2': 'value1'}, {'date1': None, 'col2': 'value2'}, {'date1': datetime.datetime(2022, 3, 3, 0, 0), 'col2': 'value3'}]
        self.assertEqual(read_in_csv(os.path.join(data_dir,'test_blank_lines.csv')), expected_output)

    def test_read_in_excel(self):
        expected_output = [{'date1': datetime.datetime(2022, 1, 1, 0, 0), 'col2': 'value1'}, {'date1': None, 'col2': 'value2'}, {'date1': datetime.datetime(2022, 3, 3, 0, 0), 'col2': 'value3'}]
        self.assertEqual(read_in_excel(os.path.join(data_dir,'test_valid.xlsx')), expected_output)

    def test_read_in_as_dict_csv(self):
        data = read_in_as_dict(os.path.join(data_dir,'test_valid.csv'))
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertIsInstance(data[0], dict)
    
    def test_read_in_as_dict_excel(self):
        data = read_in_as_dict(os.path.join(data_dir,'test_valid.xlsx'))
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertIsInstance(data[0], dict)
    
    def test_invalid_file_format(self):
        with self.assertRaises(SystemExit):
            read_in_as_dict(os.path.join(data_dir,'doesnt_exist.file'))
