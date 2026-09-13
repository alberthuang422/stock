# -*- coding: utf-8 -*-
"""
富途 MCP OAuth2 授权（quotes 只读 scope）—— 本机 macOS 版。

背景：历史富途拉数脚本读的是 Windows 路径 C:/Users/Administrator/... 凭据，
      Mac 上从未做过富途授权。本脚本按富途 OAuth 标准（RFC7591 动态客户端注册
      + PKCE S256）在浏览器里完成一次授权，把 token 存到 Mac 本地，供后续
      fetch_ho_contracts 等脚本复用。

用法：
  python scripts/futu_oauth.py      # 首次：弹浏览器授权
  python scripts/futu_oauth.py --refresh   # 仅用 refresh_token 续期（不弹窗）

凭据输出：~/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/futu_credentials.json
"""
import json
import os
import sys
import time
import secrets
import hashlib
import base64
import urllib.parse
import urllib.request
import http.server
import datetime as dt

CLIENT_ID = "d7330d1e-16d5-413c-814a-c100f960f9ac"
REDIRECT_URI = "http://127.0.0.1:48080/callback"
PORT = 48080
TOKEN_URL = "https://webapi.futunn.com/oauth2/token"
AUTH_URL = "https://webapi.futunn.com/oauth2/authorize/confirm"
CRED = os.path.expanduser(
    "~/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/futu_credentials.json")


def b64url(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def save(tok, code_verifier=None):
    exp = tok.get("expires_in")
    expires_at = int((dt.datetime.now().timestamp() + exp) * 1000) if exp else None
    cred = {
        "client_id": CLIENT_ID,
        "access_token": tok["access_token"],
        "refresh_token": tok.get("refresh_token"),
        "expires_at": expires_at,
        "token_endpoint": TOKEN_URL,
        "mcp_endpoint": "https://mcp.futunn.com/mcp",
        "scope": tok.get("scope", "quote:read"),
        "redirect_uri": REDIRECT_URI,
    }
    os.makedirs(os.path.dirname(CRED), exist_ok=True)
    json.dump(cred, open(CRED, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n已保存凭据: {CRED}")
    print(f"  access_token 前 10 位 = {tok['access_token'][:10]}...  "
          f"刷新时刻 = {dt.datetime.fromtimestamp(expires_at/1000).strftime('%Y-%m-%d %H:%M:%S') if expires_at else '?'}")


def refresh():
    cred = json.load(open(CRED, encoding="utf-8"))
    rt = cred.get("refresh_token")
    if not rt:
        print("无 refresh_token，需重新授权"); return 1
    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": rt,
        "client_id": cred["client_id"],
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=body, method="POST",
                                 headers={"Content-Type": "application/x-www-form-urlencoded",
                                          "Accept": "application/json"})
    tok = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
    if "access_token" not in tok:
        print("刷新失败:", json.dumps(tok, ensure_ascii=False)[:300]); return 1
    save(tok)
    return 0


class Callback(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.urlparse(self.path)
        if q.path == "/callback":
            code = urllib.parse.parse_qs(q.query).get("code", [None])[0]
            err = urllib.parse.parse_qs(q.query).get("error", [None])[0]
            self.server.auth_code = code
            self.server.auth_err = err
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            msg = "✅ 授权成功，可以关闭本页" if code else f"❌ 授权失败: {err}"
            self.wfile.write(f"<html><body style='font-family:sans-serif;padding:40px;'>{msg}</body></html>".encode())
        else:
            self.send_response(404); self.end_headers()

    def log_message(self, *a):
        pass


def authorize():
    verifier = secrets.token_urlsafe(64)
    challenge = b64url(hashlib.sha256(verifier.encode()).digest())
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "quote:read",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    url = AUTH_URL + "?" + urllib.parse.urlencode(params)
    print("授权 URL:\n" + url + "\n")

    srv = http.server.HTTPServer(("127.0.0.1", PORT), Callback)
    srv.auth_code = None
    srv.auth_err = None
    srv.timeout = 1

    print("正在打开浏览器，请登录富途账号并点击授权…")
    os.system(f'open "{url}"')

    deadline = time.time() + 300
    while srv.auth_code is None and srv.auth_err is None and time.time() < deadline:
        srv.handle_request()

    if srv.auth_err:
        print("授权被拒绝:", srv.auth_err); return 1
    if srv.auth_code is None:
        print("5 分钟超时未收到回调"); return 1

    code = srv.auth_code
    body = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": verifier,
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=body, method="POST",
                                 headers={"Content-Type": "application/x-www-form-urlencoded",
                                          "Accept": "application/json"})
    tok = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
    if "access_token" not in tok:
        print("换 token 失败:", json.dumps(tok, ensure_ascii=False)[:300]); return 1
    save(tok)
    return 0


if __name__ == "__main__":
    if "--refresh" in sys.argv:
        sys.exit(refresh())
    sys.exit(authorize())