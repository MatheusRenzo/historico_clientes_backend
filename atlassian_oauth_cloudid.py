import json
import secrets
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, urlencode

import requests

# ========= CONFIGURE AQUI =========
CLIENT_ID = "hgUg1gDF27Zz0w6ZNVnSeSafi4vBNkzt"
CLIENT_SECRET = "ATOA5Hn0sOGWP5ZAeKqAC1EL5kpDwwO4FiG_wL3Dk2PAdU0CgR5So5YqGop1CMP_rGSWC7E1DE44"
REDIRECT_URI = "http://localhost:3000/callback"
SCOPES = ["read:jira-user", "read:jira-work"]  # adicione write:jira-work se precisar escrever
# ==================================

AUTH_URL = "https://auth.atlassian.com/authorize"
TOKEN_URL = "https://auth.atlassian.com/oauth/token"
ACCESSIBLE_RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"


def build_authorize_url(state: str) -> str:
    # Atlassian aceita scopes separados por espaço
    params = {
        "audience": "api.atlassian.com",
        "client_id": CLIENT_ID,
        "scope": " ".join(SCOPES),
        "redirect_uri": REDIRECT_URI,
        "state": state,
        "response_type": "code",
        "prompt": "consent",
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def exchange_code_for_token(code: str) -> dict:
    payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    r = requests.post(TOKEN_URL, json=payload, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(
            f"Falha ao trocar code por token. Status={r.status_code}\nBody:\n{r.text}"
        )
    return r.json()


def get_accessible_resources(access_token: str) -> list:
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    r = requests.get(ACCESSIBLE_RESOURCES_URL, headers=headers, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(
            f"Falha ao buscar accessible-resources. Status={r.status_code}\nBody:\n{r.text}"
        )
    return r.json()


class CallbackHandler(BaseHTTPRequestHandler):
    # Vamos armazenar o code/state aqui
    code = None
    state = None
    error = None

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            return

        qs = parse_qs(parsed.query)
        if "error" in qs:
            CallbackHandler.error = qs.get("error", [""])[0]
        CallbackHandler.code = qs.get("code", [None])[0]
        CallbackHandler.state = qs.get("state", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        if CallbackHandler.code:
            self.wfile.write(
                b"<h1>OK</h1><p>Code recebido. Pode voltar para o console.</p>"
            )
        else:
            self.wfile.write(
                b"<h1>Erro</h1><p>Code nao recebido. Veja o console.</p>"
            )

    def log_message(self, format, *args):
        # silencia logs HTTP no console (opcional)
        return


def main():
    if "COLE_SEU_CLIENT_ID" in CLIENT_ID or "COLE_SEU_CLIENT_SECRET" in CLIENT_SECRET:
        print("⚠️ Edite o arquivo e preencha CLIENT_ID e CLIENT_SECRET.")
        return

    state = secrets.token_urlsafe(16)
    url = build_authorize_url(state)

    print("1) Abra esta URL no navegador e autorize o app:")
    print(url)
    print("\n(Se quiser, vou abrir automaticamente no navegador agora.)\n")

    try:
        webbrowser.open(url)
    except Exception:
        pass

    print(f"2) Aguardando callback em {REDIRECT_URI} ...")

    server = HTTPServer(("localhost", 3000), CallbackHandler)

    # atende requests até receber o code
    while CallbackHandler.code is None and CallbackHandler.error is None:
        server.handle_request()

    server.server_close()

    if CallbackHandler.error:
        print(f"❌ OAuth retornou error: {CallbackHandler.error}")
        return

    if CallbackHandler.state != state:
        print("❌ State não confere. Possível problema de segurança (CSRF).")
        print(f"Esperado: {state}")
        print(f"Recebido: {CallbackHandler.state}")
        return

    code = CallbackHandler.code
    print(f"\n✅ Code recebido:\n{code}\n")

    print("3) Trocando code por access_token...")
    token_data = exchange_code_for_token(code)

    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in")

    print("\n✅ Token obtido!")
    print(f"expires_in: {expires_in} segundos")
    print(f"refresh_token presente? {'sim' if refresh_token else 'nao'}")

    print("\n4) Buscando cloudId via accessible-resources...")
    resources = get_accessible_resources(access_token)

    print("\n✅ Accessible resources:")
    print(json.dumps(resources, indent=2, ensure_ascii=False))

    if resources:
        print("\n➡️ cloudId(s) encontrado(s):")
        for r in resources:
            print(f"- name: {r.get('name')} | cloudId: {r.get('id')} | url: {r.get('url')}")
        print("\nPronto. Use assim (exemplo):")
        first = resources[0]
        print(
            f"https://api.atlassian.com/ex/jira/{first.get('id')}/rest/api/3/myself"
        )


if __name__ == "__main__":
    main()
