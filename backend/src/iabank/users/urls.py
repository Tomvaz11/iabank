"""
URLs for users app - Authentication and user management.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
# ViewSets will be registered here after implementation

urlpatterns = [
    # Include router URLs
    path("", include(router.urls)),
    # Authentication endpoints (will be implemented later)
    # path('login/', views.LoginView.as_view(), name='login'),
    # path('logout/', views.LogoutView.as_view(), name='logout'),
    # path('refresh/', views.TokenRefreshView.as_view(), name='token_refresh'),
    # path('register/', views.RegisterView.as_view(), name='register'),
]
