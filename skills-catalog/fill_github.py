#!/usr/bin/env python3
"""تکمیل لینک گیتهاب اسکیل‌های فاقد لینک، از صفحهٔ خود اسکیل در mcpservers.org

قابل ازسرگیری: پیشرفت در github-fill.jsonl ذخیره می‌شود.
  python3 fill_github.py            # دریافت تا اتمام یا MAX_SECS
  python3 fill_github.py --merge    # ادغام نتایج + ساخت دوبارهٔ DB و CATALOG
"""
import json, os, re, time, random, threading, sys
import concurrent.futures as cf
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
SRC   = os.path.join(HERE, 'skills-index-flat.jsonl')
STATE = os.path.join(HERE, 'github-fill.jsonl')
RPS   = float(os.environ.get('RPS', '0.5'))
CONN  = int(os.environ.get('CONN', '3'))
MAX_SECS = float(os.environ.get('MAX_SECS', '1500'))
HDRS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'en-US,en;q=0.9'}
GH_RE = re.compile(r'href="(https://github\.com/[^"]+/tree/HEAD/[^"]*)"')
CF = ('Just a moment', 'Attention Required', 'cf-challenge')

_rl, _next, _pause = threading.Lock(), [0.0], [0.0]
_loc = threading.local()
t0 = time.monotonic()

def throttle():
    with _rl:
        g = 1.0 / RPS
        n = max(_next[0], time.monotonic()); _next[0] = n + g
    w = n - time.monotonic()
    if w > 0: time.sleep(w + random.uniform(0, g * 0.25))

def hold():
    while _pause[0] - time.monotonic() > 0:
        time.sleep(1)

def sess():
    if not hasattr(_loc, 's'):
        s = requests.Session(); s.headers.update(HDRS); _loc.s = s
    return _loc.s

def out_of_time():
    return time.monotonic() - t0 > MAX_SECS

def fetch_one(key):
    hold(); throttle()
    url = f"https://mcpservers.org/agent-skills/{key}"
    for i in range(3):
        try:
            r = sess().get(url, timeout=40)
            if r.status_code in (403, 429, 503) or any(m in r.text[:2500] for m in CF):
                with _rl: _pause[0] = max(_pause[0], time.monotonic() + min(90, 20 * 2 ** i))
                hold(); continue
            if r.status_code == 404:
                return 'none', ''
            m = GH_RE.search(r.text)
            if m:
                u = m.group(1).rstrip('/')
                # «/tree/HEAD/» تنها (پوشهٔ خالی) را هم نگه می‌داریم
                return 'ok', u
            return 'none', ''
        except requests.RequestException:
            time.sleep(1.5 * (i + 1))
    return 'fail', ''

def load_done():
    done = {}
    if os.path.exists(STATE):
        for line in open(STATE, encoding='utf-8'):
            try:
                d = json.loads(line); done[d['key']] = (d['status'], d.get('github', ''))
            except Exception: pass
    return done

def append(rec):
    with _lock2:
        with open(STATE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')

_lock2 = threading.Lock()

def main_fetch():
    rows = [json.loads(l) for l in open(SRC, encoding='utf-8')]
    done = load_done()
    todo = [f"{r['author']}/{r['name']}" for r in rows
            if not r.get('github') and done.get(f"{r['author']}/{r['name']}", ('', ''))[0] not in ('ok', 'none')]
    todo.sort(key=lambda k: (done.get(k, ('', ''))[0] != 'fail', k))  # failهای قبلی اول
    total = len(todo)
    print(f"باقی‌مانده: {total:,} | انجام‌شدهٔ قبلی: {len(done):,}", flush=True)
    if not total:
        return
    n = ok = 0
    with cf.ThreadPoolExecutor(CONN) as ex:
        futs = {ex.submit(fetch_one, k): k for k in todo}
        for f in cf.as_completed(futs):
            k = futs[f]
            try: st, gh = f.result()
            except Exception: st, gh = 'fail', ''
            if st in ('ok', 'none'):
                append({'key': k, 'status': st, 'github': gh})
            n += 1; ok += st == 'ok'
            if n % 100 == 0:
                el = (time.monotonic() - t0) / 60
                print(f"  {n:,}/{total:,} | ✓{ok:,} | {el:.1f} دقیقه | "
                      f"سرعت {n/el/60:.1f}/s", flush=True)
            if out_of_time():
                print(f"⏸ سهمیهٔ زمان این مرحله پر شد — برای ادامه دوباره اجرا کنید.", flush=True)
                break
    print(f"پایان مرحله: {n:,} پردازش، {ok:,} لینک جدید", flush=True)

def main_merge():
    rows = [json.loads(l) for l in open(SRC, encoding='utf-8')]
    done = load_done()
    filled = empty = still = 0
    for r in rows:
        k = f"{r['author']}/{r['name']}"
        if not r.get('github'):
            st, gh = done.get(k, ('', ''))
            if st == 'ok' and gh:
                r['github'] = gh; filled += 1
            elif st == 'none':
                empty += 1
            else:
                still += 1
    tmp = SRC + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    os.replace(tmp, SRC)
    print(f"ادغام: +{filled:,} لینک | صفحه بدون گیتهاب: {empty:,} | انجام‌نشده: {still:,}")
    import subprocess
    subprocess.run([sys.executable, os.path.join(HERE, 'build_db.py')], check=True)
    subprocess.run([sys.executable, os.path.join(HERE, 'build_catalog.py')], check=True)

if __name__ == '__main__':
    if '--merge' in sys.argv:
        main_merge()
    else:
        main_fetch()
