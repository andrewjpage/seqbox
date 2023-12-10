import sys
import os
from flask_testing import TestCase
import datetime
sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')
from app import app, db
from scripts.utils.check import check_raw_sequencing_batch
from scripts.utils.db import get_raw_sequencing_batch, add_raw_sequencing_batch

class TestSeqboxUtilsRawSequencingBatches(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app
    
    # reset the database before you start
    def setUp(self):
        assert os.environ['DATABASE_URL'].split('/')[3].startswith('test') # you really dont want to delete a production DB
        db.drop_all()
        db.create_all()

    def test_get_raw_sequencing_batch_empty_db(self):
        self.setUp()
        raw_sequencing_batch_info = {'batch_name': 'ABCs' }
        self.assertEqual(get_raw_sequencing_batch(raw_sequencing_batch_info['batch_name']), False)

    def test_add_raw_sequencing_batch(self):
        self.setUp()
        raw_sequencing_batch_info = {'date_run': '01/01/2023',
                                     'sequencing_type': 'nanopore',
                                     'batch_name': 'ABC',
                                     'instrument_model': 'MinION',
                                     'instrument_name': 'ABC123',
                                     'sequencing_centre': 'MLW',
                                     'flowcell_type': 'R12.3',
                                     'sequencing_type': 'WGS',
                                     'batch_directory': '/path/to/dir'
                                     }
        add_raw_sequencing_batch(raw_sequencing_batch_info)
        batch = get_raw_sequencing_batch(raw_sequencing_batch_info['batch_name'])
        self.assertTrue(batch.name, 'ABC')

    def test_check_raw_sequencing_batch(self):
        self.assertTrue(check_raw_sequencing_batch({'date_run': '01/01/2023', 'sequencing_type': 'nanopore', 'batch_name': 'ABC', 'instrument_model': 'MinION', 'instrument_name': 'ABC123', 'sequencing_centre': 'MLW', 'flowcell_type': 'R12.3', 'sequencing_type': 'WGS', 'batch_directory': '/path/to/dir' }))

        # empty
        with self.assertRaises(SystemExit) as cm:
            check_raw_sequencing_batch({'date_run': '', 'sequencing_type': 'nanopore', 'batch_name': 'ABC', 'instrument_model': 'MinION', 'instrument_name': 'ABC123', 'sequencing_centre': 'MLW', 'flowcell_type': 'R12.3', 'sequencing_type': 'WGS', 'batch_directory': '/path/to/dir' })
        with self.assertRaises(SystemExit) as cm:
            check_raw_sequencing_batch({'date_run': '01/01/2023', 'sequencing_type': 'nanopore', 'batch_name': 'ABC', 'instrument_model': 'MinION', 'instrument_name': 'ABC123', 'sequencing_centre': 'MLW', 'flowcell_type': 'R12.3', 'sequencing_type': 'WGS', 'batch_directory': '' })
        with self.assertRaises(SystemExit) as cm:
            check_raw_sequencing_batch({'date_run': '01/01/2023', 'sequencing_type': 'nanopore', 'batch_name': '', 'instrument_model': 'MinION', 'instrument_name': 'ABC123', 'sequencing_centre': 'MLW', 'flowcell_type': 'R12.3', 'sequencing_type': 'WGS', 'batch_directory': '/path/to/dir' })
        with self.assertRaises(SystemExit) as cm:
            check_raw_sequencing_batch({'date_run': '01/01/2023', 'sequencing_type': 'nanopore', 'batch_name': 'ABC', 'instrument_model': 'MinION', 'instrument_name': 'ABC123', 'sequencing_centre': 'MLW', 'flowcell_type': 'R12.3', 'sequencing_type': '', 'batch_directory': '/path/to/dir' })
        with self.assertRaises(SystemExit) as cm:
            check_raw_sequencing_batch({'date_run': '01/01/2023', 'sequencing_type': 'nanopore', 'batch_name': 'ABC', 'instrument_model': 'MinION', 'instrument_name': '', 'sequencing_centre': 'MLW', 'flowcell_type': 'R12.3', 'sequencing_type': 'WGS', 'batch_directory': '/path/to/dir' })
        with self.assertRaises(SystemExit) as cm:
            check_raw_sequencing_batch({'date_run': '01/01/2023', 'sequencing_type': 'nanopore', 'batch_name': 'ABC', 'instrument_model': 'MinION', 'instrument_name': 'ABC123', 'sequencing_centre': 'MLW', 'flowcell_type': '', 'sequencing_type': 'WGS', 'batch_directory': '/path/to/dir' })

        # missing
        with self.assertRaises(SystemExit) as cm:
            check_raw_sequencing_batch({ 'sequencing_type': 'nanopore', 'batch_name': 'ABC', 'instrument_model': 'MinION', 'instrument_name': 'ABC123', 'sequencing_centre': 'MLW', 'flowcell_type': 'R12.3', 'sequencing_type': 'WGS', 'batch_directory': '/path/to/dir' })
        with self.assertRaises(SystemExit) as cm:
            check_raw_sequencing_batch({'date_run': '01/01/2023', 'sequencing_type': 'nanopore', 'batch_name': 'ABC', 'instrument_model': 'MinION', 'instrument_name': 'ABC123', 'sequencing_centre': 'MLW', 'flowcell_type': 'R12.3', 'sequencing_type': 'WGS' })
        with self.assertRaises(SystemExit) as cm:
            check_raw_sequencing_batch({'date_run': '01/01/2023', 'sequencing_type': 'nanopore',  'instrument_model': 'MinION', 'instrument_name': 'ABC123', 'sequencing_centre': 'MLW', 'flowcell_type': 'R12.3', 'sequencing_type': 'WGS', 'batch_directory': '/path/to/dir' })
        with self.assertRaises(SystemExit) as cm:
            check_raw_sequencing_batch({'date_run': '01/01/2023', 'sequencing_type': 'nanopore', 'batch_name': 'ABC', 'instrument_model': 'MinION', 'instrument_name': '', 'sequencing_centre': 'MLW', 'flowcell_type': 'R12.3', 'sequencing_type': 'WGS', 'batch_directory': '/path/to/dir' })
        with self.assertRaises(SystemExit) as cm:
            check_raw_sequencing_batch({'date_run': '01/01/2023', 'sequencing_type': 'nanopore', 'batch_name': 'ABC', 'instrument_model': 'MinION', 'instrument_name': 'ABC123', 'sequencing_centre': 'MLW', 'sequencing_type': 'WGS', 'batch_directory': '/path/to/dir' })

    # TODO: prevent adding twice before adding
    def test_add_batch_twice(self):
        self.setUp()
        raw_sequencing_batch_info = {'date_run': '01/01/2023',
                                     'sequencing_type': 'nanopore',
                                     'batch_name': 'ABC',
                                     'instrument_model': 'MinION',
                                     'instrument_name': 'ABC123',
                                     'sequencing_centre': 'MLW',
                                     'flowcell_type': 'R12.3',
                                     'sequencing_type': 'WGS',
                                     'batch_directory': '/path/to/dir'
                                     }
        add_raw_sequencing_batch(raw_sequencing_batch_info)
        add_raw_sequencing_batch(raw_sequencing_batch_info)
        with self.assertRaises(SystemExit) as cm:
            get_raw_sequencing_batch(raw_sequencing_batch_info['batch_name'])
