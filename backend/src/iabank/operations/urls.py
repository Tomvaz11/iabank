"""
URLs for operations app - Loan and installment management.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# ViewSets will be registered here after implementation
# router.register(r'loans', views.LoanViewSet)
# router.register(r'installments', views.InstallmentViewSet)

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),

    # Custom endpoints (will be implemented later)
    # path('<uuid:loan_id>/installments/', views.LoanInstallmentsView.as_view(), name='loan_installments'),
    # path('installments/<uuid:installment_id>/payments/', views.InstallmentPaymentsView.as_view(), name='installment_payments'),
]