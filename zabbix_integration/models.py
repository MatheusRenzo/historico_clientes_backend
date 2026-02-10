from django.db import models

class ZabbixConnection(models.Model):
    cliente = models.OneToOneField(
        "clientes.Cliente",
        on_delete=models.CASCADE,
        related_name="zabbix_connection",
    )

    base_url = models.URLField(help_text="Ex: https://zabbix.suaempresa.com")
    usuario = models.CharField(max_length=120)
    senha = models.CharField(max_length=255)  # em produção: secret manager/criptografar

    ativo = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ZabbixConnection({self.cliente.nome})"


class ZabbixHost(models.Model):
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE)
    hostid = models.CharField(max_length=50)
    hostname = models.CharField(max_length=200)
    nome = models.CharField(max_length=200)
    status = models.CharField(max_length=20)

    ip = models.CharField(max_length=50, blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("cliente", "hostid")

    def __str__(self):
        return f"{self.nome} ({self.ip})"


class ZabbixTrigger(models.Model):
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE)
    triggerid = models.CharField(max_length=50)
    descricao = models.CharField(max_length=255)
    prioridade = models.IntegerField()
    status = models.CharField(max_length=20)
    ultima_alteracao = models.DateTimeField()

    class Meta:
        unique_together = ("cliente", "triggerid")


class ZabbixProblem(models.Model):
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE)
    eventid = models.CharField(max_length=50)
    nome = models.CharField(max_length=255)
    severidade = models.IntegerField()
    inicio = models.DateTimeField()
    reconhecido = models.BooleanField(default=False)

    host = models.ForeignKey(ZabbixHost, on_delete=models.CASCADE, null=True)

    class Meta:
        unique_together = ("cliente", "eventid")

from django.db import models

class ZabbixItem(models.Model):
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE)
    host = models.ForeignKey("zabbix_integration.ZabbixHost", on_delete=models.CASCADE, related_name="items")

    itemid = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    key = models.CharField(max_length=255)

    value_type = models.IntegerField()  # 0 float, 1 char, 2 log, 3 uint, 4 text
    units = models.CharField(max_length=20, blank=True, null=True)
    delay = models.CharField(max_length=50, blank=True, null=True)

    lastvalue = models.TextField(blank=True, null=True)
    lastclock = models.DateTimeField(blank=True, null=True)

    enabled = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("cliente", "itemid")
        indexes = [
            models.Index(fields=["cliente", "host", "key"]),
        ]

    def __str__(self):
        return f"{self.host.nome} - {self.name}"

class ZabbixHistory(models.Model):
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE)
    item = models.ForeignKey("zabbix_integration.ZabbixItem", on_delete=models.CASCADE, related_name="history")

    clock = models.DateTimeField()
    value = models.TextField()  # mantém flexível (float/uint/string)

    class Meta:
        unique_together = ("item", "clock")
        indexes = [
            models.Index(fields=["cliente", "item", "clock"]),
        ]

class ZabbixEvent(models.Model):
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE)
    eventid = models.CharField(max_length=50, unique=True)

    name = models.CharField(max_length=255, blank=True, null=True)
    severity = models.IntegerField(blank=True, null=True)
    acknowledged = models.BooleanField(default=False)

    clock = models.DateTimeField()

    host = models.ForeignKey("zabbix_integration.ZabbixHost", on_delete=models.SET_NULL, null=True, blank=True)

    raw = models.JSONField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["cliente", "clock"]),
            models.Index(fields=["cliente", "severity"]),
        ]
