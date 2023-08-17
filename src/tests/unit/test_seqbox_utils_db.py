import sys
from flask_testing import TestCase
import pandas as pd
sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')
from app import app, db
from app.models import  Project, SampleSource
from seqbox_utils import check_sample_source_associated_with_project

class TestSeqboxUtilsDB(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app
    
    def setUp(self):
        self.test_sample_source = SampleSource(
            sample_source_identifier='sample1',
            sample_source_type='patient',
            latitude=37.7749,
            longitude=-122.4194,
            country='USA',
            location_first_level='California',
            location_second_level='San Francisco',
            location_third_level='Mission District',
            notes='This is a test sample source'
        )
        self.test_sample_source_info = {'projects': 'test_project1; test_project2'}
            
    def test_check_sample_source_associated_with_project(self):
        self.test_sample_source.projects = [ Project(
            groups_id=1,
            project_name='Test Project',
            project_details='This is a test project',
            notes='This is a test note'
        ), Project(
            groups_id=2,
            project_name='Test Project2',
            project_details='This is a test project2',
            notes='This is a test note2'
        )]
        self.assertTrue(check_sample_source_associated_with_project(self.test_sample_source, self.test_sample_source_info))

