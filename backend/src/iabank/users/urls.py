"""URLs para autenticação e gestão de usuários."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AuthViewSet, UserViewSet

router = DefaultRouter(trailing_slash="/?")
router.register("users", UserViewSet, basename="users")

auth_login = AuthViewSet.as_view({"post": "login"})
auth_refresh = AuthViewSet.as_view({"post": "refresh"})

urlpatterns = [
    path("", include(router.urls)),
    path("auth/login", auth_login, name="auth-login"),
    path("auth/login/", auth_login),
    path("auth/refresh", auth_refresh, name="auth-refresh"),
    path("auth/refresh/", auth_refresh),
]
