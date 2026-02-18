import json
import re
from openai import OpenAI


def _extract_json(text: str) -> dict:
    """
    Tenta extrair JSON mesmo se o modelo devolver texto extra.
    """
    text = (text or "").strip()
    if not text:
        return {}

    # 1) tenta direto
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2) tenta achar primeiro bloco {...}
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass

    return {}


def gerar_tarefas_por_clausulas(clausulas: list[dict]) -> dict:
    client = OpenAI()

    prompt = (
        "Você é um analista de contratos.\n"
        "Gere tarefas APENAS quando a cláusula exigir uma ação/obrigação prática.\n"
        "Gere tarefas quando a cláusula exigir uma ação/obrigação prática.\n"
        "Se não exigir ação (foro, definições, disposições gerais), não gere tarefa.\n\n"
        "Retorne SOMENTE um JSON válido, SEM markdown, SEM texto extra, no formato:\n"
        "{\n"
        '  "tarefas": [\n'
        "    {\n"
        '      "clausula_id": 123,\n'
        '      "titulo": "texto curto",\n'
        '      "descricao": "detalhe da tarefa",\n'
        '      "responsavel_sugerido": "Líder|Gerente de Projeto|Analista",\n'
        '      "prioridade": "ALTA|MEDIA|BAIXA",\n'
        '      "prazo_dias_sugerido": 7\n'
        "    }\n"
        "  ]\n"
        "}\n"
    )
    print("Gerando tarefas para cláusulas:", [c.get("numero") for c in clausulas])
    resp = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_text", "text": json.dumps({"clausulas": clausulas}, ensure_ascii=False)},
                ],
            }
        ],
    )
    print(f"Resposta bruta da OpenAI para geração de tarefas: {getattr(resp, 'output_text', None)[:2000] if getattr(resp, 'output_text', None) else 'SEM output_text'}")
    # dependendo do SDK, resp.output_text existe; se não, tenta outros jeitos
    output_text = getattr(resp, "output_text", None)
    if output_text is None:
        # fallback defensivo
        output_text = str(resp)

    data = _extract_json(output_text)
    if "tarefas" not in data:
        data["tarefas"] = []

    return data
