"""
URLs para app de operações - gestão de empréstimos e parcelas.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import InstallmentViewSet, LoanViewSet

router = DefaultRouter()
router.register(r"loans", LoanViewSet, basename="loan")
router.register(r"installments", InstallmentViewSet, basename="installment")

urlpatterns = [
    path("", include(router.urls)),
]
