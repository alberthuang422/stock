#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将转换好的 blocks JSON 创建为 Notion 页面
用法: python notion_create_page.py <blocks.json> <page_title> [<parent_page_id>]
- 若传 parent_page_id, 在指定页面下创建子页; 否则搜索名为 "WorkBuddy 报告" 或已共享页面作为父页。
- 块数量 >100 时分批 PATCH children (每次最多 100)。
"""
import json
import os
import subprocess
import sys
import urllib.request

NOTION_KEY = open(os.path.expanduser("~/.config/notion/api_key")).read().strip()
NOTION_VERSION = "2025-09-03"
BASE = "https://api.notion.com/v1"


def api(method, path, payload=None):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header("Authorization", f"Bearer {NOTION_KEY}")
    req.add_header("Notion-Version", NOTION_VERSION)
    req.add_header("Content-Type", "application/json")
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    try:
        with urllib.request.urlopen(req, data=data) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"API {method} {path} -> {e.code}: {body[:500]}")
        sys.exit(1)


def find_parent():
    """找一个可用的父页面: 优先名为 WorkBuddy 报告的页面, 否则任意页面。"""
    r = api("POST", "/search", {"page_size": 100})
    results = r.get("results", [])
    pages = [x for x in results if x.get("object") == "page"]
    if not pages:
        return None
    for p in pages:
        title = "".join(t.get("plain_text", "") for t in p.get("properties", {}).get("title", {}).get("title", []))
        if "WorkBuddy" in title or "报告" in title:
            return p["id"]
    return pages[0]["id"]


def main():
    blocks_path, title = sys.argv[1], sys.argv[2]
    parent_id = sys.argv[3] if len(sys.argv) > 3 else find_parent()
    if not parent_id:
        print("NO_PARENT: 没有找到已共享的父页面, 请先在 Notion 中把页面 Connect 到 workbuddy 集成")
        sys.exit(2)

    blocks = json.load(open(blocks_path, encoding="utf-8"))
    # 页面创建时最多 100 个子块
    first, rest = blocks[:100], blocks[100:]
    page = api("POST", "/pages", {
        "parent": {"page_id": parent_id},
        "properties": {"title": {"title": [{"text": {"content": title}}]}},
        "children": first,
    })
    pid = page["id"]
    print(f"PAGE_CREATED: {pid} parent={parent_id} blocks_in_first={len(first)}")
    # 追加剩余块, 每批 100
    for i in range(0, len(rest), 100):
        api("PATCH", f"/blocks/{pid}/children", {"children": rest[i:i + 100]})
        print(f"APPENDED: {i + len(rest[i:i + 100])}/{len(blocks)}")
    print(f"DONE: 共 {len(blocks)} 块 -> https://notion.so/{pid.replace('-', '')}")


if __name__ == "__main__":
    main()