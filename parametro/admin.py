from django.contrib import admin
from .models import Parametro, ParametroCliente, ItensMonitoramento, ContextoCliente

@admin.register(Parametro)
class ParametroAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "valor", "criado_em")
    search_fields = ("nome",)

@admin.register(ParametroCliente)
class ParametroClienteAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "nome", "valor", "criado_em")
    search_fields = ("nome", "cliente__nome")
    list_filter = ("cliente",)

@admin.register(ItensMonitoramento)
class ItensMonitoramentoAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "monitoramento", "tipo", "criado_em")
    search_fields = ("monitoramento", "cliente__nome")
    list_filter = ("cliente", "tipo")

@admin.register(ContextoCliente)
class ContextoClienteAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "nome", "descricao", "criado_em", "ativo")
    search_fields = ("cliente", "nome", "descriao", "criado_em", "ativo")
    list_filter = ("cliente", "nome")
