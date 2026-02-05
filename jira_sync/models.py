from django.db import models


class JiraConnection(models.Model):
    """
    Configuração da conexão por cliente (ou por contrato).
    ⚠️ Ideal: NÃO salvar token puro em produção (use Vault/Secrets).
    """
    cliente = models.OneToOneField(
        "clientes.Cliente",
        on_delete=models.CASCADE,
        related_name="jira_connection",
    )

    base_url = models.URLField(help_text="Ex: https://suaempresa.atlassian.net")
    cloud_id = models.CharField(max_length=120, blank=True, null=True)
    email = models.EmailField()
    api_token = models.CharField(max_length=255)  # em produção: criptografar/secret manager

    ativo = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"JiraConnection({self.cliente.nome})"

class JiraProject(models.Model):
    """
    Projeto do Jira vinculado a uma JiraConnection
    """

    jira_connection = models.ForeignKey(
        "jira_sync.JiraConnection",
        on_delete=models.CASCADE,
        related_name="projects",
    )

    # Identificadores Jira
    jira_id = models.CharField(max_length=60)          # id interno do Jira
    key = models.CharField(max_length=20)              # ex: ENG
    name = models.CharField(max_length=255)

    project_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="software, service_desk, business"
    )

    is_private = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)

    # Extras úteis
    lead_account_id = models.CharField(max_length=120, blank=True, null=True)
    lead_display_name = models.CharField(max_length=160, blank=True, null=True)

    url = models.URLField(blank=True, null=True)

    raw = models.JSONField(blank=True, null=True)  # payload bruto do Jira

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (
            ("jira_connection", "key"),  # mesmo projeto não se repete na conexão
        )
        indexes = [
            models.Index(fields=["jira_connection", "key"]),
            models.Index(fields=["jira_connection", "archived"]),
        ]

    def __str__(self):
        return f"{self.key} - {self.name}"



class JiraIssue(models.Model):
    """
    Representa uma 'tarefa' do Jira (Issue) armazenada localmente.
    """
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.CASCADE,
        related_name="jira_issues",
    )
    contrato = models.ForeignKey(
        "contratos.Contrato",
        on_delete=models.SET_NULL,
        related_name="jira_issues",
        blank=True,
        null=True,
        help_text="Opcional: se você conseguir mapear issue -> contrato",
    )

    # Identificadores Jira
    jira_id = models.CharField(max_length=60, unique=True)  # id interno do Jira
    key = models.CharField(max_length=30, unique=True)      # ex: ENG-123

    project_key = models.CharField(max_length=20, blank=True, null=True)
    issue_type = models.CharField(max_length=60, blank=True, null=True)
    summary = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=80, blank=True, null=True)
    priority = models.CharField(max_length=80, blank=True, null=True)

    assignee_account_id = models.CharField(max_length=120, blank=True, null=True)
    assignee_display_name = models.CharField(max_length=160, blank=True, null=True)

    reporter_account_id = models.CharField(max_length=120, blank=True, null=True)
    reporter_display_name = models.CharField(max_length=160, blank=True, null=True)

    labels = models.JSONField(blank=True, null=True)       # lista
    components = models.JSONField(blank=True, null=True)   # lista
    raw = models.JSONField(blank=True, null=True)          # payload bruto (útil p/ debug)

    # Datas do Jira (normalmente vêm em ISO datetime)
    jira_created_at = models.DateTimeField(blank=True, null=True)
    jira_updated_at = models.DateTimeField(blank=True, null=True)
    jira_resolved_at = models.DateTimeField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)

    # Tempo (Jira costuma trazer em segundos)
    original_estimate_seconds = models.IntegerField(blank=True, null=True)
    time_spent_seconds = models.IntegerField(blank=True, null=True)

    # Link para sua Tarefa local (opcional)
    tarefa_local = models.ForeignKey(
        "tarefas.Tarefa",
        on_delete=models.SET_NULL,
        related_name="jira_issues",
        blank=True,
        null=True,
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["cliente", "contrato", "status"]),
            models.Index(fields=["project_key", "jira_updated_at"]),
        ]

    def __str__(self):
        return f"{self.key} - {self.summary}"
