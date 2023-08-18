import unittest
import sys
from flask import url_for
from flask_testing import TestCase
sys.path.append('../')
sys.path.append('./')

from app import app, db

class TestBaseView(TestCase):

    def create_app(self):
        app.config['TESTING'] = True
        return app

    #def test_index_view_not_logged_in(self):
    #    # the index page should immediately redirect you to the login page if you are not logged in
    #    response = self.client.get(url_for('index'))
    #    self.assertEqual(response.status_code, 302, msg="Should always be redirected to the login page")
    #    self.assertIn(b'login', response.data)
#
    #def test_login_view_not_logged_in(self):
    #    # if you go directly to the login page you should see the login form
    #    response = self.client.get(url_for('login'))
    #    self.assertEqual(response.status_code, 200)
    #    self.assertIn(b'Sign In', response.data)
#
    #def test_logout_view_not_logged_in(self):
    #    # the logout page should always redirect to index at the end
    #    response = self.client.get(url_for('logout'))
    #    self.assertEqual(response.status_code, 302)
    #    self.assertIn(b'index', response.data)
#
    #def test_register_view_not_logged_in(self):
    #    # the registration page should show
    #    response = self.client.get(url_for('register'))
    #    self.assertEqual(response.status_code, 200)
    #    self.assertIn(b'Register', response.data)
#
    #def test_sample_view_not_logged_in(self):
    #    url = 'sample'
    #    response = self.client.get(url_for(url))
    #    self.assertEqual(response.status_code, 302, msg="Internal page shown despite not being logged in: " + str(url))
    #    self.assertIn(b'login', response.data)
#
    #def test_list_sample_view_not_logged_in(self):
    #    url = 'list_sample'
    #    response = self.client.get(url_for(url))
    #    self.assertEqual(response.status_code, 302, msg="Internal page shown despite not being logged in: " + str(url))
    #    self.assertIn(b'login', response.data)
    #
    #def test_edit_sample_view_not_logged_in(self):
    #    url = 'edit/1'
    #    response = self.client.get(url_for(url))
    #    self.assertEqual(response.status_code, 302, msg="Internal page shown despite not being logged in: " + str(url))
    #    self.assertIn(b'login', response.data)
#
    #def test_sample_delete_view_not_logged_in(self):
    #    url = 'sample_delete/1'
    #    response = self.client.get(url_for(url))
    #    self.assertEqual(response.status_code, 302, msg="Internal page shown despite not being logged in: " + str(url))
    #    self.assertIn(b'login', response.data)
#
    #def test_batch_view_not_logged_in(self):
    #    url = 'batch'
    #    response = self.client.get(url_for(url))
    #    self.assertEqual(response.status_code, 302, msg="Internal page shown despite not being logged in: " + str(url))
    #    self.assertIn(b'login', response.data)
#
    #def test_list_batch_view_not_logged_in(self):
    #    url = 'list_batch'
    #    response = self.client.get(url_for(url))
    #    self.assertEqual(response.status_code, 302, msg="Internal page shown despite not being logged in: " + str(url))
    #    self.assertIn(b'login', response.data)
#
    #def test_batch_edit_view_not_logged_in(self):
    #    url = 'batch_edit/1'
    #    response = self.client.get(url_for(url))
    #    self.assertEqual(response.status_code, 302, msg="Internal page shown despite not being logged in: " + str(url))
    #    self.assertIn(b'login', response.data)
#
    #def test_batch_delete_view_not_logged_in(self):
    #    url = 'batch_delete/1'
    #    response = self.client.get(url_for(url))
    #    self.assertEqual(response.status_code, 302, msg="Internal page shown despite not being logged in: " + str(url))
    #    self.assertIn(b'login', response.data)
#
    #def test_location_view_not_logged_in(self):
    #    url = 'location'
    #    response = self.client.get(url_for(url))
    #    self.assertEqual(response.status_code, 302, msg="Internal page shown despite not being logged in: " + url)
    #    self.assertIn(b'login', response.data)
#
    #def test_list_location_view_not_logged_in(self):
    #    url = 'list_location'
    #    response = self.client.get(url_for(url))
    #    self.assertEqual(response.status_code, 302, msg="Internal page shown despite not being logged in: " + url)
    #    self.assertIn(b'login', response.data)
#
    #def test_location_edit_view_not_logged_in(self):
    #    url = 'location_edit/1'
    #    response = self.client.get(url_for(url))
    #    self.assertEqual(response.status_code, 302, msg="Internal page shown despite not being logged in: " + url)
    #    self.assertIn(b'login', response.data)
#
    #def test_location_delete_view_not_logged_in(self):
    #    url = 'location_delete/1'
    #    response = self.client.get(url_for(url))
    #    self.assertEqual(response.status_code, 302, msg="Internal page shown despite not being logged in: " + url)
    #    self.assertIn(b'login', response.data)
#
    #def test_result1_view_not_logged_in(self):
    #    url = 'result1'
    #    response = self.client.get(url_for(url))
    #    self.assertEqual(response.status_code, 302, msg="Internal page shown despite not being logged in: " + url)
    #    self.assertIn(b'login', response.data)
    #
    #def test_list_result1_view_not_logged_in(self):
    #    url = 'list_result1'
    #    response = self.client.get(url_for(url))
    #    self.assertEqual(response.status_code, 302, msg="Internal page shown despite not being logged in: " + url)
    #    self.assertIn(b'login', response.data)
#
    #def test_result1_edit_view_not_logged_in(self):
    #    url = 'result1_edit/1'
    #    response = self.client.get(url_for(url))
    #    self.assertEqual(response.status_code, 302, msg="Internal page shown despite not being logged in: " + url)
    #    self.assertIn(b'login', response.data)
#
    #def test_result1_delete_view_not_logged_in(self):
    #    url = 'result1_delete/1'
    #    response = self.client.get(url_for(url))
    #    self.assertEqual(response.status_code, 302, msg="Internal page shown despite not being logged in: " + url)
    #    self.assertIn(b'login', response.data)
    #
    #def test_mykrobe_view_not_logged_in(self):
    #    url = 'mykrobe'
    #    response = self.client.get(url_for(url))
    #    self.assertEqual(response.status_code, 302, msg="Internal page shown despite not being logged in: " + url)
    #    self.assertIn(b'login', response.data)
#
    #def test_list_mykrobe_view_not_logged_in(self):
    #    url = 'list_mykrobe'
    #    response = self.client.get(url_for(url))
    #    self.assertEqual(response.status_code, 302, msg="Internal page shown despite not being logged in: " + url)
    #    self.assertIn(b'login', response.data)
#
    #def test_mykrobe_edit_view_not_logged_in(self):
    #    url = 'mykrobe_edit/1'
    #    response = self.client.get(url_for(url))
    #    self.assertEqual(response.status_code, 302, msg="Internal page shown despite not being logged in:" + url)
    #    self.assertIn(b'login', response.data)
#
    #def test_mykrobe_delete_view_not_logged_in(self):
    #    url = 'mykrobe_delete/1'
    #    response = self.client.get(url_for(url))
    #    self.assertEqual(response.status_code, 302, msg="Internal page shown despite not being logged in:" + url)
    #    self.assertIn(b'login', response.data)
    #
    #def test_project_view_not_logged_in(self):
    #    url = 'project'
    #    response = self.client.get(url_for(url))
    #    self.assertEqual(response.status_code, 302, msg="Internal page shown despite not being logged in:" + url)
    #    self.assertIn(b'login', response.data)
#
    #def test_list_project_view_not_logged_in(self):
    #    url = 'list_project'
    #    response = self.client.get(url_for(url))
    #    self.assertEqual(response.status_code, 302, msg="Internal page shown despite not being logged in:" + url)
    #    self.assertIn(b'login', response.data)
    #
    #def test_project_edit_view_not_logged_in(self):
    #    url = 'project_edit/1'
    #    response = self.client.get(url_for(url))
    #    self.assertEqual(response.status_code, 302, msg="Internal page shown despite not being logged in:" + url)
    #    self.assertIn(b'login', response.data)
    #
    #def test_project_delete_view_not_logged_in(self):
    #    url = 'project_delete/1'
    #    response = self.client.get(url_for(url))
    #    self.assertEqual(response.status_code, 302, msg="Internal page shown despite not being logged in:" + url)
    #    self.assertIn(b'login', response.data)
    #
    #def test_sample_project_view_not_logged_in(self):
    #    url = 'sample_project'
    #    response = self.client.get(url_for(url))
    #    self.assertEqual(response.status_code, 302, msg="Internal page shown despite not being logged in:" + url)
    #    self.assertIn(b'login', response.data)

if __name__ == '__main__':
    unittest.main()