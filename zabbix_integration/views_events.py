# zabbix_integration/views_events.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ZabbixEvent
from .serializers import ZabbixEventSerializer
from .servico import sync_events

class ZabbixEventsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cliente_id = request.query_params.get("cliente")
        if not cliente_id:
            return Response({"detail": "Informe ?cliente=ID"}, status=400)

        limit = int(request.query_params.get("limit") or 200)
        qs = (
            ZabbixEvent.objects
            .filter(cliente_id=int(cliente_id))
            .order_by("-clock")[:limit]
        )
        return Response(ZabbixEventSerializer(qs, many=True).data)

class ZabbixSyncEventsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cliente_id = request.query_params.get("cliente")
        if not cliente_id:
            return Response({"detail": "Informe ?cliente=ID"}, status=400)

        since_hours = int(request.query_params.get("since_hours") or 24)
        summary = sync_events(int(cliente_id), since_hours=since_hours)
        return Response({"detail": "Eventos sincronizados", **summary})