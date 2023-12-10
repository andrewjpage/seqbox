import sys
import os
from flask_testing import TestCase
import datetime
import tempfile
sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')
from app import app, db
from app.models import Mykrobe
from scripts.utils.check import check_mykrobe_res
from scripts.utils.db import (
    read_in_mykrobe,
    rename_dodgy_mykrobe_variables,
    add_culture,
    add_mykrobe_result,
    get_mykrobe_result,
    add_raw_sequencing_batch,add_extraction,
    add_group,
    add_project,
    add_sample_source,
    add_sample,
    add_readset_batch,
    add_readset
)

class TestSeqboxUtilsMykrobe(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app
    
    # reset the database before you start
    def setUp(self):
        assert os.environ['DATABASE_URL'].split('/')[3].startswith('test') # you really dont want to delete a production DB
        db.drop_all()
        db.create_all()

    def populate_db(self, temp_dir):
        add_group({'group_name': 'Group', 'institution': 'MLW', 'pi': 'PI'})
        add_project({'project_name': 'Project', 'group_name': 'Group', 'institution': 'MLW', 'project_details': 'seq'})
        add_sample_source({'projects': 'Project', 'group_name': 'Group', 'institution': 'MLW', 'sample_source_identifier': 'sample_source_1', 'sample_source_type': 'patient', 'latitude': 1.23, 'longitude': -12.3, 'country': 'UK', 'location_first_level': 'Essex', 'city': 'London', 'township': 'Docklands', 'notes': 'note'})
        add_sample({'sample_identifier': 'sample1', 'sample_source_identifier': 'sample_source_1', 'institution': 'MLW', 'group_name': 'Group', 'species': 'SARS-CoV-2', 'sample_type': 'Lung aspirate', 'day_collected': '31', 'month_collected': '5', 'year_collected': '2021', 'day_received': '1', 'month_received': '1', 'year_received': '2022', 'sequencing_type_requested':'MinION SARS-CoV-2'}, False)
        add_culture({ 'group_name': 'Group','sample_identifier': 'sample1' , 'date_cultured': '01/01/2023', 'culture_identifier': '123', 'submitter_plate_id': 'CUL123', 'submitter_plate_well': 'A1'})
        add_extraction({ 'date_extracted': '01/01/2023','extraction_identifier': '1','sample_identifier': 'sample1', 'group_name': 'Group','extraction_from':'cultured_isolate', 'submitter_plate_id':'CUL','submitter_plate_well': 'A1','nucleic_acid_concentration': '1', 'sample_identifier': 'sample1','extraction_machine': 'KingFisher Flex','extraction_kit': 'MagMAX Viral/Pathogen II (MAGMAX-96)', 'what_was_extracted': 'ABC','extraction_processing_institution': 'MLW', 'culture_identifier': '123', 'date_cultured': '01/01/2023' })
        add_raw_sequencing_batch({'date_run': '01/01/2023', 'sequencing_type': 'nanopore', 'batch_name': 'ABC', 'instrument_model': 'MinION', 'instrument_name': 'ABC123', 'sequencing_centre': 'MLW', 'flowcell_type': 'R12.3', 'batch_directory': str(temp_dir) })
        add_readset_batch( {'raw_sequencing_batch_name': 'ABC', 'readset_batch_name': 'EFG', 'readset_batch_dir': str(temp_dir), 'basecaller': 'guppy' } )

        base_fastq_dir = os.path.join(temp_dir, 'fastq_pass', 'barcode01')
        base_fast5_dir = os.path.join(temp_dir, 'fast5_pass', 'barcode01')
        os.makedirs(base_fastq_dir)
        os.makedirs(base_fast5_dir)
        temp_fastq_file = os.path.join(base_fastq_dir,'abc.fastq.gz')
        temp_fast5_file = os.path.join(base_fast5_dir,'abc.fast5')
        # create an empty file
        open(temp_fastq_file, 'a').close()
        open(temp_fast5_file, 'a').close()

        readset_info = {'data_storage_device': 'storage_device_1', 
                        'readset_batch_name': 'EFG', 
                        'date_extracted': '01/01/2023', 
                        'extraction_identifier': '1',
                        'sample_identifier': 'sample1',
                        'group_name': 'Group',
                        'date_tiling_pcred': '01/01/2023',
                        'tiling_pcr_identifier':'5',
                        'path_fastq': temp_fastq_file,
                        'path_fast5': temp_fast5_file,
                        'extraction_from':'cultured_isolate',
                        'submitter_plate_id':'CUL',
                        'submitter_plate_well': 'A1',
                        'extraction_processing_institution': 'MLW',
                        'culture_identifier': '123',
                        'date_cultured': '01/01/2023',
                        'readset_identifier': '1',
                        }
        add_readset(readset_info, False, False)


    def test_check_mykrobe_res(self):
        self.assertEqual(None,check_mykrobe_res({'sample': 'sample1', 'drug': 'pen', 'susceptibility': 'resistant','mykrobe_version': '1.2.3' }))

        #empty
        with self.assertRaises(SystemExit) as cm:
            check_mykrobe_res({'sample': '', 'drug': 'pen', 'susceptibility': 'resistant','mykrobe_version': '1.2.3' })
        with self.assertRaises(SystemExit) as cm:
            check_mykrobe_res({'sample': 'sample1', 'drug': '', 'susceptibility': 'resistant','mykrobe_version': '1.2.3' })
        with self.assertRaises(SystemExit) as cm:
            check_mykrobe_res({'sample': 'sample1', 'drug': 'pen', 'susceptibility': '','mykrobe_version': '1.2.3' })
        with self.assertRaises(SystemExit) as cm:
            check_mykrobe_res({'sample': 'sample1', 'drug': 'pen', 'susceptibility': 'resistant','mykrobe_version': '' })
        #missing
        with self.assertRaises(SystemExit) as cm:
            check_mykrobe_res({ 'drug': 'pen', 'susceptibility': 'resistant','mykrobe_version': '1.2.3' })
        with self.assertRaises(SystemExit) as cm:
            check_mykrobe_res({'sample': 'sample1', 'susceptibility': 'resistant','mykrobe_version': '1.2.3' })
        with self.assertRaises(SystemExit) as cm:
            check_mykrobe_res({'sample': 'sample1', 'drug': 'pen','mykrobe_version': '1.2.3' })
        with self.assertRaises(SystemExit) as cm:
            check_mykrobe_res({'sample': 'sample1', 'drug': 'pen', 'susceptibility': 'resistant' })

    def test_read_in_mykrobe(self):
        mykrobe_result_info = {'sample': 'sample1', 
                               'drug': 'pen', 
                               'susceptibility': 'resistant',
                               'mykrobe_version': '1.2.3',
                               'variants': 'A123T',
                               'genes': 'bla',
                               'phylo_group': 'A',
                               'species': 'Salmonella enterica',
                               'lineage': '1a',
                               'phylo_group_per_covg': '1',
                               'species_per_covg': '1',
                               'lineage_per_covg':  '1',   
                               'phylo_group_depth': '10',
                               'species_depth': '10',    
                               'lineage_depth':   '10',           
                               }
        self.assertIsInstance(read_in_mykrobe(mykrobe_result_info), Mykrobe)

    def test_get_mykrobe_result_empty(self):
        self.setUp()
        mykrobe_result_info = {'sample': 'sample1', 
                               'drug': 'pen', 
                               'susceptibility': 'resistant',
                               'mykrobe_version': '1.2.3',
                               'variants': 'A123T',
                               'genes': 'bla',
                               'phylo_group': 'A',
                               'species': 'Salmonella enterica',
                               'lineage': '1a',
                               'phylo_group_per_covg': '1',
                               'species_per_covg': '1',
                               'lineage_per_covg':  '1',   
                               'phylo_group_depth': '10',
                               'species_depth': '10',    
                               'lineage_depth':   '10',     
                               'readset_identifier': '1',
                               }
        self.assertFalse(get_mykrobe_result(mykrobe_result_info))

    def test_add_mykrobe_result(self):
        self.setUp()
        with tempfile.TemporaryDirectory() as temp_dir:
            self.populate_db(temp_dir)
            mykrobe_result_info = {'sample': 'sample1', 
                               'drug': 'pen', 
                               'susceptibility': 'resistant',
                               'mykrobe_version': '1.2.3',
                               'variants': 'A123T',
                               'genes': 'bla',
                               'phylo_group': 'A',
                               'species': 'Salmonella enterica',
                               'lineage': '1a',
                               'phylo_group_per_covg': '1',
                               'species_per_covg': '1',
                               'lineage_per_covg':  '1',   
                               'phylo_group_depth': '10',
                               'species_depth': '10',    
                               'lineage_depth':   '10',     
                               'readset_identifier': '1',
                               }
            add_mykrobe_result(mykrobe_result_info)
            result = get_mykrobe_result(mykrobe_result_info)
            self.assertIsInstance(result, Mykrobe)

    def test_add_mykrobe_result_duplicate(self):
        self.setUp()
        with tempfile.TemporaryDirectory() as temp_dir:
            self.populate_db(temp_dir)
            mykrobe_result_info = {'sample': 'sample1', 
                               'drug': 'pen', 
                               'susceptibility': 'resistant',
                               'mykrobe_version': '1.2.3',
                               'variants': 'A123T',
                               'genes': 'bla',
                               'phylo_group': 'A',
                               'species': 'Salmonella enterica',
                               'lineage': '1a',
                               'phylo_group_per_covg': '1',
                               'species_per_covg': '1',
                               'lineage_per_covg':  '1',   
                               'phylo_group_depth': '10',
                               'species_depth': '10',    
                               'lineage_depth':   '10',     
                               'readset_identifier': '1',
                               'sample_identifier': 'sample1',
                               'group_name': 'Group',
                               }
            add_mykrobe_result(mykrobe_result_info)
            add_mykrobe_result(mykrobe_result_info)
            with self.assertRaises(SystemExit) as cm:
                get_mykrobe_result(mykrobe_result_info)

    def test_rename_dodgy_mykrobe_variables(self):
        mykrobe_result_info = {'variants (dna_variant-AA_variant:ref_kmer_count:alt_kmer_count:conf) [use --format json for more info]': 'A123T',
                               'genes (prot_mut-ref_mut:percent_covg:depth) [use --format json for more info]': 'bla'
                               }
        result = rename_dodgy_mykrobe_variables(mykrobe_result_info)
        self.assertEqual(result['variants'], 'A123T')
        self.assertEqual(result['genes'], 'bla')
