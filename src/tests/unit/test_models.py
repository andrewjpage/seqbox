import sys
import os
from flask_testing import TestCase
sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')
from app import app, db
from app.models import SampleSource, Project, PcrAssay, Sample

# Test methods that are standalone and dont need complex external libraries or inputs
class TestUtilsModels(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app

    # reset the database before you start
    def setUp(self):
        assert os.environ['DATABASE_URL'].split('/')[3].startswith('test') # you really dont want to delete a production DB
        db.drop_all()
        db.create_all()
    
    def test_sample_source_creation(self):
        sample_source = SampleSource(
            sample_source_identifier='sample1',
            sample_source_type='patient',
            latitude=37.7749,
            longitude=-122.4194,
            country='USA',
            location_first_level='California',
            location_second_level='San Francisco',
            location_third_level='Mission District',
            notes='This is a test sample source'
        )
        self.assertEqual(sample_source.sample_source_identifier, 'sample1')
        self.assertEqual(sample_source.sample_source_type, 'patient')
        self.assertEqual(sample_source.latitude, 37.7749)
        self.assertEqual(sample_source.longitude, -122.4194)
        self.assertEqual(sample_source.country, 'USA')
        self.assertEqual(sample_source.location_first_level, 'California')
        self.assertEqual(sample_source.location_second_level, 'San Francisco')
        self.assertEqual(sample_source.location_third_level, 'Mission District')
        self.assertEqual(sample_source.notes, 'This is a test sample source')

    def test_project_creation(self):
        project = Project(
            groups_id=1,
            project_name='Test Project',
            project_details='This is a test project',
            notes='This is a test note'
        )
        self.assertEqual(project.groups_id, 1)
        self.assertEqual(project.project_name, 'Test Project')
        self.assertEqual(project.project_details, 'This is a test project')
        self.assertEqual(project.notes, 'This is a test note')

    def test_pcr_assay_creation(self):
        pcr_assay = PcrAssay(assay_name="SARS-CoV2-CDC-N1")
        db.session.add(pcr_assay)
        db.session.commit()
        self.assertIsNotNone(pcr_assay.id)
        self.assertEqual(pcr_assay.assay_name, "SARS-CoV2-CDC-N1")

    def test_sample_creation(self):
        self.sample = Sample(sample_identifier="sample1", sample_type="isolate", species="Escherichia coli",
                                     sequencing_type_requested=["illumina"], submitted_for_sequencing=True,
                                     submitter_plate_id="plate1", submitter_plate_well="A1", day_collected=1,
                                     month_collected=1, year_collected=2022, day_received=2, month_received=1,
                                     year_received=2022, processing_institution="institution1")

        self.assertEqual(self.sample.sample_identifier, "sample1")
        self.assertEqual(self.sample.sample_type, "isolate")
        self.assertEqual(self.sample.species, "Escherichia coli")
        self.assertEqual(self.sample.sequencing_type_requested, ["illumina"])
        self.assertTrue(self.sample.submitted_for_sequencing)
        self.assertEqual(self.sample.submitter_plate_id, "plate1")
        self.assertEqual(self.sample.submitter_plate_well, "A1")
        self.assertEqual(self.sample.day_collected, 1)
        self.assertEqual(self.sample.month_collected, 1)
        self.assertEqual(self.sample.year_collected, 2022)
        self.assertEqual(self.sample.day_received, 2)
        self.assertEqual(self.sample.month_received, 1)
        self.assertEqual(self.sample.year_received, 2022)
        self.assertEqual(self.sample.processing_institution, "institution1")

    
