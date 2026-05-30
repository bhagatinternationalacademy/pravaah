from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Trainer, Attendance
from django.db import connection
from django.conf import settings
import datetime

class AttendanceHistoryDBTest(TestCase):
    def setUp(self):
        existing = User.objects.filter(username='t2').first()
        if existing:
            self.user = existing
        else:
            self.user = User.objects.create_user(username='t2', password='pass')

        self.trainer, _ = Trainer.objects.get_or_create(trainer_code='T002', defaults={
            'first_name': 'Hist', 'last_name': 'Trainer', 'email': 't2@example.com'
        })
        if not getattr(self.trainer, 'user', None):
            self.trainer.user = self.user
            self.trainer.save()

        # create participants table and insert (adapt to existing participants schema if present)
        # if test settings ask for stub participants, skip creating/inserting into real table
        if getattr(settings, 'FORCE_USE_STUB_PARTICIPANTS', False):
            pass
        else:
            with connection.cursor() as cursor:
                tables = connection.introspection.table_names()
                if 'participants' not in tables:
                    if connection.vendor == 'sqlite':
                        cursor.execute("CREATE TABLE IF NOT EXISTS participants (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, mobile TEXT, batch_id INTEGER)")
                        cursor.execute("INSERT INTO participants (name,email,mobile,batch_id) VALUES (?,?,?,?)", ('A','a@example.com','111', 2))
                        cursor.execute("INSERT INTO participants (name,email,mobile,batch_id) VALUES (?,?,?,?)", ('B','b@example.com','222', 2))
                    else:
                        cursor.execute("CREATE TABLE IF NOT EXISTS participants (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), email VARCHAR(255), mobile VARCHAR(20), batch_id INT)")
                        cursor.execute("INSERT INTO participants (name,email,mobile,batch_id) VALUES (%s,%s,%s,%s)", ('A','a@example.com','111', 2))
                        cursor.execute("INSERT INTO participants (name,email,mobile,batch_id) VALUES (%s,%s,%s,%s)", ('B','b@example.com','222', 2))
                else:
                    # adapt inserts to existing schema
                    desc = connection.introspection.get_table_description(cursor, 'participants')
                    cols = [c.name for c in desc]
                    if 'name' in cols and 'batch_id' in cols:
                        if connection.vendor == 'sqlite':
                            cursor.execute("INSERT INTO participants (name,email,mobile,batch_id) VALUES (?,?,?,?)", ('A','a@example.com','111', 2))
                            cursor.execute("INSERT INTO participants (name,email,mobile,batch_id) VALUES (?,?,?,?)", ('B','b@example.com','222', 2))
                        else:
                            cursor.execute("INSERT INTO participants (name,email,mobile,batch_id) VALUES (%s,%s,%s,%s)", ('A','a@example.com','111', 2))
                            cursor.execute("INSERT INTO participants (name,email,mobile,batch_id) VALUES (%s,%s,%s,%s)", ('B','b@example.com','222', 2))
                    elif 'first_name' in cols and 'last_name' in cols:
                        # map to first_name/last_name and try course_id as batch_id
                        if connection.vendor == 'sqlite':
                            cursor.execute("INSERT INTO participants (admission_no,first_name,last_name,email,mobile,course_id) VALUES (?,?,?,?,?,?)", ('A1','A','', 'a@example.com','111', 2))
                            cursor.execute("INSERT INTO participants (admission_no,first_name,last_name,email,mobile,course_id) VALUES (?,?,?,?,?,?)", ('B1','B','', 'b@example.com','222', 2))
                        else:
                            cursor.execute("INSERT INTO participants (admission_no,first_name,last_name,email,mobile,course_id) VALUES (%s,%s,%s,%s,%s,%s)", ('A1','A','', 'a@example.com','111', 2))
                            cursor.execute("INSERT INTO participants (admission_no,first_name,last_name,email,mobile,course_id) VALUES (%s,%s,%s,%s,%s,%s)", ('B1','B','', 'b@example.com','222', 2))
                    else:
                        # best-effort: try inserting minimal columns if available
                        if 'email' in cols and 'mobile' in cols:
                            if connection.vendor == 'sqlite':
                                cursor.execute("INSERT INTO participants (email,mobile) VALUES (?,?)", ('a@example.com','111'))
                                cursor.execute("INSERT INTO participants (email,mobile) VALUES (?,?)", ('b@example.com','222'))
                            else:
                                cursor.execute("INSERT INTO participants (email,mobile) VALUES (%s,%s)", ('a@example.com','111'))
                                cursor.execute("INSERT INTO participants (email,mobile) VALUES (%s,%s)", ('b@example.com','222'))
                    # else give up silently

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
