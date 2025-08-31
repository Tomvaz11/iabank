"""
URLs do app Finance.

Define os endpoints da API REST para operações financeiras,
incluindo contas, categorias, fornecedores e transações.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'finance'

router = DefaultRouter()
router.register(r'bank-accounts', views.BankAccountViewSet, basename='bankaccount')
router.register(r'categories', views.PaymentCategoryViewSet, basename='paymentcategory')
router.register(r'cost-centers', views.CostCenterViewSet, basename='costcenter')
router.register(r'suppliers', views.SupplierViewSet, basename='supplier')
router.register(r'transactions', views.FinancialTransactionViewSet, basename='financialtransaction')

urlpatterns = [
    path('', include(router.urls)),
]