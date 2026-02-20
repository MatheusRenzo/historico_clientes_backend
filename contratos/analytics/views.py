# contratos/analytics/views.py
from __future__ import annotations

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from contratos.models import Contrato
from contratos.copilot.policies import assert_contrato_access  # se você criou; senão comente

from contratos.analytics.dashboard_operacional import dashboard_operacional
from contratos.analytics.dashboard_executivo import dashboard_executivo
from contratos.analytics.reports import (
    report_performance_por_cliente,
    report_consumo_horas_por_contrato,
    report_obrigacoes_contratuais,
    report_tarefas_por_responsavel,
    report_apontamentos,
    report_clausulas_criticas,
)
from contratos.analytics.smart_reports import (
    smart_report_risco_contratual,
    smart_report_resumo_executivo,
    audit_runs_por_contrato,
    audit_kpis,
)


def _get_int(request, key: str, default=None):
    v = request.query_params.get(key)
    if v is None or v == "":
        return default
    try:
        return int(v)
    except Exception:
        return default


def _get_bool(request, key: str, default=False):
    v = request.query_params.get(key)
    if v is None:
        return default
    return str(v).lower() in ("1", "true", "sim", "yes", "y", "on")


def _tenant_cliente_id(request):
    """
    Se seu user tiver cliente_id, isso força multi-tenant automaticamente.
    Caso você NÃO use multi-tenant por user, retorne None.
    """
    u = request.user
    if hasattr(u, "cliente_id") and u.cliente_id:
        return int(u.cliente_id)
    return None


# -----------------------------
# DASHBOARDS (globais)
# -----------------------------
class DashboardOperacionalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # se multi-tenant: usuário define cliente automaticamente
        tenant_cliente_id = _tenant_cliente_id(request)

        # permite admin filtrar por cliente_id via query (?cliente_id=)
        cliente_id = tenant_cliente_id or _get_int(request, "cliente_id")

        data = dashboard_operacional(cliente_id=cliente_id)
        return Response(data, status=status.HTTP_200_OK)


class DashboardExecutivoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_cliente_id = _tenant_cliente_id(request)
        cliente_id = tenant_cliente_id or _get_int(request, "cliente_id")

        data = dashboard_executivo(cliente_id=cliente_id)
        return Response(data, status=status.HTTP_200_OK)


# -----------------------------
# RELATÓRIOS (globais)
# -----------------------------
class ReportPerformancePorClienteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = _get_int(request, "days", 90)
        data = report_performance_por_cliente(days=days)
        return Response(data, status=status.HTTP_200_OK)


class ReportConsumoHorasPorContratoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_cliente_id = _tenant_cliente_id(request)
        cliente_id = tenant_cliente_id or _get_int(request, "cliente_id")

        data = report_consumo_horas_por_contrato(cliente_id=cliente_id)
        return Response(data, status=status.HTTP_200_OK)


class ReportTarefasPorResponsavelView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_cliente_id = _tenant_cliente_id(request)
        cliente_id = tenant_cliente_id or _get_int(request, "cliente_id")
        days = _get_int(request, "days", 90)

        data = report_tarefas_por_responsavel(cliente_id=cliente_id, days=days)
        return Response(data, status=status.HTTP_200_OK)


class ReportApontamentosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_cliente_id = _tenant_cliente_id(request)
        cliente_id = tenant_cliente_id or _get_int(request, "cliente_id")
        days = _get_int(request, "days", 30)

        data = report_apontamentos(cliente_id=cliente_id, days=days)
        return Response(data, status=status.HTTP_200_OK)


# -----------------------------
# RELATÓRIOS por CONTRATO
# -----------------------------
class ReportObrigacoesContratuaisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, contrato_id: int):
        contrato = Contrato.objects.select_related("cliente").get(id=contrato_id)
        try:
            assert_contrato_access(request.user, contrato)
        except Exception:
            # se você não tem policy ainda, comente o assert e remova este except
            return Response({"detail": "Acesso negado."}, status=status.HTTP_403_FORBIDDEN)

        data = report_obrigacoes_contratuais(contrato_id=contrato_id)
        return Response(data, status=status.HTTP_200_OK)


class ReportClausulasCriticasView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, contrato_id: int):
        contrato = Contrato.objects.select_related("cliente").get(id=contrato_id)
        try:
            assert_contrato_access(request.user, contrato)
        except Exception:
            return Response({"detail": "Acesso negado."}, status=status.HTTP_403_FORBIDDEN)

        data = report_clausulas_criticas(contrato_id=contrato_id)
        return Response(data, status=status.HTTP_200_OK)


# -----------------------------
# SMART REPORTS (Copilot)
# -----------------------------
class SmartReportRiscoContratualView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, contrato_id: int):
        contrato = Contrato.objects.select_related("cliente").get(id=contrato_id)
        try:
            assert_contrato_access(request.user, contrato)
        except Exception:
            return Response({"detail": "Acesso negado."}, status=status.HTTP_403_FORBIDDEN)

        data = smart_report_risco_contratual(user=request.user, contrato_id=contrato_id)
        return Response(data, status=status.HTTP_200_OK)


class SmartReportResumoExecutivoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, contrato_id: int):
        contrato = Contrato.objects.select_related("cliente").get(id=contrato_id)
        try:
            assert_contrato_access(request.user, contrato)
        except Exception:
            return Response({"detail": "Acesso negado."}, status=status.HTTP_403_FORBIDDEN)

        data = smart_report_resumo_executivo(user=request.user, contrato_id=contrato_id)
        return Response(data, status=status.HTTP_200_OK)


# -----------------------------
# AUDITORIA Copilot
# -----------------------------
class CopilotAuditRunsPorContratoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, contrato_id: int):
        contrato = Contrato.objects.select_related("cliente").get(id=contrato_id)
        try:
            assert_contrato_access(request.user, contrato)
        except Exception:
            return Response({"detail": "Acesso negado."}, status=status.HTTP_403_FORBIDDEN)

        limit = _get_int(request, "limit", 50)
        data = audit_runs_por_contrato(contrato_id=contrato_id, limit=limit)
        return Response(data, status=status.HTTP_200_OK)


class CopilotAuditKpisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = _get_int(request, "days", 30)
        data = audit_kpis(days=days)
        return Response(data, status=status.HTTP_200_OK)
