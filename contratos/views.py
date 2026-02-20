import json
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from contratos.services_proposta import importar_proposta_tecnica_e_gerar_tarefas
from .serializers import ContratoSerializer, ContratoTarefaSerializer
from openai import OpenAI
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Contrato, ContratoArquivo, ContratoClausula, ContratoTarefa, TarefaTimer
from .services_tarefas import gerar_tarefas_por_clausulas
from django.db.models import Q
from .services_timer import iniciar_timer, pausar_timer, retomar_timer, finalizar_timer
from copilot.contracts.service import responder_pergunta_contrato
from .filters import ContratoTarefaFilter
from .views_pdf import AnalisarContratoPDFView

# (opcional, mas recomendado) schema para forçar JSON consistente
CONTRACT_SCHEMA = {
    "name": "contract_extraction",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "contratante": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "tipo_pessoa": {"type": "string", "enum": ["PF", "PJ", "NAO_IDENTIFICADO"]},
                    "nome_razao_social": {"type": ["string", "null"]},
                    "cpf_cnpj": {"type": ["string", "null"]},
                    "email": {"type": ["string", "null"]},
                    "telefone": {"type": ["string", "null"]},
                    "endereco": {"type": ["string", "null"]},
                    "representante_legal": {"type": ["string", "null"]},
                },
                "required": ["tipo_pessoa","nome_razao_social","cpf_cnpj","email","telefone","endereco","representante_legal"],
            },
            "contratada": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "tipo_pessoa": {"type": "string", "enum": ["PF", "PJ", "NAO_IDENTIFICADO"]},
                    "nome_razao_social": {"type": ["string", "null"]},
                    "cpf_cnpj": {"type": ["string", "null"]},
                    "email": {"type": ["string", "null"]},
                    "telefone": {"type": ["string", "null"]},
                    "endereco": {"type": ["string", "null"]},
                    "representante_legal": {"type": ["string", "null"]},
                },
                "required": ["tipo_pessoa","nome_razao_social","cpf_cnpj","email","telefone","endereco","representante_legal"],
            },
            "metadados": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "titulo_documento": {"type": ["string", "null"]},
                    "data_assinatura": {"type": ["string", "null"]},
                    "vigencia_inicio": {"type": ["string", "null"]},
                    "vigencia_fim": {"type": ["string", "null"]},
                    "local_assinatura": {"type": ["string", "null"]},
                },
                "required": ["titulo_documento","data_assinatura","vigencia_inicio","vigencia_fim","local_assinatura"],
            },
            "clausulas": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "numero": {"type": ["string", "null"]},
                        "titulo": {"type": ["string", "null"]},
                        "texto": {"type": "string"},
                    },
                    "required": ["numero", "titulo", "texto"],
                },
            },
            "observacoes": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["contratante", "contratada", "metadados", "clausulas", "observacoes"],
    },
}



class ContratoViewSet(viewsets.ModelViewSet):  # ✅ troque ... por ModelViewSet
    queryset = Contrato.objects.all()
    serializer_class = ContratoSerializer       # ✅ necessário pro router inferir basename
    permission_classes = [IsAuthenticated]

    # ✅ filtros (opcional, mas você já pediu django-filter)
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["cliente"]
    search_fields = ["titulo", "descricao"]
    ordering_fields = ["id", "data_inicio", "data_fim", "criado_em"]
    ordering = ["-id"]

    @action(detail=True, methods=["post"], url_path="copilot/query")
    def copilot_query(self, request, pk=None):
        pergunta = (request.data.get("message") or "").strip()
        if not pergunta:
            return Response({"detail": "Envie 'message'."}, status=status.HTTP_400_BAD_REQUEST)

        data = responder_pergunta_contrato(user=request.user, contrato_id=int(pk), pergunta=pergunta)
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="gerar-tarefas")
    def gerar_tarefas(self, request, pk=None):
        """
        POST /api/contratos/{id}/gerar-tarefas/
        Body JSON (opcional):
        {
          "clausula_ids": [1,2,3],     # se não enviar, usa todas do contrato
          "substituir": false,        # se true, apaga tarefas geradas por IA e recria
          "evitar_duplicadas": true   # se true, evita criar tarefa com mesmo titulo+clausula
        }
        """
        contrato = self.get_object()

        clausula_ids = request.data.get("clausula_ids") or None
        substituir = str(request.data.get("substituir") or "false").lower() in ("1", "true", "sim", "yes")
        evitar_duplicadas = str(request.data.get("evitar_duplicadas") or "true").lower() in ("1", "true", "sim", "yes")

        qs = ContratoClausula.objects.filter(contrato=contrato)

        # ✅ valida clausula_ids (garante que pertencem ao contrato)
        if clausula_ids:
            if not isinstance(clausula_ids, list):
                return Response(
                    {"detail": "clausula_ids deve ser uma lista de inteiros."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                clausula_ids = [int(x) for x in clausula_ids]
            except Exception:
                return Response(
                    {"detail": "clausula_ids contém valores inválidos (use inteiros)."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            qs = qs.filter(id__in=clausula_ids)

            # se o usuário mandou ids que não pertencem ao contrato, avisa
            encontrados = set(qs.values_list("id", flat=True))
            faltantes = [cid for cid in clausula_ids if cid not in encontrados]
            if faltantes:
                return Response(
                    {"detail": "Algumas cláusulas não existem neste contrato.", "faltantes": faltantes},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        clausulas = list(qs.values("id", "numero", "titulo", "texto"))
        if not clausulas:
            return Response(
                {"detail": "Nenhuma cláusula encontrada para gerar tarefas."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ✅ chama IA
        try:
            result = gerar_tarefas_por_clausulas(clausulas)
        except Exception as e:
            return Response(
                {"detail": f"Falha ao gerar tarefas via IA: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        tarefas = result.get("tarefas") or []
        if not isinstance(tarefas, list):
            return Response(
                {"detail": "IA retornou formato inválido.", "raw": result},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # ✅ filtra/normaliza tarefas: só aceita tarefas para clausulas deste contrato
        clausulas_validas = {c["id"] for c in clausulas}
        tarefas_normalizadas = []
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

            tarefas_normalizadas.append(
                {
                    "clausula_id": clausula_id,
                    "titulo": titulo[:200],
                    "descricao": (t.get("descricao") or "").strip(),
                    "responsavel_sugerido": t.get("responsavel_sugerido"),
                    "prioridade": t.get("prioridade"),
                    "prazo_dias_sugerido": t.get("prazo_dias_sugerido"),
                    "raw": t,
                }
            )

        if not tarefas_normalizadas:
            return Response(
                {
                    "contrato_id": contrato.id,
                    "clausulas_processadas": len(clausulas),
                    "tarefas_geradas": 0,
                    "detail": "Nenhuma tarefa necessária foi identificada nas cláusulas.",
                },
                status=status.HTTP_200_OK,
            )

        with transaction.atomic():
            if substituir:
                ContratoTarefa.objects.filter(contrato=contrato, gerada_por_ia=True).delete()

            bulk = []
            criadas = 0
            puladas = 0

            for t in tarefas_normalizadas:
                if evitar_duplicadas:
                    exists = ContratoTarefa.objects.filter(
                        contrato=contrato,
                        clausula_id=t["clausula_id"],
                        titulo__iexact=t["titulo"],
                    ).exists()
                    if exists:
                        puladas += 1
                        continue

                bulk.append(
                    ContratoTarefa(
                        contrato=contrato,
                        clausula_id=t["clausula_id"],
                        titulo=t["titulo"],
                        descricao=t["descricao"],
                        responsavel_sugerido=t["responsavel_sugerido"],
                        prioridade=t["prioridade"],
                        prazo_dias_sugerido=t["prazo_dias_sugerido"],
                        gerada_por_ia=True,
                        raw=t["raw"],
                    )
                )

            if bulk:
                ContratoTarefa.objects.bulk_create(bulk)
                criadas = len(bulk)

        return Response(
            {
                "contrato_id": contrato.id,
                "clausulas_processadas": len(clausulas),
                "tarefas_sugeridas_pela_ia": len(tarefas),
                "tarefas_geradas": criadas,
                "tarefas_puladas": puladas,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="analisar-pdf", parser_classes=[MultiPartParser, FormParser])
    def analisar_pdf(self, request, pk=None):
        # reutiliza sua APIView existente chamando o método post
        view = AnalisarContratoPDFView.as_view()
        return view(request._request, pk=pk)
    
    @action(detail=True, methods=["post"], url_path="proposta/importar-e-gerar-tarefas")
    def proposta_importar_e_gerar_tarefas(self, request, pk=None):
        contrato = self.get_object()

        arquivo_id = request.data.get("arquivo_id")
        if not arquivo_id:
            return Response({"detail": "Envie arquivo_id (ContratoArquivo.id)."}, status=status.HTTP_400_BAD_REQUEST)

        substituir_clausulas = str(request.data.get("substituir_clausulas") or "true").lower() in ("1","true","sim","yes")
        substituir_tarefas_ia = str(request.data.get("substituir_tarefas_ia") or "false").lower() in ("1","true","sim","yes")
        evitar_duplicadas = str(request.data.get("evitar_duplicadas") or "true").lower() in ("1","true","sim","yes")

        data = importar_proposta_tecnica_e_gerar_tarefas(
            contrato_id=contrato.id,
            arquivo_id=int(arquivo_id),
            substituir_clausulas=substituir_clausulas,
            substituir_tarefas_ia=substituir_tarefas_ia,
            evitar_duplicadas=evitar_duplicadas,
        )
        return Response(data, status=status.HTTP_200_OK)
    

def analisar_pdf(self, request, pk=None):
    """
    POST /api/contratos/{id}/analisar-pdf/
    form-data:
      file: PDF (obrigatório)
      tipo: CONTRATO_PRINCIPAL | ADITIVO | ANEXO | OUTRO (opcional)
      versao: int (opcional)
      substituir_clausulas: true/false (opcional; default true)
    """

    contrato: Contrato = self.get_object()

    pdf_file = request.FILES.get("file")
    if not pdf_file:
        return Response(
            {"detail": "Envie o PDF em form-data com a chave 'file'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    filename = (getattr(pdf_file, "name", "") or "contrato.pdf").strip()
    if not filename.lower().endswith(".pdf"):
        return Response(
            {"detail": "O arquivo precisa ter extensão .pdf (ex: contrato.pdf)."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    tipo = request.data.get("tipo") or ContratoArquivo.Tipo.CONTRATO_PRINCIPAL
    versao = int(request.data.get("versao") or 1)
    substituir = str(request.data.get("substituir_clausulas") or "true").lower() in (
        "1", "true", "yes", "sim"
    )

    # ✅ 1) Leia os bytes ANTES de salvar no banco (evita stream consumir e ficar vazio)
    try:
        pdf_file.seek(0)
    except Exception:
        pass

    pdf_bytes = pdf_file.read()
    if not pdf_bytes:
        return Response(
            {"detail": "O arquivo enviado está vazio (0 bytes)."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ✅ 2) Volta o ponteiro para o Django conseguir salvar o FileField corretamente
    try:
        pdf_file.seek(0)
    except Exception:
        pass

    # ✅ 3) Salva o arquivo no banco
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

    # ✅ 4) Upload para OpenAI usando bytes + filename (evita “got none” e “File is empty”)
    client = OpenAI()

    openai_file = client.files.create(
        file=(filename, pdf_bytes, "application/pdf"),
        purpose="assistants",
    )

    prompt = (
        "Você é um analista jurídico/contratual.\n"
        "Extraia do PDF:\n"
        "1) Dados do CONTRATANTE.\n"
        "2) Dados da CONTRATADA (se existir).\n"
        "3) Metadados (título, data de assinatura, vigência).\n"
        "4) Liste TODAS as cláusulas com número, título e texto completo.\n"
        "Se algo não existir, retorne null e escreva em observacoes.\n"
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
        response_format={"type": "json_schema", "json_schema": CONTRACT_SCHEMA},
    )

    data = json.loads(resp.output_text)

    # ✅ 5) Grava cláusulas
    with transaction.atomic():
        # se quiser substituir, o mais comum é substituir TUDO do contrato (ou só do arquivo)
        if substituir:
            ContratoClausula.objects.filter(contrato=contrato, fonte_arquivo=arquivo).delete()

        clausulas = data.get("clausulas") or []
        bulk = []
        for i, c in enumerate(clausulas, start=1):
            texto = (c.get("texto") or "").strip()
            if not texto:
                continue  # evita cláusula vazia
            bulk.append(
                ContratoClausula(
                    contrato=contrato,
                    fonte_arquivo=arquivo,
                    ordem=i,
                    numero=c.get("numero"),
                    titulo=c.get("titulo"),
                    texto=texto,
                    extraida_por_ia=True,
                    raw=c,
                )
            )

        if bulk:
            ContratoClausula.objects.bulk_create(bulk)

        arquivo.extraido_em = timezone.now()
        arquivo.extraido_por = request.user
        arquivo.save(update_fields=["extraido_em", "extraido_por", "atualizado_em"])

    return Response(
        {
            "contrato_id": contrato.id,
            "arquivo": {
                "id": arquivo.id,
                "tipo": arquivo.tipo,
                "versao": arquivo.versao,
                "nome_original": arquivo.nome_original,
                "sha256": arquivo.sha256,
                "url": arquivo.arquivo.url if arquivo.arquivo else None,
            },
            "extraido": {
                "contratante": data.get("contratante"),
                "contratada": data.get("contratada"),
                "metadados": data.get("metadados"),
                "observacoes": data.get("observacoes", []),
                "clausulas_count": len(data.get("clausulas") or []),
            },
        },
        status=status.HTTP_200_OK,
    )

class ContratoTarefaViewSet(viewsets.ModelViewSet):
    queryset = (
        ContratoTarefa.objects
        .select_related("contrato", "contrato__cliente", "clausula")
        .all()
    )
    serializer_class = ContratoTarefaSerializer
    permission_classes = [IsAuthenticated]

    # ✅ filtros enterprise
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ContratoTarefaFilter

    # ✅ busca textual
    search_fields = ["titulo", "descricao", "responsavel_sugerido", "prioridade"]

    # ✅ ordenação
    ordering_fields = [
        "id",
        "criado_em",
        "atualizado_em",
        "status",
        "prioridade",
        "prazo_dias_sugerido",
    ]
    ordering = ["-criado_em"]

    # --- suas actions de timer continuam iguais ---
    @action(detail=True, methods=["post"], url_path="timer/iniciar")
    def timer_iniciar(self, request, pk=None):
        contratotarefa = self.get_object()
        timer = iniciar_timer(tarefa=contratotarefa, usuario=request.user, observacao=request.data.get("observacao"))
        return Response({"timer_id": timer.id, "estado": timer.estado}, status=200)

    @action(detail=True, methods=["post"], url_path="timer/pausar")
    def timer_pausar(self, request, pk=None):
        contratotarefa = self.get_object()
        timer = TarefaTimer.objects.filter(tarefa=contratotarefa, usuario=request.user).order_by("-id").first()
        if not timer:
            return Response({"detail": "Nenhum timer encontrado."}, status=404)
        timer = pausar_timer(timer)
        return Response({"timer_id": timer.id, "estado": timer.estado}, status=200)

    @action(detail=True, methods=["post"], url_path="timer/retomar")
    def timer_retomar(self, request, pk=None):
        contratotarefa = self.get_object()
        timer = TarefaTimer.objects.filter(tarefa=contratotarefa, usuario=request.user).order_by("-id").first()
        if not timer:
            return Response({"detail": "Nenhum timer encontrado."}, status=404)
        timer = retomar_timer(timer)
        return Response({"timer_id": timer.id, "estado": timer.estado}, status=200)

    @action(detail=True, methods=["post"], url_path="timer/finalizar")
    def timer_finalizar(self, request, pk=None):
        contratotarefa = self.get_object()
        timer = TarefaTimer.objects.filter(tarefa=contratotarefa, usuario=request.user).order_by("-id").first()
        if not timer:
            return Response({"detail": "Nenhum timer encontrado."}, status=404)

        concluir = str(request.data.get("concluir_tarefa") or "true").lower() in ("1","true","sim","yes")
        descricao = request.data.get("descricao")
        result = finalizar_timer(timer, descricao_apontamento=descricao, concluir_tarefa=concluir)
        return Response(result, status=200)