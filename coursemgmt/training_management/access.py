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

    def post(self, request, *args, **kwargs):
        """Log raw POST and FILES for debugging before handling the request."""
        try:
            post_keys = list(request.POST.keys())
        except Exception:
            post_keys = None
        try:
            file_keys = list(request.FILES.keys())
        except Exception:
            file_keys = None
        logger.debug(
            "POST in %s: user=%s, path=%s, POST_keys=%s, FILES_keys=%s",
            self.__class__.__name__,
            getattr(request, "user", None),
            request.path,
            post_keys,
            file_keys,
        )
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        """Log detailed debug info, attempt to save and surface errors if saving fails.

        This ensures form.save() is called and any exceptions are logged and shown to the user
        instead of failing silently.
        """
        # Basic request/debug context
        try:
            post_keys = list(self.request.POST.keys())
        except Exception:
            post_keys = None
        try:
            file_keys = list(self.request.FILES.keys())
        except Exception:
            file_keys = None

        logger.debug(
            "Form valid in %s: user=%s, POST_keys=%s, FILES_keys=%s",
            self.__class__.__name__,
            getattr(self.request, "user", None),
            post_keys,
            file_keys,
        )

        # form is already valid at this point; attempt to save via the normal flow and catch exceptions
        try:
            response = super().form_valid(form)
        except Exception as exc:
            # Log exception with traceback and attach message to user
            logger.exception("Exception while saving form in %s: %s", self.__class__.__name__, exc)
            messages.error(self.request, f"An unexpected error occurred while saving: {exc}")
            # Re-render form with errors (if any) so user sees what went wrong
            return self.form_invalid(form)

        # After successful save, log the saved object id if available
        obj = getattr(self, "object", None)
        try:
            obj_info = f"{obj.__class__.__name__}(pk={getattr(obj, 'pk', None)})" if obj else "<no-object>"
        except Exception:
            obj_info = "<object-info-error>"
        logger.info("Form saved successfully in %s: %s", self.__class__.__name__, obj_info)
        return response
