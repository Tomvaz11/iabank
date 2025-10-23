from __future__ import annotations

from django.urls import path

from .views import RegisterFeatureScaffoldView

app_name = 'foundation'

urlpatterns = [
    path(
        'tenants/<uuid:tenant_id>/features/scaffold',
        RegisterFeatureScaffoldView.as_view(),
        name='register-feature-scaffold',
    ),
]
