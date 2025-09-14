"""
URL configuration for IABANK project.
Multi-tenant SaaS platform for loan management.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from iabank.core.health import health_check


urlpatterns = [
    # Admin interface
    path("admin/", admin.site.urls),
    # Health check
    path("health/", health_check, name="health_check"),
    # Core endpoints (JWT auth)
    path("api/v1/", include("iabank.core.urls")),
    # API v1 routes
    path("api/v1/auth/", include("iabank.users.urls")),
    path("api/v1/customers/", include("iabank.customers.urls")),
    path("api/v1/loans/", include("iabank.operations.urls")),
    path("api/v1/finance/", include("iabank.finance.urls")),
    # Prometheus metrics
    path("", include("django_prometheus.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
