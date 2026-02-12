from django.db import transaction
from zabbix_integration.services.sync import get_client_for_cliente
from zabbix_integration.models import ZabbixTemplate, ZabbixUser, ZabbixSLA


@transaction.atomic
def sync_templates(cliente_id: int):
    client = get_client_for_cliente(cliente_id)

    # Templates e alguns campos úteis
    templates = client.template_get(
        output=["templateid", "name"],
        sortfield="name",
    )

    for t in templates:
        ZabbixTemplate.objects.update_or_create(
            cliente_id=cliente_id,
            templateid=t["templateid"],
            defaults={"name": t.get("name") or ""},
        )


@transaction.atomic
def sync_users(cliente_id: int):
    client = get_client_for_cliente(cliente_id)

    users = client.user_get(
        output=["userid", "username", "name", "surname", "roleid"],
        selectUsrgrps=["usrgrpid", "name"],
        sortfield="username",
    )

    for u in users:
        ZabbixUser.objects.update_or_create(
            cliente_id=cliente_id,
            userid=u["userid"],
            defaults={
                "username": u.get("username") or "",
                "name": u.get("name"),
                "surname": u.get("surname"),
                "roleid": u.get("roleid"),
                "user_groups": u.get("usrgrps"),
            },
        )


@transaction.atomic
def sync_sla(cliente_id: int):
    client = get_client_for_cliente(cliente_id)

    # ⚠️ Pode variar por versão. Mantemos raw para compatibilidade.
    slas = client.sla_get(
        output="extend",
        sortfield="name",
    )

    for s in slas:
        ZabbixSLA.objects.update_or_create(
            cliente_id=cliente_id,
            slaid=s.get("slaid") or s.get("id") or "",  # compat
            defaults={
                "name": s.get("name") or "",
                "period": int(s["period"]) if s.get("period") is not None else None,
                "slo": s.get("slo"),
                "status": int(s["status"]) if s.get("status") is not None else None,
                "raw": s,
            },
        )
