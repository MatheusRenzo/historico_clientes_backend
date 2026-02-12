from __future__ import annotations

from datetime import datetime, timezone
import calendar

from .sync import get_client_for_cliente


def _month_range_utc(year: int, month: int) -> tuple[int, int]:
    """
    Retorna timestamps UTC do início do mês (inclusive) e do início do próximo mês (exclusive).
    """
    start = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)

    if month == 12:
        end = datetime(year + 1, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    else:
        end = datetime(year, month + 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    return int(start.timestamp()), int(end.timestamp())


def build_monthly_sla_report(cliente_id: int, year: int, month: int) -> dict:
    client = get_client_for_cliente(cliente_id)

    period_from, period_to = _month_range_utc(year, month)

    # 1) Lista SLAs visíveis para esse usuário
    slas = client.sla_get(output="extend", sortfield="name") or []

    # Normaliza: sla.get normalmente retorna LISTA
    if not isinstance(slas, list):
        slas = [slas]

    report_rows = []
    overall = {
        "month": f"{year:04d}-{month:02d}",
        "period_from": period_from,
        "period_to": period_to,
        "slas_count": len(slas),
        "services_count": 0,
        "uptime_seconds_total": 0,
        "downtime_seconds_total": 0,
        "sli_avg": None,
    }

    for sla in slas:
        if not isinstance(sla, dict):
            continue

        slaid = str(sla.get("slaid") or sla.get("id") or "")
        if not slaid:
            continue

        params = {
            "slaid": slaid,
            "period_from": period_from,
            "period_to": period_to,
            "periods": 1,
        }

        print("ZABBIX sla.getsli params:", params)
        result = client._call("sla.getsli", params) or {}
        if not isinstance(result, dict):
            result = {}

        serviceids = result.get("serviceids") or []
        sli_matrix = result.get("sli") or []

        services_data = []
        row0 = sli_matrix[0] if isinstance(sli_matrix, list) and sli_matrix else []

        for idx, sid in enumerate(serviceids):
            if idx >= len(row0):
                continue

            cell = row0[idx] or {}
            if not isinstance(cell, dict):
                cell = {}

            uptime = int(cell.get("uptime") or 0)
            downtime = int(cell.get("downtime") or 0)

            services_data.append({
                "serviceid": sid,
                "sli": cell.get("sli"),
                "uptime": uptime,
                "downtime": downtime,
                "error_budget": cell.get("error_budget"),
                "excluded_downtimes": cell.get("excluded_downtimes", []),
            })

            overall["uptime_seconds_total"] += uptime
            overall["downtime_seconds_total"] += downtime

        overall["services_count"] += len(services_data)

        sli_values = [s["sli"] for s in services_data if s.get("sli") is not None]
        sla_sli_avg = (sum(sli_values) / len(sli_values)) if sli_values else None

        report_rows.append({
            "slaid": slaid,
            "name": sla.get("name"),
            "slo": sla.get("slo"),
            "month": f"{year:04d}-{month:02d}",
            "period_from": period_from,
            "period_to": period_to,
            "services": services_data,
            "sli_avg": sla_sli_avg,
        })

    # Média geral ponderada via uptime/downtime agregados (melhor que média de médias)
    total = overall["uptime_seconds_total"] + overall["downtime_seconds_total"]
    overall["sli_avg"] = (overall["uptime_seconds_total"] / total) * 100 if total > 0 else None

    return {
        "cliente_id": cliente_id,
        "year": year,
        "month": month,
        "period_from": period_from,
        "period_to": period_to,
        "overall": overall,
        "rows": report_rows,
    }
