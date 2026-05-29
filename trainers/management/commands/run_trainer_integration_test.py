from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.test import Client
from datetime import date, timedelta
import uuid

from pravaah.trainers.models import Trainer
from pravaah.batch.models import BatchAssignment
from pravaah.assessment.models import Assessment


class Command(BaseCommand):
    help = "Run DB-backed integration test for trainer profile (uses current DB)."

    def handle(self, *args, **options):
        suffix = uuid.uuid4().hex[:6]
        username = f"test_integ_{suffix}"
        trainer_code = f"TR{suffix}"
        batch_name = f"Batch Integ {suffix}"
        assessment_name = f"Integ Assessment {suffix}"

        try:
            # create user and linked trainer
            user = User.objects.create_user(username=username, password='testpass123', email=f'{username}@example.com')
            trainer = Trainer.objects.create(
                trainer_code=trainer_code,
                first_name='TI',
                last_name='User',
                qualification='MSc',
                email=user.email,
                joining_date=date.today(),
                user=user
            )

            batch = BatchAssignment.objects.create(
                trainer=trainer,
                batch_name=batch_name,
                course_name='Integration Course',
                start_date=date.today(),
                end_date=date.today() + timedelta(days=10),
                student_count=1,
                status='accepted'
            )

            assessment = Assessment.objects.create(
                batch=batch,
                assessment_name=assessment_name,
                assessment_type='Quiz',
                due_date=date.today() + timedelta(days=5),
                total_marks=10,
                description='Integration test'
            )

            # use test client to login and fetch profile
            client = Client()
            logged_in = client.login(username=username, password='testpass123')
            if not logged_in:
                raise CommandError('Could not log in as created test user')

            # ensure Host header accepted by Django
            resp = client.get('/trainers/profile/', HTTP_HOST='127.0.0.1')
            if resp.status_code != 200:
                raise CommandError(f'trainers/profile returned status {resp.status_code}')

            content = resp.content.decode('utf-8')
            if batch_name in content and assessment_name in content:
                self.stdout.write('Integration test PASSED: batch and assessment visible on trainer profile')
                result = 0
            else:
                self.stderr.write('Integration test FAILED: expected content not found in profile HTML')
                # dump a short snippet for debugging
                self.stderr.write(content[:1000])
                result = 3

        except CommandError:
            # re-raise CommandError after cleanup
            raise
        except Exception as e:
            self.stderr.write('ERROR: Exception during integration test: ' + str(e))
            result = 4

        finally:
            # Cleanup created objects (best-effort)
            try:
                Assessment.objects.filter(assessment_name=assessment_name).delete()
                BatchAssignment.objects.filter(batch_name=batch_name).delete()
                Trainer.objects.filter(trainer_code=trainer_code).delete()
                User.objects.filter(username=username).delete()
                self.stdout.write('Cleanup completed')
            except Exception as e:
                self.stderr.write('Cleanup error: ' + str(e))

        if result != 0:
            raise CommandError('Integration test failed (see messages above)')
        else:
            self.stdout.write('Integration test completed successfully')
