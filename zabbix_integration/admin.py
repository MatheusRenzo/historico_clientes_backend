from django.contrib import admin
from django.utils.html import format_html

from .models import (
    ZabbixConnection,
    ZabbixHost,
    ZabbixTrigger,
    ZabbixProblem,
    ZabbixItem,
    ZabbixHistory,
    ZabbixEvent,
)

@admin.register(ZabbixConnection)
class ZabbixConnectionAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "base_url", "usuario", "ativo", "atualizado_em")
    list_filter = ("ativo",)
    search_fields = ("cliente__nome", "base_url", "usuario")
    ordering = ("-atualizado_em",)

    autocomplete_fields = ("cliente",)
    readonly_fields = ("criado_em", "atualizado_em")

    fieldsets = (
        ("Cliente", {"fields": ("cliente", "ativo")}),
        ("Conexão Zabbix", {"fields": ("base_url", "usuario", "senha")}),
        ("Auditoria", {"fields": ("criado_em", "atualizado_em")}),
    )


@admin.register(ZabbixHost)
class ZabbixHostAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "nome", "hostname", "ip", "status", "atualizado_em")
    list_filter = ("cliente", "status")
    search_fields = ("nome", "hostname", "ip", "cliente__nome")
    ordering = ("cliente__nome", "nome")

    autocomplete_fields = ("cliente",)
    readonly_fields = ("criado_em", "atualizado_em")


@admin.register(ZabbixTrigger)
class ZabbixTriggerAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "descricao", "prioridade", "status", "ultima_alteracao")
    list_filter = ("cliente", "prioridade", "status")
    search_fields = ("descricao", "cliente__nome")
    ordering = ("-ultima_alteracao",)

    autocomplete_fields = ("cliente",)


@admin.register(ZabbixProblem)
class ZabbixProblemAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "nome", "severidade", "reconhecido", "inicio", "host")
    list_filter = ("cliente", "severidade", "reconhecido")
    search_fields = ("nome", "cliente__nome", "host__nome", "host__hostname", "host__ip")
    ordering = ("-inicio",)

    autocomplete_fields = ("cliente", "host")

@admin.register(ZabbixItem)
class ZabbixItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "cliente",
        "host",
        "name",
        "key",
        "value_type",
        "units",
        "delay",
        "lastclock",
        "short_lastvalue",
        "enabled",
    )
    list_filter = ("cliente", "host", "value_type", "enabled")
    search_fields = ("name", "key", "host__nome", "host__hostname", "cliente__nome")
    ordering = ("cliente__nome", "host__nome", "name")

    autocomplete_fields = ("cliente", "host")
    readonly_fields = ("criado_em", "atualizado_em")

    def short_lastvalue(self, obj):
        v = obj.lastvalue or ""
        v = str(v)
        return (v[:60] + "…") if len(v) > 60 else v
    short_lastvalue.short_description = "lastvalue"


@admin.register(ZabbixHistory)
class ZabbixHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "item", "clock", "short_value")
    list_filter = ("cliente", "clock")
    search_fields = ("item__name", "item__key", "item__host__nome", "cliente__nome")
    ordering = ("-clock",)

    autocomplete_fields = ("cliente", "item")

    # 🔥 importante: histórico pode ser enorme -> evita carregar tudo de uma vez
    list_per_page = 50

    def short_value(self, obj):
        v = obj.value or ""
        v = str(v)
        return (v[:80] + "…") if len(v) > 80 else v
    short_value.short_description = "value"


@admin.register(ZabbixEvent)
class ZabbixEventAdmin(admin.ModelAdmin):
    list_display = ("eventid", "cliente", "clock", "severity_badge", "acknowledged", "host", "short_name")
    list_filter = ("cliente", "severity", "acknowledged", "clock")
    search_fields = ("eventid", "name", "host__nome", "host__hostname", "cliente__nome")
    ordering = ("-clock",)

    autocomplete_fields = ("cliente", "host")

    # raw pode ser grande
    readonly_fields = ("eventid", "clock")

    def short_name(self, obj):
        n = obj.name or ""
        return (n[:90] + "…") if len(n) > 90 else n
    short_name.short_description = "name"

    def severity_badge(self, obj):
        sev = obj.severity if obj.severity is not None else 0
        # sem depender de CSS externo, só um destaque simples
        label = f"SEV {sev}"
        return format_html("<b>{}</b>", label)
    severity_badge.short_description = "severity"
