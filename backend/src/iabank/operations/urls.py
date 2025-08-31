"""
URLs do app Operations.

Define os endpoints da API REST para operações relacionadas
aos empréstimos, consultores e parcelas.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'operations'

router = DefaultRouter()
router.register(r'consultants', views.ConsultantViewSet, basename='consultant')
router.register(r'loans', views.LoanViewSet, basename='loan')
router.register(r'installments', views.InstallmentViewSet, basename='installment')

urlpatterns = [
    path('', include(router.urls)),
]