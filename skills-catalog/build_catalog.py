#!/usr/bin/env python3
"""ساخت CATALOG.md — کاتالوگ کامل: هر اسکیل چند خط توضیح + کاربرد مشخص."""
import json, os, sqlite3, re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "skills.db")
OUT = os.path.join(HERE, "CATALOG.md")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
rows = con.execute("""
    SELECT author, name, url, github, what, use_when, description, topic, updated
    FROM skills ORDER BY lower(name), author""").fetchall()

by_letter = defaultdict(list)
for r in rows:
    ch = r['name'][0].upper()
    by_letter[ch if ch.isalpha() else '#'].append(r)

L = ["# 📖 کاتالوگ کامل اسکیل‌ها — توضیح و کاربرد", "",
     f"**{len(rows):,} اسکیل** — هر مدخل: چکار می‌کند 📌 · کاربرد/تریگر 🎯 · منبع",
     "",
     "متن کامل هر اسکیل در گیتهاب یا صفحهٔ خودش موجود است (لینک داخل مدخل).",
     "جستجوی سریع‌تر: `python3 search.py \"عبارت\"`", "",
     "بخش‌ها: " + " · ".join(
         f"[`{c}`](#{'بخش-' + c.lower()})" if c != '#' else "[`#`](#بخش-)"
         for c in sorted(by_letter, key=str.lower)), ""]
for ch in sorted(by_letter, key=str.lower):
    L += [f"## بخش {ch}  ({len(by_letter[ch])})", ""]
    for r in by_letter[ch]:
        what = r['what'] or r['description'] or ""
        what = re.sub(r'\s+', ' ', what).strip()
        use = re.sub(r'\s+', ' ', r['use_when'] or '').strip()
        gh = f" [💻 گیتهاب]({r['github']})" if r['github'] else ""
        upd = f" · به‌روزرسانی {r['updated']}" if r['updated'] else ""
        L.append(f"### `{r['name']}`  <sub>{r['author']}</sub>")
        if what:
            L.append(f"- 📌 {what}")
        if use:
            L.append(f"- 🎯 {use}")
        L.append(f"- 🔗 [صفحهٔ اسکیل]({r['url']}){gh} · {r['topic']}{upd}")
        L.append("")
open(OUT, 'w', encoding='utf-8').write("\n".join(L))
print(f"✅ CATALOG.md — {len(rows):,} مدخل، {os.path.getsize(OUT)/1e6:.1f} مگابایت")
