import sys
import os
from flask_testing import TestCase
import datetime
import tempfile
sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')
from app import app, db
from app.models import ArticCovidResult, ReadSetNanopore
from scripts.utils.db import (
    read_in_artic_covid_result,
    check_artic_covid_result,
    get_readset,
    add_artic_covid_result,
    get_artic_covid_result,
    add_raw_sequencing_batch,
    get_nanopore_readset_from_batch_and_barcode,
    add_extraction,
    add_tiling_pcr,
    add_group,
    add_project,
    add_sample_source,
    add_sample,
    add_readset_batch,
    add_readset
)

class TestSeqboxUtilsArticWorkflows(TestCase):
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
            add_extraction({ 'date_extracted': '01/01/2023','extraction_identifier': '1','sample_identifier': 'sample1','group_name': 'Group','extraction_from':'whole_sample','submitter_plate_id':'CUL','submitter_plate_well': 'A1','nucleic_acid_concentration': '1','sample_identifier': 'sample1','extraction_machine': 'KingFisher Flex','extraction_kit': 'MagMAX Viral/Pathogen II (MAGMAX-96)','what_was_extracted': 'ABC','extraction_processing_institution': 'MLW' })
            add_raw_sequencing_batch({'date_run': '01/01/2023', 'sequencing_type': 'nanopore', 'batch_name': 'ABC', 'instrument_model': 'MinION', 'instrument_name': 'ABC123', 'sequencing_centre': 'MLW', 'flowcell_type': 'R12.3', 'batch_directory': str(temp_dir) })
            add_readset_batch( {'raw_sequencing_batch_name': 'ABC', 'readset_batch_name': 'EFG', 'readset_batch_dir': str(temp_dir), 'basecaller': 'guppy' } )
            add_tiling_pcr({'sample_identifier': 'sample1', 'date_extracted': '01/01/2023', 'extraction_identifier': '3', 'date_tiling_pcred': '01/01/2023', 'tiling_pcr_identifier': '5', 'group_name': 'Group', 'tiling_pcr_protocol': 'ABC','number_of_cycles': '38', 'extraction_identifier': '1', 'sample_identifier': 'sample1', 'group_name': 'Group', 'extraction_from':'whole_sample', 'submitter_plate_id':'CUL', 'submitter_plate_well': 'A1', 'nucleic_acid_concentration': '1', 'sample_identifier': 'sample1', 'extraction_machine': 'KingFisher Flex', 'extraction_kit': 'MagMAX Viral/Pathogen II (MAGMAX-96)', 'what_was_extracted': 'ABC', 'extraction_processing_institution': 'MLW'})

            base_fastq_dir = os.path.join(temp_dir, 'fastq_pass', 'barcode01')
            base_fast5_dir = os.path.join(temp_dir, 'fast5_pass', 'barcode01')
            os.makedirs(base_fastq_dir)
            os.makedirs(base_fast5_dir)
            temp_fastq_file = os.path.join(base_fastq_dir,'abc.fastq.gz')
            temp_fast5_file = os.path.join(base_fast5_dir,'abc.fast5')
            # create an empty file
            open(temp_fastq_file, 'a').close()
            open(temp_fast5_file, 'a').close()

            readset_info = {'data_storage_device': 'storage_device_1',  'readset_batch_name': 'EFG',  'date_extracted': '01/01/2023',  'extraction_identifier': '1', 'sample_identifier': 'sample1', 'group_name': 'Group', 'date_tiling_pcred': '01/01/2023', 'tiling_pcr_identifier':'5', 'path_fastq': temp_fastq_file, 'path_fast5': temp_fast5_file, 'barcode': 'barcode01', 'library_prep_method': 'Nextera' }
            add_readset( readset_info, True, True)
            result = get_readset(readset_info, True)
            self.assertIsInstance(result, ReadSetNanopore)

    def test_get_artic_covid_results_empty_db(self):
        self.setUp()
        with tempfile.TemporaryDirectory() as temp_dir:
            self.populate_db(temp_dir)
            artic_covid_result_info = {'sample_name': 'sample1', 
                                       'pct_N_bases': '19.9', 
                                       'pct_covered_bases': '80.1', 
                                       'num_aligned_reads': '43649', 
                                       'artic_workflow':'medaka',
                                       'artic_profile':'docker',
                                       'readset_batch_name':'EFG',
                                       'barcode': 'barcode01'
                                    }
            self.assertFalse(get_artic_covid_result(artic_covid_result_info))

    def test_check_artic_covid_result(self):
        self.assertTrue(check_artic_covid_result({'sample_name': 'sample1', 'pct_N_bases': '19.9', 'pct_covered_bases': '80.1', 'num_aligned_reads': '43649'}))
        # empty
        with self.assertRaises(SystemExit) as cm:
            check_artic_covid_result({'sample_name': '', 'pct_N_bases': '19.9', 'pct_covered_bases': '80.1', 'num_aligned_reads': '43649'})
        with self.assertRaises(SystemExit) as cm:
            check_artic_covid_result({'sample_name': 'sample1', 'pct_N_bases': '', 'pct_covered_bases': '80.1', 'num_aligned_reads': '43649'})
        with self.assertRaises(SystemExit) as cm:
            check_artic_covid_result({'sample_name': 'sample1', 'pct_N_bases': '19.9', 'pct_covered_bases': '', 'num_aligned_reads': '43649'})
        with self.assertRaises(SystemExit) as cm:
            check_artic_covid_result({'sample_name': 'sample1', 'pct_N_bases': '19.9', 'pct_covered_bases': '80.1', 'num_aligned_reads': ''})
        # missing
        with self.assertRaises(SystemExit) as cm:
            check_artic_covid_result({'pct_N_bases': '19.9', 'pct_covered_bases': '80.1', 'num_aligned_reads': '43649'})
        with self.assertRaises(SystemExit) as cm:
            check_artic_covid_result({'sample_name': 'sample1', 'pct_covered_bases': '80.1', 'num_aligned_reads': '43649'})
        with self.assertRaises(SystemExit) as cm:
            check_artic_covid_result({'sample_name': 'sample1', 'pct_N_bases': '19.9', 'num_aligned_reads': '43649'})
        with self.assertRaises(SystemExit) as cm:
            check_artic_covid_result({'sample_name': 'sample1', 'pct_N_bases': '19.9', 'pct_covered_bases': '80.1'})

    def test_read_in_artic_covid_result(self):
        artic_covid_result_info = {'sample_name': 'sample1', 'pct_N_bases': '19.9', 'pct_covered_bases': '80.1', 'num_aligned_reads': '43649', 'artic_workflow':'medaka','artic_profile':'docker' }
        result = read_in_artic_covid_result(artic_covid_result_info)
        self.assertIsInstance(result, ArticCovidResult)

    def test_add_artic_covid_result(self):
        self.setUp()
        with tempfile.TemporaryDirectory() as temp_dir:
            self.populate_db(temp_dir)
            artic_covid_result_info = {'sample_name': 'sample1', 
                                       'pct_N_bases': '19.9', 
                                       'pct_covered_bases': '80.1', 
                                       'num_aligned_reads': '43649', 
                                       'artic_workflow':'medaka',
                                       'artic_profile':'docker',
                                       'readset_batch_name':'EFG',
                                       'barcode': 'barcode01'
                                    }
            add_artic_covid_result(artic_covid_result_info)
            result = get_artic_covid_result(artic_covid_result_info)
            self.assertIsInstance(result, ArticCovidResult)
            
    def test_get_nanopore_readset_from_batch_and_barcode(self):
        self.setUp()
        with tempfile.TemporaryDirectory() as temp_dir:
            self.populate_db(temp_dir)
            batch_and_barcode_info = {'readset_batch_name':'EFG',
                                       'barcode': 'barcode01'
                                     }
            result = get_nanopore_readset_from_batch_and_barcode(batch_and_barcode_info)
            self.assertIsInstance(result, ReadSetNanopore)

    def test_get_nanopore_readset_from_batch_and_barcode_no_results(self):
        self.setUp()
        with tempfile.TemporaryDirectory() as temp_dir:
            self.populate_db(temp_dir)
            batch_and_barcode_info = {'readset_batch_name':'EFG',
                                       'barcode': 'doesnt_exist'
                                     }
            result = get_nanopore_readset_from_batch_and_barcode(batch_and_barcode_info)
            self.assertFalse(result)

    def test_add_artic_covid_result_barcode_doesnt_exist(self):
        self.setUp()
        with tempfile.TemporaryDirectory() as temp_dir:
            self.populate_db(temp_dir)
            artic_covid_result_info = {'sample_name': 'sample1', 
                                       'pct_N_bases': '19.9', 
                                       'pct_covered_bases': '80.1', 
                                       'num_aligned_reads': '43649', 
                                       'artic_workflow':'medaka',
                                       'artic_profile':'docker',
                                       'readset_batch_name':'doesnt_exist',
                                       'barcode': 'doesnt_exist'
                                    }
            self.assertFalse(add_artic_covid_result(artic_covid_result_info))

    # adding the same information twice returns an error when you get it again.
    def test_add_artic_covid_result_duplicate(self):
        self.setUp()
        with tempfile.TemporaryDirectory() as temp_dir:
            self.populate_db(temp_dir)
            artic_covid_result_info = {'sample_name': 'sample1', 
                                       'pct_N_bases': '19.9', 
                                       'pct_covered_bases': '80.1', 
                                       'num_aligned_reads': '43649', 
                                       'artic_workflow':'medaka',
                                       'artic_profile':'docker',
                                       'readset_batch_name':'EFG',
                                       'barcode': 'barcode01'
                                    }
            add_artic_covid_result(artic_covid_result_info)
            add_artic_covid_result(artic_covid_result_info)
            with self.assertRaises(SystemExit) as cm:
                get_artic_covid_result(artic_covid_result_info)

