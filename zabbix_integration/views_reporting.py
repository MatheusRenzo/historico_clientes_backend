from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .services.reporting import build_monthly_sla_report


class ZabbixMonthlyReportView(APIView):
    """
    GET /api/zabbix/report/monthly/?cliente=1&year=2026&month=1
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cliente = request.query_params.get("cliente")
        year = request.query_params.get("year")
        month = request.query_params.get("month")

        if not cliente or not year or not month:
            return Response(
                {"detail": "Informe cliente, year e month. Ex: ?cliente=1&year=2026&month=1"},
                status=400,
            )

        data = build_monthly_sla_report(int(cliente), int(year), int(month))
        return Response(data)
