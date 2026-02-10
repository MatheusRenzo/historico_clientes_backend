from rest_framework import serializers
from .models import ZabbixConnection

class ZabbixConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZabbixConnection
        fields = "__all__"
        extra_kwargs = {"senha": {"write_only": True}}
