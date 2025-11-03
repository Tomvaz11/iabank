from django.urls import path

from .views import TenantSuccessMetricsView, TenantThemeView

urlpatterns = [
    path('tenants/<slug:tenant_slug>/themes/current', TenantThemeView.as_view(), name='tenant-theme-current'),
    path('tenant-metrics/<slug:tenant_slug>/sc', TenantSuccessMetricsView.as_view(), name='tenant-success-metrics'),
]
