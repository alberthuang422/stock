# -*- coding: utf-8 -*-
"""Bark 推送工具（要点推送用）

密钥读取优先级：环境变量 BARK_KEY > ~/.workbuddy/bark_key.txt
用法：
  python scripts/bark_push.py "标题" "正文" [group]
或作为模块：
  from bark_push import push; push("标题","正文")
"""
import os
import sys
import json
import urllib.request

DEFAULT_GROUP = "stock"


def _key():
    k = os.environ.get("BARK_KEY")
    if k:
        return k.strip()
    p = os.path.join(os.path.expanduser("~"), ".workbuddy", "bark_key.txt")
    if os.path.exists(p):
        return open(p, encoding="utf-8").read().strip()
    raise RuntimeError("未找到 Bark 密钥（BARK_KEY 环境变量或 ~/.workbuddy/bark_key.txt）")


def push(title, body, group=DEFAULT_GROUP, level="active", icon=None, url=None, timeout=20):
    """发送 Bark 推送。返回服务端 JSON 响应。"""
    payload = {"title": title, "body": body, "group": group, "level": level}
    if icon:
        payload["icon"] = icon
    if url:
        payload["url"] = url
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        "https://api.day.app/" + _key(),
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


def main():
    if len(sys.argv) < 3:
        print('usage: bark_push.py "标题" "正文" [group]')
        sys.exit(1)
    title, body = sys.argv[1], sys.argv[2]
    group = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_GROUP
    print(push(title, body, group))


if __name__ == "__main__":
    main()
