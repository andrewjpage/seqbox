import sys
import os
from flask_testing import TestCase
sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')
from app import app, db
from seqbox_utils import get_pcr_assay, add_pcr_assay

class TestSeqboxUtilsProjects(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app
    
    # reset the database before you start
    def setUp(self):
        assert os.environ['DATABASE_URL'].split('/')[3].startswith('test') # you really dont want to delete a production DB
        db.drop_all()
        db.create_all()

    def test_get_assay_where_none_exist_already(self):
        self.setUp()
        assay_info = {'assay_name': 'SARS-CoV2-CDC-N1'}
        matching_assay = get_pcr_assay(assay_info)
        self.assertEqual(False, matching_assay)

    def test_add_assay(self):
        self.setUp()
        assay_info = {'assay_name': 'SARS-CoV2-CDC-N1'}
        matching_assay = get_pcr_assay(assay_info)
        self.assertEqual(False, matching_assay)

        add_pcr_assay(assay_info)
        matching_assay = get_pcr_assay(assay_info)
        self.assertEqual(matching_assay.assay_name, 'SARS-CoV2-CDC-N1')

    def test_add_assay_duplicate(self):
        self.setUp()
        self.assertTrue(add_pcr_assay({'assay_name': 'SARS-CoV2-CDC-N1'}))
        self.assertFalse(add_pcr_assay({'assay_name': 'SARS-CoV2-CDC-N1'}))

