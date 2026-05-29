from django.contrib.auth import logout as auth_logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy

from training_management.access import dashboard_route


class RoleLoginView(LoginView):
    template_name = "accounts/login.html"

    def get_success_url(self):
        return reverse_lazy(dashboard_route(self.request.user))


def logout_view(request):
    auth_logout(request)
    return redirect("landing")
