# contratos/analytics/reports.py
from __future__ import annotations

from collections import defaultdict
from django.db.models import Count, Sum, Q
from django.db.models.functions import Coalesce
from django.utils import timezone

from contratos.models import Contrato, ContratoClausula, ContratoTarefa, TarefaTimer
from .helpers import parse_date_range, seconds_to_hours, qs_contratos, qs_tarefas, qs_timers


# 4.1 Performance por Cliente
def report_performance_por_cliente(days: int = 90) -> dict:
    start, end = parse_date_range(days=days)
 
    contratos = (
        Contrato.objects.select_related("cliente")
        .values("cliente_id", "cliente__nome")
        .annotate(qt_contratos=Count("id"), horas_previstas=Coalesce(Sum("horas_previstas_total"), 0, output_field=DecimalField()))
        .order_by("-qt_contratos")
    )
 
    tarefas = (
        ContratoTarefa.objects.filter(criado_em__gte=start, criado_em__lte=end)
        .values("contrato__cliente_id", "contrato__cliente__nome", "status")
        .annotate(qt=Count("id"))
    )

    # agrupa tarefas por cliente/status
    by_cliente = defaultdict(lambda: {"tarefas_por_status": defaultdict(int)})
    for row in tarefas:
        cid = row["contrato__cliente_id"]
        by_cliente[cid]["cliente"] = row["contrato__cliente__nome"]
        by_cliente[cid]["tarefas_por_status"][row["status"]] += row["qt"]

    items = []
    for c in contratos:
        cid = c["cliente_id"]
        items.append({
            "cliente_id": cid,
            "cliente": c["cliente__nome"],
            "qt_contratos": c["qt_contratos"],
            "horas_previstas_total": float(c["horas_previstas"]),
            "tarefas_por_status": dict(by_cliente[cid]["tarefas_por_status"]),
        })

    return {"periodo": {"inicio": start.isoformat(), "fim": end.isoformat()}, "items": items}


# 4.2 Consumo de Horas por Contrato
def report_consumo_horas_por_contrato(cliente_id: int | None = None) -> dict:
    contratos = list(qs_contratos(cliente_id=cliente_id))
    items = []

    for c in contratos:
        segundos = qs_timers(contrato_id=c.id).aggregate(total=Coalesce(Sum("segundos_trabalhados"), 0))["total"] or 0
        horas_apontadas = seconds_to_hours(int(segundos))
        horas_previstas = float(c.horas_previstas_total or 0)

        items.append({
            "contrato_id": c.id,
            "cliente_id": c.cliente_id,
            "titulo": c.titulo,
            "horas_previstas": round(horas_previstas, 2),
            "horas_apontadas": horas_apontadas,
            "percentual_consumo": round((horas_apontadas / horas_previstas * 100) if horas_previstas else 0, 2),
            "saldo_horas": round(horas_previstas - horas_apontadas, 2),
        })

    items.sort(key=lambda x: x["percentual_consumo"], reverse=True)
    return {"items": items}


# 4.3 Obrigações Contratuais (via cláusulas + busca por termos)
def report_obrigacoes_contratuais(contrato_id: int) -> dict:
    termos = ["obrigações", "obrigação", "dever", "responsabilidade", "encargo", "compromisso"]
    q = Q()
    for t in termos:
        q |= Q(texto__icontains=t) | Q(titulo__icontains=t)

    clausulas = list(
        ContratoClausula.objects.filter(contrato_id=contrato_id).filter(q)
        .order_by("ordem")
        .values("id", "numero", "titulo", "texto", "ordem")
    )

    return {"contrato_id": contrato_id, "termos": termos, "clausulas": clausulas}


# 4.4 Tarefas por Responsável
def report_tarefas_por_responsavel(cliente_id: int | None = None, days: int = 90) -> dict:
    start, end = parse_date_range(days=days)

    qs = qs_tarefas(cliente_id=cliente_id).filter(criado_em__gte=start, criado_em__lte=end)
    rows = (
        qs.values("usuario_responsavel", "status")
        .annotate(qt=Count("id"))
        .order_by("usuario_responsavel", "status")
    )

    out = defaultdict(lambda: {"usuario_responsavel": None, "por_status": defaultdict(int), "total": 0})
    for r in rows:
        resp = r["usuario_responsavel"] or "NÃO DEFINIDO"
        out[resp]["usuario_responsavel"] = resp
        out[resp]["por_status"][r["status"]] += r["qt"]
        out[resp]["total"] += r["qt"]

    items = list(out.values())
    items.sort(key=lambda x: x["total"], reverse=True)
    return {"periodo": {"inicio": start.isoformat(), "fim": end.isoformat()}, "items": items}


# 4.5 Relatório de Apontamentos (Timers)
def report_apontamentos(cliente_id: int | None = None, days: int = 30) -> dict:
    start, end = parse_date_range(days=days)

    qs = qs_timers(cliente_id=cliente_id).filter(criado_em__gte=start, criado_em__lte=end)

    por_usuario = (
        qs.values("usuario_id", "usuario__username")
        .annotate(segundos=Coalesce(Sum("segundos_trabalhados"), 0))
        .order_by("-segundos")
    )

    por_contrato = (
        qs.values("tarefa__contrato_id", "tarefa__contrato__titulo")
        .annotate(segundos=Coalesce(Sum("segundos_trabalhados"), 0))
        .order_by("-segundos")
    )

    return {
        "periodo": {"inicio": start.isoformat(), "fim": end.isoformat()},
        "por_usuario": [
            {"usuario_id": r["usuario_id"], "usuario": r["usuario__username"], "horas": seconds_to_hours(int(r["segundos"] or 0))}
            for r in por_usuario
        ],
        "por_contrato": [
            {"contrato_id": r["tarefa__contrato_id"], "contrato": r["tarefa__contrato__titulo"], "horas": seconds_to_hours(int(r["segundos"] or 0))}
            for r in por_contrato
        ],
    }


# 4.6 Cláusulas Críticas (por termos)
def report_clausulas_criticas(contrato_id: int) -> dict:
    termos = [
        "multa", "penalidade", "sanção", "rescisão", "rescindir", "indenização",
        "sla", "nível de serviço", "confidencialidade", "sigilo", "lgpd", "dados pessoais",
        "prazo", "vigência", "vencimento"
    ]

    q = Q()
    for t in termos:
        q |= Q(texto__icontains=t) | Q(titulo__icontains=t)

    clausulas = list(
        ContratoClausula.objects.filter(contrato_id=contrato_id).filter(q)
        .order_by("ordem")
        .values("id", "numero", "titulo", "texto", "ordem")
    )
    return {"contrato_id": contrato_id, "termos": termos, "clausulas": clausulas}
