from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import JiraConnection, JiraIssue
from .serializers import JiraConnectionSerializer, JiraIssueSerializer


class JiraConnectionViewSet(ModelViewSet):
    queryset = JiraConnection.objects.select_related("cliente").all()
    serializer_class = JiraConnectionSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {"cliente": ["exact"], "ativo": ["exact"]}
    search_fields = ["cliente__nome", "base_url", "email"]
    ordering_fields = ["criado_em", "atualizado_em"]
    ordering = ["-atualizado_em"]


class JiraIssueViewSet(ModelViewSet):
    queryset = JiraIssue.objects.select_related("cliente", "contrato", "tarefa_local").all()
    serializer_class = JiraIssueSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        # ✅ filtros principais
        "cliente": ["exact"],                 # ?cliente=1
        "contrato": ["exact", "isnull"],      # ?contrato=10
        "status": ["exact"],                  # ?status=Done
        "project_key": ["exact"],             # ?project_key=ENG
        "issue_type": ["exact"],              # ?issue_type=Task
        "priority": ["exact"],                # ?priority=High
        "assignee_account_id": ["exact", "isnull"],
        "due_date": ["exact", "gte", "lte"],

        # por datas do Jira
        "jira_updated_at": ["date", "date__gte", "date__lte"],
        "jira_created_at": ["date", "date__gte", "date__lte"],
    }

    search_fields = ["key", "summary", "description", "assignee_display_name", "reporter_display_name"]
    ordering_fields = ["jira_updated_at", "jira_created_at", "due_date", "time_spent_seconds", "original_estimate_seconds", "criado_em"]
    ordering = ["-jira_updated_at", "-criado_em"]
