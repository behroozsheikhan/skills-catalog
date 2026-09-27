#!/usr/bin/env python3
"""به‌روزرسانی افزایشی ایندکس با استفاده از lastmod"""
import os, re, json, time, html, random, threading
import concurrent.futures as cf
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "https://mcpservers.org"
SITEMAP = "https://mcpservers.org/sitemaps/skills.xml"
RPS = float(os.environ.get('RPS', '2.0'))
HDRS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'en-US, en;q=0.9'}
_rl, _next = threading.Lock(), [0.0]
_pause = [0.0]
_loc = threading.local()

def throttle():
    with _rl:
        g = 1.0 / RPS; n = max(_next[0], time.monotonic()); _next[0] = n + g
        w = n - time.monotonic()
    if w > 0: time.sleep(w + random.uniform(0, g * 0.3))

def hold():
    while True:
        with _rl: p = _pause[0]
        if p - time.monotonic() <= 0: return
        time.sleep(1)

def sess():
    if not hasattr(_loc, 's'):
        s = requests.Session(); s.headers.update(HDRS); _loc.s = s
    return _loc.s

def local_lastmod():
    """آخرین تاریخ ذخیره‌شده"""
    p = os.path.join(HERE, 'lastmod.tsv')
    if not os.path.exists(p): return ''
    return max(l.split('\t')[1][:10] for l in open(p) if '\t' in l)

def fetch_one(key, tries=3):
    a, n = key.split('/', 1)
    for i in range(tries):
        hold(); throttle()
        try:
            r = sess().get(f"{BASE}/agent-skills/{a}/{n}", timeout=40)
            if r.status_code in (403, 429, 503) or 'Just a moment' in r.text[:2500]:
                with _rl: _pause[0] = max(_pause[0], time.monotonic() + min(75, 10 * 2 ** i))
                continue
            d = re.search(r'<meta name="description" content="(.*?)"', r.text, re.S)
            g = re.search(r'href="(https://github\.com/[^"]+)"', r.text)
            return {'author': a, 'name': n, 'key': key,
                    'url': f"{BASE}/agent-skills/{a}/{n}",
                    'github': html.unescape(g.group(1)) if g else '',
                    'description': html.unescape(d.group(1)) if d else ''}
        except requests.RequestException:
            time.sleep(1.5 * (i + 1))
    return None

if __name__ == '__main__':
    since = local_lastmod()
    print(f"آخرین تاریخ محلی: {since or '—'}")
    r = sess().get(SITEMAP, timeout=60)
    items = re.findall(r'<url>\s*<loc>([^<]+)</loc>\s*<lastmod>([^<]+)</lastmod>', r.text)
    new = {}
    for u, d in items:
        p = u.replace(BASE + '/', '')
        if p.startswith('agent-skills/') and p.count('/') == 2 and d[:10] > since:
            a, n = p.split('/')[1], p.split('/')[2]
            new[f"{a}/{n}"] = d
    print(f"اسکیل‌های جدید/به‌روزشده: {len(new):,}\n")
    out, t0 = [], time.time()
    with cf.ThreadPoolExecutor(int(os.environ.get('CONN', 5))) as ex:
        for i, d in enumerate(ex.map(lambda k: fetch_one(k), list(new)), 1):
            if d:
                d['updated'] = new[d['key']][:10]; out.append(d)
            if i % 100 == 0: print(f"  {i}/{len(new)} | {(time.time()-t0)/60:.1f}دقیقه", flush=True)
    import os as _os
    removed=set()
    rp=_os.path.join(HERE,'removed.jsonl')
    if _os.path.exists(rp):
        for l in open(rp,encoding='utf-8'):
            try: removed.add(json.loads(l)['key'])
            except Exception: pass
    out=[d for d in out if d['key'] not in removed]
    with open(os.path.join(HERE, 'skills-index-flat.jsonl'), 'a', encoding='utf-8') as f:
        for d in out: f.write(json.dumps(d, ensure_ascii=False) + '\n')
    with open(os.path.join(HERE, 'lastmod.tsv'), 'a', encoding='utf-8') as f:
        for d in out: f.write(f"{d['key']}\t{d['updated']}\n")
    print(f"\nبه‌روزرسانی: {len(out):,} اسکیل در {(time.time()-t0)/60:.1f} دقیقه")
    print("حالا اجرا کنید:  python3 build_db.py")
