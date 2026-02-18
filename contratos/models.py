from __future__ import annotations
import hashlib
from django.db import models
from clientes.models import Cliente
from django.conf import settings
from django.db import models
from django.utils import timezone

class Contrato(models.Model):
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE, related_name="contratos")
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    data_inicio = models.DateField()
    data_fim = models.DateField(blank=True, null=True)
    horas_previstas_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.cliente.nome} - {self.titulo}"


class ContratoArquivo(models.Model):
    """
    Armazena arquivos (principalmente PDF) vinculados ao contrato.
    Permite múltiplos anexos e versões.
    """
    class Tipo(models.TextChoices):
        CONTRATO_PRINCIPAL = "CONTRATO_PRINCIPAL", "Contrato principal"
        ADITIVO = "ADITIVO", "Aditivo"
        ANEXO = "ANEXO", "Anexo"
        OUTRO = "OUTRO", "Outro"

    contrato = models.ForeignKey(
        "contratos.Contrato",
        on_delete=models.CASCADE,
        related_name="arquivos",
    )

    tipo = models.CharField(max_length=30, choices=Tipo.choices, default=Tipo.CONTRATO_PRINCIPAL)
    versao = models.PositiveIntegerField(default=1)

    arquivo = models.FileField(upload_to="contratos/pdfs/")
    nome_original = models.CharField(max_length=255, blank=True, null=True)

    mime_type = models.CharField(max_length=120, blank=True, null=True)
    tamanho_bytes = models.BigIntegerField(blank=True, null=True)

    sha256 = models.CharField(max_length=64, blank=True, null=True, db_index=True)

    extraido_em = models.DateTimeField(blank=True, null=True)  # quando rodou extração IA
    extraido_por = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contratos_arquivos_extraidos",
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["contrato", "tipo", "versao"]),
            models.Index(fields=["contrato", "criado_em"]),
        ]
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.contrato_id} - {self.tipo} v{self.versao}"

    def compute_sha256(self):
        if not self.arquivo:
            return None
        h = hashlib.sha256()
        for chunk in self.arquivo.chunks():
            h.update(chunk)
        return h.hexdigest()

    def save(self, *args, **kwargs):
        # preenche metadados do arquivo (defensivo)
        if self.arquivo and not self.nome_original:
            self.nome_original = getattr(self.arquivo, "name", None)

        if self.arquivo and not self.tamanho_bytes:
            try:
                self.tamanho_bytes = self.arquivo.size
            except Exception:
                pass

        # calcula sha256 apenas se não existir (ou se quiser sempre recalcular)
        if self.arquivo and not self.sha256:
            try:
                self.sha256 = self.compute_sha256()
            except Exception:
                # não bloqueia save se falhar
                pass

        return super().save(*args, **kwargs)


class ContratoClausula(models.Model):
    """
    Cláusula extraída (ou cadastrada manualmente) vinculada ao Contrato e opcionalmente ao arquivo fonte.
    """
    contrato = models.ForeignKey(
        "contratos.Contrato",
        on_delete=models.CASCADE,
        related_name="clausulas",
    )

    fonte_arquivo = models.ForeignKey(
        "contratos.ContratoArquivo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clausulas",
        help_text="Arquivo (PDF) usado como fonte desta cláusula",
    )

    # numeração pode ser '1', '1.1', 'CLÁUSULA TERCEIRA', etc.
    numero = models.CharField(max_length=50, blank=True, null=True)
    titulo = models.CharField(max_length=255, blank=True, null=True)

    texto = models.TextField()

    # para ordenar/exibir (ex.: 1, 2, 3) mesmo se 'numero' for texto
    ordem = models.PositiveIntegerField(default=0)

    # rastreabilidade
    extraida_por_ia = models.BooleanField(default=False)
    confidence = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)  # 0-100 (opcional)
    raw = models.JSONField(blank=True, null=True)  # payload/trecho original (opcional)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["contrato", "ordem"]),
            models.Index(fields=["contrato", "numero"]),
            models.Index(fields=["fonte_arquivo"]),
        ]
        ordering = ["ordem", "id"]

    def __str__(self):
        n = self.numero or "s/n"
        return f"Contrato {self.contrato_id} - Cláusula {n}"
    
    from django.db import models

class ContratoTarefa(models.Model):
    class Status(models.TextChoices):
        ABERTA = "ABERTA", "Aberta"
        EM_ANDAMENTO = "EM_ANDAMENTO", "Em andamento"
        CONCLUIDA = "CONCLUIDA", "Concluída"
        CANCELADA = "CANCELADA", "Cancelada"

    contrato = models.ForeignKey("contratos.Contrato", on_delete=models.CASCADE, related_name="tarefas_contrato")
    clausula = models.ForeignKey("contratos.ContratoClausula", on_delete=models.CASCADE, related_name="tarefas")

    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)

    responsavel_sugerido = models.CharField(max_length=80, blank=True, null=True)  # ex: "Gerente de Projeto"
    prioridade = models.CharField(max_length=20, blank=True, null=True)           # ex: "ALTA", "MEDIA", "BAIXA"
    prazo_dias_sugerido = models.IntegerField(blank=True, null=True)              # ex: 7, 15, 30

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ABERTA)

    gerada_por_ia = models.BooleanField(default=True)
    raw = models.JSONField(blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["contrato", "status"]),
            models.Index(fields=["clausula"]),
        ]

    def __str__(self):
        return f"[{self.contrato_id}] {self.titulo}"


class TarefaTimer(models.Model):
    class Estado(models.TextChoices):
        RODANDO = "RODANDO", "Rodando"
        PAUSADO = "PAUSADO", "Pausado"
        FINALIZADO = "FINALIZADO", "Finalizado"

    tarefa = models.ForeignKey("contratos.ContratoTarefa", on_delete=models.CASCADE, related_name="timers")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tarefa_timers")

    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.RODANDO)

    iniciado_em = models.DateTimeField(default=timezone.now)
    finalizado_em = models.DateTimeField(blank=True, null=True)

    # acumuladores (em segundos)
    segundos_trabalhados = models.PositiveIntegerField(default=0)
    segundos_pausados = models.PositiveIntegerField(default=0)

    # marcações para calcular delta
    ultimo_inicio_em = models.DateTimeField(blank=True, null=True)  # quando começou/retomou
    ultimo_pause_em = models.DateTimeField(blank=True, null=True)   # quando pausou

    observacao = models.CharField(max_length=255, blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["tarefa", "usuario", "estado"]),
        ]

    def __str__(self):
        return f"Timer({self.tarefa_id}, {self.usuario_id}, {self.estado})"


class TarefaTimerPausa(models.Model):
    timer = models.ForeignKey(TarefaTimer, on_delete=models.CASCADE, related_name="pausas")
    inicio = models.DateTimeField()
    fim = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Pausa({self.timer_id})"
