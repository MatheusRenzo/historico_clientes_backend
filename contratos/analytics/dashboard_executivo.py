# contratos/analytics/dashboard_executivo.py
from __future__ import annotations

from collections import defaultdict
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from contratos.models import Cliente
from .helpers import qs_contratos, qs_tarefas, sum_seconds_trabalhados, seconds_to_hours


def dashboard_executivo(cliente_id: int | None = None) -> dict:
    contratos_qs = qs_contratos(cliente_id=cliente_id).select_related("cliente")
    contratos = list(contratos_qs)

    # Top clientes por quantidade de contratos (proxy de relevância, já que não temos receita)
    top_clientes = (
        contratos_qs.values("cliente_id", "cliente__nome")
        .annotate(qt_contratos=Count("id"))
        .order_by("-qt_contratos")[:10]
    )

    # horas
    horas_previstas_total = round(float(sum((c.horas_previstas_total or 0) for c in contratos)), 2)
    horas_apontadas_total = seconds_to_hours(sum_seconds_trabalhados(cliente_id=cliente_id))

    # taxa “renovação” (proxy): contratos com data_fim nos últimos 90 dias
    hoje = timezone.localdate()
    inicio_90 = hoje - timezone.timedelta(days=90)
    encerrados_90 = [c for c in contratos if c.data_fim and inicio_90 <= c.data_fim <= hoje]
    # sem histórico de “renovado”, retornamos só o número (ativar se criar campo renovado/renovacao_de)
    taxa_renovacao = None

    # risco: contratos com tarefas críticas (ALTA) abertas
    tarefas_qs = qs_tarefas(cliente_id=cliente_id)
    contratos_com_risco = (
        tarefas_qs.filter(status__in=["ABERTA", "EM_ANDAMENTO"], prioridade__iexact="ALTA")
        .values("contrato_id")
        .annotate(qt=Count("id"))
        .order_by("-qt")[:10]
    )

    # Receita/margem: não existe no modelo hoje
    receita_contratada_ativa = None
    margem_estimada = None

    return {
        "kpis": {
            "contratos_total": len(contratos),
            "top_clientes_qt_contratos": list(top_clientes),
            "horas_previstas_total": horas_previstas_total,
            "horas_apontadas_total": horas_apontadas_total,
            "taxa_renovacao_90d": taxa_renovacao,  # precisa de campo/heurística melhor
            "receita_contratada_ativa": receita_contratada_ativa,  # requer campo valor
            "margem_estimada": margem_estimada,  # requer custo/valor hora
        },
        "risk": {
            "contratos_com_tarefas_alta_abertas": list(contratos_com_risco),
            "nota": "Indicadores de receita/margem requerem campos financeiros no modelo.",
        },
    }
