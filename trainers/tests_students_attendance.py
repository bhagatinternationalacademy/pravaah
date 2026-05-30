from django.test import SimpleTestCase
from django.template.loader import render_to_string

class StudentsAttendanceTemplateTests(SimpleTestCase):

    def test_students_list_renders(self):
        participants = [
            {'id': 1, 'name': 'Rahul', 'email': 'rahul@example.com', 'mobile': '9999999999', 'batch_id': 10},
            {'id': 2, 'name': 'Priya', 'email': 'priya@example.com', 'mobile': '8888888888', 'batch_id': 10},
        ]
        html = render_to_string('trainers/students_list.html', {'participants': participants, 'batch_id': 10})
        self.assertIn('Students', html)
        self.assertIn('Rahul', html)
        self.assertIn('Priya', html)
        self.assertIn('Mark Attendance', html)

    def test_attendance_template_renders_form(self):
        participants = [
            {'id': 1, 'name': 'Rahul', 'email': 'rahul@example.com', 'mobile': '9999999999'},
            {'id': 2, 'name': 'Priya', 'email': 'priya@example.com', 'mobile': '8888888888'},
        ]
        html = render_to_string('trainers/attendance.html', {'participants': participants, 'batch_id': 10})
        self.assertIn('Attendance for Batch 10', html)
        self.assertIn('input type="checkbox"', html)
        self.assertIn('Save Attendance', html)
