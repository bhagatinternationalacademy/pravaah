"""Standalone script to create/link a Trainer user by email.
Usage: python scripts\create_trainer_user_script.py <email>
"""
import sys
import os

if len(sys.argv) < 2:
    print('Usage: python scripts\\create_trainer_user_script.py <email>')
    sys.exit(1)

email = sys.argv[1]

# adjust path to project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pravaah.settings')

import django
django.setup()

from django.contrib.auth.models import User, Group, Permission
from django.utils.crypto import get_random_string
from django.contrib.contenttypes.models import ContentType
from trainers.models import Trainer


def main(email):
    trainer = Trainer.objects.filter(email__iexact=email).first()
    if not trainer:
        trainer = Trainer.objects.create(
            trainer_code=f"T{get_random_string(6).upper()}",
            first_name=email.split('@')[0],
            last_name='',
            email=email,
            status='Pending'
        )
        print(f'Created Trainer record with id={trainer.pk}')

    if trainer.user:
        print(f'Trainer already linked to user: {trainer.user.username}')
        return

    base_username = trainer.trainer_code or (trainer.email.split('@')[0] if trainer.email else 'trainer')
    username = base_username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1

    temp_password = get_random_string(10)
    user = User.objects.create_user(username=username, email=trainer.email)
    user.set_password(temp_password)
    user.is_active = True
    user.save()

    # ensure Trainer group exists and add basic permissions if available
    group, created = Group.objects.get_or_create(name='Trainer')
    perms_to_add = []
    try:
        ct_tr = ContentType.objects.get_for_model(Trainer)
        for codename in ['view_trainer']:
            try:
                perms_to_add.append(Permission.objects.get(codename=codename, content_type=ct_tr))
            except Permission.DoesNotExist:
                pass
    except Exception:
        pass
    if perms_to_add:
        group.permissions.add(*perms_to_add)

    user.groups.add(group)
    trainer.user = user
    trainer.status = 'Active'
    trainer.save()

    print(f'Created user {user.username} with temporary password: {temp_password}')

if __name__ == '__main__':
    main(email)
