from rest_framework import serializers
from .models import JiraConnection, JiraIssue

class JiraConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JiraConnection
        fields = "__all__"
        extra_kwargs = {
            "api_token": {"write_only": True},  # não retorna token ao listar
        }

class JiraIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = JiraIssue
        fields = "__all__"
