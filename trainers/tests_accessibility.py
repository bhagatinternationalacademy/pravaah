from django.test import SimpleTestCase
from django.template import loader
from types import SimpleNamespace
from datetime import date

class TrainerAccessibilityTests(SimpleTestCase):
    def test_sections_have_roles_and_aria_labels(self):
        trainer = SimpleNamespace(first_name='A', last_name='B', trainer_code='C', availability='Available', status='Active', joining_date=date.today(), profile_photo=None, qualification='', specialization='', mobile='', email='')
        batch = SimpleNamespace(pk=1, batch_name='Batch A', course_name='Course', start_date=date.today(), end_date=date.today(), student_count=1, status='accepted')
        assessment = SimpleNamespace(assessment_name='Assess', assessment_type='Quiz', due_date=date.today(), batch=SimpleNamespace(pk=1, batch_name='Batch A'))
        availability_entries = [SimpleNamespace(date=date.today(), note='note', status='available')]

        context = {'trainer': trainer, 'skills_qs': [], 'certifications': [], 'batches': [batch], 'assessments': [assessment], 'availability_entries': availability_entries}
        rendered = loader.get_template('trainers/trainer_profile.html').render(context)

        # check regions
        self.assertIn('role="region"', rendered)
        self.assertIn('aria-label="Assigned Batches"', rendered)
        self.assertIn('aria-label="Assessments"', rendered)
        self.assertIn('aria-label="Availability Entries"', rendered)

        # icons decorative
        self.assertIn('aria-hidden="true"', rendered)
