from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Parametro, ParametroCliente, ItensMonitoramento, ContextoCliente
from .serializers import (
    ParametroSerializer,
    ParametroClienteSerializer,
    ItensMonitoramentoSerializer,
    ContextoClienteSerializer
)

class ParametroViewSet(ModelViewSet):
    queryset = Parametro.objects.all().order_by("-criado_em")
    serializer_class = ParametroSerializer
    permission_classes = [IsAuthenticated]


class ParametroClienteViewSet(ModelViewSet):
    queryset = ParametroCliente.objects.select_related("cliente").all().order_by("-criado_em")
    serializer_class = ParametroClienteSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["cliente"]  # ✅ ?cliente=1


class ItensMonitoramentoViewSet(ModelViewSet):
    queryset = ItensMonitoramento.objects.select_related("cliente").all().order_by("-criado_em")
    serializer_class = ItensMonitoramentoSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["cliente", "tipo"]  # ✅ ?cliente=1&tipo=Grafico

class ContextoClienteViewSet(ModelViewSet):
    queryset = ContextoCliente.objects.all().order_by("-id")
    serializer_class = ContextoClienteSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    # ✅ ajuste aqui com os campos reais do seu model
    # exemplos comuns:
    filterset_fields = {
        "cliente": ["exact"],   # ?cliente=1
        # "tipo": ["exact"],    # se existir como Field
        # "monitoramento": ["exact"], # se existir como Field
    }

    # 🔍 busca textual (ajuste conforme existir)
    search_fields = [
        # "descricao",
    ]

    ordering_fields = ["id"]
    ordering = ["-id"]