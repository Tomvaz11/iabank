from django.urls import path

from .views import SeedProfileValidateView, TenantSuccessMetricsView, TenantThemeView

urlpatterns = [
    path('tenants/<slug:tenant_slug>/themes/current', TenantThemeView.as_view(), name='tenant-theme-current'),
    path('tenant-metrics/<slug:tenant_slug>/sc', TenantSuccessMetricsView.as_view(), name='tenant-success-metrics'),
    path('seed-profiles/validate', SeedProfileValidateView.as_view(), name='seed-profile-validate'),
]
