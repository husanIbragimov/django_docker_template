"""Test URLconf: namuna API'lar (django-api-rbac/demo dan) + apps.rbac.urls."""

from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import demo_views as views

router = SimpleRouter()
router.register("leads", views.LeadViewSet, basename="lead")

finance_patterns = (
    [
        path("student-payment/", views.StudentPaymentCreateView.as_view(), name="student-payment-create"),
        path("statistics/", views.FinanceStatisticsView.as_view(), name="statistics"),
        path("employee/<int:pk>/salary/", views.EmployeeSalaryView.as_view(), name="employee-salary"),
    ],
    "finance",
)

urlpatterns = [
    path("api/rbac/", include("apps.rbac.urls")),
    path("api/finance/", include(finance_patterns)),
    path("api/crm/", include((router.urls, "crm"))),
    path("api/reports/debtors/", views.debtors_report, name="debtors"),
    path("api/health/", views.HealthView.as_view(), name="health"),
    path("gw/<path:path>", views.BillingGatewayProxyView.as_view(), name="gateway"),
]
