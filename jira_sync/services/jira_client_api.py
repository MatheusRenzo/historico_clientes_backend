import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import urljoin

class JiraAPIError(Exception):
    pass

class JiraClient:
    def __init__(self, base_url: str, email: str, api_token: str, timeout: int = 30):
        # base_url DEVE ser tipo: https://suaempresa.atlassian.net
        self.base_url = base_url.rstrip("/") + "/"
        self.auth = HTTPBasicAuth(email, api_token)
        self.timeout = timeout
        self.headers = {"Accept": "application/json"}

    def _get(self, path: str, params: dict | None = None):
        url = urljoin(self.base_url, path.lstrip("/"))
        print(f"GET {url} params={params}")

        r = requests.get(
            url,
            headers=self.headers,
            auth=self.auth,           # ✅ Basic Auth aqui
            params=params,
            timeout=self.timeout,
        )

        print(f"Response: {r.status_code} {r.text[:300]}")
        if r.status_code >= 400:
            raise JiraAPIError(f"Jira GET {url} -> {r.status_code}: {r.text[:500]}")
        return r.json()

    def iter_projects(self, start_at=0, max_results=50):
        while True:
            data = self._get("/rest/api/3/project/search", {
                "startAt": start_at,
                "maxResults": max_results,
            })
            values = data.get("values") or []
            for p in values:
                yield p

            start_at += len(values)
            total = data.get("total") or 0
            if not values or start_at >= total:
                break

    def iter_issues(self, jql: str, start_at=0, max_results=50):
        while True:
            data = self._get("/rest/api/3/search", {
                "jql": jql,
                "startAt": start_at,
                "maxResults": max_results,
            })
            issues = data.get("issues") or []
            for it in issues:
                yield it

            start_at += len(issues)
            total = data.get("total") or 0
            if not issues or start_at >= total:
                break
