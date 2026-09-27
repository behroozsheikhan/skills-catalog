#!/usr/bin/env python3
"""بازیابی لینک‌های عمقی و نجات بی‌لینک‌ها

بخش A: برای لینک‌های ریشه‌ای (که مسیر عمقی‌شان ۴۰۴ شده)، مسیر جدید در درختِ
        فعلی ریپو پیدا و با HEAD تأیید می‌شود.
بخش B: برای اسکیل‌های بدون گیتهاب، صفحه با استخراج وسیع (downgit دیکودشده،
        npx، هر github) دوباره خوانده و URL تأییدشده اضافه می‌شود.
"""
import json, os, re, subprocess, sys, tempfile, time, random, threading, urllib.parse
import concurrent.futures as cf
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'skills-index-flat.jsonl')
TREES = '/tmp/repo-trees2.jsonl'
RESCUE = os.path.join(HERE, 'rescue.jsonl')
PHASE = os.environ.get('PHASE', 'both')          # trees | pages | both
MAX_SECS = float(os.environ.get('MAX_SECS', '1500'))
t0 = time.monotonic()
env = dict(os.environ, GIT_TERMINAL_PROMPT='0')
S = requests.Session()
S.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36',
                  'Accept-Encoding': 'gzip'})
_lock, _next = threading.Lock(), [0.0]

def gh_rate():
    with _lock:
        n = max(_next[0], time.monotonic()); _next[0] = n + 0.16
    t = n - time.monotonic()
    if t > 0: time.sleep(t)

def head_ok(url, tries=2):
    for i in range(tries):
        gh_rate()
        try:
            if S.head(url, timeout=15, allow_redirects=True).status_code == 200:
                return True
        except requests.RequestException:
            time.sleep(2)
    return False

def out_of_time():
    return time.monotonic() - t0 > MAX_SECS

def load_jsonl(p):
    d = {}
    if os.path.exists(p):
        for l in open(p, encoding='utf-8'):
            try:
                j = json.loads(l); d[j['key']] = j
            except Exception: pass
    return d

def ls_tree(repo_url, dest):
    if os.path.exists(dest): subprocess.run(['rm','-rf',dest], check=False)
    r = subprocess.run(['git','clone','--depth','1','--filter=blob:none','--no-checkout','-q',repo_url,dest],
                       env=env, timeout=180, capture_output=True)
    if r.returncode != 0: return None
    t = subprocess.run(['git','ls-tree','-r','--name-only','HEAD'], cwd=dest, capture_output=True, timeout=120)
    return t.stdout.decode('utf-8','replace').splitlines() if t.returncode == 0 else None

# ───────────────── بخش A ─────────────────
def phase_trees(rows):
    root = [r for r in rows if r.get('github','').startswith('http') and '/tree/' not in r['github']]
    by_repo = {}
    for r in root:
        by_repo.setdefault(r['github'], []).append(r['name'])
    print(f"[A] لینک ریشه‌ای: {len(root):,} در {len(by_repo)} ریپو", flush=True)
    trees = {}
    if os.path.exists(TREES):
        for l in open(TREES, encoding='utf-8'):
            d = json.loads(l); trees[d['repo']] = d['paths']
    todo = [u for u in by_repo if u not in trees]
    print(f"[A] کلون: {len(todo)} ریپو (کش: {len(trees)})", flush=True)

    def work(u):
        dest = tempfile.mkdtemp(prefix='rt-')
        try: return u, ls_tree(u, dest)
        except Exception: return u, None
        finally: subprocess.run(['rm','-rf',dest], check=False)

    with cf.ThreadPoolExecutor(4) as ex:
        for i, (u, paths) in enumerate(ex.map(work, todo), 1):
            if paths is not None: trees[u] = paths
            if i % 40 == 0: print(f"  [A] {i}/{len(todo)}", flush=True)
            if out_of_time(): print("[A] ⏸ زمان"); break
    with open(TREES, 'w', encoding='utf-8') as f:
        for u, p in trees.items(): f.write(json.dumps({'repo': u, 'paths': p}) + '\n')

    rescued = load_jsonl(RESCUE)
    prop = 0
    for repo, names in by_repo.items():
        paths = trees.get(repo) or []
        for name in names:
            k = f"{name}"
            pat = re.compile(rf'(?:^|/){re.escape(name)}/SKILL\.md$')
            cs = sorted((p for p in paths if pat.search(p)), key=len)
            if not cs: continue
            deep = f"{repo}/tree/HEAD/{cs[0].rsplit('/',1)[0]}"
            key = None
            for r in root:
                if r['github'] == repo and r['name'] == name:
                    key = f"{r['author']}/{r['name']}"; break
            if key and key not in rescued:
                rescued[key] = {'key': key, 'status': 'ok', 'github': deep, 'via': 'tree'}
                prop += 1
    print(f"[A] پیشنهاد عمقی: {prop:,}", flush=True)
    with open(RESCUE, 'w', encoding='utf-8') as f:
        for j in rescued.values(): f.write(json.dumps(j, ensure_ascii=False) + '\n')

# ───────────────── بخش B ─────────────────
DG_RE = re.compile(r'downgit\.github\.io/#/home\?url=([^"\']+)')
TREE_RE = re.compile(r'href="(https://github\.com/[^"]+/tree/(?:HEAD|main)/[^"]*)"')
NPX_RE = re.compile(r'npx skills add\s+(https://github\.com/[^\s"\']+)')
ANY_RE = re.compile(r'github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)')

def page_rescue(k):
    for i in range(3):
        try:
            r = S.get(f"https://mcpservers.org/agent-skills/{k}", timeout=30)
        except requests.RequestException:
            time.sleep(12); continue
        if r.status_code == 200 and 'Just a moment' not in r.text[:2500]:
            h = r.text
            dg = [urllib.parse.unquote(u).split('#')[0] for u in DG_RE.findall(h)]
            tr = [u.rstrip('/') for u in TREE_RE.findall(h)]
            np = [u.rstrip('/') for u in NPX_RE.findall(h)]
            cands = [u for u in dg + tr if '/tree/' in u] + np
            if not cands:
                ag = sorted(set(ANY_RE.findall(h)) - {'blog.mcpservers.org'})
                cands = [f"https://github.com/{x}" for x in ag[:1]]
            # اولویت: مسیر عمقی، بعد ریپو
            deep = [u for u in cands if '/tree/' in u]
            url = (deep or cands)[:1]
            return (url[0] if url else '', 'none')
        time.sleep([18, 40][min(i, 1)])
    return ('', 'fail')

def phase_pages(rows, done_keys):
    state = load_jsonl(os.path.join(HERE, 'github-fill.jsonl'))
    none_keys = [k for k, v in state.items() if v['status'] == 'none']
    byk = {f"{r['author']}/{r['name']}": r for r in rows}
    todo = [k for k in none_keys if k in byk]
    print(f"[B] صفحات none برای فراخوانی مجدد: {len(todo):,}", flush=True)
    got = 0
    for i, k in enumerate(todo, 1):
        if out_of_time(): print("[B] ⏸ زمان"); break
        url, st = page_rescue(k)
        if url:
            got += 1
            with open(RESCUE, 'a', encoding='utf-8') as f:
                f.write(json.dumps({'key': k, 'status': 'ok', 'github': url, 'via': 'page'},
                                   ensure_ascii=False) + '\n')
        else:
            with open(RESCUE, 'a', encoding='utf-8') as f:
                f.write(json.dumps({'key': k, 'status': 'confirmed-none', 'github': ''},
                                   ensure_ascii=False) + '\n')
        if i % 40 == 0: print(f"  [B] {i}/{len(todo)} | یافته: {got}", flush=True)
        time.sleep(0.9)
    print(f"[B] یافته‌شده: {got:,}", flush=True)

def main():
    rows = [json.loads(l) for l in open(SRC, encoding='utf-8')]
    rescued = load_jsonl(RESCUE)
    if PHASE in ('trees', 'both'):
        phase_trees(rows); rescued = load_jsonl(RESCUE)
    if PHASE in ('pages', 'both'):
        phase_pages(rows, set(rescued))
    rescued = load_jsonl(RESCUE)
    print(f"\nتأیید HEAD برای {len(rescued):,} URL…", flush=True)
    good = {}
    for i, (k, j) in enumerate(sorted(rescued.items()), 1):
        u = j.get('github', '')
        if u and head_ok(u):
            good[k] = u
        if i % 300 == 0: print(f"  تأیید {i:,}/{len(rescued):,} | سالم: {len(good):,}", flush=True)
    print(f"سالم: {len(good):,} / {len(rescued):,}", flush=True)

    applied = root_kept = 0
    for r in rows:
        k = f"{r['author']}/{r['name']}"
        if k in good:
            r['github'] = good[k]; applied += 1
    tmp = SRC + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    os.replace(tmp, SRC)
    print(f"اعمال‌شده: {applied:,}")
    print("حالا: python3 build_db.py && python3 build_catalog.py")

if __name__ == '__main__':
    main()
