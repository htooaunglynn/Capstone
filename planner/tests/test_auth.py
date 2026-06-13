from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken


User = get_user_model()


class PageAuthTests(TestCase):
    def test_register_page_shows_account_format_rules(self):
        response = self.client.get(reverse('register'))

        self.assertContains(response, 'Use letters, numbers, and @/./+/-/_ only')
        self.assertContains(response, 'name@example.com')
        self.assertContains(response, 'Your password can’t be too similar to your other personal information.')

    def test_login_page_shows_login_hints(self):
        response = self.client.get(reverse('login'))

        self.assertContains(response, 'Enter the username you used when creating your account.')
        self.assertContains(response, 'Passwords are case-sensitive.')

    def test_register_creates_user_logs_in_and_redirects_to_dashboard(self):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'alice',
                'email': 'alice@example.com',
                'password1': 'strong-test-pass-123',
                'password2': 'strong-test-pass-123',
            },
        )

        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(User.objects.filter(username='alice').exists())
        self.assertEqual(
            int(self.client.session['_auth_user_id']),
            User.objects.get(username='alice').id,
        )

    def test_login_and_logout_flow(self):
        User.objects.create_user(username='alice', password='strong-test-pass-123')

        login_response = self.client.post(
            reverse('login'),
            {
                'username': 'alice',
                'password': 'strong-test-pass-123',
            },
        )
        self.assertRedirects(login_response, reverse('dashboard'))

        logout_response = self.client.post(reverse('logout'))
        self.assertRedirects(logout_response, reverse('landing'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_dashboard_redirects_logged_out_users(self):
        response = self.client.get(reverse('dashboard'))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")


class ApiAuthTests(TestCase):
    def test_api_register_returns_standard_response_with_tokens(self):
        response = self.client.post(
            reverse('api_auth_register'),
            {
                'username': 'alice',
                'email': 'alice@example.com',
                'password': 'strong-test-pass-123',
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertTrue(body['ok'])
        self.assertEqual(body['data']['user']['username'], 'alice')
        self.assertIn('access', body['data']['tokens'])
        self.assertIn('refresh', body['data']['tokens'])

    def test_api_login_refresh_me_and_logout_blacklists_refresh_token(self):
        user = User.objects.create_user(
            username='alice',
            email='alice@example.com',
            password='strong-test-pass-123',
        )

        login_response = self.client.post(
            reverse('api_auth_login'),
            {
                'username': 'alice',
                'password': 'strong-test-pass-123',
            },
            content_type='application/json',
        )
        self.assertEqual(login_response.status_code, 200)
        tokens = login_response.json()['data']['tokens']

        me_response = self.client.get(
            reverse('api_auth_me'),
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
        )
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.json()['data']['user']['id'], user.id)

        refresh_response = self.client.post(
            reverse('api_auth_refresh'),
            {'refresh': tokens['refresh']},
            content_type='application/json',
        )
        self.assertEqual(refresh_response.status_code, 200)
        rotated_refresh = refresh_response.json()['data']['tokens']['refresh']

        logout_response = self.client.post(
            reverse('api_auth_logout'),
            {'refresh': rotated_refresh},
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
        )
        self.assertEqual(logout_response.status_code, 200)
        self.assertTrue(logout_response.json()['ok'])
        self.assertEqual(BlacklistedToken.objects.count(), 2)

    def test_api_me_requires_jwt_authentication(self):
        response = self.client.get(reverse('api_auth_me'))

        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json()['ok'])
        self.assertIn('errors', response.json())
