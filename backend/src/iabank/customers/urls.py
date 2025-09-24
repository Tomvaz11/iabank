"""
URLs for customers app - Customer management.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from iabank.customers.views import CustomerViewSet

router = DefaultRouter(trailing_slash="/?")
router.register(r"", CustomerViewSet, basename="customer")

urlpatterns = [
    # Include router URLs
    path("", include(router.urls)),
    # Custom endpoints (will be implemented later)
]
