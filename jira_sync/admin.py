from django.contrib import admin
from .models import JiraConnection, JiraIssue, JiraProject


@admin.register(JiraConnection)
class JiraConnectionAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "base_url", "email", "ativo", "atualizado_em")
    list_filter = ("ativo",)
    search_fields = ("cliente__nome", "base_url", "email")
    autocomplete_fields = ("cliente",)
    ordering = ("-atualizado_em",)

    # segurança básica: não mostrar token em lista
    readonly_fields = ("criado_em", "atualizado_em")

    fieldsets = (
        ("Cliente", {"fields": ("cliente", "ativo")}),
        ("Conexão Jira", {"fields": ("base_url", "cloud_id", "email", "api_token")}),
        ("Auditoria", {"fields": ("criado_em", "atualizado_em")}),
    )

@admin.register(JiraProject)
class JiraProjectAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "jira_connection",
        "key",
        "name",
        "project_type",
        "archived",
        "criado_em",
    )
    list_filter = ("project_type", "archived")
    search_fields = ("key", "name")
    ordering = ("key",)

    autocomplete_fields = ("jira_connection",)

    readonly_fields = ("criado_em", "atualizado_em")

    fieldsets = (
        ("Conexão", {"fields": ("jira_connection",)}),
        ("Projeto Jira", {"fields": ("jira_id", "key", "name", "project_type")}),
        ("Status", {"fields": ("archived", "is_private")}),
        ("Responsável", {"fields": ("lead_account_id", "lead_display_name")}),
        ("Extras", {"fields": ("url", "raw")}),
        ("Auditoria", {"fields": ("criado_em", "atualizado_em")}),
    )



@admin.register(JiraIssue)
class JiraIssueAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "cliente",
        "contrato",
        "key",
        "project_key",
        "issue_type",
        "status",
        "priority",
        "assignee_display_name",
        "jira_updated_at",
    )
    list_filter = (
        "cliente",
        "project_key",
        "issue_type",
        "status",
        "priority",
    )
    search_fields = (
        "key",
        "summary",
        "description",
        "cliente__nome",
        "contrato__titulo",
        "assignee_display_name",
        "reporter_display_name",
    )
    ordering = ("-jira_updated_at", "-criado_em")

    autocomplete_fields = ("cliente", "contrato", "tarefa_local")

    # Campos que você geralmente não quer editar manualmente
    readonly_fields = (
        "jira_id",
        "criado_em",
        "atualizado_em",
        "jira_created_at",
        "jira_updated_at",
        "jira_resolved_at",
    )

    # "raw" pode ser grande; mas manter visível ajuda em debug
    fieldsets = (
        ("Vínculo", {"fields": ("cliente", "contrato", "tarefa_local")}),
        ("Identificação Jira", {"fields": ("jira_id", "key", "project_key", "issue_type")}),
        ("Conteúdo", {"fields": ("summary", "description", "labels", "components")}),
        ("Status", {"fields": ("status", "priority", "due_date")}),
        ("Pessoas", {"fields": ("assignee_account_id", "assignee_display_name", "reporter_account_id", "reporter_display_name")}),
        ("Tempo", {"fields": ("original_estimate_seconds", "time_spent_seconds")}),
        ("Datas Jira", {"fields": ("jira_created_at", "jira_updated_at", "jira_resolved_at")}),
        ("Payload bruto", {"fields": ("raw",)}),
        ("Auditoria", {"fields": ("criado_em", "atualizado_em")}),
    )
