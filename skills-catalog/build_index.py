#!/usr/bin/env python3
"""
ساخت ایندکس جستجوی تمام‌متنی (SQLite FTS5) از skills-data.jsonl
خروجی: skills.db
"""
import json, os, sqlite3, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, "skills-data.jsonl")
DB   = os.path.join(HERE, "skills.db")

if os.path.exists(DB):
    os.remove(DB)
con = sqlite3.connect(DB)
con.executescript("""
PRAGMA journal_mode=OFF;
PRAGMA synchronous=OFF;
CREATE TABLE skills(
  id INTEGER PRIMARY KEY,
  author TEXT, name TEXT, url TEXT UNIQUE, github TEXT,
  description TEXT, content TEXT, topic TEXT, clen INT
);
CREATE VIRTUAL TABLE fts USING fts5(
  name, description, content,
  content='skills', content_rowid='id',
  tokenize="porter unicode61 remove_diacritics 2"
);
""")

TOPICS = json.load(open(os.path.join(HERE, "topics.json")))
tmap = {}
for t, items in TOPICS.items():
    for x in items:
        tmap[x] = t

rows, seen = [], set()
n = 0
with open(SRC, encoding='utf-8') as f:
    for line in f:
        try: d = json.loads(line)
        except Exception: continue
        if d['url'] in seen: continue
        seen.add(d['url'])
        key = f"{d['author']}/{d['name']}"
        rows.append((d['author'], d['name'], d['url'], d.get('github', ''),
                     d.get('description', ''), d.get('content', ''),
                     tmap.get(key, '📦 سایر / عمومی'), len(d.get('content', ''))))
        n += 1
        if n % 2000 == 0: print(f"  {n:,} …", flush=True)

con.executemany("INSERT OR IGNORE INTO skills(author,name,url,github,description,content,topic,clen)"
                " VALUES(?,?,?,?,?,?,?,?)", rows)
con.execute("INSERT INTO fts(rowid,name,description,content) SELECT id,name,description,content FROM skills")
con.commit()

cur = con.cursor()
print("\n=== ایندکس آماده ===")
print("اسکیل‌ها      :", f"{cur.execute('SELECT COUNT(*) FROM skills').fetchone()[0]:,}")
print("حجم محتوا    :", f"{cur.execute('SELECT SUM(clen) FROM skills').fetchone()[0]/1e6:.1f} مگابایت")
print("میانگین محتوا:", f"{cur.execute('SELECT AVG(clen) FROM skills').fetchone()[0]:,.0f} کاراکتر")
print("بدون توضیح   :", f"{cur.execute(chr(39).join(['SELECT COUNT(*) FROM skills WHERE LENGTH(description)<20'])).fetchone()[0]:,}")
print("اندازهٔ DB   :", f"{os.path.getsize(DB)/1e6:.1f} مگابایت\n")
for t, c in cur.execute("SELECT topic, COUNT(*) c FROM skills GROUP BY topic ORDER BY c DESC"):
    print(f"  {c:>5}  {t}")
con.close()
