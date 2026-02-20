# contratos/analytics/helpers.py
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, Tuple

from django.db.models import QuerySet, Sum, F
from django.db.models.functions import Coalesce
from django.utils import timezone

from contratos.models import Contrato, ContratoTarefa, TarefaTimer, ContratoClausula


def parse_date_range(
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    days: Optional[int] = None,
) -> Tuple[datetime, datetime]:
    """
    Retorna (start_dt, end_dt) timezone-aware.
    - se days informado, usa [agora-days, agora]
    - se data_inicio/data_fim informados, usa eles
    """
    now = timezone.now()

    if days:
        start = now - timedelta(days=int(days))
        end = now
        return start, end

    if data_inicio:
        start = timezone.make_aware(datetime.fromisoformat(data_inicio))
    else:
        start = now - timedelta(days=30)

    if data_fim:
        end = timezone.make_aware(datetime.fromisoformat(data_fim))
    else:
        end = now

    return start, end


def qs_contratos(cliente_id: Optional[int] = None) -> QuerySet:
    qs = Contrato.objects.all()
    if cliente_id:
        qs = qs.filter(cliente_id=cliente_id)
    return qs


def qs_tarefas(cliente_id: Optional[int] = None, contrato_id: Optional[int] = None) -> QuerySet:
    qs = ContratoTarefa.objects.select_related("contrato", "contrato__cliente", "clausula")
    if cliente_id:
        qs = qs.filter(contrato__cliente_id=cliente_id)
    if contrato_id:
        qs = qs.filter(contrato_id=contrato_id)
    return qs


def qs_timers(cliente_id: Optional[int] = None, contrato_id: Optional[int] = None) -> QuerySet:
    qs = TarefaTimer.objects.select_related("tarefa", "tarefa__contrato", "usuario")
    if cliente_id:
        qs = qs.filter(tarefa__contrato__cliente_id=cliente_id)
    if contrato_id:
        qs = qs.filter(tarefa__contrato_id=contrato_id)
    return qs


def sum_seconds_trabalhados(cliente_id: Optional[int] = None, contrato_id: Optional[int] = None) -> int:
    agg = qs_timers(cliente_id=cliente_id, contrato_id=contrato_id).aggregate(
        total=Coalesce(Sum("segundos_trabalhados"), 0)
    )
    return int(agg["total"] or 0)


def seconds_to_hours(seconds: int) -> float:
    return round(seconds / 3600.0, 2)


def contrato_status(contrato: Contrato) -> str:
    """
    Deriva status sem adicionar campo:
    - ATIVO: data_fim >= hoje ou data_fim null
    - VENCIDO: data_fim < hoje
    """
    today = timezone.localdate()
    if contrato.data_fim and contrato.data_fim < today:
        return "VENCIDO"
    return "ATIVO"
