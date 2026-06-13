from django.test import SimpleTestCase
from django.urls import resolve, reverse


class SetupRouteTests(SimpleTestCase):
    def test_landing_route_resolves(self):
        match = resolve(reverse('landing'))

        self.assertEqual(match.func.__name__, 'landing')
