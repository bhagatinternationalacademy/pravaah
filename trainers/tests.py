from django.test import SimpleTestCase
from django.template import loader
from types import SimpleNamespace
from datetime import date


class TrainerProfileTemplateTests(SimpleTestCase):
    """Render trainers/trainer_profile.html with constructed context objects (no DB) and assert UI sections appear."""

    def test_template_shows_batches_and_assessments(self):
        # build fake trainer
        trainer = SimpleNamespace(
            first_name='Test',
            last_name='Trainer',
            trainer_code='TR001',
            availability='Available',
            status='Active',
            joining_date=date.today(),
            profile_photo=None,
            qualification='MSc',
            specialization='Python',
            mobile='1234567890',
            email='trainer@example.com'
        )

        # fake batch objects
        batch = SimpleNamespace(
            pk=1,
            batch_name='Batch A',
            course_name='Python Full Stack',
            start_date=date.today(),
            end_date=date.today(),
            student_count=10,
            status='accepted'
        )

        # fake assessment objects; include batch with batch_name and pk as template expects
        assessment = SimpleNamespace(
            assessment_name='Python Quiz',
            assessment_type='Quiz',
            due_date=date.today(),
            batch=SimpleNamespace(pk=1, batch_name='Batch A')
        )

        context = {
            'trainer': trainer,
            'skills_qs': [],
            'certifications': [],
            'batches': [batch],
            'assessments': [assessment],
            'availability_entries': []
        }

        tmpl = loader.get_template('trainers/trainer_profile.html')
        rendered = tmpl.render(context)

        self.assertIn('Batch A', rendered)
        self.assertIn('Python Quiz', rendered)
