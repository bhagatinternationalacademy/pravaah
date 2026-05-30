from django.test import SimpleTestCase, RequestFactory
from django.template.loader import render_to_string
from django.contrib.auth.models import AnonymousUser, User

class SidebarTemplateTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User(username='tester')

    def test_sidebar_renders(self):
        request = self.factory.get('/')
        request.user = self.user
        # provide context flags expected by sidebar
        html = render_to_string('sidebar.html', {'request': request, 'is_trainer': True, 'is_admin': False})
        self.assertIn('My Profile', html)
        self.assertIn('PRAVAAH', html)
