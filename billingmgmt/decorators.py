"""
Custom view decorators for the Billing Management module.

Provides role-based access control decorators that restrict views to
users belonging to specific Django auth groups (Trainer, Accounts,
TrainerAdmin). Superusers bypass all group checks.
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden


def role_required(*group_names):
    """
    Decorator factory that restricts a view to users belonging to at
    least one of the specified Django auth groups.

    Superusers are always granted access regardless of group membership.

    Args:
        *group_names: One or more group name strings (e.g. 'Trainer',
                      'Accounts', 'TrainerAdmin').

    Returns:
        A decorator that wraps the view function with the access check.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='/accounts/login/')
        def _wrapped_view(request, *args, **kwargs):
            # Superusers bypass all group restrictions.
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            user_groups = set(
                request.user.groups.values_list('name', flat=True)
            )
            if user_groups.intersection(set(group_names)):
                return view_func(request, *args, **kwargs)

            return HttpResponseForbidden(
                '<h3 style="text-align:center;margin-top:50px;">'
                '⛔ Access Denied. You do not have permission to view this page.</h3>'
            )
        return _wrapped_view
    return decorator


def trainer_required(view_func):
    """Restrict access to users in the **Trainer** group."""
    return role_required('Trainer')(view_func)


def accounts_required(view_func):
    """Restrict access to users in the **Accounts** group."""
    return role_required('Accounts')(view_func)


def trainer_admin_required(view_func):
    """Restrict access to users in the **TrainerAdmin** group."""
    return role_required('TrainerAdmin')(view_func)
