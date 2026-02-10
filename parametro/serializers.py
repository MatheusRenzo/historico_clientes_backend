from rest_framework import serializers
from .models import Parametro, ParametroCliente, ItensMonitoramento, ContextoCliente

class ParametroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parametro
        fields = "__all__"


class ParametroClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParametroCliente
        fields = "__all__"


class ItensMonitoramentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItensMonitoramento
        fields = "__all__"

class ContextoClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContextoCliente
        fields = "__all__"
