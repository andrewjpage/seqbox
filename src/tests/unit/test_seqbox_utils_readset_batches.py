import sys
import os
from flask_testing import TestCase
import datetime
sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')
from app import app, db
from seqbox_utils import  get_readset_batch, add_readset_batch, check_readset_batches, add_raw_sequencing_batch

class TestSeqboxUtilsReadSetBatches(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app
    
    # reset the database before you start
    def setUp(self):
        assert os.environ['DATABASE_URL'].split('/')[3].startswith('test') # you really dont want to delete a production DB
        db.drop_all()
        db.create_all()

    def populate_db(self):
        add_raw_sequencing_batch({'date_run': '01/01/2023', 'sequencing_type': 'nanopore', 'batch_name': 'ABC', 'instrument_model': 'MinION', 'instrument_name': 'ABC123', 'sequencing_centre': 'MLW', 'flowcell_type': 'R12.3', 'sequencing_type': 'WGS', 'batch_directory': '/path/to/dir' })

    def test_check_readset_batches(self):
        self.assertTrue(check_readset_batches({'raw_sequencing_batch_name': 'ABC', 'readset_batch_name': 'EFG', 'readset_batch_dir': '/path/to/dir', 'basecaller': 'guppy' }))
        # empty
        with self.assertRaises(SystemExit) as cm:
            check_readset_batches({'raw_sequencing_batch_name': '', 'readset_batch_name': 'EFG', 'readset_batch_dir': '/path/to/dir', 'basecaller': 'guppy' })
        with self.assertRaises(SystemExit) as cm:
            check_readset_batches({'raw_sequencing_batch_name': 'ABC', 'readset_batch_name': '', 'readset_batch_dir': '/path/to/dir', 'basecaller': 'guppy' })
        with self.assertRaises(SystemExit) as cm:
            check_readset_batches({'raw_sequencing_batch_name': 'ABC', 'readset_batch_name': 'EFG', 'readset_batch_dir': '', 'basecaller': 'guppy' })
        with self.assertRaises(SystemExit) as cm:
            check_readset_batches({'raw_sequencing_batch_name': 'ABC', 'readset_batch_name': 'EFG', 'readset_batch_dir': '/path/to/dir', 'basecaller': '' })
        # missing
        with self.assertRaises(SystemExit) as cm:
            check_readset_batches({'readset_batch_name': 'EFG', 'readset_batch_dir': '/path/to/dir', 'basecaller': 'guppy' })
        with self.assertRaises(SystemExit) as cm:
            check_readset_batches({'raw_sequencing_batch_name': 'ABC',   'readset_batch_dir': '/path/to/dir', 'basecaller': 'guppy' })
        with self.assertRaises(SystemExit) as cm:
            check_readset_batches({'raw_sequencing_batch_name': 'ABC', 'readset_batch_name': 'EFG',  'basecaller': 'guppy' })
        with self.assertRaises(SystemExit) as cm:
            check_readset_batches({'raw_sequencing_batch_name': 'ABC', 'readset_batch_name': 'EFG', 'readset_batch_dir': '/path/to/dir' })

    def test_get_readset_batch_empty_db(self):
        self.setUp()
        readset_batch_info = {'raw_sequencing_batch_name': 'ABC', 
                              'readset_batch_name': 'EFG', 
                              'readset_batch_dir': '/path/to/dir', 
                              'basecaller': 'guppy' 
                            }
        self.assertEqual(get_readset_batch(readset_batch_info), False)

    def test_add_readset_batch(self):
        self.setUp()
        self.populate_db()
        readset_batch_info = {'raw_sequencing_batch_name': 'ABC', 
                              'readset_batch_name': 'EFG', 
                              'readset_batch_dir': '/path/to/dir', 
                              'basecaller': 'guppy' 
                            }
        add_readset_batch(readset_batch_info)
        batch = get_readset_batch(readset_batch_info)
        self.assertTrue(batch.name, 'EFG')

    def test_add_readset_batch_twice(self):
        self.setUp()
        self.populate_db()
        readset_batch_info = {'raw_sequencing_batch_name': 'ABC', 
                              'readset_batch_name': 'EFG', 
                              'readset_batch_dir': '/path/to/dir', 
                              'basecaller': 'guppy' 
                            }
        add_readset_batch(readset_batch_info)
        add_readset_batch(readset_batch_info)
        with self.assertRaises(SystemExit) as cm:
            get_readset_batch(readset_batch_info)

    def test_add_readset_batch_raw_sequencing_batch_doesnt_exist(self):
        self.setUp()
        self.populate_db()
        readset_batch_info = {'raw_sequencing_batch_name': 'doesnt_exist', 
                              'readset_batch_name': 'EFG', 
                              'readset_batch_dir': '/path/to/dir', 
                              'basecaller': 'guppy' 
                            }
        with self.assertRaises(SystemExit) as cm:
            add_readset_batch(readset_batch_info)
