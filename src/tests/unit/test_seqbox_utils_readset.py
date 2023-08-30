import sys
import os
from flask_testing import TestCase
import datetime
sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')
from app import app, db
from seqbox_utils import add_raw_sequencing_batch,add_extraction, add_tiling_pcr, add_group, add_project, add_sample_source, add_sample, add_readset_batch, basic_check_readset_fields, get_readset, add_readset, read_in_readset

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
    
    

    # get readset one matching
    # get readset where duplicates have been added
    # read_in_readset provide sequencing institution
    # read_in_readset no sequencing institution
    # read_in_readset sequencing_type is nanopore and not barcoded?
    # read_in_readset sequencing_type is nanopore and is barcoded fastq found in path
    # read_in_readset sequencing_type is nanopore and is barcoded, no fastq found in path
    # read_in_readset sequencing_type is nanopore and is barcoded, more than one fastq found in path
    # read_in_readset sequencing_type is Illumina
    # add readset but no matching readset batch
    # add readset with no matching raw sequencing batch
    # add readset raw_sequencing is true so its a rebasecalled readset
    # add readset covid is true but no tiling pcr
    # add readset covid is true and there is a tiling pcr
    # add readset covid is false but extraction not present
    # add readset covid is false and there is an extraction
    # add readset read in readset -> sets paths of files


