from datetime import datetime
from zabbix_integration.services.sync import get_client_for_cliente
from zabbix_integration.models import ZabbixHost, ZabbixTrigger, ZabbixProblem


def sync_level1(cliente_id: int):
    client = get_client_for_cliente(cliente_id)

    # 1️⃣ HOSTS
    hosts = client.host_get(
        output=["hostid", "host", "name", "status"],
        selectInterfaces=["ip"]
    )

    for h in hosts:
        ZabbixHost.objects.update_or_create(
            cliente_id=cliente_id,
            hostid=h["hostid"],
            defaults={
                "hostname": h["host"],
                "nome": h["name"],
                "status": h["status"],
                "ip": h["interfaces"][0]["ip"] if h.get("interfaces") else None,
            }
        )

    # 2️⃣ TRIGGERS
    triggers = client.trigger_get(
        output=["triggerid", "description", "priority", "status", "lastchange"]
    )

    for t in triggers:
        ZabbixTrigger.objects.update_or_create(
            cliente_id=cliente_id,
            triggerid=t["triggerid"],
            defaults={
                "descricao": t["description"],
                "prioridade": t["priority"],
                "status": t["status"],
                "ultima_alteracao": datetime.fromtimestamp(int(t["lastchange"])),
            }
        )

    # 3️⃣ PROBLEMAS
    problems = client.problem_get(output="extend", recent=True)

    for p in problems:
        ZabbixProblem.objects.update_or_create(
            cliente_id=cliente_id,
            eventid=p["eventid"],
            defaults={
                "nome": p["name"],
                "severidade": p["severity"],
                "inicio": datetime.fromtimestamp(int(p["clock"])),
                "reconhecido": bool(int(p["acknowledged"])),
            }
        )
