import sys
import os
from flask_testing import TestCase
sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')
from app import app, db
from app.models import  Culture

from scripts.utils.check import check_cultures
from scripts.utils.db import (
    get_culture,
    add_culture,
    add_group,
    add_project,
    add_sample_source,
    add_sample
)

class TestSeqboxUtilsCulture(TestCase):
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
        add_sample({'sample_identifier': 'sample1', 'sample_source_identifier': 'sample_source_1', 'institution': 'MLW', 'group_name': 'Group', 'species': 'SARS-CoV-2', 'sample_type': 'Lung aspirate', 'day_collected': '31', 'month_collected': '5', 'year_collected': '2021', 'day_received': '1', 'month_received': '1', 'year_received': '2022', 'sequencing_type_requested':'MinION SARS-CoV-2'}, False)

    def test_check_cultures(self):
        self.assertTrue(check_cultures({ 'group_name': 'Group','sample_identifier': 'sample1' , 'date_cultured': '01/01/2023', 'culture_identifier': '123', 'submitter_plate_id': 'CUL123', 'submitter_plate_well': 'A1'}))
        self.assertFalse(check_cultures({ 'group_name': 'Group','sample_identifier': 'sample1' , 'date_cultured': '', 'culture_identifier': '', 'submitter_plate_id': 'CUL123', 'submitter_plate_well': 'A1'}))
        # empty
        with self.assertRaises(SystemExit) as cm:
            self.assertFalse(check_cultures({ 'group_name': 'Group','sample_identifier': 'sample1' , 'date_cultured': '', 'culture_identifier': '123', 'submitter_plate_id': 'CUL123', 'submitter_plate_well': 'A1'}))
        with self.assertRaises(SystemExit) as cm:
            self.assertFalse(check_cultures({ 'group_name': 'Group','sample_identifier': 'sample1' , 'date_cultured': '01/01/2023', 'culture_identifier': '', 'submitter_plate_id': 'CUL123', 'submitter_plate_well': 'A1'}))
        
    def test_get_culture_empty_db(self):
        self.setUp()
        self.populate_db_dependancies()
        self.assertFalse(get_culture({}))

        self.assertFalse(get_culture({ 'group_name': 'Group','sample_identifier': 'sample1' , 'date_cultured': '01/01/2023', 'culture_identifier': '123', 'submitter_plate_id': 'CUL123', 'submitter_plate_well': 'A1'}))

    def test_add_culture(self):
        self.setUp()
        self.populate_db_dependancies()
        culture_info = { 'group_name': 'Group',
                        'sample_identifier': 'sample1' , 
                        'date_cultured': '01/01/2023', 
                        'culture_identifier': '123', 
                        'submitter_plate_id': 'CUL123', 
                        'submitter_plate_well': 'A1'
                        }

        add_culture(culture_info)
        result = get_culture(culture_info)
        self.assertIsInstance(result, Culture)

    def test_add_culture_duplicate(self):
        self.setUp()
        self.populate_db_dependancies()
        culture_info = { 'group_name': 'Group',
                        'sample_identifier': 'sample1' , 
                        'date_cultured': '01/01/2023', 
                        'culture_identifier': '123', 
                        'submitter_plate_id': 'CUL123', 
                        'submitter_plate_well': 'A1'
                        }

        add_culture(culture_info)
        with self.assertRaises(Exception) as cm:
            add_culture(culture_info)

    def test_add_culture_sample_mismatch(self):
        self.setUp()
        self.populate_db_dependancies()
        culture_info = { 'group_name': 'Group',
                        'sample_identifier': 'doesnt_exist' , 
                        'date_cultured': '01/01/2023', 
                        'culture_identifier': '123', 
                        'submitter_plate_id': 'CUL123', 
                        'submitter_plate_well': 'A1'
                        }

        with self.assertRaises(SystemExit) as cm:
            add_culture(culture_info)

    def test_read_in_culture_out(self):
        self.setUp()
        self.populate_db_dependancies()
        culture_info = { 'group_name': 'Group',
                        'sample_identifier': 'sample1' , 
                        'date_cultured': '01/01/2023', 
                        'culture_identifier': '123', 
                        'submitter_plate_id': 'OUT123', 
                        'submitter_plate_well': 'A1'
                        }

        add_culture(culture_info)
        result = get_culture(culture_info)
        self.assertIsInstance(result, Culture)
