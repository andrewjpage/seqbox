import sys
import os
from flask_testing import TestCase
import pandas as pd
sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')
from app import app, db
from app.models import Project, SampleSource,Groups
from scripts.utils.check import check_sample_sources, check_sample_source_associated_with_project
from scripts.utils.db import (
    get_sample_source,
    add_sample_source,
    add_group,
    add_project,
)

class TestSeqboxUtilsSampleSources(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app
    
    # reset the database before you start
    def setUp(self):
        assert os.environ['DATABASE_URL'].split('/')[3].startswith('test') # you really dont want to delete a production DB
        db.drop_all()
        db.create_all()

    def test_get_sample_source_doesnt_exist(self):
        add_group({'group_name': 'TestGroup', 'institution': 'Test Institution', 'pi': 'Test PI'})
        add_project({'project_name': 'Testproject', 'group_name': 'TestGroup', 'institution': 'Test Institution', 'project_details': 'sequencing'})
        sample_source_info = {'projects': 'Testproject', 'group_name': 'TestGroup', 'institution': 'Test Institution', 'sample_source_identifier': 'sample1', 'sample_source_type': 'patient', 'latitude': 37.7749, 'longitude': -122.4194, 'country': 'UK', 'location_first_level': 'Essex', 'city': 'London', 'township': 'Docklands', 'notes': 'This is a test sample source'}

        self.assertFalse(get_sample_source(sample_source_info))

    def test_add_sample_source_existing_project(self):
        self.setUp()
        add_group({'group_name': 'TestGroup', 'institution': 'Test Institution', 'pi': 'Test PI'})
        add_project({'project_name': 'Testproject', 'group_name': 'TestGroup', 'institution': 'Test Institution', 'project_details': 'sequencing'})
        sample_source_info = {'projects': 'Testproject', 'group_name': 'TestGroup', 'institution': 'Test Institution', 'sample_source_identifier': 'sample1', 'sample_source_type': 'patient', 'latitude': 37.7749, 'longitude': -122.4194, 'country': 'UK', 'location_first_level': 'Essex', 'city': 'London', 'township': 'Docklands', 'notes': 'This is a test sample source'}
        self.assertFalse(get_sample_source(sample_source_info))

        add_sample_source(sample_source_info)

        result = get_sample_source(sample_source_info)
        self.assertEqual(result.sample_source_identifier, sample_source_info['sample_source_identifier'])
        self.assertEqual(result.sample_source_type, sample_source_info['sample_source_type'])
        self.assertEqual(result.latitude, sample_source_info['latitude'])
        self.assertEqual(result.longitude, sample_source_info['longitude'])
        self.assertEqual(result.country, sample_source_info['country'])
        self.assertEqual(result.location_second_level, sample_source_info['city'])
        self.assertEqual(result.location_third_level, sample_source_info['township'])

    def test_add_same_sample_source_twice(self):
        self.setUp()
        add_group({'group_name': 'TestGroup', 'institution': 'Test Institution', 'pi': 'Test PI'})
        add_project({'project_name': 'Testproject', 'group_name': 'TestGroup', 'institution': 'Test Institution', 'project_details': 'sequencing'})
        sample_source_info = {'projects': 'Testproject', 'group_name': 'TestGroup', 'institution': 'Test Institution', 'sample_source_identifier': 'sample1', 'sample_source_type': 'patient', 'latitude': 37.7749, 'longitude': -122.4194, 'country': 'UK', 'location_first_level': 'Essex', 'city': 'London', 'township': 'Docklands', 'notes': 'This is a test sample source'}
        self.assertTrue(add_sample_source(sample_source_info))
        self.assertFalse(add_sample_source(sample_source_info))

        result = get_sample_source(sample_source_info)
        self.assertEqual(result.sample_source_identifier, sample_source_info['sample_source_identifier'])

    def test_add_sample_source_missing_project(self):
        self.setUp()
        add_group({'group_name': 'TestGroup', 'institution': 'Test Institution', 'pi': 'Test PI'})
        sample_source_info = {'projects': 'Testproject', 'group_name': 'TestGroup', 'institution': 'Test Institution', 'sample_source_identifier': 'sample1', 'sample_source_type': 'patient', 'latitude': 37.7749, 'longitude': -122.4194, 'country': 'UK', 'location_first_level': 'Essex', 'city': 'London', 'township': 'Docklands', 'notes': 'This is a test sample source'}

        with self.assertRaises(SystemExit) as cm:
            add_sample_source(sample_source_info)

    def test_add_sample_source_missing_group(self):
        self.setUp()
        
        with self.assertRaises(SystemExit) as cm:
            add_project({'project_name': 'Testproject', 'group_name': 'TestGroup', 'institution': 'Test Institution', 'project_details': 'sequencing'})
            sample_source_info = {'projects': 'Testproject', 'group_name': 'TestGroup', 'institution': 'Test Institution', 'sample_source_identifier': 'sample1', 'sample_source_type': 'patient', 'latitude': 37.7749, 'longitude': -122.4194, 'country': 'UK', 'location_first_level': 'Essex', 'city': 'London', 'township': 'Docklands', 'notes': 'This is a test sample source'}
            add_sample_source(sample_source_info)

    def test_add_sample_source_missing_sample_source(self):
        self.setUp()
        sample_source_info = {}

        self.assertFalse(add_sample_source(sample_source_info))

    def test_add_sample_source_multiple_projects(self):
        self.setUp()
        add_group({'group_name': 'TestGroup', 'institution': 'Test Institution', 'pi': 'Test PI'})
        add_project({'project_name': 'Testproject1', 'group_name': 'TestGroup', 'institution': 'Test Institution', 'project_details': 'sequencing'})
        add_project({'project_name': 'Testproject2', 'group_name': 'TestGroup', 'institution': 'Test Institution', 'project_details': 'sequencing'})

        sample_source_info = {'projects': 'Testproject1;Testproject2', 'group_name': 'TestGroup', 'institution': 'Test Institution', 'sample_source_identifier': 'sample1', 'sample_source_type': 'patient', 'latitude': 37.7749, 'longitude': -122.4194, 'country': 'UK', 'location_first_level': 'Essex', 'city': 'London', 'township': 'Docklands', 'notes': 'This is a test sample source'}
        add_sample_source(sample_source_info)

        sample_source_info['projects'] = 'Testproject1'
        result = get_sample_source(sample_source_info)
        self.assertEqual(result.sample_source_identifier, sample_source_info['sample_source_identifier'])

        sample_source_info['projects'] = 'Testproject2'
        result = get_sample_source(sample_source_info)
        self.assertEqual(result.sample_source_identifier, sample_source_info['sample_source_identifier'])

    
    def test_check_sample_source_associated_with_project(self):
        self.setUp()
        add_group({'group_name': 'TestGroup', 'institution': 'Test Institution', 'pi': 'Test PI'})
        add_project({'project_name': 'Testproject1', 'group_name': 'TestGroup', 'institution': 'Test Institution', 'project_details': 'sequencing'})
        add_project({'project_name': 'Testproject2', 'group_name': 'TestGroup', 'institution': 'Test Institution', 'project_details': 'sequencing'})

        sample_source_info = {'projects': 'Testproject1', 'group_name': 'TestGroup', 'institution': 'Test Institution', 'sample_source_identifier': 'sample1', 'sample_source_type': 'patient', 'latitude': 37.7749, 'longitude': -122.4194, 'country': 'UK', 'location_first_level': 'Essex', 'city': 'London', 'township': 'Docklands', 'notes': 'This is a test sample source'}
        add_sample_source(sample_source_info)
        sample_source = get_sample_source(sample_source_info)

        self.assertEqual([x.project_name for x in sample_source.projects], ['Testproject1'], msg='The sample source should only be associated with Testproject1 at this point')

        sample_source_info['projects'] = 'Testproject1;Testproject2'
        check_sample_source_associated_with_project(sample_source, sample_source_info)

        self.assertEqual([x.project_name for x in sample_source.projects], ['Testproject1','Testproject2'], msg='The sample source should now be assosiated with two projects')

    def test_check_sample_sources(self):
        self.assertEqual(None, check_sample_sources({'projects': 'Testproject', 'group_name': 'TestGroup', 'institution': 'Test Institution', 'sample_source_identifier': 'sample1', 'sample_source_type': 'patient'}))
        #empty
        with self.assertRaises(SystemExit) as cm:
            check_sample_sources({'projects': '', 'group_name': 'TestGroup', 'institution': 'Test Institution', 'sample_source_identifier': 'sample1', 'sample_source_type': 'patient'})
        with self.assertRaises(SystemExit) as cm:
            check_sample_sources({'projects': 'Testproject', 'group_name': '', 'institution': 'Test Institution', 'sample_source_identifier': 'sample1', 'sample_source_type': 'patient'})
        with self.assertRaises(SystemExit) as cm:
            check_sample_sources({'projects': 'Testproject', 'group_name': 'TestGroup', 'institution': '', 'sample_source_identifier': 'sample1', 'sample_source_type': 'patient'})
        with self.assertRaises(SystemExit) as cm:
            check_sample_sources({'projects': 'Testproject', 'group_name': 'TestGroup', 'institution': 'Test Institution', 'sample_source_identifier': '', 'sample_source_type': 'patient'})
        with self.assertRaises(SystemExit) as cm:
            check_sample_sources({'projects': 'Testproject', 'group_name': 'TestGroup', 'institution': 'Test Institution', 'sample_source_identifier': 'sample1', 'sample_source_type': ''})
