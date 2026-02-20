# contratos/services_proposta.py
from __future__ import annotations

import re
from typing import Tuple, List

from django.utils import timezone

from contratos.models import Contrato, ContratoArquivo, ContratoClausula, ContratoTarefa
from contratos.services_tarefas import gerar_tarefas_por_clausulas


def _extract_text_from_pdf(file_path: str) -> str:
    """
    Extração simples (sem OCR). Requer: pip install pypdf
    """
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    parts: List[str] = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        if txt.strip():
            parts.append(txt)
    return "\n\n".join(parts).strip()


def _extract_text_from_docx(file_path: str) -> str:
    """
    Requer: python-docx (já está instalado no ambiente).
    """
    from docx import Document

    doc = Document(file_path)
    parts = []
    for p in doc.paragraphs:
        if p.text and p.text.strip():
            parts.append(p.text.strip())
    return "\n".join(parts).strip()


def _extract_text_generic(arquivo: ContratoArquivo) -> str:
    """
    Detecta por extensão/mime e extrai texto.
    """
    file_path = arquivo.arquivo.path
    name = (arquivo.nome_original or arquivo.arquivo.name or "").lower()
    mime = (arquivo.mime_type or "").lower()

    if name.endswith(".pdf") or "pdf" in mime:
        return _extract_text_from_pdf(file_path)

    if name.endswith(".docx") or "word" in mime:
        return _extract_text_from_docx(file_path)

    # txt / fallback
    with open(file_path, "rb") as f:
        raw = f.read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1", errors="ignore")


def _to_markdown(text: str) -> str:
    """
    Conversão simples pra Markdown:
    - normaliza espaços
    - tenta detectar títulos (linhas curtas em CAPS ou terminando com :)
    - lista bullets
    """
    t = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"[ \t]+", " ", t)
    lines = [ln.strip() for ln in t.split("\n")]

    md: List[str] = []
    for ln in lines:
        if not ln:
            md.append("")
            continue

        # heading heurístico
        if (len(ln) <= 80 and ln.isupper()) or ln.endswith(":"):
            md.append(f"## {ln.rstrip(':')}")
            continue

        # bullets comuns
        if re.match(r"^(\-|\*|•)\s+", ln):
            ln = re.sub(r"^(•)\s+", "- ", ln)
            md.append(ln)
            continue

        # numeração tipo "1. " / "1) "
        if re.match(r"^\d+(\.\d+)*[)\.]?\s+", ln):
            md.append(f"- {ln}")
            continue

        md.append(ln)

    # remove excesso de linhas vazias
    out = "\n".join(md)
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out


def _split_markdown_into_sections(md: str) -> List[Tuple[str, str]]:
    """
    Divide markdown em seções pelo padrão '## '.
    Retorna lista (titulo, texto).
    """
    md = (md or "").strip()
    if not md:
        return []

    # se não tiver heading, retorna tudo numa seção
    if "## " not in md:
        return [("Proposta Técnica", md)]

    chunks = re.split(r"(?m)^##\s+", md)
    sections: List[Tuple[str, str]] = []
    # chunks[0] pode ser vazio/texto anterior
    prefix = chunks[0].strip()
    if prefix:
        sections.append(("Proposta Técnica", prefix))

    for c in chunks[1:]:
        c = c.strip()
        if not c:
            continue
        lines = c.splitlines()
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        if not body:
            continue
        sections.append((title[:255], body))
    return sections


def importar_proposta_tecnica_e_gerar_tarefas(
    *,
    contrato_id: int,
    arquivo_id: int,
    substituir_clausulas: bool = True,
    substituir_tarefas_ia: bool = False,
    evitar_duplicadas: bool = True,
) -> dict:
    """
    1) lê arquivo da proposta técnica
    2) converte para markdown
    3) grava no Contrato (proposta_tecnica_md)
    4) cria/atualiza Clausulas (seções) vinculadas ao arquivo
    5) gera tarefas a partir das seções
    """
    contrato = Contrato.objects.get(id=contrato_id)
    arquivo = ContratoArquivo.objects.get(id=arquivo_id, contrato_id=contrato_id)

    text = _extract_text_generic(arquivo)
    if not text.strip():
        return {"detail": "Não foi possível extrair texto do arquivo.", "contrato_id": contrato_id, "arquivo_id": arquivo_id}

    md = _to_markdown(text)
    sections = _split_markdown_into_sections(md)
    if not sections:
        return {"detail": "Texto extraído, mas não foi possível estruturar em seções.", "contrato_id": contrato_id, "arquivo_id": arquivo_id}

    # 1) grava markdown no contrato
    contrato.proposta_tecnica_md = md
    contrato.save(update_fields=["proposta_tecnica_md", "atualizado_em"])

    # 2) cria/atualiza cláusulas (seções)
    if substituir_clausulas:
        ContratoClausula.objects.filter(contrato=contrato, fonte_arquivo=arquivo).delete()

    bulk = []
    for i, (titulo, body) in enumerate(sections, start=1):
        bulk.append(
            ContratoClausula(
                contrato=contrato,
                fonte_arquivo=arquivo,
                ordem=i,
                numero=str(i),
                titulo=titulo,
                texto=body,
                extraida_por_ia=False,  # é extração local
                raw={"source": "proposta_tecnica", "section_title": titulo},
            )
        )
    ContratoClausula.objects.bulk_create(bulk)

    # marca arquivo como extraído
    arquivo.extraido_em = timezone.now()
    arquivo.save(update_fields=["extraido_em", "atualizado_em"])

    # 3) gerar tarefas baseado nas seções (cláusulas criadas)
    clausulas_payload = list(
        ContratoClausula.objects.filter(contrato=contrato, fonte_arquivo=arquivo)
        .values("id", "numero", "titulo", "texto")
        .order_by("ordem")
    )

    result = gerar_tarefas_por_clausulas(clausulas_payload)
    tarefas = result.get("tarefas") or []
    if not isinstance(tarefas, list):
        tarefas = []

    if substituir_tarefas_ia:
        ContratoTarefa.objects.filter(contrato=contrato, gerada_por_ia=True).delete()

    # 4) persistir tarefas (reaproveitando seu padrão)
    clausulas_validas = {c["id"] for c in clausulas_payload}
    criadas = 0
    puladas = 0

    for t in tarefas:
        if not isinstance(t, dict):
            continue
        clausula_id = t.get("clausula_id")
        if clausula_id is None:
            continue
        try:
            clausula_id = int(clausula_id)
        except Exception:
            continue
        if clausula_id not in clausulas_validas:
            continue

        titulo = (t.get("titulo") or "").strip()
        if not titulo:
            continue

        if evitar_duplicadas:
            exists = ContratoTarefa.objects.filter(
                contrato=contrato,
                clausula_id=clausula_id,
                titulo__iexact=titulo[:200],
            ).exists()
            if exists:
                puladas += 1
                continue

        ContratoTarefa.objects.create(
            contrato=contrato,
            clausula_id=clausula_id,
            titulo=titulo[:200],
            descricao=(t.get("descricao") or "").strip(),
            responsavel_sugerido=t.get("responsavel_sugerido"),
            prioridade=t.get("prioridade"),
            prazo_dias_sugerido=t.get("prazo_dias_sugerido"),
            gerada_por_ia=True,
            raw=t,
        )
        criadas += 1

    return {
        "contrato_id": contrato_id,
        "arquivo_id": arquivo_id,
        "markdown_gravado": True,
        "secoes_criadas": len(bulk),
        "tarefas_sugeridas_pela_ia": len(tarefas),
        "tarefas_geradas": criadas,
        "tarefas_puladas": puladas,
    }
