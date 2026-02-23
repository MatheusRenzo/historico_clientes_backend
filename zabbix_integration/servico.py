from __future__ import annotations

from typing import Any

from zabbix_integration.services.sync import get_client_for_cliente
from .models import ZabbixHost, ZabbixItem, ZabbixTrigger, ZabbixEvent
from datetime import datetime, timedelta, timezone as dt_timezone

def sync_hosts(cliente_id: int, client) -> dict[str, Any]:
    result = client.host_get(
        output=["hostid", "host", "name", "status"],
        selectInterfaces=["ip", "dns", "port"],
    )

    saved = 0
    for h in result:
        interfaces = h.get("interfaces") or []
        i0 = interfaces[0] if interfaces else {}

        defaults = {
            "host": h.get("host"),
            "name": h.get("name"),
            "status": int(h.get("status") or 0),
            "ip": i0.get("ip") or None,
            "dns": i0.get("dns") or None,
            "port": i0.get("port") or None,
            "raw": h,  # ✅ payload inteiro do Zabbix
        }

        ZabbixHost.objects.update_or_create(
            cliente_id=cliente_id,
            hostid=str(h["hostid"]),
            #defaults=defaults,
            hostname=h.get("host"),
            nome=h.get("name"),
            status=int(h.get("status") or 0), 
            ip=h.get("ip"),
        )
        saved += 1

    return {"count": len(result), "saved": saved}


def _dt_from_epoch(ts: str | int):
    return datetime.fromtimestamp(int(ts), tz=dt_timezone.utc)

def sync_triggers(cliente_id: int, hostids: list[str] | None = None) -> dict[str, Any]:
    client = get_client_for_cliente(cliente_id)
    #puxa triggers + hosts + items
    triggers = client.trigger_get(
        output=["triggerid", 
                "description", 
                "expression", 
                "recovery_expression",
                "priority", 
                "status", 
                "value",
                "state",
                "lastchange",
                "error",
                "comments",
                "url",
                "url_name",
                "manual_close",
                "recovery_mode",
                "type",
                "templateid",
                "flags",
                "opdata",
        ],
        params={"hostids": hostids or []},
        selectHosts=["hostid","host","name"],
        selectItems=["itemid","name","key_"],
        sortfield=["triggerid"],
        limit=100,
    )
    #print(f"Fetched {len(triggers)} triggers from Zabbix  {triggers}") 
    saved = 0
    for tr in triggers:

        #items
        items = tr.get("items") or []
        print(f"Itens {items} has {len(items)} items")
        for it in items:
            print(f"Trigger {tr['triggerid']} has item {it['itemid']} ({it.get('key_')})")
            zb_item = ZabbixItem.objects.filter(itemid=it["itemid"]).first()
            print(f"Found local item {zb_item} for trigger {tr['triggerid']}")  

        #print(f"Processing trigger {tr}")
        trigger_obj, _ = ZabbixTrigger.objects.update_or_create(
            cliente_id=cliente_id,
            triggerid=str(tr["triggerid"]),
            defaults={
                "descricao": tr.get("description") or "",
                "prioridade": int(tr.get("priority") or 0),
                "status": str(tr.get("status") or "0"),
                "ultima_alteracao": _dt_from_epoch(tr.get("lastchange") or 0),
                "raw": tr,
                "items": zb_item,
            },
        )
        saved += 1

        # 3) vincula hosts (M2M)
        #host_ids = []
        #hosts = tr.get("hosts") or []
        #if hosts:
        #    for h in hosts:
        #        h_local = local_hosts.get(str(h.get("hostid")))
        #        if h_local:
        #            host_ids.append(h_local.id)

        #if host_ids:
        #    trigger_obj.hosts.set(host_ids)
        #else:
        #    trigger_obj.hosts.clear()

    return {"count": len(triggers), "saved": saved}

def sync_events(cliente_id: int, since_hours: int = 24):
    client = get_client_for_cliente(cliente_id)

    time_from = int((datetime.now(tz=dt_timezone.utc) - timedelta(hours=since_hours)).timestamp())

    events = client.event_get(
        output=["eventid", "clock", "value", "name", "severity", "acknowledged", "objectid"],
        source=0,  # ✅ trigger events
        object=148958,  # ✅ trigger
        #objectids=["148958", "138328"],
        time_from=time_from,
        sortfield=["clock"],
        sortorder="DESC",
        limit=2000,
    )

    # mapas locais
    local_triggers = {
        t.triggerid: t
        for t in ZabbixTrigger.objects.filter(cliente_id=cliente_id)
    }
    local_hosts = {
        str(h.hostid): h
        for h in ZabbixHost.objects.filter(cliente_id=cliente_id)
    }

    # Para ligar host ao evento: pega o host principal da trigger (ou nenhum)
    for ev in events:
        trig_id = str(ev.get("objectid") or "")
        trig = local_triggers.get(trig_id)

        host = None
        if trig:
            # se M2M: escolha o primeiro host como "principal" pro evento
            first = trig.hosts.first()
            host = first

        ZabbixEvent.objects.update_or_create(
            eventid=str(ev["eventid"]),
            defaults={
                "cliente_id": cliente_id,
                "trigger": trig,
                "host": host,
                "name": ev.get("name"),
                "severity": int(ev.get("severity") or 0),
                "value": int(ev.get("value") or 0),
                "acknowledged": bool(int(ev.get("acknowledged") or 0)),
                "clock": _dt_from_epoch(ev["clock"]),
                "raw": ev,
            },
        )