from rest_framework import serializers
from .models import ZabbixConnection
from rest_framework import serializers
from .models import ZabbixHost, ZabbixTrigger, ZabbixEvent

class ZabbixConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZabbixConnection
        fields = "__all__"
        extra_kwargs = {"senha": {"write_only": True}}

class ZabbixHostSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZabbixHost
        fields = ["id", "cliente_id", "hostid", "host", "name", "status", "ip", "dns", "port", "atualizado_em"]

class ZabbixTriggerSerializer(serializers.ModelSerializer):
    # se você tiver M2M hosts:
    hosts = serializers.SerializerMethodField()

    class Meta:
        model = ZabbixTrigger
        fields = ["id", "cliente_id", "triggerid", "descricao", "prioridade", "status", "ultima_alteracao", "hosts"]

    def get_hosts(self, obj):
        if hasattr(obj, "hosts"):
            return [{"hostid": h.hostid, "host": getattr(h, "host", None), "name": getattr(h, "name", None)} for h in obj.hosts.all()]
        return []

class ZabbixEventSerializer(serializers.ModelSerializer):
    host = serializers.SerializerMethodField()
    trigger = serializers.SerializerMethodField()

    class Meta:
        model = ZabbixEvent
        fields = [
            "id", "cliente_id", "eventid", "name", "severity", "value", "acknowledged", "clock",
            "host", "trigger",
        ]

    def get_host(self, obj):
        if obj.host_id and obj.host:
            return {"hostid": obj.host.hostid, "host": getattr(obj.host, "host", None), "name": getattr(obj.host, "name", None)}
        return None

    def get_trigger(self, obj):
        if obj.trigger_id and obj.trigger:
            return {"triggerid": obj.trigger.triggerid, "descricao": obj.trigger.descricao, "prioridade": obj.trigger.prioridade}
        return None
