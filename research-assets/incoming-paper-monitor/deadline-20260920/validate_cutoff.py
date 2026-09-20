"""Validate immutable cutoff artifacts only; never revisit/mutate live queue or source folders."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import hashlib,json,sys
O=Path(sys.argv[1]).resolve()
assert O.parent==Path(__file__).resolve().parent and O.name.startswith('cutoff-')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_bytes())
m=load(O/'cutoff-snapshot-manifest.json');inv=load(O/'file-inventory.json');mapping=load(O/'last-authoritative-group-mapping.json');ledger=load(O/'ledger-at-cutoff.json');q=load(O/'queue-status-at-cutoff.json')
checks=[]
def ck(name,ok):checks.append({'check':name,'passed':bool(ok)})
for p,h in m['bound_files'].items():ck('bound file '+Path(p).name,Path(p).parent==O and sha(p)==h)
ck('Immutable copied ledger equals capture before/after hash',sha(O/'ledger-at-cutoff.json')==m['shared_ledger_before_sha256']==m['shared_ledger_after_sha256']==mapping['ledger_sha256'])
ck('Copied queue describes the same ledger',q['ledger_sha256']==mapping['ledger_sha256'] and inv['last_queue_hash_matches_bound_ledger'])
ck('Actual capture ordering',datetime.fromisoformat(inv['capture_started_at'])<=datetime.fromisoformat(inv['first_pass']['completed_at'])<=datetime.fromisoformat(inv['verification_pass']['started_at'])<=datetime.fromisoformat(m['cutoff_at']))
ck('Cutoff binds end of identical verification pass',m['cutoff_at']==inv['cutoff_at']==inv['verification_pass']['completed_at'] and m['two_identical_observation_passes'])
entries=inv['entries'];ids=[(e['source_id'],e['relative_path']) for e in entries]
ck('Every inventory path unique',len(ids)==len(set(ids)))
for e in entries:
    ck('Contained original path '+e['source_id']+'/'+e['relative_path'],Path(e['absolute_path']).resolve()==(Path(inv['source_paths'][e['source_id']])/e['relative_path']).resolve() and Path(e['absolute_path']).resolve().is_relative_to(Path(inv['source_paths'][e['source_id']]).resolve()))
ck('All file dispositions exhaustive',dict(Counter(e['disposition'] for e in entries))==m['counts']['dispositions'])
ck('Existing mapped copies vs new unmapped reconciliation',m['counts']['monitor_eligible_top_level_documents']==m['counts']['dispositions']['mapped_stat_unchanged']+m['counts']['newly_seen_monitor_documents']==13831)
ck('No new file assigned an authoritative group',all(e['last_known_canonical_group_id'] is None for e in entries if e['disposition'].startswith('newly_seen')))
ck('Historical scope baseline remains separate',mapping['pending_group_count']==len(mapping['pending_group_ids'])==9470 and mapping['group_count']==len(mapping['groups'])==9492)
ck('Mapped data respects original queue order/generation',all(ledger['groups'][g['group_id']]['queue_order']==g['queue_order'] and ledger['groups'][g['group_id']]['generation']==g['source_generation'] for g in mapping['groups']))
ck('No content fingerprint claim',not inv['content_hashes_recomputed'] and all(e['cached_hash_status'] in ['historical_only_not_content_verified_by_this_stat_inventory','unhashed_in_snapshot'] for e in entries if e['kind']=='regular_file'))
ck('No active filter/source mutation claim',not m['deadline_filter_activated'] and not m['source_files_written'] and m['bound_monitor_readonly_helpers']['mutating_functions_called']==[])
binding=load(O/'report-binding.json');ck('Report and manifest exact binding',sha(O/'report.md')==binding['report_sha256'] and sha(O/'cutoff-snapshot-manifest.json')==binding['cutoff_manifest_sha256'])
result={'schema':'mattersyn-cutoff-artifact-validation/1','author':'/root/backlog_eta','at':datetime.now(timezone.utc).isoformat(),'independent_review':False,'status':'passed' if all(c['passed'] for c in checks) else 'failed','check_count':len(checks),'failed':[c for c in checks if not c['passed']],'counts':m['counts'],'manifest_sha256':sha(O/'cutoff-snapshot-manifest.json'),'inventory_sha256':sha(O/'file-inventory.json'),'validator_sha256':sha(__file__),'checks':checks,'scope':'Artifact identities, exhaustive path/stat membership disposition, retained mapping and no-mutation declarations; no fresh document hashing or live-ledger scan.'}
p=O/'capture-validation.json';assert not p.exists();p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'checks':len(checks),'failed':result['failed'],'validation_sha256':sha(p),'nested_candidates':[{'path':e['relative_path'],'size_bytes':e['size_bytes']} for e in entries if e['disposition'].startswith('nested_document')]}))
