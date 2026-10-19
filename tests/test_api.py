"""
Automated Backend API Tests for QA Test & Defect Tracker.
Uses Python's standard unittest framework to test all REST endpoints.
"""

import unittest
import json
import os
import sys
import time

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
        """Creates a fresh test client for each test with authenticated session as demo user sreya."""
        self.client = app.test_client()
        self.client.testing = True
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'sreya'

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
        unique_id = int(time.time() * 1000)
        username = f"emma_{unique_id}"
        email = f"emma_{unique_id}@testco.io"
        payload = {
            "username": username,
            "email": email,
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
        self.assertEqual(data['user']['username'], username)

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

    def test_12_new_user_has_isolated_empty_data(self):
        """Asserts a newly registered user starts with 0 test cases and 0 defects (data isolation)."""
        unique_id = int(time.time() * 1000) + 1
        username = f"newuser_{unique_id}"
        email = f"newuser_{unique_id}@example.com"

        # 1. Register a new user account (this logs them in automatically)
        reg_res = self.client.post(
            '/api/auth/register',
            data=json.dumps({
                "username": username,
                "email": email,
                "password": "Password123!",
                "role": "QA Analyst"
            }),
            content_type='application/json'
        )
        self.assertEqual(reg_res.status_code, 201)

        # 2. Check stats: new account must have 0 test cases and 0 defects
        stats_res = self.client.get('/api/stats')
        self.assertEqual(stats_res.status_code, 200)
        stats = json.loads(stats_res.data)
        self.assertEqual(stats['total_test_cases'], 0)
        self.assertEqual(stats['passed'], 0)
        self.assertEqual(stats['failed'], 0)
        self.assertEqual(stats['total_defects'], 0)
        self.assertEqual(stats['open_defects'], 0)
        self.assertEqual(stats['pass_rate_percent'], 0)

        # 3. Check test cases: new account must have empty list
        tests_res = self.client.get('/api/testcases')
        self.assertEqual(tests_res.status_code, 200)
        tests_data = json.loads(tests_res.data)
        self.assertEqual(tests_data['count'], 0)
        self.assertEqual(len(tests_data['test_cases']), 0)

        # 4. Check defects: new account must have empty list
        defects_res = self.client.get('/api/defects')
        self.assertEqual(defects_res.status_code, 200)
        defects_data = json.loads(defects_res.data)
        self.assertEqual(defects_data['count'], 0)
        self.assertEqual(len(defects_data['defects']), 0)

        # 5. New user creates 1 test case
        create_res = self.client.post(
            '/api/testcases',
            data=json.dumps({
                "title": "New User Custom Smoke Test",
                "description": "Custom test belonging exclusively to this user",
                "module": "Checkout",
                "priority": "High",
                "status": "Passed",
                "automated_by": "Playwright"
            }),
            content_type='application/json'
        )
        self.assertEqual(create_res.status_code, 201)

        # 6. Verify new user now sees exactly 1 test case
        my_tests_res = self.client.get('/api/testcases')
        my_tests = json.loads(my_tests_res.data)
        self.assertEqual(my_tests['count'], 1)
        self.assertEqual(my_tests['test_cases'][0]['title'], "New User Custom Smoke Test")

        # 7. Log out new user and log in as sreya
        self.client.post('/api/auth/logout')
        self.client.post(
            '/api/auth/login',
            data=json.dumps({"login": "sreya", "password": "Password123!"}),
            content_type='application/json'
        )

        # 8. Verify sreya does NOT see new user's test case
        sreya_tests_res = self.client.get('/api/testcases')
        sreya_tests = json.loads(sreya_tests_res.data)['test_cases']
        sreya_titles = [t['title'] for t in sreya_tests]
        self.assertNotIn("New User Custom Smoke Test", sreya_titles)
        self.assertGreaterEqual(len(sreya_tests), 8)

    def test_13_unauthenticated_cannot_create_or_modify(self):
        """Asserts unauthenticated requests cannot create test cases or defects."""
        # Clear session to simulate logged out user
        with self.client.session_transaction() as sess:
            sess.clear()

        # Attempt to create a test case without authentication
        res = self.client.post(
            '/api/testcases',
            data=json.dumps({"title": "Hacker Test", "module": "Security"}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 401)

        # Attempt to create a defect without authentication
        res_defect = self.client.post(
            '/api/defects',
            data=json.dumps({"title": "Hacker Defect"}),
            content_type='application/json'
        )
        self.assertEqual(res_defect.status_code, 401)

if __name__ == '__main__':
    unittest.main()
