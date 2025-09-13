"""
URL configuration for IABANK project.
Multi-tenant SaaS platform for loan management.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_check(request):
    """Health check endpoint for load balancers."""
    return JsonResponse({"status": "healthy", "version": "1.0.0"})


urlpatterns = [
    # Admin interface
    path("admin/", admin.site.urls),
    # Health check
    path("health/", health_check, name="health_check"),
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
