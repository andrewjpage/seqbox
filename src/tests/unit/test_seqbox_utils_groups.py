import sys
import os
from flask_testing import TestCase
import pandas as pd
sys.path.append('../')
sys.path.append('./')
sys.path.append('../scripts')
from app import app, db
from app.models import  Project, SampleSource
from scripts.utils.db import add_group, get_group

class TestSeqboxUtilsGroups(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app
    
    # reset the database before you start
    def setUp(self):
        assert os.environ['DATABASE_URL'].split('/')[3].startswith('test') # you really dont want to delete a production DB
        db.drop_all()
        db.create_all()

    def test_get_group_where_none_exist_already(self):
        self.setUp()
        group_info = {'group_name': 'TestGroup', 'institution': 'Test Institution', 'pi': 'Test PI'}
        matching_group = get_group(group_info)
        self.assertFalse(matching_group)

    def test_add_group(self):
        self.setUp()
        group_info = {'group_name': 'TestGroup', 'institution': 'Test Institution', 'pi': 'Test PI'}
        matching_group = get_group(group_info)
        self.assertFalse(matching_group, msg="Group should not exist in the database already")

        add_group(group_info)
        matching_group = get_group(group_info)
        self.assertEqual(matching_group.group_name, 'TestGroup')
        self.assertEqual(matching_group.institution, 'Test Institution')
        self.assertEqual(matching_group.pi, 'Test PI')
    
    def test_add_multiple_groups(self):
        self.setUp()
        group_info_list = [
            {'group_name': 'TestGroup', 'institution': 'Test Institution', 'pi': 'Test PI'},
            {'group_name': 'AnotherGroup', 'institution': 'Another Institution', 'pi': 'Another PI'},
            {'group_name': 'ThirdGroup', 'institution': 'Third Institution', 'pi': 'Third PI'}
        ]
        for group_info in group_info_list:
            matching_group = get_group(group_info)
            self.assertFalse(matching_group, msg="Group should not exist in the database already")

            add_group(group_info)
            matching_group = get_group(group_info)
            self.assertEqual(matching_group.group_name, group_info['group_name'])
            self.assertEqual(matching_group.institution, group_info['institution'])
            self.assertEqual(matching_group.pi, group_info['pi'])

    def test_add_group_with_invalid_group_names(self):
        self.setUp()
        # Groups cant have spaces in their names
        group_info = {'group_name': 'Test Group', 'institution': 'Test Institution', 'pi': 'Test PI'}
        with self.assertRaises(ValueError) as cm:
            add_group(group_info)

        # groups cant have backsalshes in their names
        group_info['group_name'] = 'Test/Group'
        with self.assertRaises(ValueError) as cm:
            add_group(group_info)

        # groups cant be empty
        group_info['group_name'] = None
        with self.assertRaises(ValueError) as cm:
            add_group(group_info)

    def test_add_group_with_invalid_intitute(self):
        self.setUp()
        group_info = {'group_name': 'TestGroup', 'institution': None, 'pi': 'Test PI'}
        with self.assertRaises(ValueError) as cm:
            add_group(group_info)

    def test_add_same_group_twice(self):
        self.setUp()
        group_info = {'group_name': 'TestGroup', 'institution': 'Test Institution', 'pi': 'Test PI'}
        self.assertTrue(add_group(group_info))
        self.assertFalse(add_group(group_info))
