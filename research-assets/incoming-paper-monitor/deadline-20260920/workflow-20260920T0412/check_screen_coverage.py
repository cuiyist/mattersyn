"""Account for cutoff files and held nested copies without assigning review status."""
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib, json, sys
HERE = Path(__file__).resolve().parent
MON = HERE.parent.parent
sys.path.insert(0, str(MON))
import screen_corpus as s

read = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
partition = read(HERE/'scope-partition.json')
report = read(HERE/'screen/ranked-scopes.json')
ledger = read(HERE/'ledger-snapshot.json')
rows = [json.loads(line) for line in (HERE/'screen/documents.jsonl').read_text(encoding='utf8').splitlines() if line]
bykey = {r['file_key']: r for r in rows}
byhash = defaultdict(list)
for r in rows: byhash[r.get('sha256')].append(r)
tasks = s.tasks_from_ledger(ledger)
assert len(tasks) == len(rows) == len(bykey) == 13862
assert set(bykey) == {t['file_key'] for t in tasks}
assert all(r['source_unchanged_from_snapshot'] and r['hash_computed'] for r in rows)
recomputed, _ = s.rank_scopes(ledger, rows)
assert recomputed == report['scopes']
included = set(partition['included_canonical_group_ids'])
inc = [r for r in rows if r['group_id'] in included]
# Alias documents can refer to canonical keys; use immutable paths for counts.
inventory = read(HERE.parent/'cutoff-20260920T033439542641Z/file-inventory.json')
norm = lambda p: str(Path(p).resolve()).replace('\\','/').casefold()
cutpaths = {norm(e['absolute_path']) for e in inventory['entries'] if e.get('monitor_eligible')}
cutrows = [r for r in rows if norm(r['source_path']) in cutpaths]
assert len(cutrows) == len(cutpaths) == 13831
nested = []
for e in partition['nested_cutoff_candidates_held_for_scope_review']:
    p = Path(e['absolute_path']); before = p.stat(); h = sha(p); after = p.stat()
    assert (before.st_size, before.st_mtime_ns) == (e['size_bytes'], e['mtime_ns'])
    assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
    matches = byhash[h]
    item = {'source_path': str(p), 'relative_path': e['relative_path'], 'sha256': h,
            'actual_bytes_hashed': True, 'source_unchanged_from_cutoff': True,
            'byte_identical_screened_copies': [{'file_key': r['file_key'], 'group_id': r['group_id'],
                'in_cutoff': norm(r['source_path']) in cutpaths} for r in matches]}
    if matches:
        item['disposition'] = 'byte_identical_copy_of_screened_document_no_new_reading_scope'
    else:
        meta, text = s.extract_source(p, p.read_bytes()[:1024])
        cache = HERE/'screen/cache/text'/f'{h}.txt'; cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(text, encoding='utf8')
        item.update(disposition='unique_nested_candidate_requires_queue_admission_and_pairing',
                    extraction=meta, features=s.text_features(text, h), text_path=str(cache))
    nested.append(item)
out = {'schema': 'mattersyn-cutoff-screen-coverage/1', 'checked_at': datetime.now(timezone.utc).isoformat(),
       'screen_report_sha256': sha(HERE/'screen/ranked-scopes.json'),
       'documents_sha256': sha(HERE/'screen/documents.jsonl'),
       'snapshot_sha256': sha(HERE/'ledger-snapshot.json'),
       'snapshot_file_dispositions': len(rows), 'fixed_cutoff_file_dispositions': len(cutrows),
       'fixed_cutoff_status_counts': dict(Counter(r['status'] for r in cutrows)),
       'fixed_cutoff_unique_content_hashes': len({r['sha256'] for r in cutrows}),
       'later_top_level_copies_separate': len(rows)-len(cutrows),
       'held_nested_copy_dispositions': nested, 'ranking_recomputation_matches': True,
       'all_current_claims_and_scientific_statuses_unchanged_by_screen': True,
       'screening_is_not_full_reading_or_exclusion': True,
       'unresolved_rule': 'Image-only, unsupported and bounded-reader cases remain for manual inspection; low scores are not no-recipe exclusions.'}
(HERE/'screen-coverage-check.json').write_text(json.dumps(out, indent=2)+'\n', encoding='utf8')
print(json.dumps({k:v for k,v in out.items() if k not in ('held_nested_copy_dispositions',)}))
print(json.dumps(nested, indent=2))
