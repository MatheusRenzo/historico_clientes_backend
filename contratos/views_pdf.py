import json
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from openai import OpenAI

from .models import Contrato, ContratoArquivo, ContratoClausula
#from .prompts import CONTRACT_SCHEMA  # se você tiver; senão remova


class AnalisarContratoPDFView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        contrato = get_object_or_404(Contrato, pk=pk)
        print(f"Analisando PDF para contrato {contrato.id} - {contrato.titulo}")
        pdf_file = request.FILES.get("file")
        if not pdf_file:
            return Response({"detail": "Envie o PDF em form-data com a chave 'file'."}, status=400)

        filename = (getattr(pdf_file, "name", "") or "contrato.pdf").strip()
        if not filename.lower().endswith(".pdf"):
            return Response({"detail": "O arquivo precisa ser .pdf"}, status=400)

        # lê bytes antes
        try:
            pdf_file.seek(0)
        except Exception:
            pass
        pdf_bytes = pdf_file.read()
        if not pdf_bytes:
            return Response({"detail": "Arquivo enviado está vazio."}, status=400)

        # volta ponteiro para salvar no storage
        try:
            pdf_file.seek(0)
        except Exception:
            pass

        tipo = request.data.get("tipo") or ContratoArquivo.Tipo.CONTRATO_PRINCIPAL
        versao = int(request.data.get("versao") or 1)
        substituir = str(request.data.get("substituir_clausulas") or "true").lower() in ("1","true","yes","sim")

        # 1) salva arquivo
        with transaction.atomic():
            arquivo = ContratoArquivo.objects.create(
                contrato=contrato,
                tipo=tipo,
                versao=versao,
                arquivo=pdf_file,
                nome_original=filename,
                mime_type=getattr(pdf_file, "content_type", None) or "application/pdf",
                tamanho_bytes=getattr(pdf_file, "size", None) or len(pdf_bytes),
            )
        print(f"Arquivo salvo com ID {arquivo.id} para contrato {contrato.id}")
        # 2) chama OpenAI
        client = OpenAI()
        openai_file = client.files.create(
            file=(filename, pdf_bytes, "application/pdf"),
            purpose="assistants",
        )

        prompt = (
            "Extraia do PDF dados do contratante/contratada e TODAS as cláusulas.\n"
            "Retorne JSON com a chave 'clausulas' como lista de objetos: {numero,titulo,texto}.\n"
            "Retorne APENAS JSON."
        )

        resp = client.responses.create(
            model="gpt-4o-mini",
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_file", "file_id": openai_file.id},
                ],
            }],
            # se você não tiver schema, comente a linha abaixo
            #response_format={"type": "json_schema", "json_schema": CONTRACT_SCHEMA},
        )

        #data = json.loads(resp.output_text)
        raw_text = getattr(resp, "output_text", None)
        print(f"Resposta bruta da OpenAI para contrato {contrato.id}:", raw_text[:2000] if raw_text else "SEM output_text")
        # fallback: tenta extrair de resp.output
        if not raw_text:
            try:
                parts = []
                for item in (resp.output or []):
                    for c in (item.get("content") or []):
                        if c.get("type") in ("output_text", "text"):
                            parts.append(c.get("text", ""))
                raw_text = "\n".join([p for p in parts if p]).strip()
            except Exception:
                raw_text = ""

        if not raw_text:
            # ajuda MUITO a debugar sem quebrar
            return Response(
                {
                    "detail": "OpenAI retornou resposta vazia (sem output_text).",
                    "debug": {
                        "has_output": bool(getattr(resp, "output", None)),
                        "model": "gpt-4o-mini",
                    },
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Se vier JSON cercado por ```json ... ```
        raw_text = raw_text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`")
            raw_text = raw_text.replace("json", "", 1).strip()

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            return Response(
                {
                    "detail": "OpenAI não retornou JSON válido.",
                    "raw": raw_text[:2000],
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        clausulas = data.get("clausulas") or []
        print(f"Cláusulas extraídas para contrato {contrato.id}: {len(clausulas)}")
        if not isinstance(clausulas, list):
            return Response({"detail": "Resposta IA sem lista de clausulas."}, status=400)

        # 3) grava cláusulas no banco
        with transaction.atomic():
            if substituir:
                # apaga só as cláusulas desse arquivo (ou troque para contrato inteiro se preferir)
                ContratoClausula.objects.filter(contrato=contrato, fonte_arquivo=arquivo).delete()

            bulk = []
            for i, c in enumerate(clausulas, start=1):
                texto = (c.get("texto") or "").strip()
                if not texto:
                    continue

                bulk.append(
                    ContratoClausula(
                        contrato=contrato,
                        fonte_arquivo=arquivo,
                        ordem=i,
                        numero=c.get("numero"),
                        titulo=c.get("titulo"),
                        texto=texto,
                        raw=c,
                        extraida_por_ia=True,
                    )
                )

            ContratoClausula.objects.bulk_create(bulk)

            arquivo.extraido_em = timezone.now()
            arquivo.extraido_por = request.user
            arquivo.save(update_fields=["extraido_em", "extraido_por", "atualizado_em"])

        return Response(
            {
                "contrato_id": contrato.id,
                "arquivo_id": arquivo.id,
                "clausulas_gravadas": len(bulk),
            },
            status=status.HTTP_200_OK,
        )
