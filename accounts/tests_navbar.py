from django.test import SimpleTestCase, RequestFactory
from django.template.loader import render_to_string
from django.contrib.auth.models import AnonymousUser, User

class NavbarTemplateTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        # lightweight fake user to avoid DB access
        class _User:
            username = 'tester'
            is_authenticated = True
            is_staff = False
            email = ''
        self.user = _User()

    def test_navbar_renders_for_anonymous(self):
        request = self.factory.get('/')
        request.user = AnonymousUser()
        html = render_to_string('navbar.html', request=request)
        self.assertIn('PRAVAAH', html)
        self.assertTrue(('Sign in' in html) or ('Login' in html))

    def test_navbar_renders_for_authenticated(self):
        request = self.factory.get('/')
        request.user = self.user
        html = render_to_string('navbar.html', request=request)
        self.assertIn('tester', html)
        self.assertIn('Logout', html)
