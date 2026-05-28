from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def create_trainer_group(sender, **kwargs):
    """Ensure 'Trainer' group exists and has basic view/change permissions after migrations."""
    try:
        group, created = Group.objects.get_or_create(name='Trainer')
        perms = []

        model_perms_map = {
            'trainers': [('Trainer', ['view_trainer', 'change_trainer'])],
            'skills': [('Skill', ['view_skill'])],
            'certifications': [('Certification', ['view_certification'])],
        }

        for app_label, models_info in model_perms_map.items():
            for model_name, codenames in models_info:
                try:
                    model = apps.get_model(app_label, model_name)
                    if not model:
                        continue
                    ct = ContentType.objects.get_for_model(model)
                    for codename in codenames:
                        try:
                            perm = Permission.objects.get(codename=codename, content_type=ct)
                            perms.append(perm)
                        except Permission.DoesNotExist:
                            # skip missing perms
                            continue
                except LookupError:
                    continue

        if perms:
            group.permissions.add(*perms)
    except Exception as e:
        # avoid breaking migrations; print for debugging
        print('accounts.signals.create_trainer_group error:', e)
