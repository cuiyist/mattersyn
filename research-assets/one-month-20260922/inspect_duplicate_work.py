"""Read-only opportunity scan using hash-verified screening metadata; never close reviews."""
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone
import hashlib,json

ROOT=Path(__file__).resolve().parents[2]
MON=ROOT/'research-assets/incoming-paper-monitor'
OUT=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf8'))
ledger_raw=(MON/'ledger.json').read_bytes()
ledger=json.loads(ledger_raw)
partition=read(MON/'deadline-20260920/resume-20260922/resume-partition.json')
included=set(partition['included_canonical_group_ids'])
screen=MON/'deadline-20260920/workflow-20260920T0412/screen/documents.jsonl'
hashes={};held=[]
with screen.open(encoding='utf8') as handle:
    for line in handle:
        row=json.loads(line);key=row['file_key'];item=ledger['files'].get(key)
        if not item or not item.get('exists') or not row.get('hash_computed') or not row.get('source_unchanged_from_snapshot'):
            continue
        source=Path(row['source_path'])
        stat=source.stat()
        sig={'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns}
        if sig!=row['observed_signature']:
            held.append(key);continue
        hashes[key]=row['sha256']
bundles=defaultdict(list);mains=defaultdict(list);unresolved=[]
for gid in sorted(included):
    group=ledger['groups'][gid]
    if group.get('alias_of'):continue
    files=group['files']
    if not files or not all(k in hashes for k in files):
        unresolved.append(gid);continue
    main={hashes[k] for k in files if ledger['files'][k]['role']=='main'}
    if len(main)!=1:continue
    roles=tuple(sorted({(ledger['files'][k]['role'],hashes[k]) for k in files}))
    bundles[roles].append(gid)
    mains[next(iter(main))].append(gid)
bundle_duplicates=[v for v in bundles.values() if len(v)>1]
main_duplicates=[{'main_sha256':k,'groups':v} for k,v in mains.items() if len(v)>1]
report={'created_at':datetime.now(timezone.utc).isoformat(),
        'scope':'Read-only redundant-work candidates; source reading, pairing and scientific statuses unchanged.',
        'input_ledger_sha256':hashlib.sha256(ledger_raw).hexdigest(),
        'cutoff_scopes':len(included),'screened_hashes_with_unchanged_source_signature':len(hashes),
        'changed_since_screen':held,'incomplete_hash_bundles':unresolved,
        'identical_role_and_content_bundle_sets':bundle_duplicates,
        'potential_redundant_bundle_reviews':sum(len(v)-1 for v in bundle_duplicates),
        'identical_main_candidates':main_duplicates,
        'potential_redundant_main_reviews':sum(len(v['groups'])-1 for v in main_duplicates),
        'limits':'Screening computed source SHA-256; this pass rechecks current file signatures, not all source bytes. Before merging, independently verify exact current bytes, preserve all SI variants and active claims, recompute cutoff and ranking generation. Same DOI alone is insufficient. No exclusions or complete statuses assigned.'}
(OUT/'duplicate-work-opportunities.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
assert (MON/'ledger.json').read_bytes()==ledger_raw
print(json.dumps({k:report[k] for k in ('cutoff_scopes','screened_hashes_with_unchanged_source_signature','potential_redundant_bundle_reviews','potential_redundant_main_reviews')}))
