# -*- coding: utf-8 -*-
"""补全 CFTC deacot (Futures-Only legacy) 年度数据包 2017-2026。
用系统 curl 下载（Python urllib 对 CFTC 证书链 SSL 校验失败），带重试 + 完整性校验。"""
import os, sys, time, zipfile, subprocess

BASE = "https://www.cftc.gov/files/dea/history/"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Temp", "cot", "deacot")
os.makedirs(OUT, exist_ok=True)

YEARS = [2017, 2020, 2021, 2022, 2023, 2024, 2025, 2026]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def valid(path):
    if not os.path.exists(path):
        return False
    try:
        with zipfile.ZipFile(path) as z:
            return z.testzip() is None and len(z.namelist()) > 0
    except Exception:
        return False


def fetch(y):
    fn = f"deacot{y}.zip"
    path = os.path.join(OUT, fn)
    if valid(path):
        print(f"{fn}: already OK")
        return True
    url = BASE + fn
    for attempt in range(6):
        try:
            r = subprocess.run(
                ["curl", "-sSL", "-A", UA, "-o", path, "--max-time", "150", url],
                capture_output=True, timeout=180,
            )
            if valid(path):
                print(f"{fn}: OK {os.path.getsize(path)}B (attempt {attempt+1})")
                return True
            print(f"{fn}: corrupt/empty (attempt {attempt+1}), retry...")
        except Exception as e:
            print(f"{fn}: {type(e).__name__} (attempt {attempt+1})")
        time.sleep(3 * (attempt + 1))
    print(f"{fn}: FAILED")
    return False


def main():
    ok = True
    for y in YEARS:
        ok = fetch(y) and ok
        sys.stdout.flush()
    print("ALL OK" if ok else "SOME FAILED")


if __name__ == "__main__":
    main()
