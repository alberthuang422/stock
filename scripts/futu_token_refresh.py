# -*- coding: utf-8 -*-
"""刷新富途 MCP 的 OAuth access_token（refresh_token 授权，公共客户端）。

端点（来自 https://mcp.futunn.com/.well-known/oauth-authorization-server）：
  token_endpoint = https://webapi.futunn.com/oauth2/token
  token_endpoint_auth_methods_supported = ["none"]  → 无需 client_secret

用法：python scripts/futu_token_refresh.py [--dry]
"""
import json
import os
import sys
import shutil
import datetime as dt
import urllib.request
import urllib.parse

CRED = r"C:/Users/Administrator/.workbuddy/connectors/2e7b65ad-3a22-424a-a190-5066a615e2dc/.credentials.v3.json"
KEY = "futu-mcp|e818c1846070ff2a"
TOKEN_URL = "https://webapi.futunn.com/oauth2/token"


def refresh(dry=False):
    cfg = json.load(open(CRED, encoding="utf-8"))
    m = cfg["mcpOAuth"][KEY]
    cid = (cfg.get("mcpClientInfo", {}).get(KEY, {}) or {}).get("client_id") or m.get("client_id")
    if not cid:
        raise RuntimeError("未找到 client_id")
    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": m["refreshToken"],
        "client_id": cid,
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=body, method="POST",
                                 headers={"Content-Type": "application/x-www-form-urlencoded",
                                          "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            tok = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read().decode("utf-8", "replace")[:400])
        return None
    if "access_token" not in tok:
        print("刷新失败:", json.dumps(tok, ensure_ascii=False)[:400])
        return None
    exp = tok.get("expires_in")
    new_exp = int((dt.datetime.now().timestamp() + exp) * 1000) if exp else None
    print(f"新 access_token 前 8 位 = {tok['access_token'][:8]}...  expires_in={exp}s"
          f"  -> {dt.datetime.fromtimestamp(new_exp/1000).strftime('%Y-%m-%d %H:%M:%S') if new_exp else '?'}")
    if dry:
        return tok
    shutil.copy2(CRED, CRED + ".bak")
    if m["accessToken"] != tok["access_token"]:
        print("新 token 与旧 token 不同 -> 写入凭据文件")
        m["accessToken"] = tok["access_token"]
    if tok.get("refresh_token"):
        m["refreshToken"] = tok["refresh_token"]
    if new_exp:
        m["expiresAt"] = new_exp
    with open(CRED, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=1)
    print("已更新:", CRED, "（备份 .bak）")
    return tok


if __name__ == "__main__":
    refresh(dry="--dry" in sys.argv)
