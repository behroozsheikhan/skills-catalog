#!/usr/bin/env python3
"""تکمیل منابع ناقص — فقط جاهایی که هنوز اسکیل جا مانده"""
import importlib.util, json, os, sys, time, collections
import concurrent.futures as cf

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("m", os.path.join(HERE, "fetch_listings.py"))
m = importlib.util.module_from_spec(spec); sys.modules['m'] = m; spec.loader.exec_module(m)

real = collections.Counter()
for l in open(os.path.join(HERE, "all-skill-urls.txt")):
    p = l.strip().lstrip('/').split('/')
    if len(p) == 3 and p[0] == 'agent-skills' and p[1] != 'author':
        real[p[1]] += 1

got = collections.Counter()
for line in open(os.path.join(HERE, "skills-index.jsonl"), encoding='utf-8'):
    for k, v in json.loads(line)['skills'].items():
        got[v['author']] += 1

todo = [a for a in real if got.get(a, 0) < real[a]]
print(f"منابع ناقص: {len(todo)} | کمبود: {sum(real[a]-got.get(a,0) for a in todo):,}\n", flush=True)

merged, t0 = {}, time.time()
with open(os.path.join(HERE, "skills-index.jsonl"), 'a', encoding='utf-8') as f:
    with cf.ThreadPoolExecutor(int(os.environ.get('CONN', 5))) as ex:
        for i, a in enumerate(ex.map(lambda x: (x, m.crawl('author', x)), todo), 1):
            name, res = a
            merged.update(res)
            f.write(json.dumps({'author': name, 'skills': res}, ensure_ascii=False) + '\n'); f.flush()
            if i % 5 == 0:
                print(f"  {i}/{len(todo)} | {name:<22} +{len(res):>3} "
                      f"| مجموع {len(merged):,} | {(time.time()-t0)/60:.1f}دقیقه", flush=True)
print(f"\nجمع جدید: {len(merged):,} | {(time.time()-t0)/60:.1f} دقیقه")
