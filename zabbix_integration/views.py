from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import ZabbixConnection
from .serializers import ZabbixConnectionSerializer
from .services.sync import get_client_for_cliente
from .services.sync_level1 import sync_level1


class ZabbixConnectionViewSet(ModelViewSet):
    queryset = ZabbixConnection.objects.select_related("cliente").all().order_by("-atualizado_em")
    serializer_class = ZabbixConnectionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {"cliente": ["exact"], "ativo": ["exact"]}


class ZabbixHostsView(APIView):
    """
    GET /api/zabbix/hosts/?cliente=1
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cliente_id = request.query_params.get("cliente")
        if not cliente_id:
            return Response({"detail": "Informe ?cliente=ID"}, status=400)

        client = get_client_for_cliente(int(cliente_id))

        result = client.host_get(
            output=["hostid", "host", "name", "status"],
            selectInterfaces=["ip", "dns", "port"],
        )
        return Response(result)


class ZabbixProblemsView(APIView):
    """
    GET /api/zabbix/problems/?cliente=1
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cliente_id = request.query_params.get("cliente")
        if not cliente_id:
            return Response({"detail": "Informe ?cliente=ID"}, status=400)

        client = get_client_for_cliente(int(cliente_id))

        result = client.problem_get(
            output="extend",
            sortfield=["eventid"],
            sortorder="DESC",
            recent=True,
        )
        return Response(result)

class ZabbixSyncLevel1View(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cliente_id = request.data.get("cliente")

        if not cliente_id:
            return Response({"detail": "cliente é obrigatório"}, status=400)

        sync_level1(int(cliente_id))
        return Response({"status": "ok"})
