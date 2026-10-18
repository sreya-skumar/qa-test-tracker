"""
Automated Backend API Tests for QA Test & Defect Tracker.
Uses Python's standard unittest framework to test all REST endpoints.
"""

import unittest
import json
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from database import init_db

class TestTrackerAPITestCase(unittest.TestCase):
    """Test suite for QA Test Case & Bug Tracker REST API."""

    @classmethod
    def setUpClass(cls):
        """Initializes database before tests."""
        init_db()

    def setUp(self):
        """Creates a fresh test client for each test."""
        self.client = app.test_client()
        self.client.testing = True

    def test_01_health_check(self):
        """Asserts health endpoint returns HTTP 200 and database connected."""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data.get('status'), 'healthy')
        self.assertEqual(data.get('database'), 'connected')

    def test_02_get_stats(self):
        """Asserts stats endpoint returns calculated metrics."""
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('total_test_cases', data)
        self.assertIn('pass_rate_percent', data)
        self.assertIn('total_defects', data)
        self.assertGreater(data['total_test_cases'], 0)

    def test_03_create_test_case_success(self):
        """Asserts creating a valid test case returns HTTP 201 Created."""
        payload = {
            "title": "Automated Unit Test - Playwright Gateway Ping",
            "description": "Verifies test case creation via REST API",
            "module": "API Endpoints",
            "priority": "High",
            "status": "Pending",
            "automated_by": "Playwright"
        }
        response = self.client.post(
            '/api/testcases',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('test_case', data)
        self.assertEqual(data['test_case']['title'], payload['title'])
        self.__class__.created_test_id = data['test_case']['id']

    def test_04_create_test_case_validation_error(self):
        """Asserts missing required title returns HTTP 400 Bad Request."""
        payload = {
            "title": "",
            "module": "Auth"
        }
        response = self.client.post(
            '/api/testcases',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_05_update_test_status(self):
        """Asserts updating a test case status works."""
        test_id = getattr(self.__class__, 'created_test_id', 1)
        payload = {
            "status": "Passed",
            "execution_time_ms": 135
        }
        response = self.client.post(
            f'/api/testcases/{test_id}/status',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['test_case']['status'], 'Passed')
        self.assertEqual(data['test_case']['execution_time_ms'], 135)

    def test_06_create_defect(self):
        """Asserts logging a defect linked to a test case returns HTTP 201."""
        test_id = getattr(self.__class__, 'created_test_id', 1)
        payload = {
            "test_case_id": test_id,
            "title": "Mock Timeout Defect during Playwright run",
            "severity": "Major",
            "status": "Open",
            "steps_to_reproduce": "1. Run automated suite\n2. Gateway timed out after 3000ms"
        }
        response = self.client.post(
            '/api/defects',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('defect', data)
        self.assertEqual(data['defect']['title'], payload['title'])

    def test_07_list_defects(self):
        """Asserts fetching defects list returns HTTP 200 and items."""
        response = self.client.get('/api/defects')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('defects', data)
        self.assertGreater(data['count'], 0)

    def test_08_login_success(self):
        """Asserts logging in with valid demo credentials returns HTTP 200."""
        payload = {
            "login": "sreya",
            "password": "Password123!"
        }
        response = self.client.post(
            '/api/auth/login',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['username'], 'sreya')

    def test_09_login_invalid_password(self):
        """Asserts logging in with incorrect password returns HTTP 401 Unauthorized."""
        payload = {
            "login": "sreya",
            "password": "WrongPassword!"
        }
        response = self.client.post(
            '/api/auth/login',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_10_register_user(self):
        """Asserts creating a new QA account returns HTTP 201 Created."""
        payload = {
            "username": "emma_tester",
            "email": "emma@testco.io",
            "password": "SecurePassword99!",
            "role": "QA Automation Tester"
        }
        response = self.client.post(
            '/api/auth/register',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['username'], 'emma_tester')

    def test_11_auth_me_and_logout(self):
        """Asserts /api/auth/me returns session state and logout clears it."""
        # Login first
        self.client.post(
            '/api/auth/login',
            data=json.dumps({"login": "sreya", "password": "Password123!"}),
            content_type='application/json'
        )

        # Check me
        me_res = self.client.get('/api/auth/me')
        self.assertEqual(me_res.status_code, 200)
        me_data = json.loads(me_res.data)
        self.assertTrue(me_data['authenticated'])
        self.assertEqual(me_data['user']['username'], 'sreya')

        # Logout
        logout_res = self.client.post('/api/auth/logout')
        self.assertEqual(logout_res.status_code, 200)

        # Verify logged out
        after_me = self.client.get('/api/auth/me')
        after_data = json.loads(after_me.data)
        self.assertFalse(after_data['authenticated'])

if __name__ == '__main__':
    unittest.main()
