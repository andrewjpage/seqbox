import sys
import os
from flask_testing import TestCase
import pandas as pd
sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')
from app import app, db
from scripts.utils.db import add_project, query_projects, add_group


class TestSeqboxUtilsProjects(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app
    
    # reset the database before you start
    def setUp(self):
        assert os.environ['DATABASE_URL'].split('/')[3].startswith('test') # you really dont want to delete a production DB
        db.drop_all()
        db.create_all()

    def test_get_project_where_none_exist_already(self):
        self.setUp()
        project_info = {'project_name': 'Testproject', 'group_name': 'TestGroup', 'institution': 'Test Institution', 'project_details': 'sequencing'}
        matching_project = query_projects(project_info, project_info['project_name'])
        self.assertEqual((False, ), matching_project)

    def test_add_project_missing_group(self):
        self.setUp()
        project_info = {'project_name': 'Testproject', 'group_name': 'TestGroup', 'institution': 'Test Institution', 'project_details': 'sequencing'}
        with self.assertRaises(SystemExit) as cm:
            add_project(project_info)

    def test_add_project(self):
        self.setUp()
        project_info = {'project_name': 'Testproject', 'group_name': 'TestGroup', 'institution': 'Test Institution', 'project_details': 'sequencing'}
        matching_project = query_projects(project_info, project_info['project_name'])
        self.assertEqual((False, ), matching_project)

        add_group({'group_name': 'TestGroup', 'institution': 'Test Institution', 'pi': 'pi'})
        add_project(project_info)
        matching_project = query_projects(project_info, project_info['project_name'])
        self.assertTrue(matching_project[0])
        self.assertEqual(matching_project[1].project_name, 'Testproject')
        self.assertEqual(matching_project[1].project_details, 'sequencing')

    def test_add_project_mismatch_group(self):
        self.setUp()
        project_info = {'project_name': 'Testproject', 'group_name': 'TestGroup', 'institution': 'Test Institution', 'project_details': 'sequencing'}
        add_group({'group_name': 'MismatchGroup', 'institution': 'Test Institution', 'pi': 'pi'})
        with self.assertRaises(SystemExit) as cm:
            add_project(project_info)

    def test_add_project_mismatch_institute(self):
        self.setUp()
        project_info = {'project_name': 'Testproject', 'group_name': 'TestGroup', 'institution': 'Test Institution', 'project_details': 'sequencing'}
        add_group({'group_name': 'TestGroup', 'institution': 'Mismatch Institution', 'pi': 'pi'})
        with self.assertRaises(SystemExit) as cm:
            add_project(project_info)

    def test_add_project_missing_essential_info(self):
        self.setUp()
        project_info = {'group_name': 'TestGroup', 'institution': 'Test Institution', 'project_details': 'sequencing'}
        with self.assertRaises(SystemExit, msg='Missing project_name') as cm:
            add_project(project_info)
        
        project_info = {'project_name': 'Testproject',  'institution': 'Test Institution', 'project_details': 'sequencing'}
        with self.assertRaises(SystemExit, msg='Missing group_name') as cm:
            add_project(project_info)
        
        project_info = {'project_name': 'Testproject', 'group_name': 'TestGroup', 'project_details': 'sequencing'}
        with self.assertRaises(SystemExit, msg='Missing institution') as cm:
            add_project(project_info)

        project_info = {'project_name': 'Testproject', 'group_name': 'TestGroup', 'institution': 'Test Institution'}
        with self.assertRaises(SystemExit, msg='Missing project_details') as cm:
            add_project(project_info)
