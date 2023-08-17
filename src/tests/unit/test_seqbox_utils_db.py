import sys
from flask_testing import TestCase
import pandas as pd
sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')
from app import app, db
from app.models import  Project, SampleSource
from seqbox_utils import add_group, get_group

class TestSeqboxUtilsDB(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app
    
    def setUp(self):
        assert os.environ['DATABASE_URL'].split('/')[-1].startswith('test') # you really dont want to delete a production DB
        db.drop_all()
        db.create_all()

    def test_get_group_where_none_exist_already(self):
        group_info = {'group_name': 'TestGroup', 'institution': 'Test Institution', 'pi': 'Test PI'}
        matching_group = get_group(group_info)
        self.assertFalse(matching_group)

    def test_add_group(self):
        group_info = {'group_name': 'TestGroup', 'institution': 'Test Institution', 'pi': 'Test PI'}
        matching_group = get_group(group_info)
        self.assertFalse(matching_group, msg="Group should not exist in the database already")

        actual_group = add_group(group_info)
        matching_group = get_group(group_info)
        self.assertFalse(matching_group, msg="Group should now exist in the database")

        self.assertEqual(actual_group.group_name, 'TestGroup')
        self.assertEqual(actual_group.institution, 'Test Institution')
        self.assertEqual(actual_group.pi, 'Test PI')
    
    def test_add_multiple_groups(self):
        group_info_list = [
            {'group_name': 'TestGroup', 'institution': 'Test Institution', 'pi': 'Test PI'},
            {'group_name': 'AnotherGroup', 'institution': 'Another Institution', 'pi': 'Another PI'},
            {'group_name': 'ThirdGroup', 'institution': 'Third Institution', 'pi': 'Third PI'}
        ]
        for group_info in group_info_list:
            matching_group = get_group(group_info)
            self.assertFalse(matching_group, msg="Group should not exist in the database already")

            actual_group = add_group(group_info)
            matching_group = get_group(group_info)
            self.assertTrue(matching_group, msg="Group should now exist in the database")

            self.assertEqual(actual_group.group_name, group_info['group_name'])
            self.assertEqual(actual_group.institution, group_info['institution'])
            self.assertEqual(actual_group.pi, group_info['pi'])
