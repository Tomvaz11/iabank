"""
URLs do app Core.

Define endpoints básicos como health check e outros endpoints
de infraestrutura não relacionados ao domínio de negócio.
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HealthCheckView.as_view(), name='health-check'),
]