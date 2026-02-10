from django.contrib import admin
from .models import RagDocument

@admin.register(RagDocument)
class RagDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "cliente",
        "titulo",
        "fonte",
        "criado_em",
    )

    list_filter = (
        "cliente",
        "fonte",
    )

    search_fields = (
        "titulo",
        "conteudo",
    )

    ordering = ("-criado_em",)

    readonly_fields = (
        "criado_em",
        "atualizado_em",
    )

    fieldsets = (
        ("Cliente", {
            "fields": ("cliente",)
        }),
        ("Documento", {
            "fields": ("titulo", "conteudo", "fonte")
        }),
        ("Auditoria", {
            "fields": ("criado_em", "atualizado_em")
        }),
    )
