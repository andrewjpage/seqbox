import sys
import os
from flask_testing import TestCase
import datetime
sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')
from app import app, db
from app.models import  Extraction, Culture
from seqbox_utils import check_extraction_fields, get_extraction, add_extraction, add_group, add_project, add_sample_source, add_culture, add_sample

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
        add_sample({'sample_identifier': 'sample1', 'sample_source_identifier': 'sample_source_1', 'institution': 'MLW', 'group_name': 'Group', 'species': 'SARS-CoV-2', 'sample_type': 'Lung aspirate', 'day_collected': '31', 'month_collected': '5', 'year_collected': '2021', 'day_received': '1', 'month_received': '1', 'year_received': '2022', 'sequencing_type_requested':'MinION SARS-CoV-2'}, False)

    def test_check_extraction_fields(self):
        extraction_info = { 'date_extracted': '1/2/2023',
                            'extraction_identifier': '1',
                            'sample_identifier': 'sample1',
                            'group_name': 'Group',
                            'extraction_from':'cultured_isolate',
                            'submitter_plate_id':'CUL',
                            'submitter_plate_well': 'A1',
                            'nucleic_acid_concentration': '1'
                            }
        self.assertTrue(check_extraction_fields(extraction_info))

    # TODO: check if this should be OR rather than AND
    def test_date_extracted_and_extraction_identifier_blank(self):
        extraction_info = { 'date_extracted': None,
                            'extraction_identifier': None,
                            'sample_identifier': 'sample1',
                            'group_name': 'Group',
                            'extraction_from':'cultured_isolate',
                            'submitter_plate_id':'CUL',
                            'submitter_plate_well': 'A1',
                            'nucleic_acid_concentration': '1'
                            }
        self.assertFalse(check_extraction_fields(extraction_info))

    def test_missing_sample_identifier(self):
        extraction_info = { 'date_extracted': '1/2/2023',
                            'extraction_identifier': '1',
                            'group_name': 'Group',
                            'extraction_from':'cultured_isolate',
                            'submitter_plate_id':'CUL',
                            'submitter_plate_well': 'A1',
                            'nucleic_acid_concentration': '1'
                            }
        with self.assertRaises(SystemExit) as cm:
            check_extraction_fields(extraction_info)

        extraction_info['sample_identifier'] = ''
        with self.assertRaises(SystemExit) as cm:
            check_extraction_fields(extraction_info)

        extraction_info['sample_identifier'] = 'abc'
        self.assertTrue(check_extraction_fields(extraction_info))
        

    def test_missing_date_extracted(self):
        extraction_info = { 'extraction_identifier': '1',
                            'sample_identifier': 'sample1',
                            'group_name': 'Group',
                            'extraction_from':'cultured_isolate',
                            'submitter_plate_id':'CUL',
                            'submitter_plate_well': 'A1',
                            'nucleic_acid_concentration': '1'
                            }
        with self.assertRaises(SystemExit) as cm:
            check_extraction_fields(extraction_info)

        extraction_info['date_extracted'] = ''
        with self.assertRaises(SystemExit) as cm:
            check_extraction_fields(extraction_info)

        extraction_info['date_extracted'] = '1/1/2023'
        self.assertTrue(check_extraction_fields(extraction_info))

    def test_missing_extraction_identifier(self):
        extraction_info = { 'date_extracted': '1/2/2023',
                            'sample_identifier': 'sample1',
                            'group_name': 'Group',
                            'extraction_from':'cultured_isolate',
                            'submitter_plate_id':'CUL',
                            'submitter_plate_well': 'A1',
                            'nucleic_acid_concentration': '1'
                            }
        with self.assertRaises(SystemExit) as cm:
            check_extraction_fields(extraction_info)

        extraction_info['extraction_identifier'] = ''
        with self.assertRaises(SystemExit) as cm:
            check_extraction_fields(extraction_info)

        extraction_info['extraction_identifier'] = '1'
        self.assertTrue(check_extraction_fields(extraction_info))

    def test_missing_group_name(self):
        extraction_info = { 'date_extracted': '1/2/2023',
                            'extraction_identifier': '1',
                            'sample_identifier': 'sample1',
                            'extraction_from':'cultured_isolate',
                            'submitter_plate_id':'CUL',
                            'submitter_plate_well': 'A1',
                            'nucleic_acid_concentration': '1'
                            }
        with self.assertRaises(SystemExit) as cm:
            check_extraction_fields(extraction_info)

        extraction_info['group_name'] = ''
        with self.assertRaises(SystemExit) as cm:
            check_extraction_fields(extraction_info)

        extraction_info['group_name'] = 'abc'
        self.assertTrue(check_extraction_fields(extraction_info))

    def test_missing_extraction_from(self):
        extraction_info = { 'date_extracted': '1/2/2023',
                            'extraction_identifier': '1',
                            'sample_identifier': 'sample1',
                            'group_name': 'Group',
                            'submitter_plate_id':'CUL',
                            'submitter_plate_well': 'A1',
                            'nucleic_acid_concentration': '1'
                            }
        with self.assertRaises(SystemExit) as cm:
            check_extraction_fields(extraction_info)

        extraction_info['extraction_from'] = ''
        with self.assertRaises(SystemExit) as cm:
            check_extraction_fields(extraction_info)

        extraction_info['extraction_from'] = 'cultured_isolate'
        self.assertTrue(check_extraction_fields(extraction_info))

    def test_extraction_from_invalid(self):
        extraction_info = { 'date_extracted': '1/2/2023',
                            'extraction_identifier': '1',
                            'extraction_from': 'invalid_type',
                            'sample_identifier': 'sample1',
                            'group_name': 'Group',
                            'submitter_plate_id':'CUL',
                            'submitter_plate_well': 'A1',
                            'nucleic_acid_concentration': '1'
                            }
        with self.assertRaises(SystemExit) as cm:
            check_extraction_fields(extraction_info)

    def test_nucleic_acid_concentration(self):
        extraction_info = { 'date_extracted': '1/2/2023',
                            'extraction_identifier': '1',
                            'extraction_from': 'cultured_isolate',
                            'sample_identifier': 'sample1',
                            'group_name': 'Group',
                            'submitter_plate_id':'CUL',
                            'submitter_plate_well': 'A1',
                            'nucleic_acid_concentration': None
                            }
        with self.assertRaises(SystemExit) as cm:
            check_extraction_fields(extraction_info)

        extraction_info['nucleic_acid_concentration'] = '1'
        self.assertTrue(check_extraction_fields(extraction_info))

    def test_submitter_plate_well(self):
        extraction_info = { 'date_extracted': '1/2/2023',
                            'extraction_identifier': '1',
                            'extraction_from': 'cultured_isolate',
                            'sample_identifier': 'sample1',
                            'group_name': 'Group',
                            'submitter_plate_id':'CUL',
                            'submitter_plate_well': None,
                            'nucleic_acid_concentration': '1'
                            }
        with self.assertRaises(SystemExit, msg="An empty value for the submitter plate well should raise an error") as cm:
            check_extraction_fields(extraction_info)

        valid_wells = {'A1', 'A2', 'A3', 'A4',  'B1', 'B2', 'B10', 'B11', 'B12', 'C1', 'C2', 'C11', 'C12', 'H8', 'H9', 'H10', 'H11', 'H12'}
        for well in valid_wells:
            extraction_info['submitter_plate_well'] = well
            self.assertTrue(check_extraction_fields(extraction_info))

        invalid_wells = {'A0', 'A13', 'B0', 'B13', 'C0', 'C13', 'H0', 'H 1', 'H13', 'A', 'B', 'C', 'H ', '1', '2', '3', '4', '10', '11', '12', '13'}
        for well in invalid_wells:
            extraction_info['submitter_plate_well'] = well
            with self.assertRaises(SystemExit, msg="An invalid value for the submitter plate well should raise an error") as cm:
                check_extraction_fields(extraction_info)

    def test_check_plate_prefixes(self):
        extraction_info = { 'date_extracted': '1/2/2023',
                            'extraction_identifier': '1',
                            'sample_identifier': 'sample1',
                            'group_name': 'Group',
                            'extraction_from':'cultured_isolate',
                            'submitter_plate_id': '',
                            'submitter_plate_well': 'A1',
                            'nucleic_acid_concentration': '1'
                            }
        with self.assertRaises(SystemExit, msg="An empty value for the submitter plate id should raise an error") as cm:
            check_extraction_fields(extraction_info)

        valid_plate_prefixes = ['EXT', 'CUL', 'SAM', 'OUT']
        for prefix in valid_plate_prefixes:
            extraction_info['submitter_plate_id'] = prefix
            self.assertTrue(check_extraction_fields(extraction_info))

        invalid_plate_prefixes = ['ext', 'cul', 'sam', 'out',  ' EXT', '123EXT', 'xxxx', '1234']
        for prefix in invalid_plate_prefixes:
            extraction_info['submitter_plate_id'] = prefix
            with self.assertRaises(SystemExit, msg="An invalid value for the submitter plate id should raise an error") as cm:
                check_extraction_fields(extraction_info)

    def test_get_extraction_from_empty_database_whole_sample(self):
        self.setUp()
        self.populate_db_dependancies()
        extraction_info = { 'date_extracted': '1/2/2023',
                            'extraction_identifier': '1',
                            'sample_identifier': 'sample1',
                            'group_name': 'Group',
                            'extraction_from':'whole_sample',
                            'submitter_plate_id':'CUL',
                            'submitter_plate_well': 'A1',
                            'nucleic_acid_concentration': '1',
                            'sample_identifier': 'sample1',
                            'extraction_machine': 'KingFisher Flex'
                            }
        result = get_extraction(extraction_info)
        self.assertFalse(result)

    def test_get_extraction_from_empty_database_isolate(self):
        self.setUp()
        self.populate_db_dependancies()
        extraction_info = { 'date_extracted': '1/2/2023',
                            'extraction_identifier': '1',
                            'sample_identifier': 'sample1',
                            'group_name': 'Group',
                            'extraction_from':'cultured_isolate',
                            'submitter_plate_id':'CUL',
                            'submitter_plate_well': 'A1',
                            'nucleic_acid_concentration': '1',
                            'sample_identifier': 'sample1',
                            'extraction_machine': 'KingFisher Flex'
                            }
        result = get_extraction(extraction_info)
        self.assertFalse(result)

    def test_add_extraction_whole_sample(self):
        self.setUp()
        self.populate_db_dependancies()
        extraction_info = { 'date_extracted': '01/01/2023',
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
        add_extraction(extraction_info)
        result = get_extraction(extraction_info)
        self.assertEqual(result.date_extracted.strftime('%d/%m/%Y') , extraction_info['date_extracted'])
        self.assertEqual(result.extraction_identifier, int(extraction_info['extraction_identifier']))
        self.assertEqual(result.extraction_from, extraction_info['extraction_from'])
        self.assertEqual(float(result.nucleic_acid_concentration), float(extraction_info['nucleic_acid_concentration']))
        self.assertEqual(result.extraction_machine, extraction_info['extraction_machine'])
        self.assertEqual(result.extraction_kit, extraction_info['extraction_kit'])
        self.assertEqual(result.what_was_extracted, extraction_info['what_was_extracted'])

    def test_add_extraction_whole_sample_no_matching_sample(self):
        self.setUp()
        self.populate_db_dependancies()
        extraction_info = { 'date_extracted': '01/01/2023',
                            'extraction_identifier': '1',
                            'sample_identifier': 'sample1_doesnt_exist',
                            'group_name': 'Group',
                            'extraction_from':'whole_sample',
                            'submitter_plate_id':'CUL',
                            'submitter_plate_well': 'A1',
                            'nucleic_acid_concentration': '1',
                            'sample_identifier': 'sample1_really_doesnt_exist',
                            'extraction_machine': 'KingFisher Flex',
                            'extraction_kit': 'MagMAX Viral/Pathogen II (MAGMAX-96)',
                            'what_was_extracted': 'ABC',
                            'extraction_processing_institution': 'MLW',
                            }
        with self.assertRaises(SystemExit) as cm:
            add_extraction(extraction_info)

    def test_add_extraction_isolate_without_culture(self):
        self.setUp()
        self.populate_db_dependancies()
        extraction_info = { 'date_extracted': '01/01/2023',
                            'extraction_identifier': '1',
                            'sample_identifier': 'sample1',
                            'group_name': 'Group',
                            'extraction_from':'cultured_isolate',
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
            add_extraction(extraction_info)
        
    def test_add_extraction_isolate(self):
        self.setUp()
        self.populate_db_dependancies()
        add_culture({ 'group_name': 'Group','sample_identifier': 'sample1' , 'date_cultured': '01/01/2023', 'culture_identifier': '123', 'submitter_plate_id': 'CUL123', 'submitter_plate_well': 'A1'})

        extraction_info = { 'date_extracted': '01/01/2023',
                            'extraction_identifier': '1',
                            'sample_identifier': 'sample1',
                            'group_name': 'Group',
                            'extraction_from':'cultured_isolate',
                            'submitter_plate_id':'CUL',
                            'submitter_plate_well': 'A1',
                            'nucleic_acid_concentration': '1',
                            'extraction_machine': 'KingFisher Flex',
                            'extraction_kit': 'MagMAX Viral/Pathogen II (MAGMAX-96)',
                            'what_was_extracted': 'ABC',
                            'extraction_processing_institution': 'MLW',
                            'culture_identifier': '123',
                            'date_cultured': '01/01/2023',
                            }
        add_extraction(extraction_info)
        result = get_extraction(extraction_info)
        self.assertEqual(result.date_extracted.strftime('%d/%m/%Y') , extraction_info['date_extracted'])
        self.assertEqual(result.extraction_identifier, int(extraction_info['extraction_identifier']))
        self.assertEqual(result.extraction_from, extraction_info['extraction_from'])
        self.assertEqual(float(result.nucleic_acid_concentration), float(extraction_info['nucleic_acid_concentration']))
        self.assertEqual(result.extraction_machine, extraction_info['extraction_machine'])
        self.assertEqual(result.extraction_kit, extraction_info['extraction_kit'])
        self.assertEqual(result.what_was_extracted, extraction_info['what_was_extracted'])

