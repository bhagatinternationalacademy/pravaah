from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

# Importing Trainer inside function to avoid circular import at module import time

def trainer_required(view_func):
    """Decorator that allows only trainer users (linked Trainer or email match).
    Redirects non-trainers to dashboard with a message.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect('accounts:login')
        has_profile = False
        try:
            # safe attribute access
            if hasattr(user, 'trainer_profile') and user.trainer_profile:
                has_profile = True
        except Exception:
            has_profile = False
        if not has_profile:
            from pravaah.trainers.models import Trainer
            if user.email and Trainer.objects.filter(email__iexact=user.email).exists():
                has_profile = True
        if not has_profile:
            messages.error(request, 'Access restricted to trainers only.')
            return redirect('dashboard:home')
        return view_func(request, *args, **kwargs)
    return _wrapped

