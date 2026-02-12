from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from zabbix_integration.services.sla_ai import analyze_zabbix_sla

class ZabbixSlaAnalyzeView(APIView):
    """
    POST /api/zabbix/sla/analyze/
    Body:
    {
      "cliente": 1,
      "prompt": "Quais SLAs estão fora do SLO?"
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cliente = request.data.get("cliente")
        prompt = request.data.get("prompt")

        if not cliente or not prompt:
            return Response({"detail": "Informe 'cliente' e 'prompt'."}, status=400)

        try:
            result = analyze_zabbix_sla(int(cliente), str(prompt))
            return Response(result, status=200)
        except Exception as e:
            return Response({"detail": str(e)}, status=400)
