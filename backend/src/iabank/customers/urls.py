"""
URLs for customers app - Customer management.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
# ViewSets will be registered here after implementation
# router.register(r'customers', views.CustomerViewSet)
# router.register(r'addresses', views.AddressViewSet)

urlpatterns = [
    # Include router URLs
    path("", include(router.urls)),
    # Custom endpoints (will be implemented later)
    # path('<uuid:customer_id>/credit-analysis/', views.CreditAnalysisView.as_view(), name='credit_analysis'),
]
