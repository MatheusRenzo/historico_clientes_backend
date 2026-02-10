from rest_framework import serializers
from .models import RagDocument

class RagDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RagDocument
        fields = "__all__"
