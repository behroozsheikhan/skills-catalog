#!/usr/bin/env python3
"""ساخت پایگاه‌دادهٔ جستجوی تمام‌متنی از skills-index-flat.jsonl (+ متن کامل موجود)"""
import json, os, sqlite3, collections

HERE = os.path.dirname(os.path.abspath(__file__))
IDX  = os.path.join(HERE, "skills-index-flat.jsonl")
FULL = os.path.join(HERE, "skills-data.jsonl")   # متن کاملِ ۳۴۸ اسکیلِ قبلاً دانلودشده
DB   = os.path.join(HERE, "skills.db")
TOP  = json.load(open(os.path.join(HERE, "topics.json")))

tmap = {}
for t, items in TOP.items():
    for x in items:
        tmap[x] = t

full = {}
if os.path.exists(FULL):
    for line in open(FULL, encoding='utf-8'):
        try:
            d = json.loads(line)
            full[f"{d['author']}/{d['name']}"] = d.get('content', '')
        except Exception:
            pass

if os.path.exists(DB):
    os.remove(DB)
con = sqlite3.connect(DB)
con.executescript("""
PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;
CREATE TABLE skills(
  id INTEGER PRIMARY KEY, author TEXT, name TEXT, url TEXT, github TEXT,
  description TEXT, topic TEXT, full INTEGER DEFAULT 0);
CREATE VIRTUAL TABLE fts USING fts5(
  name, description, content='skills', content_rowid='id',
  tokenize="porter unicode61 remove_diacritics 2");
""")

rows, seen = [], set()
for line in open(IDX, encoding='utf-8'):
    d = json.loads(line)
    k = f"{d['author']}/{d['name']}"
    if k in seen:
        continue
    seen.add(k)
    rows.append((d['author'], d['name'], d['url'], d.get('github', ''),
                 d.get('description', ''), tmap.get(k, '📦 سایر / عمومی'),
                 1 if full.get(k) else 0))
con.executemany("INSERT INTO skills(author,name,url,github,description,topic,full) VALUES(?,?,?,?,?,?,?)", rows)
con.execute("INSERT INTO fts(rowid,name,description) SELECT id,name,description FROM skills")
con.commit()

c = con.cursor()
n = c.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
dlen = c.execute("SELECT SUM(LENGTH(description)) FROM skills").fetchone()[0]
print(f"""
✅ پایگاه‌داده ساخته شد — skills.db ({os.path.getsize(DB)/1e6:.1f} مگابایت)

   اسکیل‌ها        : {n:,}
   متن توضیحات    : {dlen/1e6:.1f} مگابایت
   میانگین توضیح  : {dlen/n:,.0f} کاراکتر
   با متن کامل    : {c.execute('SELECT COUNT(*) FROM skills WHERE full=1').fetchone()[0]:,}
""")
for t, k in c.execute("SELECT topic, COUNT(*) x FROM skills GROUP BY topic ORDER BY x DESC"):
    print(f"  {k:>6,}  {t}")
con.close()
