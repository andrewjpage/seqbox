import sys
from flask_testing import TestCase
sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')
from app import app, db
from app.models import SampleSource, Project

# Test methods that are standalone and dont need complex external libraries or inputs
class TestUtilsModels(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app
    
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