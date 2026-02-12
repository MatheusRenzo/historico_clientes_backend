import os
from typing import Any
from langchain_openai import ChatOpenAI
from zabbix_integration.models import ZabbixSLA

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def _serialize_slas(qs) -> list[dict[str, Any]]:
    # Mantenha só o essencial para não explodir tokens
    return [
        {
            "slaid": s.slaid,
            "name": s.name,
            "period": s.period,
            "slo": float(s.slo) if s.slo is not None else None,
            "status": s.status,
            "updated_at": s.atualizado_em.isoformat() if s.atualizado_em else None,
        }
        for s in qs
    ]


def analyze_zabbix_sla(cliente_id: int, user_prompt: str, limit: int = 200) -> dict:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY não configurada no servidor.")

    qs = ZabbixSLA.objects.filter(cliente_id=cliente_id).order_by("-atualizado_em")[:limit]
    slas = _serialize_slas(qs)

    if not slas:
        return {
            "answer": "Não encontrei registros na tabela ZabbixSLA para este cliente.",
            "insights": [],
            "data_points": {"slas_count": 0},
        }

    system = (
        "Você é um analista de dados. "
        "Responda APENAS com base nos dados fornecidos (ZabbixSLA). "
        "Se a pergunta pedir algo que não dá para inferir, diga o que falta."
    )

    # Contexto em JSON (o LLM entende bem)
    context = {
        "table": "ZabbixSLA",
        "cliente_id": cliente_id,
        "slas": slas,
        "columns": ["slaid", "name", "period", "slo", "status", "updated_at"],
    }

    llm = ChatOpenAI(model="gpt-4.1-mini", api_key=OPENAI_API_KEY)

    prompt = (
        f"DADOS (JSON):\n{context}\n\n"
        f"TAREFA DO USUÁRIO:\n{user_prompt}\n\n"
        "FORMATO DA RESPOSTA:\n"
        "- answer: texto curto\n"
        "- insights: lista (no máximo 8 itens)\n"
        "- data_points: objeto com contagens/valores agregados quando possível\n"
    )

    resp = llm.invoke(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
    )

    return {
        "answer": getattr(resp, "content", str(resp)),
        "data_points": {"slas_count": len(slas)},
    }
