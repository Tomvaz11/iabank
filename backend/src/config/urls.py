"""
URL configuration for IABANK project.
Multi-tenant SaaS platform for loan management.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path

from iabank.core.health import health_check

api_v1_urlpatterns = [
    # Users module (autenticação + gestão de usuários)
    re_path(r"^api/v1/?", include("iabank.users.urls")),
    # Core endpoints (MFA, helpers de teste)
    re_path(r"^api/v1/?", include("iabank.core.urls")),
    # Customers endpoints com prefixo dedicado
    re_path(r"^api/v1/customers/?", include("iabank.customers.urls")),
    # Operations module (empréstimos, parcelas, pagamentos)
    re_path(r"^api/v1/?", include("iabank.operations.urls")),
    # Finance module (contas, transações, relatórios)
    re_path(r"^api/v1/?", include("iabank.finance.urls")),
]

urlpatterns = [
    # Admin interface
    path("admin/", admin.site.urls),
    # Health check
    path("health/", health_check, name="health_check"),
    # API versionada v1
    *api_v1_urlpatterns,
    # Prometheus metrics
    path("", include("django_prometheus.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
