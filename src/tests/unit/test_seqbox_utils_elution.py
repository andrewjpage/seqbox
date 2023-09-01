import sys
import os
from flask_testing import TestCase
import datetime
import tempfile
sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')
from app import app, db
from seqbox_utils import add_elution_info_to_extraction,add_extraction, add_group, add_project, add_sample_source, add_sample

class TestSeqboxUtilsElution(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app
    
    # reset the database before you start
    def setUp(self):
        assert os.environ['DATABASE_URL'].split('/')[3].startswith('test') # you really dont want to delete a production DB
        db.drop_all()
        db.create_all()

    def populate_db(self):
        add_group({'group_name': 'Group', 'institution': 'MLW', 'pi': 'PI'})
        add_project({'project_name': 'Project', 'group_name': 'Group', 'institution': 'MLW', 'project_details': 'seq'})
        add_sample_source({'projects': 'Project', 'group_name': 'Group', 'institution': 'MLW', 'sample_source_identifier': 'sample_source_1', 'sample_source_type': 'patient', 'latitude': 1.23, 'longitude': -12.3, 'country': 'UK', 'location_first_level': 'Essex', 'city': 'London', 'township': 'Docklands', 'notes': 'note'})
        add_sample({'sample_identifier': 'sample1', 'sample_source_identifier': 'sample_source_1', 'institution': 'MLW', 'group_name': 'Group', 'species': 'SARS-CoV-2', 'sample_type': 'Lung aspirate', 'day_collected': '31', 'month_collected': '5', 'year_collected': '2021', 'day_received': '1', 'month_received': '1', 'year_received': '2022', 'sequencing_type_requested':'MinION SARS-CoV-2'}, False)
        add_extraction({ 'date_extracted': '01/01/2023','extraction_identifier': '1','sample_identifier': 'sample1','group_name': 'Group','extraction_from':'whole_sample','submitter_plate_id':'CUL','submitter_plate_well': 'A1','nucleic_acid_concentration': '1','sample_identifier': 'sample1','extraction_machine': 'KingFisher Flex','extraction_kit': 'MagMAX Viral/Pathogen II (MAGMAX-96)','what_was_extracted': 'ABC','extraction_processing_institution': 'MLW',})
    
    def test_add_elution_info_to_extraction(self):
        self.populate_db()
        elution_info = {'elution_plate_id': 'ELU123',
                        'elution_plate_well': 'A1',
                        'sample_identifier': 'sample1',
                        'extraction_identifier': '1',
                        'date_extracted': '01/01/2023',
                        'extraction_from':'whole_sample',
                        'group_name': 'Group'
                        }
        self.assertEqual(None,add_elution_info_to_extraction(elution_info))

    def test_add_elution_info_to_extraction_empty_db(self):
        elution_info = {'elution_plate_id': 'ELU123',
                        'elution_plate_well': 'A1',
                        'sample_identifier': 'sample1',
                        'extraction_identifier': '1',
                        'date_extracted': '01/01/2023',
                        'extraction_from':'whole_sample',
                        'group_name': 'Group'
                        }
        with self.assertRaises(SystemExit) as cm:
            add_elution_info_to_extraction(elution_info)

        