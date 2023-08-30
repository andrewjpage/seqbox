import sys
import os
from flask_testing import TestCase
import datetime
import tempfile
sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')
from app import app, db
from app.models import ReadSet
from seqbox_utils import add_raw_sequencing_batch,add_extraction, get_readset_batch, get_raw_sequencing_batch, add_tiling_pcr, add_group, add_project, add_sample_source, add_sample, add_readset_batch, basic_check_readset_fields, get_readset, add_readset, read_in_readset

class TestSeqboxUtilsReadset(TestCase):
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
        add_extraction({ 'date_extracted': '01/01/2023','extraction_identifier': '1','sample_identifier': 'sample1','group_name': 'Group','extraction_from':'whole_sample','submitter_plate_id':'CUL','submitter_plate_well': 'A1','nucleic_acid_concentration': '1','sample_identifier': 'sample1','extraction_machine': 'KingFisher Flex','extraction_kit': 'MagMAX Viral/Pathogen II (MAGMAX-96)','what_was_extracted': 'ABC','extraction_processing_institution': 'MLW' })
        add_raw_sequencing_batch({'date_run': '01/01/2023', 'sequencing_type': 'nanopore', 'batch_name': 'ABC', 'instrument_model': 'MinION', 'instrument_name': 'ABC123', 'sequencing_centre': 'MLW', 'flowcell_type': 'R12.3', 'batch_directory': '/path/to/dir' })
        add_readset_batch( {'raw_sequencing_batch_name': 'ABC', 'readset_batch_name': 'EFG', 'readset_batch_dir': '/path/to/dir', 'basecaller': 'guppy' } )
        add_tiling_pcr({'sample_identifier': 'sample1', 'date_extracted': '01/01/2023', 'extraction_identifier': '3', 'date_tiling_pcred': '01/01/2023', 'tiling_pcr_identifier': '5', 'group_name': 'Group', 'tiling_pcr_protocol': 'ABC','number_of_cycles': '38', 'extraction_identifier': '1', 'sample_identifier': 'sample1', 'group_name': 'Group', 'extraction_from':'whole_sample', 'submitter_plate_id':'CUL', 'submitter_plate_well': 'A1', 'nucleic_acid_concentration': '1', 'sample_identifier': 'sample1', 'extraction_machine': 'KingFisher Flex', 'extraction_kit': 'MagMAX Viral/Pathogen II (MAGMAX-96)', 'what_was_extracted': 'ABC', 'extraction_processing_institution': 'MLW'})

    # check readset fields for all values
    def test_basic_check_readset_fields(self):
        self.assertFalse(basic_check_readset_fields({'data_storage_device': '', 'readset_batch_name': 'EFG'}))
        self.assertFalse(basic_check_readset_fields({'data_storage_device': 'storage_device_1', 'readset_batch_name': ''}))
        self.assertFalse(basic_check_readset_fields({ 'readset_batch_name': 'EFG'}))
        self.assertFalse(basic_check_readset_fields({'data_storage_device': 'storage_device_1'}))
        self.assertTrue(basic_check_readset_fields({'data_storage_device': 'storage_device_1', 'readset_batch_name': 'EFG'}))

    # get readset where readset_batch is false
    def test_get_readset_batch_name_doesnt_exist(self):
        self.setUp()
        self.populate_db()
        readset_info = {'data_storage_device': 'storage_device_1', 'readset_batch_name': 'doesnt_exist'}
        with self.assertRaises(SystemExit) as cm:
            get_readset(readset_info, False)

    # get readset where readset_batch is false
    def test_get_readset_batch_name_illumina(self):
        self.setUp()
        add_group({'group_name': 'Group', 'institution': 'MLW', 'pi': 'PI'})
        add_project({'project_name': 'Project', 'group_name': 'Group', 'institution': 'MLW', 'project_details': 'seq'})
        add_sample_source({'projects': 'Project', 'group_name': 'Group', 'institution': 'MLW', 'sample_source_identifier': 'sample_source_1', 'sample_source_type': 'patient', 'latitude': 1.23, 'longitude': -12.3, 'country': 'UK', 'location_first_level': 'Essex', 'city': 'London', 'township': 'Docklands', 'notes': 'note'})
        add_sample({'sample_identifier': 'sample1', 'sample_source_identifier': 'sample_source_1', 'institution': 'MLW', 'group_name': 'Group', 'species': 'SARS-CoV-2', 'sample_type': 'Lung aspirate', 'day_collected': '31', 'month_collected': '5', 'year_collected': '2021', 'day_received': '1', 'month_received': '1', 'year_received': '2022', 'sequencing_type_requested':'MinION SARS-CoV-2'}, False)
        add_extraction({ 'date_extracted': '01/01/2023','extraction_identifier': '1','sample_identifier': 'sample1','group_name': 'Group','extraction_from':'whole_sample','submitter_plate_id':'CUL','submitter_plate_well': 'A1','nucleic_acid_concentration': '1','sample_identifier': 'sample1','extraction_machine': 'KingFisher Flex','extraction_kit': 'MagMAX Viral/Pathogen II (MAGMAX-96)','what_was_extracted': 'ABC','extraction_processing_institution': 'MLW' })
        add_raw_sequencing_batch({'date_run': '01/01/2023', 'sequencing_type': 'illumina', 'batch_name': 'ABC', 'instrument_model': 'MinION', 'instrument_name': 'ABC123', 'sequencing_centre': 'MLW', 'flowcell_type': 'R12.3', 'batch_directory': '/path/to/dir' })
        add_readset_batch( {'raw_sequencing_batch_name': 'ABC', 'readset_batch_name': 'EFG', 'readset_batch_dir': '/path/to/dir', 'basecaller': 'guppy' } )
        readset_info = {'data_storage_device': 'storage_device_1', 
                        'readset_batch_name': 'EFG', 
                        'date_extracted': '01/01/2023', 
                        'extraction_identifier': '1',
                        'sample_identifier': 'sample1',
                        'group_name': 'Group',
                        'date_tiling_pcred': '01/01/2023',
                        'tiling_pcr_identifier':'5'
                        }
        self.assertFalse(get_readset(readset_info, False))
        self.assertFalse(get_readset(readset_info, True))

    # get readset where readset_batch is false
    def test_get_readset_batch_name_nanopore(self):
        self.setUp()
        self.populate_db()
        readset_info = {'data_storage_device': 'storage_device_1', 
                        'readset_batch_name': 'EFG', 
                        'date_extracted': '01/01/2023', 
                        'extraction_identifier': '1',
                        'sample_identifier': 'sample1',
                        'group_name': 'Group',
                        'date_tiling_pcred': '01/01/2023',
                        'tiling_pcr_identifier':'5'
                        }
        self.assertFalse(get_readset(readset_info, False))
        self.assertFalse(get_readset(readset_info, True))
    
    #add readset but no matching readset batch
    def test_add_readset_with_missing_readset_batch(self):
        self.setUp()
        self.populate_db()
        readset_info = {'data_storage_device': 'storage_device_1', 'readset_batch_name': 'doesnt_exist'}
        with self.assertRaises(SystemExit) as cm:
            add_readset(readset_info, False, False)

    # read_in_readset provide sequencing institution
    def test_read_in_readset_sequencing_institution_illumina(self):
        self.setUp()
        add_group({'group_name': 'Group', 'institution': 'MLW', 'pi': 'PI'})
        add_project({'project_name': 'Project', 'group_name': 'Group', 'institution': 'MLW', 'project_details': 'seq'})
        add_sample_source({'projects': 'Project', 'group_name': 'Group', 'institution': 'MLW', 'sample_source_identifier': 'sample_source_1', 'sample_source_type': 'patient', 'latitude': 1.23, 'longitude': -12.3, 'country': 'UK', 'location_first_level': 'Essex', 'city': 'London', 'township': 'Docklands', 'notes': 'note'})
        add_sample({'sample_identifier': 'sample1', 'sample_source_identifier': 'sample_source_1', 'institution': 'MLW', 'group_name': 'Group', 'species': 'SARS-CoV-2', 'sample_type': 'Lung aspirate', 'day_collected': '31', 'month_collected': '5', 'year_collected': '2021', 'day_received': '1', 'month_received': '1', 'year_received': '2022', 'sequencing_type_requested':'MinION SARS-CoV-2'}, False)
        add_extraction({ 'date_extracted': '01/01/2023','extraction_identifier': '1','sample_identifier': 'sample1','group_name': 'Group','extraction_from':'whole_sample','submitter_plate_id':'CUL','submitter_plate_well': 'A1','nucleic_acid_concentration': '1','sample_identifier': 'sample1','extraction_machine': 'KingFisher Flex','extraction_kit': 'MagMAX Viral/Pathogen II (MAGMAX-96)','what_was_extracted': 'ABC','extraction_processing_institution': 'MLW' })
        add_raw_sequencing_batch({'date_run': '01/01/2023', 'sequencing_type': 'illumina', 'batch_name': 'ABC', 'instrument_model': 'MinION', 'instrument_name': 'ABC123', 'sequencing_centre': 'MLW', 'flowcell_type': 'R12.3', 'batch_directory': '/path/to/dir' })
        add_readset_batch( {'raw_sequencing_batch_name': 'ABC', 'readset_batch_name': 'EFG', 'readset_batch_dir': '/path/to/dir', 'basecaller': 'guppy' } )
        readset_info = {'data_storage_device': 'storage_device_1', 
                        'readset_batch_name': 'EFG', 
                        'date_extracted': '01/01/2023', 
                        'extraction_identifier': '1',
                        'sample_identifier': 'sample1',
                        'group_name': 'Group',
                        'date_tiling_pcred': '01/01/2023',
                        'tiling_pcr_identifier':'5',
                        'sequencing_institution': 'PHE'
                        }
        raw_sequencing_batch_result = get_raw_sequencing_batch('ABC')
        readset_batch_result = get_readset_batch(readset_info)
        result = read_in_readset(readset_info, False, raw_sequencing_batch_result , readset_batch_result, False)
        self.assertIsInstance(result, ReadSet)
        self.assertEqual(result.sequencing_institution, 'PHE')

    # read_in_readset provide sequencing institution
    def test_read_in_readset_sequencing_institution_nanopore(self):
        self.setUp()
        self.populate_db()
        readset_info = {'data_storage_device': 'storage_device_1', 
                        'readset_batch_name': 'EFG', 
                        'date_extracted': '01/01/2023', 
                        'extraction_identifier': '1',
                        'sample_identifier': 'sample1',
                        'group_name': 'Group',
                        'date_tiling_pcred': '01/01/2023',
                        'tiling_pcr_identifier':'5',
                        'sequencing_institution': 'PHE',
                        'path_fastq': '/path/to/abc.fastq.gz',
                        'path_fast5': '/path/to/abc.fast5'
                        }
        raw_sequencing_batch_result = get_raw_sequencing_batch('ABC')
        readset_batch_result = get_readset_batch(readset_info)
        result = read_in_readset(readset_info, False, raw_sequencing_batch_result , readset_batch_result, False)
        self.assertIsInstance(result, ReadSet)
        self.assertEqual(result.sequencing_institution, 'PHE')

    # read_in_readset no sequencing institution
    def test_read_in_readset_no_sequencing_institution_nanopore(self):
        self.setUp()
        self.populate_db()
        readset_info = {'data_storage_device': 'storage_device_1', 
                        'readset_batch_name': 'EFG', 
                        'date_extracted': '01/01/2023', 
                        'extraction_identifier': '1',
                        'sample_identifier': 'sample1',
                        'group_name': 'Group',
                        'date_tiling_pcred': '01/01/2023',
                        'tiling_pcr_identifier':'5',
                        'path_fastq': '/path/to/abc.fastq.gz',
                        'path_fast5': '/path/to/abc.fast5'
                        }
        raw_sequencing_batch_result = get_raw_sequencing_batch('ABC')
        readset_batch_result = get_readset_batch(readset_info)
        result = read_in_readset(readset_info, False, raw_sequencing_batch_result , readset_batch_result, False)
        self.assertIsInstance(result, ReadSet)
        self.assertEqual(result.sequencing_institution, None)

    def test_read_in_readset_nanopore_not_ending_in_fastq_gz(self):
        self.setUp()
        self.populate_db()
        readset_info = {'data_storage_device': 'storage_device_1', 
                        'readset_batch_name': 'EFG', 
                        'date_extracted': '01/01/2023', 
                        'extraction_identifier': '1',
                        'sample_identifier': 'sample1',
                        'group_name': 'Group',
                        'date_tiling_pcred': '01/01/2023',
                        'tiling_pcr_identifier':'5',
                        'path_fastq': '/path/to/abc.invalid_extension',
                        'path_fast5': '/path/to/abc.fast5'
                        }
        raw_sequencing_batch_result = get_raw_sequencing_batch('ABC')
        readset_batch_result = get_readset_batch(readset_info)
        with self.assertRaises(AssertionError) as cm:
            read_in_readset(readset_info, False, raw_sequencing_batch_result , readset_batch_result, False)


    # read_in_readset sequencing_type is nanopore and barcoded and file found
    def test_read_in_readset_nanopore_default(self):
        self.setUp()

        with tempfile.TemporaryDirectory() as temp_dir:
            add_group({'group_name': 'Group', 'institution': 'MLW', 'pi': 'PI'})
            add_project({'project_name': 'Project', 'group_name': 'Group', 'institution': 'MLW', 'project_details': 'seq'})
            add_sample_source({'projects': 'Project', 'group_name': 'Group', 'institution': 'MLW', 'sample_source_identifier': 'sample_source_1', 'sample_source_type': 'patient', 'latitude': 1.23, 'longitude': -12.3, 'country': 'UK', 'location_first_level': 'Essex', 'city': 'London', 'township': 'Docklands', 'notes': 'note'})
            add_sample({'sample_identifier': 'sample1', 'sample_source_identifier': 'sample_source_1', 'institution': 'MLW', 'group_name': 'Group', 'species': 'SARS-CoV-2', 'sample_type': 'Lung aspirate', 'day_collected': '31', 'month_collected': '5', 'year_collected': '2021', 'day_received': '1', 'month_received': '1', 'year_received': '2022', 'sequencing_type_requested':'MinION SARS-CoV-2'}, False)
            add_extraction({ 'date_extracted': '01/01/2023','extraction_identifier': '1','sample_identifier': 'sample1','group_name': 'Group','extraction_from':'whole_sample','submitter_plate_id':'CUL','submitter_plate_well': 'A1','nucleic_acid_concentration': '1','sample_identifier': 'sample1','extraction_machine': 'KingFisher Flex','extraction_kit': 'MagMAX Viral/Pathogen II (MAGMAX-96)','what_was_extracted': 'ABC','extraction_processing_institution': 'MLW' })
            add_raw_sequencing_batch({'date_run': '01/01/2023', 'sequencing_type': 'nanopore', 'batch_name': 'ABC', 'instrument_model': 'MinION', 'instrument_name': 'ABC123', 'sequencing_centre': 'MLW', 'flowcell_type': 'R12.3', 'batch_directory': str(temp_dir) })
            add_readset_batch( {'raw_sequencing_batch_name': 'ABC', 'readset_batch_name': 'EFG', 'readset_batch_dir': str(temp_dir), 'basecaller': 'guppy' } )
            add_tiling_pcr({'sample_identifier': 'sample1', 'date_extracted': '01/01/2023', 'extraction_identifier': '3', 'date_tiling_pcred': '01/01/2023', 'tiling_pcr_identifier': '5', 'group_name': 'Group', 'tiling_pcr_protocol': 'ABC','number_of_cycles': '38', 'extraction_identifier': '1', 'sample_identifier': 'sample1', 'group_name': 'Group', 'extraction_from':'whole_sample', 'submitter_plate_id':'CUL', 'submitter_plate_well': 'A1', 'nucleic_acid_concentration': '1', 'sample_identifier': 'sample1', 'extraction_machine': 'KingFisher Flex', 'extraction_kit': 'MagMAX Viral/Pathogen II (MAGMAX-96)', 'what_was_extracted': 'ABC', 'extraction_processing_institution': 'MLW'})

            base_fastq_dir = os.path.join(temp_dir, 'fastq_pass', 'barcode01')
            os.makedirs(base_fastq_dir)
            temp_fastq_file = os.path.join(base_fastq_dir,'abc.fastq.gz')
            temp_fast5_file = os.path.join(base_fastq_dir,'abc.fast5')
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
                        'barcode': 'barcode01'
                        }
            raw_sequencing_batch_result = get_raw_sequencing_batch('ABC')
            readset_batch_result = get_readset_batch(readset_info)

            result = read_in_readset(readset_info, True, raw_sequencing_batch_result , readset_batch_result, False)
            self.assertIsInstance(result, ReadSet)
    

    # read_in_readset sequencing_type is nanopore and is barcoded, no fastq found in path
    def test_read_in_readset_nanopore_default(self):
        self.setUp()

        with tempfile.TemporaryDirectory() as temp_dir:
            add_group({'group_name': 'Group', 'institution': 'MLW', 'pi': 'PI'})
            add_project({'project_name': 'Project', 'group_name': 'Group', 'institution': 'MLW', 'project_details': 'seq'})
            add_sample_source({'projects': 'Project', 'group_name': 'Group', 'institution': 'MLW', 'sample_source_identifier': 'sample_source_1', 'sample_source_type': 'patient', 'latitude': 1.23, 'longitude': -12.3, 'country': 'UK', 'location_first_level': 'Essex', 'city': 'London', 'township': 'Docklands', 'notes': 'note'})
            add_sample({'sample_identifier': 'sample1', 'sample_source_identifier': 'sample_source_1', 'institution': 'MLW', 'group_name': 'Group', 'species': 'SARS-CoV-2', 'sample_type': 'Lung aspirate', 'day_collected': '31', 'month_collected': '5', 'year_collected': '2021', 'day_received': '1', 'month_received': '1', 'year_received': '2022', 'sequencing_type_requested':'MinION SARS-CoV-2'}, False)
            add_extraction({ 'date_extracted': '01/01/2023','extraction_identifier': '1','sample_identifier': 'sample1','group_name': 'Group','extraction_from':'whole_sample','submitter_plate_id':'CUL','submitter_plate_well': 'A1','nucleic_acid_concentration': '1','sample_identifier': 'sample1','extraction_machine': 'KingFisher Flex','extraction_kit': 'MagMAX Viral/Pathogen II (MAGMAX-96)','what_was_extracted': 'ABC','extraction_processing_institution': 'MLW' })
            add_raw_sequencing_batch({'date_run': '01/01/2023', 'sequencing_type': 'nanopore', 'batch_name': 'ABC', 'instrument_model': 'MinION', 'instrument_name': 'ABC123', 'sequencing_centre': 'MLW', 'flowcell_type': 'R12.3', 'batch_directory': str(temp_dir) })
            add_readset_batch( {'raw_sequencing_batch_name': 'ABC', 'readset_batch_name': 'EFG', 'readset_batch_dir': str(temp_dir), 'basecaller': 'guppy' } )
            add_tiling_pcr({'sample_identifier': 'sample1', 'date_extracted': '01/01/2023', 'extraction_identifier': '3', 'date_tiling_pcred': '01/01/2023', 'tiling_pcr_identifier': '5', 'group_name': 'Group', 'tiling_pcr_protocol': 'ABC','number_of_cycles': '38', 'extraction_identifier': '1', 'sample_identifier': 'sample1', 'group_name': 'Group', 'extraction_from':'whole_sample', 'submitter_plate_id':'CUL', 'submitter_plate_well': 'A1', 'nucleic_acid_concentration': '1', 'sample_identifier': 'sample1', 'extraction_machine': 'KingFisher Flex', 'extraction_kit': 'MagMAX Viral/Pathogen II (MAGMAX-96)', 'what_was_extracted': 'ABC', 'extraction_processing_institution': 'MLW'})

            base_fastq_dir = os.path.join(temp_dir, 'fastq_pass', 'barcode01')
            os.makedirs(base_fastq_dir)
            temp_fastq_file = os.path.join(base_fastq_dir,'abc.fastq.gz')
            temp_fast5_file = os.path.join(base_fastq_dir,'abc.fast5')

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
                        'barcode': 'barcode01'
                        }
            raw_sequencing_batch_result = get_raw_sequencing_batch('ABC')
            readset_batch_result = get_readset_batch(readset_info)

            with self.assertRaises(SystemExit) as cm:
                read_in_readset(readset_info, True, raw_sequencing_batch_result , readset_batch_result, False)

    # add readset but no matching readset batch
    def test_add_readset_no_matching_readset_batch(self):
        self.setUp()
        self.populate_db()
        readset_info = {'data_storage_device': 'storage_device_1', 
                        'readset_batch_name': 'does_not_match', 
                        'date_extracted': '01/01/2023', 
                        'extraction_identifier': '1',
                        'sample_identifier': 'sample1',
                        'group_name': 'Group',
                        'date_tiling_pcred': '01/01/2023',
                        'tiling_pcr_identifier':'5',
                        'path_fastq': '/path/to/abc.fastq.gz',
                        'path_fast5': '/path/to/abc.fast5'
                        }
        with self.assertRaises(SystemExit) as cm:
            add_readset(readset_info, False, False)


    # add readset covid is true but no tiling pcr
    def test_add_readset_no_matching_readset_batch(self):
        self.setUp()
        with tempfile.TemporaryDirectory() as temp_dir:
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

            readset_info = {'data_storage_device': 'storage_device_1', 
                            'readset_batch_name': 'EFG', 
                            'date_extracted': '01/01/2023', 
                            'extraction_identifier': '1',
                            'sample_identifier': 'sample1',
                            'group_name': 'Group',
                            'date_tiling_pcred': '02/02/2023',
                            'tiling_pcr_identifier':'5000',
                            'path_fastq': temp_fastq_file,
                            'path_fast5': temp_fast5_file,
                            }
            with self.assertRaises(SystemExit) as cm:
                add_readset(readset_info, True, False)

    # add readset nanopore, default, file exists
    def test_add_readset_nanopore_default_files_exist(self):
        self.setUp()
        with tempfile.TemporaryDirectory() as temp_dir:
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
                            }
            
            add_readset(readset_info, True, False)
            result = get_readset(readset_info, False)
            self.assertIsInstance(result, ReadSet)



    # add readset covid is true and there is a tiling pcr
    # add readset covid is false but extraction not present
    # add readset covid is false and there is an extraction
    # add readset read in readset -> sets paths of files

    # get readset where duplicates have been added
