#!/usr/bin/env python3
"""بازتولید ALPHABETICAL.md و BY-SOURCE.md از skills.db (منبعِ حقیقت)"""
import os, sqlite3
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "skills.db")

con = sqlite3.connect(DB)
rows = con.execute("SELECT author, name FROM skills ORDER BY lower(name), author").fetchall()
con.close()

OFFICIAL_NOTE = ("منابع رسمی (Anthropic, OpenAI, GitHub, Microsoft, NVIDIA, Vercel, Google, "
                 "Cloudflare, Figma, Notion, Stripe, Sentry, Hugging Face, Prisma, Firecrawl) "
                 "معمولاً قابل‌اعتماد‌ترند.")
FOOTER = ("> منبع: <https://mcpservers.org/agent-skills> — استخراج‌شده از `sitemaps/skills.xml`\n"
          "> فقط صفحات انگلیسی (بدون ۱۶ نسخهٔ ترجمه‌شده).\n")

# ────────── ALPHABETICAL.md ──────────
by_letter = defaultdict(list)
for a, n in rows:
    ch = n[0].upper()
    key = ch if ch.isalpha() else (ch if ch.isdigit() else '#')
    by_letter[key].append((n, a))

def letter_sort(k):
    return (1, k) if k == '#' else (0, k)

letters = sorted(by_letter, key=letter_sort)
L = ["# 🔤 فهرست الفبایی کامل اسکیل‌ها", "",
     f"**{len(rows):,} اسکیل** مرتب‌شده بر اساس نام.", "",
     " · ".join(f"`{c}`: {len(by_letter[c])}" for c in letters), "",
     FOOTER, "", "---", ""]
for c in letters:
    L += [f"## {c}  ({len(by_letter[c])})", ""]
    for n, a in by_letter[c]:
        L.append(f"- `{n}`  <sub>{a}</sub>")
    L.append("")
open(os.path.join(HERE, "ALPHABETICAL.md"), 'w', encoding='utf-8').write("\n".join(L))

# ────────── BY-SOURCE.md ──────────
by_src = defaultdict(list)
for a, n in rows:
    by_src[a].append(n)
srcs = sorted(by_src, key=lambda a: (-len(by_src[a]), a.lower()))
B = ["# 👥 فهرست کامل بر اساس منبع", "",
     f"**{len(srcs)} منبع**، از بزرگ‌ترین تا کوچک‌ترین.", "",
     OFFICIAL_NOTE, "", FOOTER, "",
     "## خلاصه", "",
     "| منبع | اسکیل |", "|---|---:|"]
for a in srcs:
    B.append(f"| `{a}` | {len(by_src[a])} |")
B.append("")
for a in srcs:
    B += [f"## {a}", "", f"**{len(by_src[a])} اسکیل**", ""]
    for n in sorted(by_src[a], key=str.lower):
        B.append(f"- `{n}`")
    B.append("")
open(os.path.join(HERE, "BY-SOURCE.md"), 'w', encoding='utf-8').write("\n".join(B))

print(f"✓ ALPHABETICAL.md — {len(rows):,} اسکیل در {len(letters)} بخش")
print(f"✓ BY-SOURCE.md — {len(rows):,} اسکیل در {len(srcs)} منبع")
