from django.db import models

class Parametro(models.Model):
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    valor = models.TextField(blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome  # ✅ não existe cliente aqui


class ParametroCliente(models.Model):
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.CASCADE,
        related_name="parametros",
    )
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    valor = models.CharField(max_length=400, blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.cliente.nome} - {self.nome}"


class ItensMonitoramento(models.Model):
    class TipoSaida(models.TextChoices):
        GRAFICO = "Grafico", "Gráfico"
        TABELA = "Tabela", "Tabela"

    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.CASCADE,
        related_name="monitoramento",  # ✅ corrigido typo (opcional)
    )
    monitoramento = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    tipo = models.TextField(choices=TipoSaida.choices, blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.cliente.nome} - {self.monitoramento}"  # ✅
