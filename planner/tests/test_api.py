from django.test import RequestFactory, SimpleTestCase
from rest_framework import status

from planner.api import api_error, api_success, json_error, json_success


class GlobalApiResponseTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/api/test/')

    def test_drf_success_and_error_responses_use_standard_shape(self):
        success = api_success('Loaded.', {'count': 2})
        error = api_error(
            'Validation failed.',
            {'title': ['This field is required.']},
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

        self.assertEqual(success.status_code, 200)
        self.assertEqual(success.data, {
            'ok': True,
            'message': 'Loaded.',
            'data': {'count': 2},
        })
        self.assertEqual(error.status_code, 422)
        self.assertEqual(error.data, {
            'ok': False,
            'message': 'Validation failed.',
            'errors': {'title': ['This field is required.']},
        })

    def test_json_success_and_error_responses_use_standard_shape(self):
        success = json_success('Saved.', {'id': 1})
        error = json_error('Invalid JSON.', {'json': ['Request body must be valid JSON.']})

        self.assertEqual(success.status_code, 200)
        self.assertJSONEqual(success.content, {
            'ok': True,
            'message': 'Saved.',
            'data': {'id': 1},
        })
        self.assertEqual(error.status_code, 400)
        self.assertJSONEqual(error.content, {
            'ok': False,
            'message': 'Invalid JSON.',
            'errors': {'json': ['Request body must be valid JSON.']},
        })
