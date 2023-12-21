import sys
import os
from flask_testing import TestCase
import datetime
import tempfile
sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')
from app import app, db
from app.models import PangolinResult
from scripts.utils.check import check_pangolin_result
from scripts.utils.db import (
    read_in_pangolin_result,
    add_pangolin_result,
    get_pangolin_result,
    add_artic_covid_result,
    add_raw_sequencing_batch,
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
            add_readset( {'data_storage_device': 'storage_device_1',  'readset_batch_name': 'EFG',  'date_extracted': '01/01/2023',  'extraction_identifier': '1', 'sample_identifier': 'sample1', 'group_name': 'Group', 'date_tiling_pcred': '01/01/2023', 'tiling_pcr_identifier':'5', 'path_fastq': temp_fastq_file, 'path_fast5': temp_fast5_file, 'barcode': 'barcode01', 'library_prep_method': 'Nextera' }, True, True)
            add_artic_covid_result({'sample_name': 'sample1', 'pct_N_bases': '19.9', 'pct_covered_bases': '80.1', 'num_aligned_reads': '43649', 'artic_workflow':'medaka', 'artic_profile':'docker', 'readset_batch_name':'EFG', 'barcode': 'barcode01'})

    def test_check_pangolin_result(self):
        self.assertTrue(check_pangolin_result({'taxon': '20200101_123_MN1234_FAO1234_123_barcode01/ARTIC/medaka_MN908947.3','lineage': 'B.1.351','qc_status': 'passed_qc', 'status': 'passed_qc'}))
        # status renamed
        self.assertTrue(check_pangolin_result({'taxon': '20200101_123_MN1234_FAO1234_123_barcode01/ARTIC/medaka_MN908947.3','lineage': 'B.1.351','qc_status': 'passed_qc', 'status': 'xx'}))
        self.assertTrue(check_pangolin_result({'taxon': '20200101_123_MN1234_FAO1234_123_barcode01/ARTIC/medaka_MN908947.3','lineage': 'B.1.351', 'status': 'passed_qc'}))
        self.assertTrue(check_pangolin_result({'taxon': '20200101_123_MN1234_FAO1234_123_barcode01/ARTIC/medaka_MN908947.3','lineage': 'B.1.351','qc_status': '', 'status': 'passed_qc'}))
        # empty
        with self.assertRaises(ValueError) as cm:
            check_pangolin_result({'taxon': '','lineage': 'B.1.351','qc_status': 'passed_qc', 'status': 'passed_qc'})
        with self.assertRaises(ValueError) as cm:
            check_pangolin_result({'taxon': '20200101_123_MN1234_FAO1234_123_barcode01/ARTIC/medaka_MN908947.3','lineage': '','qc_status': 'passed_qc', 'status': 'passed_qc'})
        with self.assertRaises(ValueError) as cm:
            check_pangolin_result({'taxon': '20200101_123_MN1234_FAO1234_123_barcode01/ARTIC/medaka_MN908947.3','lineage': 'B.1.351','qc_status': 'passed_qc', 'status': ''})
        # missing
        with self.assertRaises(ValueError) as cm:
            check_pangolin_result({'lineage': 'B.1.351','qc_status': 'passed_qc', 'status': 'passed_qc'})
        with self.assertRaises(ValueError) as cm:
            check_pangolin_result({'taxon': '20200101_123_MN1234_FAO1234_123_barcode01/ARTIC/medaka_MN908947.3','qc_status': 'passed_qc', 'status': 'passed_qc'})

    def test_read_in_pangolin_result(self):
        pangolin_result_info = {'taxon': '20200101_123_MN1234_FAO1234_123_barcode01/ARTIC/medaka_MN908947.3',
                                'lineage': 'B.1.351',
                                'qc_status': 'passed_qc',
                                'conflict': '0',
                                'ambiguity_score': '0.933810738',
                                'scorpio_call': 'Beta (B.1.351-like)',
                                'scorpio_support':'0.8571',
                                'scorpio_conflict':'0',
                                'version':'PLEARN-v1.2.13',
                                'pangolin_version':'3.1.5',
                                'pango_version':'15/06/2021',
                                'status':'passed_qc',
                                'note':'scorpio call: Alt alleles 12; Ref alleles 0; Amb alleles 0',
                                }
        result = read_in_pangolin_result(pangolin_result_info)
        self.assertIsInstance(result, PangolinResult)

    def test_read_in_pangolin_result_no_scorpio_conflict(self):
        pangolin_result_info = {'taxon': '20200101_123_MN1234_FAO1234_123_barcode01/ARTIC/medaka_MN908947.3',
                                'lineage': 'B.1.351',
                                'qc_status': 'passed_qc',
                                'conflict': '0',
                                'ambiguity_score': '0.933810738',
                                'scorpio_call': 'Beta (B.1.351-like)',
                                'scorpio_support':'0.8571',
                                'scorpio_conflict':'',
                                'version':'PLEARN-v1.2.13',
                                'pangolin_version':'3.1.5',
                                'pango_version':'15/06/2021',
                                'status':'passed_qc',
                                'note':'scorpio call: Alt alleles 12; Ref alleles 0; Amb alleles 0',
                                }
        result = read_in_pangolin_result(pangolin_result_info)
        self.assertIsInstance(result, PangolinResult)

    # some fields can be missing
    def test_read_in_pangolin_result_missing(self):
        result = read_in_pangolin_result({'taxon': '20200101_123_MN1234_FAO1234_123_barcode01/ARTIC/medaka_MN908947.3', 'lineage': 'B.1.351', 'qc_status': 'passed_qc',  'ambiguity_score': '0.933810738', 'scorpio_call': 'Beta (B.1.351-like)', 'scorpio_support':'0.8571', 'scorpio_conflict':'0', 'version':'PLEARN-v1.2.13', 'pangolin_version':'3.1.5', 'pango_version':'15/06/2021', 'status':'passed_qc', 'note':'scorpio call: Alt alleles 12; Ref alleles 0; Amb alleles 0', })
        self.assertIsInstance(result, PangolinResult)

        result = read_in_pangolin_result({'taxon': '20200101_123_MN1234_FAO1234_123_barcode01/ARTIC/medaka_MN908947.3', 'lineage': 'B.1.351', 'qc_status': 'passed_qc', 'conflict': '0', 'scorpio_call': 'Beta (B.1.351-like)', 'scorpio_support':'0.8571', 'scorpio_conflict':'0', 'version':'PLEARN-v1.2.13', 'pangolin_version':'3.1.5', 'pango_version':'15/06/2021', 'status':'passed_qc', 'note':'scorpio call: Alt alleles 12; Ref alleles 0; Amb alleles 0', })
        self.assertIsInstance(result, PangolinResult)

        result = read_in_pangolin_result({'taxon': '20200101_123_MN1234_FAO1234_123_barcode01/ARTIC/medaka_MN908947.3', 'lineage': 'B.1.351', 'qc_status': 'passed_qc', 'conflict': '0', 'ambiguity_score': '0.933810738', 'scorpio_support':'0.8571', 'scorpio_conflict':'0', 'version':'PLEARN-v1.2.13', 'pangolin_version':'3.1.5', 'pango_version':'15/06/2021', 'status':'passed_qc', 'note':'scorpio call: Alt alleles 12; Ref alleles 0; Amb alleles 0', })
        self.assertIsInstance(result, PangolinResult)

        result = read_in_pangolin_result({'taxon': '20200101_123_MN1234_FAO1234_123_barcode01/ARTIC/medaka_MN908947.3', 'lineage': 'B.1.351', 'qc_status': 'passed_qc', 'conflict': '0', 'ambiguity_score': '0.933810738', 'scorpio_call': 'Beta (B.1.351-like)', 'scorpio_conflict':'0', 'version':'PLEARN-v1.2.13', 'pangolin_version':'3.1.5', 'pango_version':'15/06/2021', 'status':'passed_qc', 'note':'scorpio call: Alt alleles 12; Ref alleles 0; Amb alleles 0', })
        self.assertIsInstance(result, PangolinResult)

        result = read_in_pangolin_result({'taxon': '20200101_123_MN1234_FAO1234_123_barcode01/ARTIC/medaka_MN908947.3', 'lineage': 'B.1.351', 'qc_status': 'passed_qc', 'conflict': '0', 'ambiguity_score': '0.933810738', 'scorpio_call': 'Beta (B.1.351-like)', 'scorpio_support':'0.8571', 'scorpio_conflict':'0', 'version':'PLEARN-v1.2.13', 'pangolin_version':'3.1.5', 'status':'passed_qc', 'note':'scorpio call: Alt alleles 12; Ref alleles 0; Amb alleles 0', })
        self.assertIsInstance(result, PangolinResult)

    def test_get_pangolin_result_empty(self):
        self.setUp()
        with tempfile.TemporaryDirectory() as temp_dir:
            self.populate_db(temp_dir)
            pangolin_result_info = {'taxon': '20200101_123_MN1234_FAO1234_123_barcode01/ARTIC/medaka_MN908947.3',
                                'lineage': 'B.1.351',
                                'qc_status': 'passed_qc',
                                'conflict': '0',
                                'ambiguity_score': '0.933810738',
                                'scorpio_call': 'Beta (B.1.351-like)',
                                'scorpio_support':'0.8571',
                                'scorpio_conflict':'0',
                                'version':'PLEARN-v1.2.13',
                                'pangolin_version':'3.1.5',
                                'pango_version':'15/06/2021',
                                'status':'passed_qc',
                                'note':'scorpio call: Alt alleles 12; Ref alleles 0; Amb alleles 0',
                                'artic_profile': 'docker',
                                'artic_workflow': 'medaka',
                                'readset_batch_name': 'EFG',
                                'barcode': 'barcode01'
                                }
            self.assertFalse(get_pangolin_result(pangolin_result_info))

    def test_add_pangolin_result(self):
        self.setUp()
        with tempfile.TemporaryDirectory() as temp_dir:
            self.populate_db(temp_dir)
            pangolin_result_info = {'taxon': '20200101_123_MN1234_FAO1234_123_barcode01/ARTIC/medaka_MN908947.3',
                                'lineage': 'B.1.351',
                                'qc_status': 'passed_qc',
                                'conflict': '0',
                                'ambiguity_score': '0.933810738',
                                'scorpio_call': 'Beta (B.1.351-like)',
                                'scorpio_support':'0.8571',
                                'scorpio_conflict':'0',
                                'version':'PLEARN-v1.2.13',
                                'pangolin_version':'3.1.5',
                                'pango_version':'15/06/2021',
                                'status':'passed_qc',
                                'note':'scorpio call: Alt alleles 12; Ref alleles 0; Amb alleles 0',
                                'artic_profile': 'docker',
                                'artic_workflow': 'medaka',
                                'readset_batch_name': 'EFG',
                                'barcode': 'barcode01'
                                }
            add_pangolin_result(pangolin_result_info)
            result = get_pangolin_result(pangolin_result_info)
            self.assertIsInstance(result, PangolinResult)
            self.assertEqual(result.scorpio_call, 'Beta (B.1.351-like)')

    def test_add_pangolin_result_no_matching_artic_resuts(self):
        self.setUp()
        with tempfile.TemporaryDirectory() as temp_dir:
            self.populate_db(temp_dir)
            pangolin_result_info = {'taxon': '20200101_123_MN1234_FAO1234_123_barcode01/ARTIC/medaka_MN908947.3',
                                'lineage': 'B.1.351',
                                'qc_status': 'passed_qc',
                                'conflict': '0',
                                'ambiguity_score': '0.933810738',
                                'scorpio_call': 'Beta (B.1.351-like)',
                                'scorpio_support':'0.8571',
                                'scorpio_conflict':'0',
                                'version':'PLEARN-v1.2.13',
                                'pangolin_version':'3.1.5',
                                'pango_version':'15/06/2021',
                                'status':'passed_qc',
                                'note':'scorpio call: Alt alleles 12; Ref alleles 0; Amb alleles 0',
                                'artic_profile': 'manual',
                                'artic_workflow': 'medaka',
                                'readset_batch_name': 'EFG',
                                'barcode': 'doesnt_exist'
                                }
            add_pangolin_result(pangolin_result_info)
            self.assertFalse(get_pangolin_result(pangolin_result_info))

    def test_add_pangolin_result_duplicate(self):
        self.setUp()
        with tempfile.TemporaryDirectory() as temp_dir:
            self.populate_db(temp_dir)
            pangolin_result_info = {'taxon': '20200101_123_MN1234_FAO1234_123_barcode01/ARTIC/medaka_MN908947.3',
                                'lineage': 'B.1.351',
                                'qc_status': 'passed_qc',
                                'conflict': '0',
                                'ambiguity_score': '0.933810738',
                                'scorpio_call': 'Beta (B.1.351-like)',
                                'scorpio_support':'0.8571',
                                'scorpio_conflict':'0',
                                'version':'PLEARN-v1.2.13',
                                'pangolin_version':'3.1.5',
                                'pango_version':'15/06/2021',
                                'status':'passed_qc',
                                'note':'scorpio call: Alt alleles 12; Ref alleles 0; Amb alleles 0',
                                'artic_profile': 'docker',
                                'artic_workflow': 'medaka',
                                'readset_batch_name': 'EFG',
                                'barcode': 'barcode01'
                                }
            add_pangolin_result(pangolin_result_info)
            add_pangolin_result(pangolin_result_info)
            with self.assertRaises(SystemExit) as cm:
                get_pangolin_result(pangolin_result_info)
