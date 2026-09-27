#!/usr/bin/env python3
"""Validate a translation artifact before updating tracked drafts.

No generated cache or logs are committed. Existing authored translations win.
"""
import json
from pathlib import Path
import sys
from bulk_translate import source_hash, protect, valid_cached

root = Path(__file__).resolve().parents[1]
path = Path(sys.argv[1])
rows = [json.loads(line) for line in (root/'skills-catalog/skills-index-flat.jsonl').read_text().splitlines()]
by_key = {row['author']+'/'+row['name']: row for row in rows}
current = json.loads((root/'data/fa.json').read_text())
incoming = json.loads(path.read_text())
for key, entry in incoming.items():
    row = by_key.get(key)
    if not row or entry['sourceHash'] != source_hash(row):
        raise ValueError(f'Stale or unknown source: {key}')
    for field in ('what', 'use_when'):
        if bool(entry.get(field)) != bool(row.get(field)):
            raise ValueError(f'Empty field mismatch: {key}/{field}')
    if not row.get('what') and row.get('description') and not entry.get('description'):
        raise ValueError(f'Missing fallback translation: {key}')
    if entry.get('method') == 'machine':
        for field in ('what','use_when', 'description'):
            if field == 'description' and row.get('what'): continue
            source = row.get(field,''); target = entry.get(field,'')
            if not valid_cached(source, target):
                raise ValueError(f'Untranslated text or missing technical term: {key}/{field}')
            _, tokens = protect(source)
            for token in tokens:
                if token not in target:
                    raise ValueError(f'Technical term lost: {key}/{field}: {token}')
    if entry.get('status') != 'draft':
        raise ValueError(f'Unexpected review claim: {key}')
for key, entry in current.items():
    if entry.get('method') != 'machine' and entry['sourceHash'] == source_hash(by_key[key]):
        incoming[key] = entry
hashes = {entry['sourceHash'] for entry in incoming.values()}
covered = sum(source_hash(row) in hashes for row in rows)
(root/'data/fa.json').write_text(json.dumps(incoming,ensure_ascii=False,indent=2)+'\n')
report = {'total':len(rows), 'translated':covered, 'pending':len(rows)-covered,
          'uniqueTranslationRecords':len(incoming),
          'machineTranslationRecords':sum(entry.get('method') == 'machine' for entry in incoming.values()),
          'humanReviewed':False, 'status':'draft',
          'checks':['source hash','empty source fields','description fallback','protected technical terms']}
(root/'data/translation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
