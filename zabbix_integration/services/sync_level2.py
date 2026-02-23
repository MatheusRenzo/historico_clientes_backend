from datetime import datetime, timedelta, timezone
from django.db import transaction

from zabbix_integration.models import ZabbixHost, ZabbixItem, ZabbixHistory, ZabbixEvent, ZabbixTrigger
from zabbix_integration.services.sync import get_client_for_cliente


def _dt_from_epoch(epoch: str | int):
    return datetime.fromtimestamp(int(epoch), tz=timezone.utc)


@transaction.atomic
def sync_items(cliente_id: int, hostids: list[str] | None = None, key_contains: str | None = None):
    """
    Sincroniza itens (item.get). Recomendação: filtrar por key para trazer só itens relevantes.
    """
    client = get_client_for_cliente(cliente_id)

    params = {
        "output": ["itemid", "name", "key_", "value_type", "units", "delay", "lastvalue", "lastclock", "status", "hostid"],
        "hostids": hostids or [],
        #"limit": 1,
    }
    items = client.item_get(**params)
    for it in items:
        print(it)
        hostok = it.get("hostid")
        host = ZabbixHost.objects.filter(hostid=hostok).first() if hostok else None
        print(f"Hostid {hostok} maps to host {host}")
        print(f"Found host {hostok} for item {it['itemid']}")
        ZabbixItem.objects.update_or_create(
            cliente_id=cliente_id,
            itemid=it["itemid"],
            defaults={
                "host": host if host else None,
                "name": it.get("name") or "",
                "key": it.get("key_") or "",
                "value_type": int(it.get("value_type") or 0),
                "units": it.get("units"),
                "delay": it.get("delay"),
                "lastvalue": it.get("lastvalue"),
                "lastclock": _dt_from_epoch(it["lastclock"]) if it.get("lastclock") else None,
                "enabled": (it.get("status") == "0"),
            },
        )


@transaction.atomic
def sync_events(cliente_id: int, since_hours: int = 24):
    """
    Sincroniza eventos (event.get) das últimas N horas.
    """
    client = get_client_for_cliente(cliente_id)

    time_from = int((datetime.now(tz=timezone.utc) - timedelta(hours=since_hours)).timestamp())

    events = client.event_get(
        source=0,  # ✅ trigger events
        object=0,
        #objectids=["13015"],
        output=[
                "eventid",
                "source",
                "object",
                "objectid",
                "clock",
                "value",
                "acknowledged",
                "ns",
                "name",
                "severity",
                "r_eventid",
                "c_eventid",
                "correlationid",
                "userid",
                "opdata",
                "suppressed",
                "urls",
                ],
        time_from=time_from,
        sortfield=["clock"],
        sortorder="DESC",
        limit=1,
    )
    print(f"eventos: {events}")
    local_hosts = {h.hostid: h for h in ZabbixHost.objects.filter(cliente_id=cliente_id)}

    for ev in events:
        print(f"Syncing event {ev}")
        host = None
        hostname = None
        hostid = None

        hosts = ev.get("hosts") or []
        #print(f"Event {ev}")
        if hosts:
            hostid = str(hosts[0]["hostid"])
            hostname = hosts[0].get("host")
            host = local_hosts.get(hostid)

        triggerid = ev.get("objectid") if ev.get("object") == "0" else None
        if triggerid:
            trigger = ZabbixTrigger.objects.filter(cliente_id=cliente_id, triggerid=triggerid).first()
            if trigger and trigger.hosts.exists():
                host = trigger.hosts.first()
                hostname = host.hostname
        else:
            triggerid = None

        ZabbixEvent.objects.update_or_create(
            eventid=ev["eventid"],
            defaults={
                "cliente_id": cliente_id,
                "name": ev.get("name"),
                "severity": int(ev.get("severity") or 0),
                "acknowledged": bool(int(ev.get("acknowledged") or 0)),
                "clock": _dt_from_epoch(ev["clock"]),
                "host": host,
                "hostid": host,
                "hostname": hostname,
                "raw": ev,
                "objectid": ev.get("objectid"),
                "objectname": ev.get("objectname"),
                "trigger":triggerid,
            },
        )


@transaction.atomic
def sync_history(cliente_id: int, itemids: list[str], time_from: datetime, time_till: datetime):
    """
    Sincroniza histórico (history.get) para uma lista de itemids em uma janela.
    OBS: history.get precisa do tipo (history=0/3/1/2/4) baseado em value_type.
    """
    client = get_client_for_cliente(cliente_id)

    items = list(ZabbixItem.objects.filter(cliente_id=cliente_id, itemid__in=itemids).select_related("host"))

    if not items:
        return

    # agrupamento por value_type (porque history.get exige o 'history' correto)
    by_type: dict[int, list[ZabbixItem]] = {}
    for it in items:
        by_type.setdefault(it.value_type, []).append(it)

    tf = int(time_from.replace(tzinfo=timezone.utc).timestamp())
    tt = int(time_till.replace(tzinfo=timezone.utc).timestamp())

    for value_type, typed_items in by_type.items():
        ids = [it.itemid for it in typed_items]

        rows = client.history_get(
            output="extend",
            history=value_type,  # 0 float, 1 char, 2 log, 3 uint, 4 text
            itemids=ids,
            time_from=tf,
            time_till=tt,
            sortfield="clock",
            sortorder="ASC",
            limit=50000,
        )

        # Mapa itemid -> item local
        local_item_map = {it.itemid: it for it in typed_items}

        # Bulk insert ignorando duplicados (mais rápido)
        to_create = []
        for r in rows:
            item = local_item_map.get(r["itemid"])
            if not item:
                continue
            to_create.append(
                ZabbixHistory(
                    cliente_id=cliente_id,
                    item=item,
                    clock=_dt_from_epoch(r["clock"]),
                    value=r.get("value"),
                )
            )

        # evita crash se vier muito grande (você pode chunkar depois)
        if to_create:
            ZabbixHistory.objects.bulk_create(to_create, ignore_conflicts=True, batch_size=2000)
