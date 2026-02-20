# contratos/analytics/dashboard_operacional.py
from __future__ import annotations

from django.db.models import Count, Q
from django.utils import timezone

from .helpers import qs_contratos, qs_tarefas, sum_seconds_trabalhados, seconds_to_hours, contrato_status


def dashboard_operacional(cliente_id: int | None = None) -> dict:
    contratos = list(qs_contratos(cliente_id=cliente_id).select_related("cliente"))
    contrato_ids = [c.id for c in contratos]

    # contratos vencendo em 30 dias
    hoje = timezone.localdate()
    em_30 = hoje + timezone.timedelta(days=30)
    vencendo_30 = [c for c in contratos if c.data_fim and hoje <= c.data_fim <= em_30]

    tarefas_qs = qs_tarefas(cliente_id=cliente_id)
    tarefas_total = tarefas_qs.count()

    tarefas_por_status = dict(
        tarefas_qs.values("status").annotate(qt=Count("id")).values_list("status", "qt")
    )

    tarefas_atrasadas = tarefas_qs.filter(
        status__in=["ABERTA", "EM_ANDAMENTO"],
        prazo_dias_sugerido__isnull=False,
    ).count()
    # (como você ainda não tem "data_prazo", atrasado aqui é heurístico.
    # se criar data_prazo, trocamos por data_prazo__lt=hoje.)

    segundos = sum_seconds_trabalhados(cliente_id=cliente_id)
    horas_trabalhadas = seconds_to_hours(segundos)

    horas_previstas_total = float(sum((c.horas_previstas_total or 0) for c in contratos))

    contratos_por_status = {"ATIVO": 0, "VENCIDO": 0}
    for c in contratos:
        contratos_por_status[contrato_status(c)] += 1

    return {
        "kpis": {
            "contratos_total": len(contratos),
            "contratos_ativos": contratos_por_status["ATIVO"],
            "contratos_vencidos": contratos_por_status["VENCIDO"],
            "contratos_vencendo_30_dias": len(vencendo_30),
            "tarefas_total": tarefas_total,
            "tarefas_atrasadas_estimada": tarefas_atrasadas,
            "horas_previstas_total": round(horas_previstas_total, 2),
            "horas_apontadas_total": horas_trabalhadas,
            "saldo_horas_estimado": round(horas_previstas_total - horas_trabalhadas, 2),
        },
        "charts": {
            "contratos_por_status": contratos_por_status,
            "tarefas_por_status": tarefas_por_status,
        },
        "lists": {
            "contratos_vencendo_30_dias": [
                {
                    "contrato_id": c.id,
                    "cliente_id": c.cliente_id,
                    "cliente": c.cliente.nome,
                    "titulo": c.titulo,
                    "data_fim": c.data_fim.isoformat() if c.data_fim else None,
                }
                for c in vencendo_30
            ][:50]
        },
    }
