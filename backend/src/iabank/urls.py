"""
Configuração de URLs do projeto IABANK.
Este módulo define os padrões de URL principais da aplicação.
"""

from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]