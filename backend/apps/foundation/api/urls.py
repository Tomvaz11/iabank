from __future__ import annotations

from django.urls import path

from .views import RegisterFeatureScaffoldView, TenantThemeView

app_name = 'foundation'

urlpatterns = [
    path(
        'tenants/<uuid:tenant_id>/features/scaffold',
        RegisterFeatureScaffoldView.as_view(),
        name='register-feature-scaffold',
    ),
    path(
        'tenants/<uuid:tenant_id>/themes/current',
        TenantThemeView.as_view(),
        name='get-tenant-theme',
    ),
]
