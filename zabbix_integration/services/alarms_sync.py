from datetime import datetime, timedelta, timezone
from django.db import transaction

from zabbix_integration.services.sync import get_client_for_cliente
from zabbix_integration.models import ZabbixAlarm, ZabbixAlarmEvent, ZabbixAlertSent


def _dt(epoch: str | int) -> datetime:
    return datetime.fromtimestamp(int(epoch), tz=timezone.utc)


@transaction.atomic
def sync_active_alarms(cliente_id: int, since_hours: int = 24) -> dict:
    """
    Captura alarmes ATIVOS (problem.get).
    """
    client = get_client_for_cliente(cliente_id)
    time_from = int((datetime.now(tz=timezone.utc) - timedelta(hours=since_hours)).timestamp())

    problems = client.problem_get(
        output="extend",
        recent=True,
        time_from=time_from,
        sortfield=["eventid"],
        sortorder="DESC",
        selectHosts=["hostid", "name"],
        selectTags="extend",
    ) or []

    upserts = 0
    for p in problems:
        hosts = p.get("hosts") or []
        hostid = str(hosts[0].get("hostid")) if hosts else None
        hostname = hosts[0].get("name") if hosts else None

        ZabbixAlarm.objects.update_or_create(
            cliente_id=cliente_id,
            eventid=str(p["eventid"]),
            defaults={
                "name": p.get("name") or "",
                "severity": int(p.get("severity") or 0),
                "acknowledged": bool(int(p.get("acknowledged") or 0)),
                "clock": _dt(p["clock"]),
                "hostid": hostid,
                "hostname": hostname,
                "raw": p,
            },
        )
        upserts += 1

    return {"synced_active_alarms": upserts, "since_hours": since_hours}


@transaction.atomic
def sync_alarm_events(cliente_id: int, since_hours: int = 24, limit: int = 2000) -> dict:
    """
    Captura histórico de eventos (event.get).
    """
    client = get_client_for_cliente(cliente_id)
    time_from = int((datetime.now(tz=timezone.utc) - timedelta(hours=since_hours)).timestamp())

    events = client.event_get(
        output="extend",
        time_from=time_from,
        sortfield=["clock"],
        sortorder="DESC",
        selectHosts=["hostid", "name"],
        selectTags="extend",
        limit=limit,
    ) or []

    created = 0
    for ev in events:
        # event.get às vezes retorna hosts; às vezes não dependendo do selectHosts.
        hosts = ev.get("hosts") or []
        hostid = str(hosts[0].get("hostid")) if hosts else None
        hostname = hosts[0].get("name") if hosts else None

        obj, was_created = ZabbixAlarmEvent.objects.update_or_create(
            eventid=str(ev["eventid"]),
            defaults={
                "cliente_id": cliente_id,
                "name": ev.get("name"),
                "severity": int(ev.get("severity") or 0) if ev.get("severity") is not None else None,
                "acknowledged": bool(int(ev.get("acknowledged") or 0)),
                "clock": _dt(ev["clock"]),
                "hostid": hostid,
                "hostname": hostname,
                "raw": ev,
            },
        )
        if was_created:
            created += 1

    return {"synced_events": len(events), "new_events": created, "since_hours": since_hours}


@transaction.atomic
def sync_alerts_sent(cliente_id: int, since_hours: int = 24, limit: int = 2000) -> dict:
    """
    (Opcional) Captura alertas ENVIADOS (alert.get).
    """
    client = get_client_for_cliente(cliente_id)
    time_from = int((datetime.now(tz=timezone.utc) - timedelta(hours=since_hours)).timestamp())

    alerts = client.alert_get(
        output="extend",
        time_from=time_from,
        sortfield="clock",
        sortorder="DESC",
        limit=limit,
    ) or []

    created = 0
    for a in alerts:
        obj, was_created = ZabbixAlertSent.objects.update_or_create(
            alertid=str(a["alertid"]),
            defaults={
                "cliente_id": cliente_id,
                "eventid": str(a.get("eventid")) if a.get("eventid") else None,
                "clock": _dt(a["clock"]),
                "sendto": a.get("sendto"),
                "subject": a.get("subject"),
                "message": a.get("message"),
                "status": int(a.get("status") or 0) if a.get("status") is not None else None,
                "raw": a,
            },
        )
        if was_created:
            created += 1

    return {"synced_alerts": len(alerts), "new_alerts": created, "since_hours": since_hours}
