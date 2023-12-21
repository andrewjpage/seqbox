import sys
import os
from flask_testing import TestCase
import datetime
sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')
from app import app, db
from app.models import  PcrAssay, Sample, PcrResult
from scripts.utils.check import check_pcr_result
from scripts.utils.db import (
    add_pcr_result,
    get_pcr_result,
    add_group,
    add_project,
    add_sample_source,
    add_sample,
    add_pcr_assay,
    read_in_pcr_result
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
        add_sample({'sample_identifier': 'sample1', 'sample_source_identifier': 'sample_source_1', 'institution': 'MLW', 'group_name': 'Group', 'species': 'SARS-CoV-2', 'sample_type': 'Lung aspirate', 'day_collected': '31', 'month_collected': '5', 'year_collected': '2021', 'day_received': '1', 'month_received': '1', 'year_received': '2022', 'sequencing_type_requested':'MinION SARS-CoV-2'}, False)
        add_pcr_assay({'assay_name': 'SARS-CoV2-CDC-N1'})

    def test_get_result_if_none_exist(self):
        self.setUp()
        self.populate_db_dependancies()
        pcr_result_info = {'date_pcred': '01/06/2021',
                           'pcr_identifier': '1',
                           'assay_name': 'SARS-CoV2-CDC-N1',
                           'sample_identifier': 'sample1',
                           'pcr_result': 'Positive',
                           'assay': 'xxxx',
                           'group_name': 'Group'
                           }
        self.assertFalse(get_pcr_result(pcr_result_info))

    def test_add_result(self):
        self.setUp()
        self.populate_db_dependancies()
        pcr_result_info = {'date_pcred': '01/06/2021',
                           'pcr_identifier': '1',
                           'assay_name': 'SARS-CoV2-CDC-N1',
                           'sample_identifier': 'sample1',
                           'pcr_result': 'Positive',
                           'assay': 'xxxx',
                           'group_name': 'Group',
                           'ct': '20.1'
                           }
        add_pcr_result(pcr_result_info)
        result = get_pcr_result(pcr_result_info)
        #self.assertEqual(result.date_pcred.strftime('%d/%m/%Y'), '01/06/2021') #Update docker dateformat not to use US format
        self.assertEqual(result.pcr_identifier, 1)
        self.assertEqual(PcrAssay.query.filter_by(id=result.pcr_assay_id).first().assay_name, 'SARS-CoV2-CDC-N1')
        self.assertEqual(Sample.query.filter_by(id=result.sample_id).first().sample_identifier, 'sample1')
        self.assertEqual(result.pcr_result, 'Positive')
        self.assertAlmostEqual(float(result.ct), 20.1, places=1)
        self.assertEqual(result.notes, None)
        self.assertEqual(result.institution, None)

    def test_add_two_results_on_same_day_for_one_sample(self):
        self.setUp()
        self.populate_db_dependancies()
        pcr_result_info = {'date_pcred': '01/06/2021',
                           'pcr_identifier': '1',
                           'assay_name': 'SARS-CoV2-CDC-N1',
                           'sample_identifier': 'sample1',
                           'pcr_result': 'Positive',
                           'assay': 'xxxx',
                           'group_name': 'Group',
                           'ct': '20.1'
                           }
        add_pcr_result(pcr_result_info)
        self.assertEqual(len(Sample.query.filter_by(sample_identifier='sample1').first().pcr_results), 1, msg='The single sample should have one pcr result assosiated with it')

        pcr_result_info['pcr_identifier'] = '2'
        add_pcr_result(pcr_result_info)
        self.assertEqual(len(Sample.query.filter_by(sample_identifier='sample1').first().pcr_results), 2, msg='The single sample should have two pcr results assosiated with it')

        result2 = get_pcr_result(pcr_result_info)
        pcr_result_info['pcr_identifier'] = '1'
        result1 = get_pcr_result(pcr_result_info)

        self.assertNotEqual(result1.id, result2.id)
        self.assertEqual(PcrAssay.query.filter_by(id=result1.pcr_assay_id).first().assay_name, PcrAssay.query.filter_by(id=result2.pcr_assay_id).first().assay_name)
        self.assertEqual(Sample.query.filter_by(id=result1.sample_id).first().sample_identifier, Sample.query.filter_by(id=result2.sample_id).first().sample_identifier)
        self.assertEqual(result1.pcr_result, result2.pcr_result)
        self.assertEqual(result1.ct, result2.ct)

    def test_add_same_result_twice(self):
        self.setUp()
        self.populate_db_dependancies()
        pcr_result_info = {'date_pcred': '01/06/2021',
                           'pcr_identifier': '1',
                           'assay_name': 'SARS-CoV2-CDC-N1',
                           'sample_identifier': 'sample1',
                           'pcr_result': 'Positive',
                           'assay': 'xxxx',
                           'group_name': 'Group',
                           'ct': '20.1'
                           }
        add_pcr_result(pcr_result_info)
        with self.assertRaises(SystemExit) as cm:
            add_pcr_result(pcr_result_info)

    def test_add_pcr_result_missing_sample_identifier(self):
        self.setUp()
        self.populate_db_dependancies()
        pcr_result_info = {'date_pcred': '01/06/2021', 'pcr_identifier': '1', 'assay_name': 'SARS-CoV2-CDC-N1', 'pcr_result': 'Positive', 'assay': 'xxxx', 'group_name': 'Group', 'ct': '20.1'}
        self.assertFalse(check_pcr_result(pcr_result_info))
        with self.assertRaises(SystemExit) as cm:
            add_pcr_result(pcr_result_info)

    def test_add_pcr_result_missing_date_pcred(self):
        self.setUp()
        self.populate_db_dependancies()
        pcr_result_info = { 'pcr_identifier': '1', 'assay_name': 'SARS-CoV2-CDC-N1','sample_identifier': 'sample1', 'pcr_result': 'Positive', 'assay': 'xxxx', 'group_name': 'Group', 'ct': '20.1'}
        self.assertFalse(check_pcr_result(pcr_result_info))
        with self.assertRaises(SystemExit) as cm:
            add_pcr_result(pcr_result_info)

    def test_add_pcr_result_missing_pcr_identifier(self):
        self.setUp()
        self.populate_db_dependancies()
        pcr_result_info = {'date_pcred': '01/06/2021', 'assay_name': 'SARS-CoV2-CDC-N1','sample_identifier': 'sample1', 'pcr_result': 'Positive', 'assay': 'xxxx', 'group_name': 'Group', 'ct': '20.1'}
        self.assertFalse(check_pcr_result(pcr_result_info))
        with self.assertRaises(SystemExit) as cm:
            add_pcr_result(pcr_result_info)

    def test_add_pcr_result_missing_group_name(self):
        self.setUp()
        self.populate_db_dependancies()
        pcr_result_info = {'date_pcred': '01/06/2021', 'pcr_identifier': '1', 'assay_name': 'SARS-CoV2-CDC-N1','sample_identifier': 'sample1', 'pcr_result': 'Positive', 'assay': 'xxxx', 'ct': '20.1'}
        self.assertFalse(check_pcr_result(pcr_result_info))
        with self.assertRaises(SystemExit) as cm:
            add_pcr_result(pcr_result_info)

    def test_add_pcr_result_missing_assay_name(self):
        self.setUp()
        self.populate_db_dependancies()
        pcr_result_info = {'date_pcred': '01/06/2021', 'pcr_identifier': '1', 'sample_identifier': 'sample1', 'pcr_result': 'Positive', 'assay': 'xxxx', 'group_name': 'Group', 'ct': '20.1'}
        self.assertFalse(check_pcr_result(pcr_result_info))
        with self.assertRaises(SystemExit) as cm:
            add_pcr_result(pcr_result_info)

    def test_add_pcr_result_allowable(self):
        self.setUp()
        self.populate_db_dependancies()
        pcr_result_info = {'date_pcred': '01/06/2021', 'pcr_identifier': '1', 'assay_name': 'SARS-CoV2-CDC-N1', 'sample_identifier': 'sample1', 'pcr_result': 'Positive', 'assay': 'xxxx', 'group_name': 'Group', 'ct': '20.1'}

        for valid_result in ['Negative', 'Negative - Followup', 'Positive - Followup', 'Positive', 'Indeterminate', 'Not Done']:
            pcr_result_info['pcr_result'] = valid_result
            self.assertTrue(check_pcr_result(pcr_result_info))

    def test_add_pcr_result_notallowable(self):
        self.setUp()
        self.populate_db_dependancies()
        pcr_result_info = {'date_pcred': '01/06/2021', 'pcr_identifier': '1', 'assay_name': 'SARS-CoV2-CDC-N1', 'sample_identifier': 'sample1', 'pcr_result': 'xxxx', 'assay': 'xxxx', 'group_name': 'Group', 'ct': '20.1'}

        for invalid_result in [' Negative', ' Negative ', 'xNegative - Followup', 'Positive - xxxx', 'Possssitive', 'Indeterminate\n', 'not done']:
            pcr_result_info['pcr_result'] = invalid_result
            with self.assertRaises(ValueError) as cm:
                check_pcr_result(pcr_result_info)

    def test_add_result_sample_doesnt_exist(self):
        self.setUp()
        self.populate_db_dependancies()
        pcr_result_info = {'date_pcred': '01/06/2021',
                           'pcr_identifier': '1',
                           'assay_name': 'SARS-CoV2-CDC-N1',
                           'sample_identifier': 'sample1_doesnt_exist',
                           'pcr_result': 'Positive',
                           'assay': 'xxxx',
                           'group_name': 'Group',
                           'ct': '20.1'
                           }
        with self.assertRaises(SystemExit) as cm:
            add_pcr_result(pcr_result_info)

    def test_add_result_assay_doesnt_exist(self):
        self.setUp()
        self.populate_db_dependancies()
        pcr_result_info = {'date_pcred': '01/06/2021',
                           'pcr_identifier': '1',
                           'assay_name': 'assay_doesnt_exist',
                           'sample_identifier': 'sample1',
                           'pcr_result': 'Positive',
                           'assay': 'xxxx',
                           'group_name': 'Group',
                           'ct': '20.1'
                           }
        with self.assertRaises(SystemExit) as cm:
            add_pcr_result(pcr_result_info)

    def test_read_in_pcr_result_missing_ct(self):
        self.setUp()
        self.populate_db_dependancies()
        pcr_result_info = {'date_pcred': '01/06/2021',
                           'pcr_identifier': '1',
                           'assay_name': 'SARS-CoV2-CDC-N1',
                           'sample_identifier': 'sample1',
                           'pcr_result': 'Positive',
                           'assay': 'xxxx',
                           'group_name': 'Group',
                           'ct': ''
                           }
        self.assertIsInstance(read_in_pcr_result(pcr_result_info), PcrResult)

    def test_read_in_pcr_result_no_matching(self):
        self.setUp()
        self.populate_db_dependancies()
        pcr_result_info = {'date_pcred': '01/06/2021', 'pcr_identifier': '1', 'assay_name': 'SARS-CoV2-CDC-N1', 'pcr_result': 'Positive', 'assay': 'xxxx', 'group_name': 'Group', 'ct': '20.1'}
        with self.assertRaises(SystemExit) as cm:
            read_in_pcr_result(pcr_result_info)
            