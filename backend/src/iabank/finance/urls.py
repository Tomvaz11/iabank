"""URLs para o módulo financeiro."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"bank-accounts", views.BankAccountViewSet, basename="finance-bank-account")
router.register(r"payment-categories", views.PaymentCategoryViewSet, basename="finance-payment-category")
router.register(r"cost-centers", views.CostCenterViewSet, basename="finance-cost-center")
router.register(r"suppliers", views.SupplierViewSet, basename="finance-supplier")
router.register(r"financial-transactions", views.FinancialTransactionViewSet, basename="finance-transaction")

urlpatterns = [
    path("", include(router.urls)),
    path("reports/dashboard", views.DashboardReportView.as_view(), name="finance-dashboard-report"),
    path("reports/cash-flow", views.CashFlowReportView.as_view(), name="finance-cash-flow-report"),
]
