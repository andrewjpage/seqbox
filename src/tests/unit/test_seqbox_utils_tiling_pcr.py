import sys
import os
from flask_testing import TestCase
import datetime
sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')
from app import app, db
from app.models import TilingPcr
from scripts.utils.check import check_tiling_pcr
from scripts.utils.db import (
    add_extraction,
    add_group,
    add_project,
    add_sample_source,
    add_sample,
    get_tiling_pcr,
    add_tiling_pcr,
)


class TestSeqboxUtilsTilingPcr(TestCase):
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

    def test_check_tiling_pcr(self):
        self.assertEqual(check_tiling_pcr({}), False)
        self.assertEqual(check_tiling_pcr({'sample_identifier': '1', 'date_extracted': '01/01/2023'}), False)
        self.assertEqual(check_tiling_pcr({'sample_identifier': '1', 'date_extracted': '01/01/2023', 'extraction_identifier': '3', 'date_tiling_pcred': '01/01/2023', 'tiling_pcr_identifier': '5', 'group_name': 'Group', 'tiling_pcr_protocol': 'ABC'}
), True)

    # get tiling_pcr from empty database
    def test_get_tiling_pcr_empty_db(self):
        self.setUp()

        tiling_pcr_info = {'sample_identifier': 'sample1', 
                           'date_extracted': '01/01/2023', 
                           'extraction_identifier': '3', 
                           'date_tiling_pcred': '01/01/2023', 
                           'tiling_pcr_identifier': '5', 
                           'group_name': 'Group', 
                           'tiling_pcr_protocol': 'ABC'}
        self.assertFalse(get_tiling_pcr(tiling_pcr_info))

    def test_add_tiling_pcr(self):
        self.setUp()
        self.populate_db_dependancies()
        tiling_pcr_info = {'sample_identifier': 'sample1', 
                           'date_extracted': '01/01/2023', 
                           'extraction_identifier': '3', 
                           'date_tiling_pcred': '01/01/2023', 
                           'tiling_pcr_identifier': '5', 
                           'group_name': 'Group', 
                           'tiling_pcr_protocol': 'ABC',
                           'number_of_cycles': '38',
                            'extraction_identifier': '1',
                            'sample_identifier': 'sample1',
                            'group_name': 'Group',
                            'extraction_from':'whole_sample',
                            'submitter_plate_id':'CUL',
                            'submitter_plate_well': 'A1',
                            'nucleic_acid_concentration': '1',
                            'sample_identifier': 'sample1',
                            'extraction_machine': 'KingFisher Flex',
                            'extraction_kit': 'MagMAX Viral/Pathogen II (MAGMAX-96)',
                            'what_was_extracted': 'ABC',
                            'extraction_processing_institution': 'MLW',
                           }
        add_tiling_pcr(tiling_pcr_info)
        self.assertTrue(get_tiling_pcr(tiling_pcr_info))

    def test_add_tiling_pcr_no_matching_extraction(self):
        self.setUp()
        self.populate_db_dependancies()
        tiling_pcr_info = {'sample_identifier': 'sample1', 
                           'date_extracted': '01/01/2023', 
                           'extraction_identifier': '3', 
                           'date_tiling_pcred': '01/01/2023', 
                           'tiling_pcr_identifier': '5', 
                           'group_name': 'Group', 
                           'tiling_pcr_protocol': 'ABC',
                           'number_of_cycles': '38',
                            'extraction_identifier': '5000',
                            'sample_identifier': 'sample1',
                            'group_name': 'Group',
                            'extraction_from':'whole_sample',
                            'submitter_plate_id':'CUL',
                            'submitter_plate_well': 'A1',
                            'nucleic_acid_concentration': '1',
                            'sample_identifier': 'sample1',
                            'extraction_machine': 'KingFisher Flex',
                            'extraction_kit': 'MagMAX Viral/Pathogen II (MAGMAX-96)',
                            'what_was_extracted': 'ABC',
                            'extraction_processing_institution': 'MLW',
                           }
        with self.assertRaises(SystemExit) as cm:
            add_tiling_pcr(tiling_pcr_info)

    def test_add_tiling_pcr_twice(self):
        self.setUp()
        self.populate_db_dependancies()
        tiling_pcr_info = {'sample_identifier': 'sample1', 
                           'date_extracted': '01/01/2023', 
                           'extraction_identifier': '3', 
                           'date_tiling_pcred': '01/01/2023', 
                           'tiling_pcr_identifier': '5', 
                           'group_name': 'Group', 
                           'tiling_pcr_protocol': 'ABC',
                           'number_of_cycles': '38',
                            'extraction_identifier': '1',
                            'sample_identifier': 'sample1',
                            'group_name': 'Group',
                            'extraction_from':'whole_sample',
                            'submitter_plate_id':'CUL',
                            'submitter_plate_well': 'A1',
                            'nucleic_acid_concentration': '1',
                            'sample_identifier': 'sample1',
                            'extraction_machine': 'KingFisher Flex',
                            'extraction_kit': 'MagMAX Viral/Pathogen II (MAGMAX-96)',
                            'what_was_extracted': 'ABC',
                            'extraction_processing_institution': 'MLW',
                           }
        add_tiling_pcr(tiling_pcr_info)
        add_tiling_pcr(tiling_pcr_info)
        with self.assertRaises(SystemExit) as cm:
            get_tiling_pcr(tiling_pcr_info)
