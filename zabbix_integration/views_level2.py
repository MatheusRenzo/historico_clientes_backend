from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from zabbix_integration.services.sync_level2 import sync_items, sync_events, sync_history


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

class ZabbixSyncItemsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data

        cliente = data.get("cliente")
        host = data.get("host")

        if not cliente:
            return Response(
                {"detail": "Campo 'cliente' é obrigatório"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not host:
            return Response(
                {"detail": "Campo 'host' é obrigatório"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            cliente = int(cliente)
        except ValueError:
            return Response(
                {"detail": "Campo 'cliente' deve ser inteiro"},
                status=status.HTTP_400_BAD_REQUEST
            )

        filtros = {
            "name": data.get("name"),
            "key_": data.get("key_"),
            "status": data.get("status"),
        }

        summary = sync_items(
            cliente_id=cliente,
            host=host,
            filtros=filtros
        )

        return Response(summary)


class ZabbixSyncEventsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cliente = int(request.data.get("cliente"))
        since_hours = int(request.data.get("since_hours", 240))
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
