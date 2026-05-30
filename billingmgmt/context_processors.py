"""
Context processor for the Billing Management module.

Provides global template context variables — most importantly the
``unread_count`` used by the sidebar and topbar notification badges.
"""

from .models import Notification


def unread_notifications(request):
    """
    Inject ``unread_count`` into every template context.

    Returns:
        dict: Contains ``unread_count`` (int) for authenticated users,
        or ``0`` for anonymous visitors.
    """
    if request.user.is_authenticated:
        count = Notification.objects.filter(
            user=request.user,
            is_read=False,
        ).count()
        return {'unread_count': count}
    return {'unread_count': 0}
