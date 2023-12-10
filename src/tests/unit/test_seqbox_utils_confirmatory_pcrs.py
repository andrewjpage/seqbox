import sys
import os
from flask_testing import TestCase
import datetime
sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')
from app.models import CovidConfirmatoryPcr
from app import app, db
from scripts.utils.db import (
    add_extraction,
    add_group,
    add_project,
    add_sample_source,
    add_sample,
    read_in_covid_confirmatory_pcr,
    check_covid_confirmatory_pcr,
    add_covid_confirmatory_pcr,
    get_covid_confirmatory_pcr
)

class TestSeqboxUtilsConfirmatoryPCRs(TestCase):
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
        add_extraction({ 'date_extracted': '01/01/2023','extraction_identifier': '1','sample_identifier': 'sample1','group_name': 'Group','extraction_from':'whole_sample','submitter_plate_id':'CUL','submitter_plate_well': 'A1','nucleic_acid_concentration': '1','sample_identifier': 'sample1','extraction_machine': 'KingFisher Flex','extraction_kit': 'MagMAX Viral/Pathogen II (MAGMAX-96)','what_was_extracted': 'ABC','extraction_processing_institution': 'MLW' })

    def test_check_covid_confirmatory_pcr(self):
        # missing
        with self.assertRaises(SystemExit) as cm:
            check_covid_confirmatory_pcr({})
        with self.assertRaises(SystemExit) as cm:
            check_covid_confirmatory_pcr({'sample_identifier': 'sample1'})
        with self.assertRaises(SystemExit) as cm:
            check_covid_confirmatory_pcr({'sample_identifier': 'sample1', 'date_extracted': '01/01/2023'})  
        with self.assertRaises(SystemExit) as cm:
            check_covid_confirmatory_pcr({'sample_identifier': 'sample1', 'date_extracted': '01/01/2023','extraction_identifier': '1'})                       
        with self.assertRaises(SystemExit) as cm:
            check_covid_confirmatory_pcr({'sample_identifier': 'sample1', 'date_extracted': '01/01/2023','extraction_identifier': '1','date_covid_confirmatory_pcred': '01/01/2023'}) 
        with self.assertRaises(SystemExit) as cm:
            check_covid_confirmatory_pcr({'sample_identifier': 'sample1', 'date_extracted': '01/01/2023','extraction_identifier': '1','date_covid_confirmatory_pcred': '01/01/2023', 'covid_confirmatory_pcr_identifier': '1'})
        with self.assertRaises(SystemExit) as cm:
            check_covid_confirmatory_pcr({'sample_identifier': 'sample1', 'date_extracted': '01/01/2023','extraction_identifier': '1','date_covid_confirmatory_pcred': '01/01/2023', 'covid_confirmatory_pcr_identifier': '1', 'group_name': 'Group'})
        
        # empty
        with self.assertRaises(SystemExit) as cm:
            check_covid_confirmatory_pcr({'sample_identifier': ''})
        with self.assertRaises(SystemExit) as cm:
            check_covid_confirmatory_pcr({'sample_identifier': 'sample1', 'date_extracted': ''})  
        with self.assertRaises(SystemExit) as cm:
            check_covid_confirmatory_pcr({'sample_identifier': 'sample1', 'date_extracted': '01/01/2023','extraction_identifier': ''})                       
        with self.assertRaises(SystemExit) as cm:
            check_covid_confirmatory_pcr({'sample_identifier': 'sample1', 'date_extracted': '01/01/2023','extraction_identifier': '1','date_covid_confirmatory_pcred': ''}) 
        with self.assertRaises(SystemExit) as cm:
            check_covid_confirmatory_pcr({'sample_identifier': 'sample1', 'date_extracted': '01/01/2023','extraction_identifier': '1','date_covid_confirmatory_pcred': '01/01/2023', 'covid_confirmatory_pcr_identifier': ''})
        with self.assertRaises(SystemExit) as cm:
            check_covid_confirmatory_pcr({'sample_identifier': 'sample1', 'date_extracted': '01/01/2023','extraction_identifier': '1','date_covid_confirmatory_pcred': '01/01/2023', 'covid_confirmatory_pcr_identifier': '1', 'group_name': ''})
        with self.assertRaises(SystemExit) as cm:
            check_covid_confirmatory_pcr({'sample_identifier': 'sample1', 'date_extracted': '01/01/2023','extraction_identifier': '1','date_covid_confirmatory_pcred': '01/01/2023', 'covid_confirmatory_pcr_identifier': '1', 'group_name': 'Group', 'covid_confirmatory_pcr_protocol': ''})
        
        self.assertTrue(check_covid_confirmatory_pcr({'sample_identifier': 'sample1', 'date_extracted': '01/01/2023','extraction_identifier': '1','date_covid_confirmatory_pcred': '01/01/2023', 'covid_confirmatory_pcr_identifier': '1', 'group_name': 'Group', 'covid_confirmatory_pcr_protocol': 'ABC'}))
                               
    def test_get_covid_confirmatory_pcr_empty_db(self):
        self.setUp()
        covid_confirmatory_pcr_info = {'sample_identifier': 'sample1', 
                                       'date_extracted': '01/01/2023',
                                       'extraction_identifier': '1',
                                       'date_covid_confirmatory_pcred': '01/01/2023', 
                                       'covid_confirmatory_pcr_identifier': '1', 
                                       'group_name': 'Group', 
                                       'covid_confirmatory_pcr_protocol': 'ABC',
                                       'covid_confirmatory_pcr_ct': '34'}
        self.assertFalse(get_covid_confirmatory_pcr(covid_confirmatory_pcr_info))

    def test_add_covid_confirmatory_pcr(self):
        self.setUp()
        self.populate_db_dependancies()
        covid_confirmatory_pcr_info = {'sample_identifier': 'sample1', 
                                       'date_extracted': '01/01/2023',
                                       'extraction_identifier': '1',
                                       'date_covid_confirmatory_pcred': '01/01/2023', 
                                       'covid_confirmatory_pcr_identifier': '1', 
                                       'group_name': 'Group', 
                                       'covid_confirmatory_pcr_protocol': 'ABC',
                                       'covid_confirmatory_pcr_ct': '34',
                                       'extraction_from':'whole_sample'}
        add_covid_confirmatory_pcr(covid_confirmatory_pcr_info)
        self.assertTrue(get_covid_confirmatory_pcr(covid_confirmatory_pcr_info))

    def test_add_covid_confirmatory_pcr(self):
        self.setUp()
        self.populate_db_dependancies()
        covid_confirmatory_pcr_info = {'sample_identifier': 'sample1', 
                                       'date_extracted': '01/01/2023',
                                       'extraction_identifier': '1',
                                       'date_covid_confirmatory_pcred': '01/01/2023', 
                                       'covid_confirmatory_pcr_identifier': '1', 
                                       'group_name': 'Group', 
                                       'covid_confirmatory_pcr_protocol': 'ABC',
                                       'covid_confirmatory_pcr_ct': '',
                                       'extraction_from':'whole_sample'}
        
        self.assertIsInstance(read_in_covid_confirmatory_pcr(covid_confirmatory_pcr_info), CovidConfirmatoryPcr)
        

    def test_add_covid_confirmatory_pcr_no_matching_extraction(self):
        self.setUp()
        self.populate_db_dependancies()
        covid_confirmatory_pcr_info = {'sample_identifier': 'sample1', 
                                       'date_extracted': '01/01/2023',
                                       'extraction_identifier': '500',
                                       'date_covid_confirmatory_pcred': '01/01/2023', 
                                       'covid_confirmatory_pcr_identifier': '1', 
                                       'group_name': 'Group', 
                                       'covid_confirmatory_pcr_protocol': 'ABC',
                                       'covid_confirmatory_pcr_ct': '34',
                                       'extraction_from':'whole_sample'}
        with self.assertRaises(SystemExit) as cm:
            add_covid_confirmatory_pcr(covid_confirmatory_pcr_info)

    def test_add_covid_confirmatory_pcr_twice(self):
        self.setUp()
        self.populate_db_dependancies()
        covid_confirmatory_pcr_info = {'sample_identifier': 'sample1', 
                                       'date_extracted': '01/01/2023',
                                       'extraction_identifier': '1',
                                       'date_covid_confirmatory_pcred': '01/01/2023', 
                                       'covid_confirmatory_pcr_identifier': '1', 
                                       'group_name': 'Group', 
                                       'covid_confirmatory_pcr_protocol': 'ABC',
                                       'covid_confirmatory_pcr_ct': '34',
                                       'extraction_from':'whole_sample'}
        add_covid_confirmatory_pcr(covid_confirmatory_pcr_info)
        add_covid_confirmatory_pcr(covid_confirmatory_pcr_info)
        with self.assertRaises(SystemExit) as cm:
            get_covid_confirmatory_pcr(covid_confirmatory_pcr_info)
