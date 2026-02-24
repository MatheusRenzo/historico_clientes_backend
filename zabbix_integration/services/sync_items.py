from django.utils import timezone
from zabbix_integration.models import ZabbixItem, ZabbixHost
from zabbix_integration.services.sync import get_client_for_cliente
from .utils import dt_from_epoch


PAGE_SIZE = 2000


def sync_items_enterprise(cliente_id: int):

    client = get_client_for_cliente(cliente_id)

    last_itemid = 0
    total_processed = 0

    host_map = {
        h.hostid: h
        for h in ZabbixHost.objects.filter(cliente_id=cliente_id)
    }

    while True:

        items = client.item_get(
            output=[
                "itemid",
                "hostid",
                "name",
                "key_",
                "value_type",
                "units",
                "delay",
                "lastvalue",
                "lastclock",
                "status",
            ],
            sortfield="itemid",
            sortorder="ASC",
            filter={"itemid": f">{last_itemid}"},
            limit=PAGE_SIZE,
        )

        if not items:
            break

        itemids = [str(it["itemid"]) for it in items]

        existing = {
            obj.itemid: obj
            for obj in ZabbixItem.objects.filter(
                cliente_id=cliente_id,
                itemid__in=itemids
            )
        }

        to_create = []
        to_update = []

        for it in items:

            itemid = str(it["itemid"])
            host = host_map.get(str(it["hostid"]))

            if not host:
                continue

            if itemid in existing:
                obj = existing[itemid]
                obj.name = it.get("name")
                obj.lastvalue = it.get("lastvalue")
                obj.lastclock = dt_from_epoch(it.get("lastclock"))
                obj.enabled = (it.get("status") == "0")
                to_update.append(obj)
            else:
                to_create.append(
                    ZabbixItem(
                        cliente_id=cliente_id,
                        itemid=itemid,
                        host=host,
                        name=it.get("name"),
                        key=it.get("key_"),
                        value_type=int(it.get("value_type") or 0),
                        units=it.get("units"),
                        delay=it.get("delay"),
                        lastvalue=it.get("lastvalue"),
                        lastclock=dt_from_epoch(it.get("lastclock")),
                        enabled=(it.get("status") == "0"),
                        raw=it,
                    )
                )

        if to_create:
            ZabbixItem.objects.bulk_create(to_create, batch_size=1000)

        if to_update:
            ZabbixItem.objects.bulk_update(
                to_update,
                ["name", "lastvalue", "lastclock", "enabled"],
                batch_size=1000
            )

        last_itemid = int(items[-1]["itemid"])
        total_processed += len(items)

        print(f"Processados até itemid {last_itemid} | total {total_processed}")

    return {"total_items_processados": total_processed}