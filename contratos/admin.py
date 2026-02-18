from django.contrib import admin
from .models import Contrato, ContratoArquivo, ContratoClausula, ContratoTarefa, TarefaTimer


class ContratoArquivoInline(admin.TabularInline):
    model = ContratoArquivo
    extra = 0
    fields = ("tipo", "versao", "arquivo", "sha256", "extraido_em", "criado_em")
    readonly_fields = ("sha256", "extraido_em", "criado_em")


class ContratoClausulaInline(admin.TabularInline):
    model = ContratoClausula
    extra = 0
    fields = ("ordem", "numero", "titulo", "extraida_por_ia")
    readonly_fields = ()


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "titulo", "data_inicio", "data_fim", "horas_previstas_total", "atualizado_em")
    list_filter = ("cliente",)
    search_fields = ("titulo", "cliente__nome")
    inlines = [ContratoArquivoInline, ContratoClausulaInline]


@admin.register(ContratoArquivo)
class ContratoTarefaAdmin(admin.ModelAdmin):
    list_display = ("id", "contrato", "tipo", "versao", "sha256", "criado_em", "extraido_em")
    list_filter = ("tipo", "contrato__cliente")
    search_fields = ("contrato__titulo", "contrato__cliente__nome", "sha256", "nome_original")


@admin.register(ContratoClausula)
class ContratoClausulaAdmin(admin.ModelAdmin):
    list_display = ("id", "contrato", "ordem", "numero", "titulo", "extraida_por_ia", "atualizado_em")
    list_filter = ("extraida_por_ia", "contrato__cliente")
    search_fields = ("contrato__titulo", "numero", "titulo", "texto")

@admin.register(ContratoTarefa)
class ContratoTarefaAdmin(admin.ModelAdmin):
    list_display = ("id", "contrato", "status", "clausula", "titulo", "descricao", "atualizado_em")
    list_filter = ("status", "contrato", "titulo", "clausula", "descricao")
    search_fields = ("status", "contrato", "titulo", "clausula", "descricao")

@admin.register(TarefaTimer)
class TarefatimerAdmin(admin.ModelAdmin):
    list_display = ("id", "tarefa", "usuario", "estado", "atualizado_em")
    list_filter = ("tarefa", "usuario", "estado",)
    search_fields = ("tarefa", "usuario", "estado",)
