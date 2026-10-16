"""
Namuna API'lar — bular CRUD emas, "biznes API"lar:
bir nechta modelga tegadigan, yoki umuman modelga bog'liq bo'lmagan.
"""

from rest_framework import viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.rbac.decorators import rbac


class StudentPaymentCreateView(APIView):
    """O'quvchidan to'lov qabul qilish"""

    def post(self, request):
        # Haqiqatda: Student.balance, GroupPayment, Transaction, Income ... bir nechta jadval
        return Response({"ok": True}, status=201)


class FinanceStatisticsView(APIView):
    """Moliya statistikasi (modelga bog'liq emas, agregat)"""

    def get(self, request):
        return Response({"income": 100, "expense": 40})


class EmployeeSalaryView(APIView):
    """Xodim maoshi: ko'rish va to'lash alohida ruxsat"""

    rbac_per_method = True

    def get(self, request, pk):
        return Response({"employee": pk, "salary": 1000})

    def post(self, request, pk):
        return Response({"employee": pk, "paid": True})


class LeadViewSet(viewsets.ViewSet):
    """Lidlar"""

    def list(self, request):
        return Response([])

    def create(self, request):
        return Response({}, status=201)

    @action(detail=True, methods=["post"])
    def convert(self, request, pk=None):
        """Lidni o'quvchiga aylantirish"""
        return Response({"converted": pk})


@rbac(key="reports.debtors", name="Qarzdorlar hisoboti", group="report")
@api_view(["GET"])
def debtors_report(request):
    return Response([])


class HealthView(APIView):
    rbac_public = True
    permission_classes = []

    def get(self, request):
        return Response({"status": "ok"})


class BillingGatewayProxyView(APIView):
    """
    Django ichidagi proxy: /gw/<path> -> billing-service.
    Kalit ``ApiEndpoint(kind=gateway, path=<regex>)`` yozuvlaridan topiladi.
    """

    rbac_gateway = True

    def dispatch_proxy(self, request, path):
        # Haqiqatda: requests/httpx bilan upstream'ga yuborish
        return Response({"proxied": path, "method": request.method, "rbac_key": request._request.rbac_key})

    def get(self, request, path):
        return self.dispatch_proxy(request, path)

    def post(self, request, path):
        return self.dispatch_proxy(request, path)
