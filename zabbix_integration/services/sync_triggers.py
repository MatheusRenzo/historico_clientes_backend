from zabbix_integration.models import ZabbixTrigger, ZabbixItem
from zabbix_integration.services.sync import get_client_for_cliente
from .utils import dt_from_epoch


PAGE_SIZE = 1000


def sync_triggers_enterprise(cliente_id: int):

    client = get_client_for_cliente(cliente_id)

    last_triggerid = 0
    total_processed = 0

    item_map = {
        i.itemid: i
        for i in ZabbixItem.objects.filter(cliente_id=cliente_id)
    }

    while True:

        triggers = client.trigger_get(
            output=[
                "triggerid",
                "description",
                "priority",
                "status",
                "lastchange",
            ],
            selectItems=["itemid"],
            sortfield="triggerid",
            sortorder="ASC",
            filter={"triggerid": f">{last_triggerid}"},
            limit=PAGE_SIZE,
        )

        if not triggers:
            break

        triggerids = [str(t["triggerid"]) for t in triggers]

        existing = {
            t.triggerid: t
            for t in ZabbixTrigger.objects.filter(
                cliente_id=cliente_id,
                triggerid__in=triggerids
            )
        }

        to_create = []
        to_update = []

        for trg in triggers:

            triggerid = str(trg["triggerid"])

            if triggerid in existing:
                obj = existing[triggerid]
                obj.description = trg.get("description")
                obj.priority = int(trg.get("priority") or 0)
                obj.status = (trg.get("status") == "0")
                obj.lastchange = dt_from_epoch(trg.get("lastchange"))
                to_update.append(obj)
            else:
                to_create.append(
                    ZabbixTrigger(
                        cliente_id=cliente_id,
                        triggerid=triggerid,
                        description=trg.get("description"),
                        priority=int(trg.get("priority") or 0),
                        status=(trg.get("status") == "0"),
                        lastchange=dt_from_epoch(trg.get("lastchange")),
                        raw=trg,
                    )
                )

        if to_create:
            ZabbixTrigger.objects.bulk_create(to_create, batch_size=1000)

        if to_update:
            ZabbixTrigger.objects.bulk_update(
                to_update,
                ["description", "priority", "status", "lastchange"],
                batch_size=1000,
            )

        last_triggerid = int(triggers[-1]["triggerid"])
        total_processed += len(triggers)

        print(f"Triggers processadas até {last_triggerid} | total {total_processed}")

    return {"total_triggers_processadas": total_processed}