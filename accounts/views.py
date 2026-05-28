from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.conf import settings


def login_view(request):
    next_url = request.POST.get('next') or request.GET.get('next', '')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # ensure UserProfile exists for this user (handles users created before profile model)
            try:
                from .models import UserProfile
                UserProfile.objects.get_or_create(user=user)
            except Exception:
                pass
            # If 'remember' not checked, expire session on browser close
            if not remember:
                request.session.set_expiry(0)
            # Safe redirect
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect(settings.LOGIN_REDIRECT_URL or 'dashboard:home')
        messages.error(request, 'Invalid username or password')
    return render(request, 'accounts/login.html', {'next': next_url})


def logout_view(request):
    logout(request)
    return redirect('accounts:login')
