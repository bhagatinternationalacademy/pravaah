from functools import wraps
import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages

logger = logging.getLogger(__name__)


def user_roles(user):
    if not user.is_authenticated:
        return set()
    return set(user.user_roles.select_related("role").values_list("role__role_name", flat=True))


def has_role(user, *roles):
    return bool(user.is_authenticated and user_roles(user).intersection(roles))


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if roles and not has_role(request.user, *roles):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def dashboard_route(user):
    role_map = {
        "Admin": "dashboard:index",
        "Trainer": "trainers:dashboard",
        "Student": "students:dashboard",
    }
    for role_name, route in role_map.items():
        if role_name in user_roles(user):
            return route
    return "dashboard:index"


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    roles = ()

    def test_func(self):
        return has_role(self.request.user, *self.roles)


class CrudFormMixin:
    title = ""
    button_text = "Save"
    back_url = None
    enctype = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("title", self.title)
        context.setdefault("button_text", self.button_text)
        context.setdefault("back_url", self.back_url)
        context.setdefault("enctype", self.enctype)
        return context

    def form_invalid(self, form):
        """Log form errors and show a generic error message to the user."""
        try:
            err_json = form.errors.as_json()
        except Exception:
            err_json = str(form.errors)
        logger.error("Form invalid in %s: %s", self.__class__.__name__, err_json)
        messages.error(self.request, "There were errors with your submission. See the form for details.")
        return super().form_invalid(form)
