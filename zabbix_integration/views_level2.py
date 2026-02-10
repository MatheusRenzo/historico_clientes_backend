from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from zabbix_integration.services.sync_level2 import sync_items, sync_events, sync_history


class ZabbixSyncItemsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cliente = int(request.data.get("cliente"))
        key_contains = request.data.get("key_contains")  # opcional
        sync_items(cliente_id=cliente, key_contains=key_contains)
        return Response({"status": "ok"})


class ZabbixSyncEventsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cliente = int(request.data.get("cliente"))
        since_hours = int(request.data.get("since_hours", 24))
        sync_events(cliente_id=cliente, since_hours=since_hours)
        return Response({"status": "ok"})


class ZabbixSyncHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cliente = int(request.data.get("cliente"))
        itemids = request.data.get("itemids") or []
        hours = int(request.data.get("hours", 6))

        time_till = datetime.utcnow()
        time_from = time_till - timedelta(hours=hours)

        sync_history(cliente_id=cliente, itemids=itemids, time_from=time_from, time_till=time_till)
        return Response({"status": "ok"})
