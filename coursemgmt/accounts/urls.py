from django.urls import path

from .views import RoleLoginView, logout_view

urlpatterns = [
    path("login/", RoleLoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
]
