from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from zabbix_integration.services.sync_level3 import sync_templates, sync_users, sync_sla


class ZabbixSyncTemplatesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cliente = request.data.get("cliente")
        if not cliente:
            return Response({"detail": "cliente é obrigatório"}, status=400)

        sync_templates(int(cliente))
        return Response({"status": "ok"})


class ZabbixSyncUsersView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cliente = request.data.get("cliente")
        if not cliente:
            return Response({"detail": "cliente é obrigatório"}, status=400)

        sync_users(int(cliente))
        return Response({"status": "ok"})


class ZabbixSyncSLAView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cliente = request.data.get("cliente")
        if not cliente:
            return Response({"detail": "cliente é obrigatório"}, status=400)

        sync_sla(int(cliente))
        return Response({"status": "ok"})
