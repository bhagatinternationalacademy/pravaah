

def role_flags(request):
    """Adds is_admin and is_trainer flags to template context safely."""
    is_admin = False
    is_trainer = False
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        is_admin = user.is_staff
        try:
            if hasattr(user, 'trainer_profile') and user.trainer_profile:
                is_trainer = True
        except Exception:
            is_trainer = False
        if not is_trainer and getattr(user, 'email', None):
            # import here to avoid startup import issues
            from pravaah.trainers.models import Trainer
            is_trainer = Trainer.objects.filter(email__iexact=user.email).exists()
    return {'is_admin': is_admin, 'is_trainer': is_trainer}

