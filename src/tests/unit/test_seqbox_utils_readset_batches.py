import sys
import os
from flask_testing import TestCase
import datetime
sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')
from app import app, db
from seqbox_utils import  get_readset_batch, add_readset_batch, read_in_readset_batch, check_readset_batches

class TestSeqboxUtilsRawSequencingBatches(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app
    
    # reset the database before you start
    def setUp(self):
        assert os.environ['DATABASE_URL'].split('/')[3].startswith('test') # you really dont want to delete a production DB
        db.drop_all()
        db.create_all()

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
