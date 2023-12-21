import sys
import os
from flask_testing import TestCase
import pandas as pd
sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')
from app import app, db
from scripts.utils.db import (
    add_sample_source,
    add_group,
    add_project,
    add_sample,
    get_sample,
    update_sample
)

class TestSeqboxUtilsSample(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app
    
    # reset the database before you start
    def setUp(self):
        assert os.environ['DATABASE_URL'].split('/')[3].startswith('test') # you really dont want to delete a production DB
        db.drop_all()
        db.create_all()

    def populate_db_dependancies(self):
        add_group({'group_name': 'Group', 'institution': 'MLW', 'pi': 'PI'})
        add_project({'project_name': 'Project', 'group_name': 'Group', 'institution': 'MLW', 'project_details': 'seq'})
        add_sample_source({'projects': 'Project', 'group_name': 'Group', 'institution': 'MLW', 'sample_source_identifier': 'sample_source_1', 'sample_source_type': 'patient', 'latitude': 1.23, 'longitude': -12.3, 'country': 'UK', 'location_first_level': 'Essex', 'city': 'London', 'township': 'Docklands', 'notes': 'note'})

    def test_get_sample_that_doesnt_exist(self):
        self.setUp()
        self.populate_db_dependancies()
        self.assertFalse(get_sample({'sample_identifier': 'sample1', 'group_name': 'Group'}))

    def test_add_sample(self):
        self.setUp()
        self.populate_db_dependancies()
        sample_info = {'sample_identifier': 'sample1', 'sample_source_identifier': 'sample_source_1', 'institution': 'MLW', 'group_name': 'Group', 'species': 'SARS-CoV-2', 'sample_type': 'Lung aspirate', 'day_collected': '31', 'month_collected': '5', 'year_collected': '2021', 'day_received': '1', 'month_received': '1', 'year_received': '2022', 'sequencing_type_requested':'MinION SARS-CoV-2'}

        add_sample(sample_info, False)
        sample = get_sample({'sample_identifier': 'sample1', 'group_name': 'Group'})
        self.assertEqual(sample.sample_identifier, 'sample1')
        self.assertEqual(sample.species, 'SARS-CoV-2')
        self.assertEqual(sample.sample_type, 'Lung aspirate')
        self.assertEqual(sample.day_collected, 31)
        self.assertEqual(sample.month_collected, 5)
        self.assertEqual(sample.year_collected, 2021)
        self.assertEqual(sample.day_received, 1)
        self.assertEqual(sample.month_received, 1)
        self.assertEqual(sample.year_received, 2022)
        self.assertEqual(sample.sequencing_type_requested, ['MinION SARS-CoV-2'])
        self.assertFalse(sample.submitted_for_sequencing)
        self.assertIsNone(sample.submitter_plate_id)
        self.assertIsNone(sample.submitter_plate_well)
    
    def test_add_two_different_samples(self):
        self.setUp()
        self.populate_db_dependancies()
        sample_info = {'sample_identifier': 'sample1', 'sample_source_identifier': 'sample_source_1', 'institution': 'MLW', 'group_name': 'Group', 'species': 'SARS-CoV-2', 'sample_type': 'Lung aspirate', 'day_collected': '31', 'month_collected': '5', 'year_collected': '2021', 'day_received': '1', 'month_received': '1', 'year_received': '2022', 'sequencing_type_requested':'MinION SARS-CoV-2'}

        add_sample(sample_info, False)
        sample_info['sample_identifier'] = 'sample2'
        add_sample(sample_info, False) 
        sample1 = get_sample({'sample_identifier': 'sample1', 'group_name': 'Group'})
        sample2 = get_sample({'sample_identifier': 'sample2', 'group_name': 'Group'})
        self.assertEqual(sample1.sample_identifier, 'sample1')
        self.assertEqual(sample2.sample_identifier, 'sample2')

    def test_add_sample_and_submit_for_sequencing_later(self):
        self.setUp()
        self.populate_db_dependancies()
        sample_info = {'sample_identifier': 'sample1', 'sample_source_identifier': 'sample_source_1', 'institution': 'MLW', 'group_name': 'Group', 'species': 'SARS-CoV-2', 'sample_type': 'Lung aspirate', 'day_collected': '31', 'month_collected': '5', 'year_collected': '2021', 'day_received': '1', 'month_received': '1', 'year_received': '2022', 'sequencing_type_requested':'MinION SARS-CoV-2'}

        add_sample(sample_info, False)
        sample = get_sample(sample_info)
        self.assertFalse(sample.submitted_for_sequencing)
        update_sample(sample)
        self.assertTrue(sample.submitted_for_sequencing)

    def test_add_sample_and_submit_for_sequencing(self):
        self.setUp()
        self.populate_db_dependancies()
        sample_info = {'sample_identifier': 'sample1', 'sample_source_identifier': 'sample_source_1', 'institution': 'MLW', 'group_name': 'Group', 'species': 'SARS-CoV-2', 'sample_type': 'Lung aspirate', 'day_collected': '31', 'month_collected': '5', 'year_collected': '2021', 'day_received': '1', 'month_received': '1', 'year_received': '2022', 'sequencing_type_requested':'MinION SARS-CoV-2', 'submitter_plate_id': 'SAM123', 'submitter_plate_well': 'A1'}

        add_sample(sample_info, True)
        sample = get_sample(sample_info)
        self.assertEqual(sample.submitter_plate_id, 'SAM123')
        self.assertEqual(sample.submitter_plate_well, 'A1')

    def test_add_sample_with_no_matching_group(self):
        self.setUp()
        self.populate_db_dependancies()
        sample_info = {'sample_identifier': 'sample1', 'sample_source_identifier': 'sample_source_1', 'institution': 'MLW', 'group_name': 'GroupDoesNotExist', 'species': 'SARS-CoV-2', 'sample_type': 'Lung aspirate', 'day_collected': '31', 'month_collected': '5', 'year_collected': '2021', 'day_received': '1', 'month_received': '1', 'year_received': '2022', 'sequencing_type_requested':'MinION SARS-CoV-2'}

        with self.assertRaises(SystemExit) as cm:
            add_sample(sample_info, False)
    
    def test_add_sample_with_no_matching_sample_source(self):
        self.setUp()
        self.populate_db_dependancies()
        sample_info = {'sample_identifier': 'sample1', 'sample_source_identifier': 'sample_source_doesnt_exist', 'institution': 'MLW', 'group_name': 'Group', 'species': 'SARS-CoV-2', 'sample_type': 'Lung aspirate', 'day_collected': '31', 'month_collected': '5', 'year_collected': '2021', 'day_received': '1', 'month_received': '1', 'year_received': '2022', 'sequencing_type_requested':'MinION SARS-CoV-2'}

        with self.assertRaises(SystemExit) as cm:
            add_sample(sample_info, False)

    def test_add_sample_with_missing_sample_source_identifier(self):
        self.setUp()
        self.populate_db_dependancies()
        sample_info = {'sample_identifier': 'sample1', 'institution': 'MLW', 'group_name': 'Group', 'species': 'SARS-CoV-2', 'sample_type': 'Lung aspirate', 'day_collected': '31', 'month_collected': '5', 'year_collected': '2021', 'day_received': '1', 'month_received': '1', 'year_received': '2022', 'sequencing_type_requested':'MinION SARS-CoV-2'}

        with self.assertRaises(ValueError) as cm:
            add_sample(sample_info, False)

    def test_add_sample_with_missing_sample_identifier(self):
        self.setUp()
        self.populate_db_dependancies()
        sample_info = {'sample_source_identifier': 'sample_source_1', 'institution': 'MLW', 'group_name': 'Group', 'species': 'SARS-CoV-2', 'sample_type': 'Lung aspirate', 'day_collected': '31', 'month_collected': '5', 'year_collected': '2021', 'day_received': '1', 'month_received': '1', 'year_received': '2022', 'sequencing_type_requested':'MinION SARS-CoV-2'}

        with self.assertRaises(ValueError) as cm:
            add_sample(sample_info, False)

    def test_add_sample_with_missing_group_name(self):
        self.setUp()
        self.populate_db_dependancies()
        sample_info = {'sample_identifier': 'sample1', 'sample_source_identifier': 'sample_source_1', 'institution': 'MLW', 'species': 'SARS-CoV-2', 'sample_type': 'Lung aspirate', 'day_collected': '31', 'month_collected': '5', 'year_collected': '2021', 'day_received': '1', 'month_received': '1', 'year_received': '2022', 'sequencing_type_requested':'MinION SARS-CoV-2'}

        with self.assertRaises(ValueError) as cm:
            add_sample(sample_info, False)

    def test_add_sample_with_missing_institution(self):
        self.setUp()
        self.populate_db_dependancies()
        sample_info = {'sample_identifier': 'sample1', 'sample_source_identifier': 'sample_source_1', 'group_name': 'Group', 'species': 'SARS-CoV-2', 'sample_type': 'Lung aspirate', 'day_collected': '31', 'month_collected': '5', 'year_collected': '2021', 'day_received': '1', 'month_received': '1', 'year_received': '2022', 'sequencing_type_requested':'MinION SARS-CoV-2'}

        with self.assertRaises(ValueError) as cm:
            add_sample(sample_info, False)

    # TODO: check the institute exists
    #def test_add_sample_with_no_matching_institution(self):
    #    self.setUp()
    #    self.populate_db_dependancies()
    #    sample_info = {'sample_identifier': 'sample1', 'sample_source_identifier': 'sample_source_1', 'institution': 'InstituteDoesNotExist', 'group_name': 'Group', 'species': #'SARS-CoV-2', 'sample_type': 'Lung aspirate', 'day_collected': '31', 'month_collected': '5', 'year_collected': '2021', 'day_received': '1', 'month_received': '1', #'year_received': '2022', 'sequencing_type_requested':'MinION SARS-CoV-2'}
    #    self.assertFalse(add_sample(sample_info, False))


    # TODO: check dates are valid
    #def test_add_sample_with_invalid_dates(self):
    #    self.setUp()
    #    self.populate_db_dependancies()
    #    sample_info = {'sample_identifier': 'sample1', 'sample_source_identifier': 'sample_source_1', 'institution': 'MLW', 'group_name': 'Group', 'species': 'SARS-CoV-2', #'sample_type': 'Lung aspirate', 'day_collected': '32', 'month_collected': '13', 'year_collected': '-1', 'day_received': '0', 'month_received': '0', 'year_received': #'2022', 'sequencing_type_requested':'MinION SARS-CoV-2'}
    #    self.assertFalse(add_sample(sample_info, False))

    # TODO: Check for adding the same sample twice. Error or Update?
    #def test_add_same_sample_twice(self):
    #    self.setUp()
    #    self.populate_db_dependancies()
    #    sample_info = {'sample_identifier': 'sample1', 'sample_source_identifier': 'sample_source_1', 'institution': 'MLW', 'group_name': 'Group', 'species': 'SARS-CoV-2', #'sample_type': 'Lung aspirate', 'day_collected': '31', 'month_collected': '5', 'year_collected': '2021', 'day_received': '1', 'month_received': '1', 'year_received': #'2022', 'sequencing_type_requested':'MinION SARS-CoV-2'}
    #    add_sample(sample_info, False)
    #    with self.assertRaises(SystemExit) as cm:
    #       add_sample(sample_info, False) 
#
