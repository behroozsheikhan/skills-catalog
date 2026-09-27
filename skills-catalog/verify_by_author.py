#!/usr/bin/env python3
"""تأیید نویسنده‌محور لینک‌های مشتق‌شده از درخت ریپو

برای هر author که همهٔ حدس‌هایش در «یک» ریپو است: تا ۳ صفحهٔ نمونه گرفته می‌شود؛
اگر همه مطابق بودند، همهٔ اسکیل‌های آن author از درخت پذیرفته می‌شود.
خروجی: append به github-fill.jsonl (فقط موارد تأییدشده یا مطابق انفرادی)
"""
import json, os, re, time, random, threading
from collections import Counter, defaultdict
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'skills-index-flat.jsonl')
STATE = os.path.join(HERE, 'github-fill.jsonl')
TREES = '/tmp/repo-trees.jsonl'
HDRS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36',
        'Accept-Encoding': 'gzip'}
GH_RE = re.compile(r'href="(https://github\.com/[^"]+/tree/HEAD/[^"]*)"')

def load_state():
    st = {}
    if os.path.exists(STATE):
        for l in open(STATE, encoding='utf-8'):
            try: d = json.loads(l); st[d['key']] = d
            except Exception: pass
    return st

def page_gh(s, k, tries=4):
    """← URL درخت گیتهاب صفحه، یا None در بن‌بست"""
    for i in range(tries):
        try:
            r = s.get(f"https://mcpservers.org/agent-skills/{k}", timeout=30)
        except requests.RequestException:
            time.sleep(10); continue
        if r.status_code == 200 and 'Just a moment' not in r.text[:2500]:
            m = GH_RE.search(r.text)
            return m.group(1).rstrip('/') if m else ''
        time.sleep([20, 45, 90][min(i, 2)])
    return None

def norm(u):
    b, _, p = u.partition('/tree/HEAD/')
    return b, p.rstrip('/')

def main():
    rows = [json.loads(l) for l in open(SRC, encoding='utf-8')]
    state = load_state()
    trees = {}
    if os.path.exists(TREES):
        for l in open(TREES, encoding='utf-8'):
            d = json.loads(l); trees[d['repo']] = d['paths']
    A = defaultdict(lambda: {'empty': [], 'repos': set(), 'paths': {}})
    for r in rows:
        a = A[r['author']]
        if r.get('github'):
            base, _, path = r['github'].partition('/tree/HEAD/')
            a['repos'].add(base); a['paths'].setdefault(base, []).append(path.rstrip('/'))
        elif f"{r['author']}/{r['name']}" not in state:
            a['empty'].append(r['name'])

    def derive(a, v):
        cand = list(v['repos']) or [f"https://github.com/{a}/skills", f"https://github.com/{a}/{a}-skills"]
        pref = {}
        for repo in v['repos']:
            ps = [p.rsplit('/', 1)[0] for p in v['paths'].get(repo, []) if '/' in p]
            pref[repo] = Counter(ps).most_common()
        out = {}
        for name in v['empty']:
            best = None
            for repo in cand:
                paths = trees.get(repo)
                if not paths: continue
                pat = re.compile(rf'(?:^|/){re.escape(name)}/SKILL\.md$')
                cs = [p for p in paths if pat.search(p)]
                if not cs: continue
                def score(p):
                    d = p.rsplit('/', 1)[0]
                    for rank, (pp, _) in enumerate(pref.get(repo, [])):
                        if d == pp: return (0, rank, len(d))
                    return (1, 0, len(d))
                c = sorted(cs, key=score)[0]; sc = score(c)
                if best is None or sc < best[0]: best = (sc, repo, c)
            if best: out[name] = f"{best[1]}/tree/HEAD/{best[2].rsplit('/',1)[0]}"
        return out

    s = requests.Session(); s.headers.update(HDRS)
    lock = threading.Lock()
    f_out = open(STATE, 'a', encoding='utf-8')

    def plan_for(a, v):
        g = derive(a, v)
        if not g: return None
        bases = {norm(u)[0] for u in g.values()}
        return g, bases

    plans = []
    for a, v in sorted(A.items()):
        if not v['empty']: continue
        p = plan_for(a, v)
        if p: plans.append((a, v, p[0], p[1]))
    single = [(a, v, g, b) for a, v, g, b in plans if len(b) == 1]
    print(f"author با حدس: {len(plans)} | تک‌ریپو (قابل تأیید گروهی): {len(single)}", flush=True)

    total_accept = total_sample_ok = total_sample_bad = 0
    for a, v, g, bases in single:
        names = sorted(g)
        random.seed(a)
        sample = random.sample(names, min(3, len(names)))
        results = []
        for k in [f"{a}/{n}" for n in sample]:
            pg = page_gh(s, k)
            if pg is None:
                results.append(None); continue
            results.append(norm(pg) == norm(g[k.split('/', 1)[1]]))
            time.sleep(2.2)
        decided = [x for x in results if x is True or x is False]
        with lock:
            for k, okk in zip([f"{a}/{n}" for n in sample], results):
                if okk is True:
                    f_out.write(json.dumps({'key': k, 'status': 'ok', 'github': g[k.split('/', 1)[1]]},
                                           ensure_ascii=False) + '\n'); total_sample_ok += 1
                elif okk is False:
                    total_sample_bad += 1
            if decided and all(decided) and len(decided) == len(sample):
                # کل author تأیید شد — بقیه هم از درخت پذیرفته می‌شوند
                for n in names:
                    k = f"{a}/{n}"
                    if k in [f"{a}/{sn}" for sn in sample]: continue
                    f_out.write(json.dumps({'key': k, 'status': 'ok', 'github': g[n]},
                                           ensure_ascii=False) + '\n'); total_accept += 1
            f_out.flush()
    f_out.close()
    print(f"\nنمونه‌ها: {total_sample_ok} ✓ / {total_sample_bad} ✗ | پذیرش گروهی: +{total_accept:,}")
    print("حالا: python3 fill_github.py   (باقی‌مانده از صفحه)  سپس  python3 fill_github.py --merge")

if __name__ == '__main__':
    main()
