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
    objectid = models.CharField(max_length=50, blank=True, null=True)

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
    raw = models.JSONField(default=dict, blank=True)
    items = models.ForeignKey("zabbix_integration.ZabbixItem", on_delete=models.CASCADE, related_name="triggers", null=True)
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
    host = models.ForeignKey("zabbix_integration.ZabbixHost", on_delete=models.CASCADE, related_name="items", null=True)

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
        # ajuste os campos conforme seu model real
        host_nome = getattr(self.host, "nome", None) or getattr(self.host, "name", None) or "SEM_HOST"
        item_nome = getattr(self, "nome", None) or getattr(self, "name", None) or f"Item#{self.pk}"
        return f"{host_nome} - {item_nome}"

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
    trigger = models.ForeignKey("zabbix_integration.ZabbixTrigger", null=True, blank=True, on_delete=models.SET_NULL)
    
    name = models.CharField(max_length=255, blank=True, null=True)
    severity = models.IntegerField(blank=True, null=True)
    acknowledged = models.BooleanField(default=False)

    clock = models.DateTimeField()

    host = models.ForeignKey("zabbix_integration.ZabbixHost", on_delete=models.SET_NULL, null=True, blank=True)

    hostid = models.CharField(max_length=50, blank=True, null=True)  # redundante mas útil para consultas sem join
    raw = models.JSONField(blank=True, null=True)

    hostname = models.CharField(max_length=255, blank=True, null=True)
    objectid = models.CharField(max_length=50, blank=True, null=True)
    objectname = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["cliente", "clock"]),
            models.Index(fields=["cliente", "severity"]),
        ]

class ZabbixTemplate(models.Model):
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE)
    templateid = models.CharField(max_length=50)
    name = models.CharField(max_length=255)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("cliente", "templateid")
        indexes = [models.Index(fields=["cliente", "name"])]

    def __str__(self):
        return self.name
    
class ZabbixUser(models.Model):
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE)
    userid = models.CharField(max_length=50)
    username = models.CharField(max_length=120)  # alias/username
    name = models.CharField(max_length=120, blank=True, null=True)
    surname = models.CharField(max_length=120, blank=True, null=True)

    roleid = models.CharField(max_length=50, blank=True, null=True)
    user_groups = models.JSONField(blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("cliente", "userid")
        indexes = [models.Index(fields=["cliente", "username"])]

    def __str__(self):
        return self.username
    
class ZabbixSLA(models.Model):
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE)
    slaid = models.CharField(max_length=50)
    name = models.CharField(max_length=255)

    # campos típicos (podem variar conforme versão/config)
    period = models.IntegerField(blank=True, null=True)
    slo = models.DecimalField(max_digits=6, decimal_places=3, blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)

    raw = models.JSONField(blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("cliente", "slaid")
        indexes = [models.Index(fields=["cliente", "name"])]

    def __str__(self):
        return self.name

class ZabbixAlarm(models.Model):
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE)
    eventid = models.CharField(max_length=50)  # event do problema
    name = models.CharField(max_length=255)
    severity = models.IntegerField(default=0)
    acknowledged = models.BooleanField(default=False)

    clock = models.DateTimeField()  # início do problema (epoch -> datetime)

    hostid = models.CharField(max_length=50, blank=True, null=True)
    hostname = models.CharField(max_length=255, blank=True, null=True)

    raw = models.JSONField(blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("cliente", "eventid")
        indexes = [
            models.Index(fields=["cliente", "severity"]),
            models.Index(fields=["cliente", "clock"]),
        ]

    def __str__(self):
        return f"[SEV {self.severity}] {self.name}"

class ZabbixAlarmEvent(models.Model):
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE)
    eventid = models.CharField(max_length=50, unique=True)

    name = models.CharField(max_length=255, blank=True, null=True)
    severity = models.IntegerField(blank=True, null=True)
    acknowledged = models.BooleanField(default=False)
    clock = models.DateTimeField()

    hostid = models.CharField(max_length=50, blank=True, null=True)
    hostname = models.CharField(max_length=255, blank=True, null=True)

    raw = models.JSONField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["cliente", "clock"]),
            models.Index(fields=["cliente", "severity"]),
        ]

class ZabbixAlertSent(models.Model):
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE)
    alertid = models.CharField(max_length=50, unique=True)

    eventid = models.CharField(max_length=50, blank=True, null=True)
    clock = models.DateTimeField()

    sendto = models.CharField(max_length=255, blank=True, null=True)
    subject = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)

    raw = models.JSONField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["cliente", "clock"]),
        ]
