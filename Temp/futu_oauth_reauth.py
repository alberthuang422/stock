# -*- coding: utf-8 -*-
"""One-shot Futu MCP OAuth re-auth: register client -> local callback server -> open browser -> exchange code -> write WorkBuddy credentials."""
import base64
import hashlib
import json
import secrets
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

CRED_PATH = r"C:/Users/Administrator/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/.credentials.v3.json"
CRED_KEY = "futu-mcp|e818c1846070ff2a"
REDIRECT_URI = "http://127.0.0.1:59407/oauth/callback"
RESOURCE = "https://mcp.futunn.com/mcp"
SCOPE = "quote:read quote:write"

result = {}


def b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def post_json(url, payload=None, form=None):
    import subprocess
    cmd = ["curl", "-s", "--max-time", "25", "-X", "POST", url]
    if form is not None:
        cmd += ["-H", "Content-Type: application/x-www-form-urlencoded",
                "-d", urllib.parse.urlencode(form)]
    else:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(payload)]
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8").stdout
    return json.loads(out)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        if parsed.path == "/oauth/callback":
            if "code" in qs:
                result["code"] = qs["code"][0]
                result["state"] = qs.get("state", [None])[0]
                body = b"Authorization complete. You can close this tab."
            else:
                result["error"] = str(qs)
                body = b"Authorization failed - see console."
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *a):
        pass


def main():
    verifier = b64url(secrets.token_bytes(32))
    challenge = b64url(hashlib.sha256(verifier.encode()).digest())
    state = secrets.token_hex(16)

    reg = post_json("https://webapi.futunn.com/oauth2/register", {
        "client_name": "workbuddy-local-reauth",
        "redirect_uris": [REDIRECT_URI],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
    })
    client_id = reg["client_id"]
    print("CLIENT_ID=" + client_id, flush=True)

    auth_url = "https://webapi.futunn.com/oauth2/authorize/confirm?" + urllib.parse.urlencode({
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "resource": RESOURCE,
    })
    print("AUTH_URL=" + auth_url, flush=True)

    srv = HTTPServer(("127.0.0.1", 59407), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    import subprocess
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Start-Process", "-Uri", auth_url])
    print("BROWSER_OPENED waiting for callback (300s)...", flush=True)

    t0 = time.time()
    while time.time() - t0 < 300:
        if "code" in result or "error" in result:
            break
        time.sleep(0.5)
    srv.shutdown()
    if "code" not in result:
        print("FAIL no code: " + str(result.get("error", "timeout")), flush=True)
        return

    tok = post_json("https://webapi.futunn.com/oauth2/token", form={
        "grant_type": "authorization_code",
        "code": result["code"],
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": verifier,
        "resource": RESOURCE,
    })
    if "access_token" not in tok:
        print("FAIL token exchange: " + json.dumps(tok)[:300], flush=True)
        return
    print("TOKEN_OK expires_in=%s scope=%s" % (tok.get("expires_in"), tok.get("scope")), flush=True)

    with open(CRED_PATH, encoding="utf-8") as f:
        d = json.load(f)
    import shutil
    shutil.copy2(CRED_PATH, CRED_PATH + ".bak")
    old = d["mcpOAuth"][CRED_KEY]
    d["mcpOAuth"][CRED_KEY] = {
        "serverName": old.get("serverName", "futu-mcp"),
        "serverUrl": old.get("serverUrl", RESOURCE),
        "tokenType": tok.get("token_type", "Bearer"),
        "accessToken": tok["access_token"],
        "refreshToken": tok.get("refresh_token", old["refreshToken"]),
        "expiresAt": int((time.time() + int(tok.get("expires_in", 86400))) * 1000),
        "scope": tok.get("scope", SCOPE),
    }
    d["mcpClientInfo"][CRED_KEY] = {"client_id": client_id, "redirect_uris": [REDIRECT_URI]}
    with open(CRED_PATH, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    print("CREDENTIALS_WRITTEN", flush=True)


if __name__ == "__main__":
    main()
