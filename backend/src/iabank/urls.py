"""
URL Configuration for IABANK project.

Configuração principal de roteamento da API REST, incluindo endpoints
de administração, saúde e APIs de cada módulo de negócio.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# API v1 patterns
api_v1_patterns = [
    path('auth/', include('iabank.users.urls')),
    path('customers/', include('iabank.customers.urls')),
    path('operations/', include('iabank.operations.urls')),
    path('finance/', include('iabank.finance.urls')),
]

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/v1/', include(api_v1_patterns)),
    
    # Health check endpoint
    path('health/', include('iabank.core.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)