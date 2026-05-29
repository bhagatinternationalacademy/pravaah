from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create trainer user trainer1 and Trainer entry'

    def handle(self, *args, **options):
        User = get_user_model()
        username = 'trainer1'
        password = 'Trainer@123'
        u, created = User.objects.get_or_create(username=username, defaults={'email':'trainer1@example.com'})
        if created:
            u.set_password(password)
            u.is_active = True
            u.save()
        # import Trainer model lazily
        try:
            from pravaah.trainers.models import Trainer
        except Exception:
            self.stdout.write(self.style.ERROR('Could not import Trainer model'))
            return
        t, tcreated = Trainer.objects.get_or_create(trainer_code='T001', defaults={'user': u, 'first_name': 'Test', 'last_name': 'Trainer'})
        if not t.user:
            t.user = u
            t.save()
        self.stdout.write(self.style.SUCCESS(f'User created={created}, Trainer created={tcreated}, username={u.username}'))
