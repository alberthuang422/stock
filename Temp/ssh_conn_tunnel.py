# -*- coding: utf-8 -*-
"""临时 SSH-over-HTTP-CONNECT 隧道：127.0.0.1:2222 -> ssh.github.com:443 (via 127.0.0.1:7890)
仅用于本次 git push 绕开直连干扰，用完即删。不修改任何项目文件。
"""
import select
import socket
import sys
import threading

PROXY = ("127.0.0.1", 7890)
TARGET = ("ssh.github.com", 443)
LISTEN = ("127.0.0.1", 2222)


def handle(client):
    proxy = None
    try:
        proxy = socket.create_connection(PROXY, timeout=15)
        req = "CONNECT %s:%d HTTP/1.1\r\nHost: %s:%d\r\n\r\n" % (TARGET[0], TARGET[1], TARGET[0], TARGET[1])
        proxy.sendall(req.encode("ascii"))
        resp = proxy.recv(4096)
        if b" 200 " not in resp.split(b"\r\n", 1)[0] + b" ":
            return
        client.setblocking(False)
        proxy.setblocking(False)
        while True:
            r, _, _ = select.select([client, proxy], [], [], 5)
            if not r:
                continue
            for s in r:
                data = s.recv(65536)
                if not data:
                    raise ConnectionError("closed")
                (proxy if s is client else client).sendall(data)
    except Exception:
        pass
    finally:
        for s in (client, proxy):
            try:
                s.close()
            except Exception:
                pass


def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(LISTEN)
    srv.listen(16)
    print("tunnel listening %s:%d -> %s:%d" % (LISTEN[0], LISTEN[1], TARGET[0], TARGET[1]), flush=True)
    while True:
        c, _ = srv.accept()
        threading.Thread(target=handle, args=(c,), daemon=True).start()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)