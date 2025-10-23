from django.urls import include, path

urlpatterns = [
    path('', include('django_prometheus.urls')),
    path('api/v1/', include('backend.apps.tenancy.urls')),
    path('api/v1/', include('backend.apps.foundation.api.urls')),
]
