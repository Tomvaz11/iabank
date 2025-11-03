from __future__ import annotations

from django.urls import path

from .views import (
    DesignSystemStoryViewSet,
    RegisterFeatureScaffoldView,
    TenantSuccessMetricListView,
    TenantThemeView,
)

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
    path(
        'tenant-metrics/<uuid:tenant_id>/sc',
        TenantSuccessMetricListView.as_view(),
        name='list-tenant-success-metrics',
    ),
    path(
        'design-system/stories',
        DesignSystemStoryViewSet.as_view({'get': 'list'}),
        name='list-design-system-stories',
    ),
]
