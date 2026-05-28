from django.shortcuts import redirect
from django.urls import reverse


class MustChangePasswordMiddleware:
    """Redirects authenticated users with must_change_password=True to the password change page."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip for anonymous users or staff accessing admin
        if request.user.is_authenticated:
            try:
                profile = request.user.userprofile
            except Exception:
                profile = None
            if profile and profile.must_change_password:
                path = request.path
                allowed = [
                    reverse('accounts:password_change'),
                    reverse('accounts:password_change_done'),
                    reverse('accounts:logout'),
                    '/admin/',
                ]
                # allow static and media
                if any(path.startswith(a) for a in allowed) or path.startswith('/static/') or path.startswith('/media/'):
                    return self.get_response(request)
                return redirect('accounts:password_change')
        return self.get_response(request)
