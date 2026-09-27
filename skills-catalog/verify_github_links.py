#!/usr/bin/env python3
"""تست همهٔ لینک‌های گیتهاب؛ ۴۰۴ها به ریشهٔ ریپو برمی‌گردند، ریپوی مرده خالی می‌شود."""
import json, os, time, threading, collections
import concurrent.futures as cf
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'skills-index-flat.jsonl')
S = requests.Session()
S.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) Chrome/131.0'})
_lock, _next = threading.Lock(), [0.0]

def head(url):
    with _lock:
        n = max(_next[0], time.monotonic()); _next[0] = n + 0.17
    t = n - time.monotonic()
    if t > 0: time.sleep(t)
    for i in range(2):
        try:
            r = S.head(url, timeout=15, allow_redirects=True)
            if r.status_code == 429: time.sleep(5); continue
            return r.status_code
        except requests.RequestException:
            time.sleep(2)
    return 0

def main():
    rows = [json.loads(l) for l in open(SRC, encoding='utf-8')]
    urls = sorted({r['github'] for r in rows if r.get('github', '').startswith('http')})
    print(f"URL یکتا: {len(urls):,}", flush=True)
    code = {}
    with cf.ThreadPoolExecutor(8) as ex:
        for i, (u, c) in enumerate(zip(urls, ex.map(head, urls)), 1):
            code[u] = c
            if i % 500 == 0: print(f"  {i:,}/{len(urls):,}", flush=True)
    stat = collections.Counter(code.values())
    print("وضعیت:", dict(stat), flush=True)

    fixed_root = dead = 0
    for r in rows:
        u = r.get('github', '')
        if not u.startswith('http'): continue
        if code.get(u) == 200: continue
        base = u.split('/tree/')[0]
        if base != u and code.get(base, head(base)) == 200:
            r['github'] = base; fixed_root += 1
        elif code.get(base) == 404:
            r['github'] = ''; dead += 1
    print(f"اصلاح‌شده به ریشهٔ ریپو: {fixed_root:,} | ریپوی مرده/خالی‌شده: {dead:,}")

    tmp = SRC + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    os.replace(tmp, SRC)
    bad_urls = [u for u, c in code.items() if c not in (200, 404, 301) and c != 200]
    print("حالا: python3 build_db.py && python3 build_catalog.py")

if __name__ == '__main__':
    main()
