import requests
import json
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
            "params": params if params is not None else {},
            "id": self._id,  # ✅ usa o contador
        }
        self._id += 1

        if auth and self.auth_token:
            payload["auth"] = self.auth_token

        #print("ZABBIX RPC:", json.dumps(payload, ensure_ascii=False)[:2000])
        #print(f"Calling Zabbix API at {self.endpoint} with method {method} and params {params}")
        r = requests.post(self.endpoint, json=payload, timeout=self.timeout)
        #print(r)
        #print(f"ZABBIX RESPONSE (status {r.status_code}): {r.text[:2000]}")  # ✅ log da resposta
        # ✅ log útil antes de estourar
        if r.status_code >= 400:
            print("ZABBIX HTTP ERROR:", r.status_code, r.text[:2000])
            raise ZabbixAPIError(f"HTTP {r.status_code}: {r.text[:500]}")

        # ✅ protege contra resposta não-JSON
        try:
            data = r.json()
        except Exception:
            print("ZABBIX NON-JSON RESPONSE:", r.text[:2000])
            raise ZabbixAPIError(f"Resposta não-JSON do Zabbix: {r.text[:500]}")

        if "error" in data:
            print("ZABBIX RPC ERROR:", data["error"])
            raise ZabbixAPIError(f"{data['error']}")

        return data.get("result")


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

    def template_get(self, **kwargs):
        return self._call("template.get", kwargs)

    def user_get(self, **kwargs):
        return self._call("user.get", kwargs)

    def sla_get(self, **kwargs):
        return self._call("sla.get", kwargs)

    def sla_getsli(self, **kwargs):
        return self._call("sla.getsli", kwargs)

    def problem_get(self, **kwargs):
        return self._call("problem.get", kwargs)

    def event_get(self, **kwargs):
        return self._call("event.get", kwargs)

    def alert_get(self, **kwargs):
        return self._call("alert.get", kwargs)
