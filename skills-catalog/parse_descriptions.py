#!/usr/bin/env python3
"""استخراج ساختاریافتهٔ «چکار می‌کند» و «کاربرد» از توضیح خام.

خروجی روی skills-index-flat.jsonl نوشته می‌شود (فیلدهای what/use_when)
و build_db.py آن‌ها را به ستون‌های DB اضافه می‌کند.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))

# الگوهای رایج مرز «توضیح → کاربرد» در SKILL.mdهای رسمی
SPLIT_PATTERNS = [
    r'use this skill when',
    r'use (?:this )?(?:skill )?(?:when|for|it (?:when|for|to)|to)\b',
    r'trigger(?:s| with|ed)?\b',
    r'activate (?:when|this|with)\b',
    r'when (?:the )?user\b',
    r'when(?:ever)? (?:asked|working|the user|you need|handling|a user)\b',
    r'(?:ideal|perfect|best|useful|helpful|great) for\b',
    r'required when\b',
    r'helps (?:when|with|users)\b',
]
SPLIT_RE = re.compile('|'.join(SPLIT_PATTERNS), re.I)

# جاهایی که نباید برش بخورد (ادامهٔ جمله‌اند)
NOT_BOUNDARY = re.compile(
    r'(?:used|useful|helpful|great|good|ideal|perfect|best|known|used)\s*$', re.I)


def clean_truncation(text):
    """«…» انتهایی ناشی از بریدن سایت را تا آخرین جملهٔ کامل عقب می‌کشد."""
    t = text.strip()
    m = re.search(r'(…|\.\.\.)\s*$', t)
    if not m:
        return t
    body = t[:m.start()].rstrip(' ,;:-')
    # آخرین پایان جمله را پیدا کن
    cut = None
    for mm in re.finditer(r'[.!?]["\')\]]?\s', body):
        cut = mm.end()
    if cut and cut >= 40:
        return body[:cut].strip()
    return body + ('…' if body else '')


def parse_description(desc):
    """← (what, use_when) از توضیح خام."""
    d = ' '.join(desc.split())
    m = SPLIT_RE.search(d)
    if m and m.start() <= 25 and not NOT_BOUNDARY.search(d[:m.start()]):
        # کل توضیح «کاربرد» است (با Use when شروع می‌شود)
        return '', clean_truncation(d)
    if m and m.start() > 25 and not NOT_BOUNDARY.search(d[:m.start()]):
        what = clean_truncation(d[:m.start()])
        use = d[m.start():].strip()
        use = re.sub(r'^(Use this skill|Use|use)\s+', '', use)
        # شروع ناخوانا («This when…»، «It when…») را یکدست کن
        use = re.sub(r"^(?:This|It(?:'s)?|That)(?:\s+is)?\s+when\b", 'Use when', use, flags=re.I)
        if not re.match(r'^(Use|when|for|trigger)', use, re.I):
            use = 'Use when ' + use[0].lower() + use[1:] if use else use
        # متن لایسنس/متادیتا که به توضیح چسبیده را جدا کن
        use = re.split(r'\blicense:|\blicense\b|\bmetadata\b', use, flags=re.I)[0].rstrip(' .,-')
        use = use if use else ''
        return what, use
    return clean_truncation(d), ''


if __name__ == '__main__':
    src = os.path.join(HERE, 'skills-index-flat.jsonl')
    tmp = src + '.tmp'
    n = use_n = 0
    with open(src, encoding='utf-8') as f, open(tmp, 'w', encoding='utf-8') as out:
        for line in f:
            r = json.loads(line)
            what, use = parse_description(r.get('description', ''))
            r['what'], r['use_when'] = what, use
            out.write(json.dumps(r, ensure_ascii=False) + '\n')
            n += 1
            use_n += bool(use)
    os.replace(tmp, src)
    print(f"✓ {n:,} رکورد | کاربرد شناسایی‌شده: {use_n:,} ({use_n/n*100:.0f}%)")
    print("حالا اجرا کنید:  python3 build_db.py")
