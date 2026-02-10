import requests
from urllib.parse import urljoin


class ZabbixAPIError(Exception):
    pass


class ZabbixClient:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout
        self.auth_token = None
        self._id = 1

    @property
    def endpoint(self) -> str:
        # Zabbix JSON-RPC endpoint padrão
        return urljoin(self.base_url, "api_jsonrpc.php")

    def _call(self, method: str, params: dict | list | None = None, auth: bool = True):
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self._id,
        }
        self._id += 1

        if auth and self.auth_token:
            payload["auth"] = self.auth_token

        r = requests.post(self.endpoint, json=payload, timeout=self.timeout)
        if r.status_code >= 400:
            raise ZabbixAPIError(f"HTTP {r.status_code}: {r.text[:500]}")

        data = r.json()
        if "error" in data:
            raise ZabbixAPIError(f"{data['error']}")

        return data["result"]

    def login(self, user: str, password: str) -> str:
        token = self._call("user.login", {"username": user, "password": password}, auth=False)
        self.auth_token = token
        return token

    # Métodos úteis (exemplos)
    def host_get(self, **kwargs):
        # kwargs pode incluir: output, selectInterfaces, filter, search, groupids, hostids...
        return self._call("host.get", kwargs)

    def item_get(self, **kwargs):
        return self._call("item.get", kwargs)

    def trigger_get(self, **kwargs):
        return self._call("trigger.get", kwargs)

    def problem_get(self, **kwargs):
        # Zabbix 6+ costuma usar problem.get
        return self._call("problem.get", kwargs)

    def history_get(self, **kwargs):
        return self._call("history.get", kwargs)

    def event_get(self, **kwargs):
        return self._call("event.get", kwargs)
