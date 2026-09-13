# -*- coding: utf-8 -*-
"""在 Mac 上跑富途 MCP 的 OAuth 授权码 + PKCE 流程。
1. 生成 PKCE + 授权 URL（写入 /tmp/futu_auth_url.txt）
2. 起本地回调服务器 127.0.0.1:59407 等用户授权
3. 收到 code 后换 token，落地到 ~/.workbuddy/futu_credentials.json
"""
import base64, hashlib, secrets, json, os, sys
import urllib.parse, urllib.request
import http.server, socketserver, threading

CLIENT_ID = "918ffc1f-ee92-4b8c-8147-6939a1e223b0"
REDIRECT_URI = "http://127.0.0.1:59407/oauth/callback"
PORT = 59407
AUTH_ENDPOINT = "https://webapi.futunn.com/oauth2/authorize/confirm"
TOKEN_ENDPOINT = "https://webapi.futunn.com/oauth2/token"
SCOPE = "quote:read quote:write"
KEY = f"futu-mcp|{CLIENT_ID}"
OUT = os.path.expanduser("~/.workbuddy/futu_credentials.json")

verifier = secrets.token_urlsafe(64)
challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
state = secrets.token_urlsafe(16)

auth_url = AUTH_ENDPOINT + "?" + urllib.parse.urlencode({
    "response_type": "code", "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI, "scope": SCOPE,
    "code_challenge": challenge, "code_challenge_method": "S256",
    "state": state,
})
open("/tmp/futu_auth_url.txt", "w").write(auth_url)
print("AUTH_URL=" + auth_url, flush=True)


def exchange(code):
    body = urllib.parse.urlencode({
        "grant_type": "authorization_code", "code": code,
        "redirect_uri": REDIRECT_URI, "client_id": CLIENT_ID,
        "code_verifier": verifier,
    }).encode()
    req = urllib.request.Request(TOKEN_ENDPOINT, data=body, method="POST",
                                 headers={"Content-Type": "application/x-www-form-urlencoded",
                                          "Accept": "application/json"})
    try:
        tok = json.loads(urllib.request.urlopen(req, timeout=30).read())
    except urllib.error.HTTPError as e:
        print("TOKEN_HTTP_ERR " + str(e.code) + " " + e.read().decode("utf-8", "replace")[:500], flush=True)
        os._exit(1)
    if "access_token" not in tok:
        print("TOKEN_ERR " + json.dumps(tok, ensure_ascii=False)[:500], flush=True)
        os._exit(1)
    import datetime as dt
    exp = tok.get("expires_in")
    expires_at = int((dt.datetime.now().timestamp() + exp) * 1000) if exp else None
    cred = {
        "mcpOAuth": {KEY: {"accessToken": tok["access_token"],
                           "refreshToken": tok.get("refresh_token", ""),
                           "expiresAt": expires_at}},
        "mcpClientInfo": {KEY: {"client_id": CLIENT_ID}},
        "fetched_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(cred, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("TOKEN_OK expires_in=%s -> %s" % (exp, OUT), flush=True)
    print("ACCID=" + json.dumps(tok.get("accid_url") or tok.get("accid") or tok.get("scope", ""), ensure_ascii=False), flush=True)
    os._exit(0)


class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.urlparse(self.path)
        if q.path == "/oauth/callback":
            qs = urllib.parse.parse_qs(q.query)
            code = qs.get("code", [None])[0]
            err = qs.get("error", [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            if code:
                self.wfile.write(b"<h3>authorized, you may close this tab</h3>")
                threading.Thread(target=exchange, args=(code,), daemon=True).start()
            else:
                print("AUTH_ERR " + str(qs), flush=True)
                self.wfile.write(b"<h3>authorization failed</h3>")
        else:
            self.send_response(404); self.end_headers()

    def log_message(self, *a):
        pass


srv = socketserver.TCPServer(("127.0.0.1", PORT), H)
print("LISTENING " + REDIRECT_URI, flush=True)
srv.serve_forever()