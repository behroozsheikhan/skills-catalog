#!/usr/bin/env python3
"""
🔎 جستجوی تمام‌متنی در کتابخانهٔ Agent Skills (mcpservers.org)

  python3 search.py "saas pricing"            جستجوی طبیعی
  python3 search.py "pricing" --author stripe محدود به منبع
  python3 search.py "pdf" --topic document     محدود به موضوع
  python3 search.py "seo" -n 5                 فقط ۵ نتیجه
  python3 search.py "kubernetes" --show        نمایش متن تطبیق‌یافته
  python3 search.py --stats                    آمار ایندکس
  python3 search.py --topics                   نقشهٔ موضوعی
  python3 search.py --sources                  فهرست منابع
"""
import sqlite3, os, sys, re, textwrap

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills.db")
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cur = con.cursor()

OFFICIAL = {'anthropic','openai','github','microsoft','nvidia','vercel','google','cloudflare',
            'figma','notion','stripe','sentry','huggingface','prisma','firecrawl','postHog'.lower()}

def fmt(q):
    """تبدیل عبارت طبیعی به عبارت جستجوی FTS5"""
    toks = re.findall(r'[\w\+]+', q.lower())
    if not toks:
        return None
    return ' '.join(f'"{t}"' for t in toks)

def search(q, author=None, topic=None, n=15, show=False, official=False):
    m = fmt(q)
    if not m:
        print("عبارت جستجو خالی است."); return
    where, args = ['fts MATCH ?'], [m]
    if author:  where.append('s.author LIKE ?'); args.append('%' + author.lower() + '%')
    if topic:   where.append('s.topic LIKE ?'); args.append('%' + topic + '%')
    if official: where.append("s.author IN (%s)" % ','.join('?'*len(OFFICIAL)))
    args += list(OFFICIAL) if official else []
    args.append(n)
    rows = cur.execute(f"""
        SELECT s.*, bm25(fts) AS score,
               snippet(fts, 1, '[', ']', ' … ', 22) AS snip
        FROM fts JOIN skills s ON s.id = fts.rowid
        WHERE {' AND '.join(where)}
        ORDER BY score LIMIT ?""", args).fetchall()
    if not rows:
        print(f"\n❌ نتیجه‌ای برای «{q}» پیدا نشد.\n"); return
    print(f"\n🔍 {len(rows)} نتیجه برای «{q}»" +
          (f" | منبع: {author}" if author else "") +
          (f" | موضوع: {topic}" if topic else "") +
          (" | فقط رسمی" if official else "") + "\n" + "─" * 70)
    for r in rows:
        flag = "  ★" if r['author'] in OFFICIAL else "   "
        upd = f"  🕐{r['updated']}" if r['updated'] else ""
        print(f"{flag} {r['author']}/{r['name']}  [{r['topic'].split(' ')[0]}]{upd}")
        what = re.sub(r'\s+', ' ', r['what'] or r['description'] or '')[:150]
        if what:
            print(f"      📌 {what}")
        use = re.sub(r'\s+', ' ', r['use_when'] or '')[:170]
        if use:
            print(f"      🎯 {use}")
        if show:
            snip = re.sub(r'\s+', ' ', r['snip'] or '')[:260]
            print(textwrap.fill(snip, 66, initial_indent='      ', subsequent_indent='      '))
        print(f"      ↳ {r['url']}")
    print()

def stats():
    n, tot = cur.execute("SELECT COUNT(*), SUM(LENGTH(description)) FROM skills").fetchone()
    print(f"\n📊 ایندکس: {n:,} اسکیل | {tot/1e6:.1f} مگابایت متن | "
          f"میانگین {tot/max(n,1):,.0f} کاراکتر\n" + "─" * 46)
    for t_, c in cur.execute("SELECT topic, COUNT(*) c FROM skills GROUP BY topic ORDER BY c DESC"):
        print(f"  {c:>6,}  {t_}")
    off = cur.execute("SELECT COUNT(*) FROM skills WHERE author IN (%s)" % ','.join('?' * len(OFFICIAL)),
                      list(OFFICIAL)).fetchone()[0]
    print(f"\n  منابع رسمی : {off:,}")
    print(f"  بدون توضیح: {cur.execute('SELECT COUNT(*) FROM skills WHERE LENGTH(description)<20').fetchone()[0]:,}")
    print(f"  متن کامل  : {cur.execute('SELECT COUNT(*) FROM skills WHERE full=1').fetchone()[0]:,}\n")

def topics():
    print("\n🗺️  موضوعات\n" + "─" * 46)
    for t, c in cur.execute("SELECT topic, COUNT(*) c FROM skills GROUP BY topic ORDER BY c DESC"):
        print(f"  {c:>6,}  {t}")
    print("─" * 46 + "\n")

def sources():
    rows = cur.execute("SELECT author, COUNT(*) c FROM skills GROUP BY author ORDER BY c DESC").fetchall()
    print(f"\n👥  {len(rows)} منبع\n" + "─" * 46)
    for r in rows:
        print(f"  {'★' if r['author'] in OFFICIAL else ' '} {r['c']:>5}  {r['author']}")
    print("  ★ = منبع رسمی\n")

if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or a[0] in ('-h', '--help'):
        print(__doc__)
    elif a[0] == '--stats':  stats()
    elif a[0] == '--topics': topics()
    elif a[0] == '--sources': sources()
    else:
        g = lambda k, d=None: a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else d
        search(a[0], g('--author'), g('--topic'), int(g('-n', 15)), '--show' in a, '--official' in a)
