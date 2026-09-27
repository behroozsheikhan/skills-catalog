#!/usr/bin/env python3
"""حل انبوه لینک گیتهاب از درخت ریپوها (به‌جای صفحات تکی)

مرحله ۱: git clone --filter=blob:none (فقط درخت، بدون محتوا) برای ریپوهای شناخته‌شدهٔ هر author
مرحله ۲: واریانت‌های عمومی (author/skills، author/{author}-skills) برای authorهای بی‌سرنخ
مرحله ۳: تطبیق {name}/SKILL.md در درخت ← URL کامل
خروجی: github-fill.jsonl (همان فرمت fill_github.py) — فقط پس از تأیید نمونه‌ای نوشته می‌شود.
"""
import json, os, re, subprocess, sys, tempfile, random
import concurrent.futures as cf
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'skills-index-flat.jsonl')
STATE = os.path.join(HERE, 'github-fill.jsonl')
TREES = '/tmp/repo-trees.jsonl'
SPOT = int(os.environ.get('SPOT', '30'))
env = dict(os.environ, GIT_TERMINAL_PROMPT='0')

def load_state():
    st = {}
    if os.path.exists(STATE):
        for l in open(STATE, encoding='utf-8'):
            try: d = json.loads(l); st[d['key']] = d
            except Exception: pass
    return st

def ls_tree(repo_url, dest):
    """← فهرست کامل مسیرهای ریپو یا None"""
    if os.path.exists(dest): subprocess.run(['rm','-rf',dest], check=False)
    r = subprocess.run(['git','clone','--depth','1','--filter=blob:none','--no-checkout','-q',repo_url,dest],
                       env=env, timeout=150, capture_output=True)
    if r.returncode != 0: return None
    t = subprocess.run(['git','ls-tree','-r','--name-only','HEAD'], cwd=dest, capture_output=True, timeout=120)
    if t.returncode != 0: return None
    return t.stdout.decode('utf-8','replace').splitlines()

def main():
    rows = [json.loads(l) for l in open(SRC, encoding='utf-8')]
    state = load_state()
    # author → {empty:[names], repos:set, examples:{repo: [known paths]}}
    A = {}
    for r in rows:
        a = A.setdefault(r['author'], {'empty': [], 'repos': set(), 'paths': {}})
        if r.get('github'):
            base, _, path = r['github'].partition('/tree/HEAD/')
            a['repos'].add(base)
            a['paths'].setdefault(base, []).append(path.rstrip('/'))
        elif f"{r['author']}/{r['name']}" not in state:
            a['empty'].append(r['name'])

    # ── فاز ۱: ریپوهای شناخته‌شده ──
    jobs = []   # (repo_url, is_variant, author)
    for a, v in A.items():
        for repo in v['repos']: jobs.append((repo, False, a))
    # ── فاز ۲: واریانت برای authorهای بی‌سرنخ ──
    for a, v in A.items():
        if v['empty'] and not v['repos']:
            jobs.append((f"https://github.com/{a}/skills", True, a))
            jobs.append((f"https://github.com/{a}/{a}-skills", True, a))
    print(f"کلون: {sum(1 for j in jobs if not j[1])} شناخته‌شده + "
          f"{sum(1 for j in jobs if j[1])} واریانت", flush=True)

    trees = {}
    if os.path.exists(TREES):
        for l in open(TREES, encoding='utf-8'):
            d = json.loads(l); trees[d['repo']] = d['paths']
    todo = [j for j in jobs if j[0] not in trees]

    def work(j):
        repo, variant, a = j
        dest = tempfile.mkdtemp(prefix='gt-')
        try:
            return repo, variant, a, ls_tree(repo, dest)
        except Exception:
            return repo, variant, a, None
        finally:
            subprocess.run(['rm','-rf',dest], check=False)

    with cf.ThreadPoolExecutor(4) as ex:
        for i, (repo, variant, a, paths) in enumerate(ex.map(work, todo), 1):
            if paths is not None: trees[repo] = paths
            if i % 40 == 0: print(f"  {i}/{len(todo)} | درخت: {len(trees)}", flush=True)
    with open(TREES, 'w', encoding='utf-8') as f:
        for repo, paths in trees.items():
            f.write(json.dumps({'repo': repo, 'paths': paths}, ensure_ascii=False) + '\n')
    print(f"درخت گرفته‌شده: {len(trees):,} ریپو", flush=True)

    # ── فاز ۳: تطبیق ──
    derived = {}   # key → github_url
    stats = {'hit':0,'miss':0,'norepo':0,'variant_author_ok':0,'variant_author_no':0}
    for a, v in A.items():
        if not v['empty']: continue
        cand = list(v['repos'])
        variant_mode = not cand
        if variant_mode:
            cand = [f"https://github.com/{a}/skills", f"https://github.com/{a}/{a}-skills"]
        # اولویت پیشوند از نمونه‌های شناخته‌شدهٔ همان ریپو
        pref = {}
        for repo in v['repos']:
            ps = [p.rsplit('/',1)[0] for p in v['paths'].get(repo, []) if '/' in p]
            from collections import Counter
            pref[repo] = Counter(ps).most_common()
        hits = {}
        for name in v['empty']:
            best = None
            for repo in cand:
                paths = trees.get(repo)
                if not paths: continue
                pat = re.compile(rf'(?:^|/){re.escape(name)}/SKILL\.md$')
                cands = [p for p in paths if pat.search(p)]
                if not cands: continue
                # امتیاز: هم‌پیشوندی با نمونه‌ها > مسیر کوتاه‌تر
                def score(p):
                    d = p.rsplit('/',1)[0]
                    for rank,(pp,_) in enumerate(pref.get(repo,[])):
                        if d == pp: return (0, rank, len(d))
                    return (1, 0, len(d))
                c = sorted(cands, key=score)[0]
                s = score(c)
                if best is None or s < best[0]:
                    best = (s, repo, c)
            if best:
                hits[name] = f"{best[1]}/tree/HEAD/{best[2].rsplit('/',1)[0]}"
        matched = len(hits)
        if variant_mode and cand and matched == 0:
            stats['variant_author_no'] += 1
        if variant_mode and matched:
            stats['variant_author_ok'] += 1
        for name, url in hits.items():
            derived[f"{a}/{name}"] = url
        stats['hit'] += matched
        stats['miss'] += len(v['empty']) - matched
    print(f"تطبیق: {stats['hit']:,} پیدا شد | {stats['miss']:,} پیدا نشد | "
          f"author واریانتی موفق: {stats['variant_author_ok']} / ناموفق: {stats['variant_author_no']}", flush=True)

    # ── فاز ۴: تأیید نمونه‌ای در برابر صفحهٔ واقعی اسکیل ──
    if not derived:
        print("چیزی برای تأیید نیست."); return
    random.seed(1)
    sample = random.sample(sorted(derived), min(SPOT, len(derived)))
    ok = bad = 0
    s = requests.Session(); s.headers.update({'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) Chrome/131.0','Accept-Encoding':'gzip'})
    for i, k in enumerate(sample, 1):
        try:
            h = s.get(f"https://mcpservers.org/agent-skills/{k}", timeout=30).text
            m = re.search(r'href="(https://github\.com/[^"]+/tree/HEAD/[^"]*)"', h)
            page = m.group(1).rstrip('/') if m else ''
            mine = derived[k]
            same = (page.rstrip('/').split('/tree/HEAD/')[0] == mine.split('/tree/HEAD/')[0]
                    and page.split('/tree/HEAD/')[-1].rstrip('/') == mine.split('/tree/HEAD/')[-1])
            ok += same; bad += not same
            if not same: print(f"  ✗ {k}\n      درخت: {mine}\n      صفحه: {page}")
        except Exception as e:
            print(f"  ? {k}: {e}")
        import time; time.sleep(0.4)
        if i % 10 == 0: print(f"  تأیید {i}/{len(sample)}: {ok}✓ {bad}✗", flush=True)
    print(f"\nتأیید نمونه: {ok}✓ / {bad}✗ از {len(sample)}")
    if ok >= len(sample) * 0.9:
        with open(STATE, 'a', encoding='utf-8') as f:
            for k, url in sorted(derived.items()):
                if k not in state:
                    f.write(json.dumps({'key': k, 'status': 'ok', 'github': url}, ensure_ascii=False) + '\n')
        print(f"✓ {len(derived):,} لینک تأییدشده به {os.path.basename(STATE)} اضافه شد.")
        print("حالا: python3 fill_github.py   (باقی‌مانده از صفحهٔ اسکیل)  سپس  python3 fill_github.py --merge")
    else:
        print("⚠ تطبیق کمتر از ۹۰٪ — چیزی نوشته نشد؛ لینک‌های مطابق فقط از صفحه گرفته می‌شوند.")

if __name__ == '__main__':
    main()
