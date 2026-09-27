#!/usr/bin/env python3
"""
جمع‌آوری توضیحات همهٔ اسکیل‌ها از صفحات فهرست (۲۹ اسکیل در هر درخواست)
خروجی: skills-index.jsonl   (نام + منبع + توضیح + مسیر گیت‌هاب)
"""
import re, json, os, time, html, random, threading
import concurrent.futures as cf
import requests
from requests.adapters import HTTPAdapter

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "https://mcpservers.org"
OUT  = os.path.join(HERE, "skills-index.jsonl")
HDRS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'en-US,en;q=0.9'}
RPS   = float(os.environ.get('RPS', '2.0'))
CONN  = int(os.environ.get('CONN', '5'))

TAG = re.compile(r'<[^>]+>')
_rl, _next = threading.Lock(), [0.0]
_pause_until = [0.0]
_loc = threading.local()

def throttle():
    with _rl:
        gap = 1.0 / RPS
        nxt = max(_next[0], time.monotonic())
        _next[0] = nxt + gap
        w = nxt - time.monotonic()
    if w > 0:
        time.sleep(w + random.uniform(0, gap * 0.3))

def hold():
    while True:
        with _rl: until = _pause_until[0]
        left = until - time.monotonic()
        if left <= 0: return
        time.sleep(min(left, 1.0))

def sess():
    if not hasattr(_loc, 's'):
        s = requests.Session(); s.headers.update(HDRS)
        s.mount('https://', HTTPAdapter(pool_connections=1, pool_maxsize=1, max_retries=0))
        _loc.s = s
    return _loc.s

CARD = re.compile(
    r'<a href="/agent-skills/(?P<a>[^"/]+)/(?P<n>[^"/]+)"[^>]*class="group flex min-w-0.*?</a>', re.S)

def unesc(s):
    return html.unescape(TAG.sub('', s)).strip()

def parse(h):
    out = {}
    for m in CARD.finditer(h):
        a, n = m.group('a'), m.group('n')
        if a in ('author', 'category'):
            continue
        card = m.group(0)
        gh = re.search(r'title="(https://github\.com/[^"]+)"', card) or re.search(r'>([a-z0-9\-_]+/[^<]*?/skills?/[^<]+)</p>', card)
        d = re.search(r'<p class="mt-1\.5 line-clamp-2[^"]*">(.*?)</p>', card, re.S)
        out[f"{a}/{n}"] = {'author': a, 'name': n,
                           'github': html.unescape(gh.group(1)) if gh and gh.lastindex else '',
                           'description': unesc(d.group(1)) if d else ''}
    return out

def get(url, tries=4):
    for a_ in range(tries):
        hold(); throttle()
        try:
            r = sess().get(url, timeout=40)
            if r.status_code in (403, 429, 503) or 'Just a moment' in r.text[:2500]:
                with _rl:
                    _pause_until[0] = max(_pause_until[0], time.monotonic() + min(75, 10 * 2 ** a_))
                continue
            return r.text
        except requests.RequestException:
            time.sleep(1.5 * (a_ + 1))
    return None

def crawl(kind, key):
    """صفحات یک منبع/دسته را تا انتها می‌خواند"""
    got, page, seen = {}, 1, set()
    while page <= 400:
        h = get(f"{BASE}/agent-skills/{kind}/{key}" + (f"?page={page}" if page > 1 else ""))
        if h is None:
            break
        d = parse(h)
        if not d:
            break
        new = {k: v for k, v in d.items() if k not in seen}
        if not new:
            break
        seen |= set(d)
        got.update(new)
        page += 1
    return got

if __name__ == '__main__':
    # منابع و دسته‌ها از فهرست کامل
    src = sorted({l.strip().lstrip('/').split('/')[2] for l in open(os.path.join(HERE, "all-skill-urls.txt"))
                  if l.strip().lstrip('/').startswith('agent-skills/author/')})
    cats = sorted({l.strip().lstrip('/').split('/')[2] for l in open(os.path.join(HERE, "all-skill-urls.txt"))
                   if l.strip().lstrip('/').startswith('agent-skills/category/')})
    jobs = [('author', a) for a in src] + [('category', c) for c in cats]
    print(f"کارها: {len(src)} منبع + {len(cats)} دسته = {len(jobs)} | نرخ {RPS}/ثانیه\n", flush=True)

    merged, t0 = {}, time.time()
    with open(OUT, 'w', encoding='utf-8') as f:
        with cf.ThreadPoolExecutor(CONN) as ex:
            for i, res in enumerate(ex.map(lambda j: crawl(*j), jobs), 1):
                merged.update(res)
                f.write(json.dumps({'author': res and list(res.values())[0]['author'] or '',
                                   'skills': res}, ensure_ascii=False) + '\n')
                f.flush()
                if i % 10 == 0:
                    el = time.time() - t0
                    print(f"  {i}/{len(jobs)} | اسکیل‌ها: {len(merged):,} | {el/60:.1f}دقیقه", flush=True)
    # یکپارچه‌سازی نهایی
    with open(OUT.replace('.jsonl', '-flat.jsonl'), 'w', encoding='utf-8') as f:
        for k, v in sorted(merged.items()):
            v['key'] = k
            v['url'] = f"{BASE}/agent-skills/{v['author']}/{v['name']}"
            f.write(json.dumps(v, ensure_ascii=False) + '\n')
    print(f"\nتمام: {len(merged):,} اسکیل یکتا از {len(jobs)} صفحه | {(time.time()-t0)/60:.1f} دقیقه")
