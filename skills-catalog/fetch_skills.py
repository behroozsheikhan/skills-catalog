#!/usr/bin/env python3
"""
دانلود و استخراج متن کامل اسکیل‌های mcpservers.org — نسخهٔ مودب (rate-limited)
خروجی: skills-data.jsonl  (هر خط یک اسکیل) — قابل ازسرگیری

  CONN=6 RPS=2.5 python3 fetch_skills.py
"""
import re, json, os, sys, time, html, random, threading
import concurrent.futures as cf
import requests
from requests.adapters import HTTPAdapter

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "https://mcpservers.org"
LIST = os.path.join(HERE, "all-skill-urls.txt")
OUT  = os.path.join(HERE, "skills-data.jsonl")
HDRS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9'}
CONN = int(os.environ.get('CONN', '6'))
RPS  = float(os.environ.get('RPS', '2.5'))

TAG = re.compile(r'<[^>]+>')
WS  = re.compile(r'[ \t]+')
_loc = threading.local()

# ---------- محدودکنندهٔ نرخ سراسری (توکن‌باکت) ----------
_rl   = threading.Lock()
_next = [0.0]
def throttle():
    with _rl:
        gap = 1.0 / RPS
        nxt = max(_next[0], time.monotonic())
        _next[0] = nxt + gap
        wait = nxt - time.monotonic()
    if wait > 0:
        time.sleep(wait + random.uniform(0, gap * 0.35))

# ---------- توقف سراسری هنگام چالش Cloudflare ----------
# نکته: در این محیط threading.Event().wait() قفل می‌شود،
# پس به‌جای Event از یک «زمان پایان» استفاده می‌کنیم.
_pause_until = [0.0]
_chall = {'n': 0}

def hold_if_paused():
    while True:
        with _rl:
            until = _pause_until[0]
        left = until - time.monotonic()
        if left <= 0:
            return
        time.sleep(min(left, 1.0))

def session():
    if not hasattr(_loc, 's'):
        s = requests.Session()
        s.headers.update(HDRS)
        s.mount('https://', HTTPAdapter(pool_connections=1, pool_maxsize=1, max_retries=0))
        _loc.s = s
    return _loc.s

def strip_html(s):
    s = re.sub(r'<(script|style|svg)[^>]*>.*?</\1>', ' ', s, flags=re.S | re.I)
    s = re.sub(r'<br\s*/?>|</p>|</div>|</li>|</h[1-6]>|</tr>', '\n', s, flags=re.I)
    s = re.sub(r'</t[dh]>', ' | ', s, flags=re.I)
    s = TAG.sub('', s)
    s = html.unescape(s)
    s = WS.sub(' ', s)
    s = re.sub(r'[ \t]*\n[ \t]*', '\n', s)
    return re.sub(r'\n{3,}', '\n\n', s).strip()

def meta(h, n):
    m = re.search(r'<meta name="%s" content="(.*?)"' % re.escape(n), h, re.S)
    return html.unescape(m.group(1)) if m else ''

def parse(h, author, name):
    g = (re.search(r'href="(https://github\.com/[^"]+)"[^>]*>\s*(?:<(?:svg|path)[^>]*>\s*)*GitHub', h)
         or re.search(r'href="(https://github\.com/[^"]+)"', h))
    m = (re.search(r'class="border rounded-lg p-4 border-gray-200 markdown-body">(.*?)</div>\s*</div>', h, re.S)
         or re.search(r'markdown-body">(.*)', h, re.S))
    return {'author': author, 'name': name,
            'url': f"{BASE}/agent-skills/{author}/{name}",
            'description': meta(h, 'description'),
            'github': html.unescape(g.group(1)) if g else '',
            'content': strip_html(m.group(1)) if m else ''}

lock  = threading.Lock()
state = {'ok': 0, 'fail': 0, 'empty': 0, 'bytes': 0}

def challenged(r):
    if r.status_code in (403, 429, 503):
        return True
    return 'Just a moment' in r.text[:3000] or 'cf-browser-verification' in r.text[:3000]

def fetch(rel, tries=5):
    for a in range(tries):
        hold_if_paused()                          # اگر چالش فعال است، صبر کن
        throttle()
        try:
            r = session().get(BASE + '/' + rel, timeout=45)
            if challenged(r):
                with _rl:
                    _chall['n'] += 1
                    back = min(90, 12 * (2 ** min(_chall['n'], 4)))
                    _pause_until[0] = max(_pause_until[0], time.monotonic() + back)
                if _chall['n'] >= 2:
                    print(f"  ⚠ چالش Cloudflare — توقف کامل {back}ثانیه", flush=True)
                with _rl: _chall['n'] = 0
                continue
            _chall['n'] = 0
            parts = rel.strip('/').replace('agent-skills/', '', 1).split('/')
            if len(parts) != 2 or not all(parts):
                return None
            d = parse(r.text, parts[0], parts[1])
            if not d['content']:
                d['content'] = d['description']
                with lock: state['empty'] += 1
            with lock:
                state['ok'] += 1
                state['bytes'] += len(r.content)
            return d
        except requests.RequestException:
            if a == tries - 1:
                with lock: state['fail'] += 1
                return None
            time.sleep(2 * (a + 1) + random.random())
    with lock: state['fail'] += 1
    return None

def done(paths):
    have = set()
    if os.path.exists(OUT):
        with open(OUT, encoding='utf-8') as f:
            for line in f:
                try: have.add(json.loads(line)['url'])
                except Exception: pass
    return [p for p in paths if BASE + '/' + p not in have]

if __name__ == '__main__':
    paths = [l.strip().replace(BASE + '/', '').lstrip('/') for l in open(LIST) if l.strip()]
    paths = [p for p in paths
             if p.startswith('agent-skills/') and p.count('/') == 2 and p.split('/')[1] != 'author']
    todo  = done(paths)
    print(f"کل: {len(paths)} | موجود: {len(paths)-len(todo)} | مانده: {len(todo)} | "
          f"ترد: {CONN} | نرخ: {RPS}/ثانیه | تخمین: {len(todo)/RPS/60:.0f} دقیقه\n", flush=True)
    if not todo:
        print("همه دانلود شده‌اند."); sys.exit(0)
    t0 = time.time()
    with open(OUT, 'a', encoding='utf-8') as fout:
        with cf.ThreadPoolExecutor(CONN) as ex:
            for i, d in enumerate(ex.map(fetch, todo), 1):
                if d: fout.write(json.dumps(d, ensure_ascii=False) + '\n')
                if i % 250 == 0:
                    fout.flush(); el = time.time() - t0
                    pct = state['ok'] / len(todo) * 100
                    eta = (len(todo) - i) / max(state['ok'] / max(el, 1), 0.01) / 60
                    print(f"  ✓ {state['ok']}/{len(todo)} ({pct:.0f}%) | {state['bytes']/1e6:.0f}MB | "
                          f"{el/60:.1f}دقیقه | باقی ~{eta:.0f}دقیقه", flush=True)
    el = time.time() - t0
    print(f"\nتمام: ✓ {state['ok']} | ✗ {state['fail']} | خالی: {state['empty']} | "
          f"{state['bytes']/1e6:.0f}MB | {el/60:.1f} دقیقه")
