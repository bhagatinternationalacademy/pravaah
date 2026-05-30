from django.test import SimpleTestCase, RequestFactory
from django.template.loader import render_to_string
from django.contrib.auth.models import AnonymousUser, User

class NavbarTemplateTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User(username='tester')
        self.user.set_password('pass')

    def test_navbar_renders_for_anonymous(self):
        request = self.factory.get('/')
        request.user = AnonymousUser()
        html = render_to_string('navbar.html', request=request)
        self.assertIn('PRAVAAH', html)
        self.assertIn('Sign in', html)

    def test_navbar_renders_for_authenticated(self):
        request = self.factory.get('/')
        request.user = self.user
        html = render_to_string('navbar.html', request=request)
        self.assertIn('Notifications', html)
        self.assertIn('Logout', html)
