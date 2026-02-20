# contratos/analytics/smart_reports.py
from __future__ import annotations

from django.db.models import Count
from django.utils import timezone

from contratos.models import CopilotRun
from contratos.copilot.service import responder_pergunta_contrato


def smart_report_risco_contratual(*, user, contrato_id: int) -> dict:
    """
    Gera um relatório de risco usando o próprio Copilot (auditável em CopilotRun).
    """
    pergunta = (
        "Analise o contrato e identifique riscos jurídicos/financeiros relevantes. "
        "Procure cláusulas sobre multa, penalidades, rescisão, SLA, prazos e confidencialidade. "
        "Retorne: (1) riscos, (2) severidade, (3) cláusulas citadas, (4) recomendações."
    )
    return responder_pergunta_contrato(user=user, contrato_id=contrato_id, pergunta=pergunta)


def smart_report_resumo_executivo(*, user, contrato_id: int) -> dict:
    pergunta = (
        "Gere um resumo executivo do contrato: objeto/escopo, principais obrigações do contratado e do contratante, "
        "prazos/vigência, SLA (se houver), penalidades/multa, rescisão, e recomendações de ações. "
        "Cite as cláusulas usadas."
    )
    return responder_pergunta_contrato(user=user, contrato_id=contrato_id, pergunta=pergunta)


def audit_runs_por_contrato(contrato_id: int, limit: int = 50) -> dict:
    qs = CopilotRun.objects.filter(contrato_id=contrato_id).order_by("-criado_em")[:limit]
    return {
        "contrato_id": contrato_id,
        "items": [
            {
                "run_id": r.id,
                "status": r.status,
                "mode": r.mode,
                "usuario_id": r.usuario_id,
                "criado_em": r.criado_em.isoformat(),
                "model": r.model,
                "prompt_version": r.prompt_version,
                "latency_ms": r.latency_ms,
                "user_message": r.user_message[:300],
            }
            for r in qs
        ],
    }


def audit_kpis(days: int = 30) -> dict:
    start = timezone.now() - timezone.timedelta(days=days)
    qs = CopilotRun.objects.filter(criado_em__gte=start)

    by_status = dict(qs.values("status").annotate(qt=Count("id")).values_list("status", "qt"))
    by_mode = dict(qs.values("mode").annotate(qt=Count("id")).values_list("mode", "qt"))

    return {
        "periodo_days": days,
        "runs_total": qs.count(),
        "por_status": by_status,
        "por_mode": by_mode,
    }
