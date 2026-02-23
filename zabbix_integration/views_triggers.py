# zabbix_integration/views_triggers.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ZabbixTrigger
from .serializers import ZabbixTriggerSerializer
from .servico import sync_triggers

class ZabbixTriggersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cliente_id = request.query_params.get("cliente")
        if not cliente_id:
            return Response({"detail": "Informe ?cliente=ID"}, status=400)

        qs = ZabbixTrigger.objects.filter(cliente_id=int(cliente_id)).order_by("-ultima_alteracao")
        return Response(ZabbixTriggerSerializer(qs, many=True).data)

class ZabbixSyncTriggersView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cliente_id = int(request.data.get("cliente"))
        hostids = request.data.get("hostids")  # opcional
        if not cliente_id:
            return Response({"detail": "Informe ?cliente=ID"}, status=400)

        summary = sync_triggers(int(cliente_id), hostids=hostids) or {}  # ✅ garante dict
        return Response({"detail": "Triggers sincronizadas", **summary})