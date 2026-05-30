from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Trainer, Attendance
from django.db import connection
from django.conf import settings
import datetime

class AttendanceDBTest(TestCase):
    def setUp(self):
        # ensure user exists (use existing if present)
        existing = User.objects.filter(username='t1').first()
        if existing:
            self.user = existing
        else:
            self.user = User.objects.create_user(username='t1', password='pass')

        self.trainer, _ = Trainer.objects.get_or_create(trainer_code='T001', defaults={
            'first_name': 'Test', 'last_name': 'Trainer', 'email': 't1@example.com'
        })
        # link trainer to user if not already linked
        if not getattr(self.trainer, 'user', None):
            self.trainer.user = self.user
            self.trainer.save()

        # create participants table in test DB and insert two rows (adapt to existing schema if present)
        # if test settings ask for stub participants, skip creating/inserting into real table
        if getattr(settings, 'FORCE_USE_STUB_PARTICIPANTS', False):
            pass
        else:
            with connection.cursor() as cursor:
                tables = connection.introspection.table_names()
                if 'participants' not in tables:
                    if connection.vendor == 'sqlite':
                        cursor.execute("CREATE TABLE IF NOT EXISTS participants (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, mobile TEXT, batch_id INTEGER)")
                        cursor.execute("INSERT INTO participants (name,email,mobile,batch_id) VALUES (?,?,?,?)", ('Rahul','r@example.com','9999999999', 1))
                        cursor.execute("INSERT INTO participants (name,email,mobile,batch_id) VALUES (?,?,?,?)", ('Priya','p@example.com','8888888888', 1))
                    else:
                        cursor.execute("CREATE TABLE IF NOT EXISTS participants (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), email VARCHAR(255), mobile VARCHAR(20), batch_id INT)")
                        cursor.execute("INSERT INTO participants (name,email,mobile,batch_id) VALUES (%s,%s,%s,%s)", ('Rahul','r@example.com','9999999999', 1))
                        cursor.execute("INSERT INTO participants (name,email,mobile,batch_id) VALUES (%s,%s,%s,%s)", ('Priya','p@example.com','8888888888', 1))
                else:
                    desc = connection.introspection.get_table_description(cursor, 'participants')
                    cols = [c.name for c in desc]
                    if 'name' in cols and 'batch_id' in cols:
                        if connection.vendor == 'sqlite':
                            cursor.execute("INSERT INTO participants (name,email,mobile,batch_id) VALUES (?,?,?,?)", ('Rahul','r@example.com','9999999999', 1))
                            cursor.execute("INSERT INTO participants (name,email,mobile,batch_id) VALUES (?,?,?,?)", ('Priya','p@example.com','8888888888', 1))
                        else:
                            cursor.execute("INSERT INTO participants (name,email,mobile,batch_id) VALUES (%s,%s,%s,%s)", ('Rahul','r@example.com','9999999999', 1))
                            cursor.execute("INSERT INTO participants (name,email,mobile,batch_id) VALUES (%s,%s,%s,%s)", ('Priya','p@example.com','8888888888', 1))
                    elif 'first_name' in cols and 'last_name' in cols:
                        if connection.vendor == 'sqlite':
                            cursor.execute("INSERT INTO participants (admission_no,first_name,last_name,email,mobile,course_id) VALUES (?,?,?,?,?,?)", ('R001','Rahul','', 'r@example.com','9999999999', 1))
                            cursor.execute("INSERT INTO participants (admission_no,first_name,last_name,email,mobile,course_id) VALUES (?,?,?,?,?,?)", ('P001','Priya','', 'p@example.com','8888888888', 1))
                        else:
                            cursor.execute("INSERT INTO participants (admission_no,first_name,last_name,email,mobile,course_id) VALUES (%s,%s,%s,%s,%s,%s)", ('R001','Rahul','', 'r@example.com','9999999999', 1))
                            cursor.execute("INSERT INTO participants (admission_no,first_name,last_name,email,mobile,course_id) VALUES (%s,%s,%s,%s,%s,%s)", ('P001','Priya','', 'p@example.com','8888888888', 1))
                    else:
                        if 'email' in cols and 'mobile' in cols:
                            if connection.vendor == 'sqlite':
                                cursor.execute("INSERT INTO participants (email,mobile) VALUES (?,?)", ('r@example.com','9999999999'))
                                cursor.execute("INSERT INTO participants (email,mobile) VALUES (?,?)", ('p@example.com','8888888888'))
                            else:
                                cursor.execute("INSERT INTO participants (email,mobile) VALUES (%s,%s)", ('r@example.com','9999999999'))
                                cursor.execute("INSERT INTO participants (email,mobile) VALUES (%s,%s)", ('p@example.com','8888888888'))

    def test_attendance_post_creates_records(self):
        client = Client()
        logged_in = client.login(username='t1', password='pass')
        self.assertTrue(logged_in)
        url = reverse('trainers:attendance', args=[1])
        resp = client.post(url, {'present_1': 'on', 'present_2': 'on', 'session_date': '2026-05-30'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        # check attendance objects (both present)
        qs = Attendance.objects.filter(session_date=datetime.date(2026,5,30))
        self.assertEqual(qs.count(), 2)

    def test_attendance_records_absent_for_unmarked(self):
        client = Client()
        logged_in = client.login(username='t1', password='pass')
        self.assertTrue(logged_in)
        url = reverse('trainers:attendance', args=[1])
        # only mark participant 1 as present
        resp = client.post(url, {'present_1': 'on', 'session_date': '2026-05-31'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        qs = Attendance.objects.filter(session_date=datetime.date(2026,5,31))
        # two participants -> one present, one absent
        self.assertEqual(qs.count(), 2)
        statuses = set(q.status for q in qs)
        self.assertIn('Present', statuses)
        self.assertIn('Absent', statuses)

    def test_attendance_idempotent(self):
        client = Client()
        logged_in = client.login(username='t1', password='pass')
        self.assertTrue(logged_in)
        url = reverse('trainers:attendance', args=[1])
        resp1 = client.post(url, {'present_1': 'on', 'present_2': 'on', 'session_date': '2026-06-01'}, follow=True)
        self.assertEqual(resp1.status_code, 200)
        resp2 = client.post(url, {'present_1': 'on', 'present_2': 'on', 'session_date': '2026-06-01'}, follow=True)
        self.assertEqual(resp2.status_code, 200)
        qs = Attendance.objects.filter(session_date=datetime.date(2026,6,1))
        # should still be only two records
        self.assertEqual(qs.count(), 2)
