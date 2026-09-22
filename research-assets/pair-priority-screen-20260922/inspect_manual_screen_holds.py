"""Compact accounting of text/format holds, without claiming source review."""
from pathlib import Path
from collections import Counter
import hashlib
import json

HERE = Path(__file__).resolve().parent
MONITOR = HERE.parent/'incoming-paper-monitor'
DOCS = MONITOR/'deadline-20260920/workflow-20260920T0412/screen/documents.jsonl'
INVENTORY = MONITOR/'deadline-20260920/cutoff-20260920T033439542641Z/file-inventory.json'
paths = {str(Path(r['absolute_path']).resolve()).casefold() for r in json.loads(INVENTORY.read_bytes())['entries']
         if r.get('kind') == 'regular_file' and r.get('top_level') and r.get('monitor_eligible')}
held = []
for row in map(json.loads, DOCS.open(encoding='utf8')):
    if str(Path(row['source_path']).resolve()).casefold() not in paths or row['status'] != 'manual_format_or_text_review_required':
        continue
    held.append({k: row.get(k) for k in ('file_key', 'group_id', 'sha256', 'detected_format', 'extraction_status', 'page_count', 'manual_flags', 'empty_text_pages', 'failed_text_pages', 'role_candidate')})
assert len(held) == 238
report = {'schema': 'mattersyn-manual-text-screen-hold-accounting/1',
          'documents_sha256': hashlib.sha256(DOCS.read_bytes()).hexdigest(),
          'file_copies': len(held), 'source_hashes': len({r['sha256'] for r in held}),
          'formats': dict(Counter(str(r['detected_format']) for r in held)),
          'extraction_statuses': dict(Counter(str(r['extraction_status']) for r in held)),
          'candidate_roles': dict(Counter(str(r['role_candidate']) for r in held)),
          'manual_flags': dict(Counter(str(flag) for r in held for flag in (r['manual_flags'] or []))),
          'scope': 'Unresolved text/format dispositions, not no-recipe exclusions or completed manual review.',
          'files': held}
(HERE/'manual-text-screen-holds.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k != 'files'}, indent=2))
