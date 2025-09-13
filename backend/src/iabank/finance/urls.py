"""
URLs for finance app - Financial management and reporting.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
# ViewSets will be registered here after implementation
# router.register(r'accounts', views.BankAccountViewSet)
# router.register(r'transactions', views.FinancialTransactionViewSet)
# router.register(r'categories', views.PaymentCategoryViewSet)
# router.register(r'cost-centers', views.CostCenterViewSet)
# router.register(r'suppliers', views.SupplierViewSet)

urlpatterns = [
    # Include router URLs
    path("", include(router.urls)),
    # Reports endpoints (will be implemented later)
    # path('reports/dashboard/', views.DashboardReportView.as_view(), name='dashboard_report'),
    # path('reports/cash-flow/', views.CashFlowReportView.as_view(), name='cash_flow_report'),
    # path('reports/loans/', views.LoansReportView.as_view(), name='loans_report'),
]
