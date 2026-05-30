from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Trainer, Attendance
from django.db import connection
import datetime

class AttendanceHistoryDBTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='t2', password='pass')
        self.trainer = Trainer.objects.create(trainer_code='T002', first_name='Hist', last_name='Trainer', email='t2@example.com')
        self.trainer.user = self.user
        self.trainer.save()

        # create participants table and insert
        with connection.cursor() as cursor:
            if connection.vendor == 'sqlite':
                cursor.execute("CREATE TABLE IF NOT EXISTS participants (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, mobile TEXT, batch_id INTEGER)")
                cursor.execute("INSERT INTO participants (name,email,mobile,batch_id) VALUES (?,?,?,?)", ('A','a@example.com','111', 2))
                cursor.execute("INSERT INTO participants (name,email,mobile,batch_id) VALUES (?,?,?,?)", ('B','b@example.com','222', 2))
            else:
                cursor.execute("CREATE TABLE IF NOT EXISTS participants (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), email VARCHAR(255), mobile VARCHAR(20), batch_id INT)")
                cursor.execute("INSERT INTO participants (name,email,mobile,batch_id) VALUES (%s,%s,%s,%s)", ('A','a@example.com','111', 2))
                cursor.execute("INSERT INTO participants (name,email,mobile,batch_id) VALUES (%s,%s,%s,%s)", ('B','b@example.com','222', 2))

        # create attendance records
        Attendance.objects.create(participant_id=1, batch_id=2, session_date=datetime.date(2026,5,20), status='Present', marked_by=self.user)
        Attendance.objects.create(participant_id=2, batch_id=2, session_date=datetime.date(2026,5,20), status='Absent', marked_by=self.user)

    def test_history_summary_shows_counts(self):
        client = Client()
        client.login(username='t2', password='pass')
        url = reverse('trainers:attendance_history', args=[2])
        resp = client.get(url)
        self.assertEqual(resp.status_code, 200)
        # should contain the session date and counts
        self.assertIn('2026-05-20', resp.content.decode())
        self.assertIn('Present', resp.content.decode())
        self.assertIn('Absent', resp.content.decode())

    def test_history_detail_shows_rows(self):
        client = Client()
        client.login(username='t2', password='pass')
        url = reverse('trainers:attendance_history', args=[2]) + '?session_date=2026-05-20'
        resp = client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('A', resp.content.decode())
        self.assertIn('B', resp.content.decode())

    def test_history_export_csv(self):
        client = Client()
        client.login(username='t2', password='pass')
        url = reverse('trainers:attendance_history', args=[2]) + '?session_date=2026-05-20&export=csv'
        resp = client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp['Content-Type'].startswith('text/csv'))
        content = resp.content.decode()
        self.assertIn('participant_id,participant_name,status,marked_at,marked_by', content)
        self.assertIn('A', content)
        self.assertIn('B', content)
