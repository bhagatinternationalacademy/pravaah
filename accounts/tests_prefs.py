from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import UserProfile

class SidebarPrefAPITest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='prefuser', password='pass')
        self.client = Client()
        self.client.login(username='prefuser', password='pass')

    def test_get_default_pref(self):
        url = reverse('accounts:sidebar_pref')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('sidebar_collapsed', data)

    def test_post_pref_updates_profile(self):
        url = reverse('accounts:sidebar_pref')
        resp = self.client.post(url, {'collapsed': 'true'})
        self.assertEqual(resp.status_code, 200)
        up = UserProfile.objects.get(user=self.user)
        self.assertTrue(up.sidebar_collapsed)

        # now POST false
        resp2 = self.client.post(url, {'collapsed': 'false'})
        up.refresh_from_db()
        self.assertFalse(up.sidebar_collapsed)
