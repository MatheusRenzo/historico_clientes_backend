from zabbix_integration.models import ZabbixConnection
from .zabbix_client import ZabbixClient


def get_client_for_cliente(cliente_id: int) -> ZabbixClient:
    conn = ZabbixConnection.objects.get(cliente_id=cliente_id, ativo=True)
    client = ZabbixClient(conn.base_url)
    client.login(conn.usuario, conn.senha)
    return client
