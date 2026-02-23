# zabbix_integration/views_hosts.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ZabbixHost
from .serializers import ZabbixHostSerializer
from .servico import sync_hosts

class ZabbixHostsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cliente_id = request.query_params.get("cliente")
        if not cliente_id:
            return Response({"detail": "Informe ?cliente=ID"}, status=400)

        qs = ZabbixHost.objects.filter(cliente_id=int(cliente_id)).order_by("name")
        return Response(ZabbixHostSerializer(qs, many=True).data)

class ZabbixSyncHostsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cliente_id = request.query_params.get("cliente")
        if not cliente_id:
            return Response({"detail": "Informe ?cliente=ID"}, status=400)

        summary = sync_hosts(int(cliente_id))
        return Response({"detail": "Hosts sincronizados", **summary})