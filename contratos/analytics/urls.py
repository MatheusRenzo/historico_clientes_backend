# contratos/analytics/urls.py
from django.urls import path

from contratos.analytics.views import (
    DashboardOperacionalView,
    DashboardExecutivoView,

    ReportPerformancePorClienteView,
    ReportConsumoHorasPorContratoView,
    ReportTarefasPorResponsavelView,
    ReportApontamentosView,

    ReportObrigacoesContratuaisView,
    ReportClausulasCriticasView,

    SmartReportRiscoContratualView,
    SmartReportResumoExecutivoView,

    CopilotAuditRunsPorContratoView,
    CopilotAuditKpisView,
)

urlpatterns = [
    # Dashboards (globais)
    path("contratos/dashboard/operacional/", DashboardOperacionalView.as_view(), name="contratos-dashboard-operacional"),
    path("contratos/dashboard/executivo/", DashboardExecutivoView.as_view(), name="contratos-dashboard-executivo"),

    # Relatórios (globais)
    path("contratos/reports/performance-por-cliente/", ReportPerformancePorClienteView.as_view(), name="contratos-report-performance-por-cliente"),
    path("contratos/reports/consumo-horas-por-contrato/", ReportConsumoHorasPorContratoView.as_view(), name="contratos-report-consumo-horas-por-contrato"),
    path("contratos/reports/tarefas-por-responsavel/", ReportTarefasPorResponsavelView.as_view(), name="contratos-report-tarefas-por-responsavel"),
    path("contratos/reports/apontamentos/", ReportApontamentosView.as_view(), name="contratos-report-apontamentos"),

    # Relatórios por contrato
    path("contratos/<int:contrato_id>/reports/obrigacoes/", ReportObrigacoesContratuaisView.as_view(), name="contrato-report-obrigacoes"),
    path("contratos/<int:contrato_id>/reports/clausulas-criticas/", ReportClausulasCriticasView.as_view(), name="contrato-report-clausulas-criticas"),

    # Smart reports (Copilot) por contrato
    path("contratos/<int:contrato_id>/smart/risco-contratual/", SmartReportRiscoContratualView.as_view(), name="contrato-smart-risco-contratual"),
    path("contratos/<int:contrato_id>/smart/resumo-executivo/", SmartReportResumoExecutivoView.as_view(), name="contrato-smart-resumo-executivo"),

    # Auditoria Copilot
    path("contratos/<int:contrato_id>/copilot/audit/runs/", CopilotAuditRunsPorContratoView.as_view(), name="copilot-audit-runs-por-contrato"),
    path("contratos/copilot/audit/kpis/", CopilotAuditKpisView.as_view(), name="copilot-audit-kpis"),
]
