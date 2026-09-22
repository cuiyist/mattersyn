"""Read saved monitoring state only; never scan sources or mutate shared state."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib, importlib.util, json

P = Path(__file__).resolve().parent
M = P.parents[1] / 'incoming-paper-monitor'
bound = {}
def read(p):
    p = Path(p); raw = p.read_bytes()
    bound[str(p)] = hashlib.sha256(raw).hexdigest()
    return json.loads(raw)

ledger = read(M/'ledger.json')
active = read(M/'deadline-20260920/active-cutoff.json')
cutoff = Path(active['cutoff_manifest']['path']).parent
spec = importlib.util.spec_from_file_location('readonly_partition', M/'deadline-20260920/partition_deadline_scope.py')
partitioner = importlib.util.module_from_spec(spec); spec.loader.exec_module(partitioner)
partition = partitioner.partition(ledger, read(cutoff/'file-inventory.json'), read(cutoff/'last-authoritative-group-mapping.json'))
pending = set(partition['included_pending_group_ids'])
rankings = {x['group_id']: x for x in ledger['selection_policy']['rankings']}
screen = read(M/'deadline-20260920/workflow-20260920T0412/screen/ranked-scopes.json')
screen_rows = {x['group_id']: x for x in screen['scopes']}
tiers = Counter(); no_tier=[]; rows=[]
for gid in sorted(pending):
    rank = rankings.get(gid)
    source = screen_rows.get(gid)
    tier = (rank or {}).get('priority_tier') or (source or {}).get('priority_tier')
    if not tier:
        # Explicit confirmed aliases only; never infer identity from DOI text.
        aliases = [k for k,g in ledger['groups'].items() if g.get('alias_of') == gid and k in screen_rows]
        choices = {screen_rows[k]['priority_tier'] for k in aliases}
        if len(choices) == 1: tier = choices.pop()
    tier = tier or 'not_resolved_to_frozen_screen_tier'
    if tier.startswith('not_resolved'): no_tier.append(gid)
    tiers[tier] += 1
    rows.append({'group_id':gid,'tier':tier,'review_status':ledger['groups'][gid].get('review',{}).get('status'),
                 'current_generation':ledger['groups'][gid]['generation'],
                 'screened_generation':(rank or {}).get('source_generation')})
missing_main = [gid for gid in pending if not any(ledger['files'][f].get('role')=='main' and ledger['files'][f].get('present',True) for f in ledger['groups'][gid]['files'])]
terminal = [gid for gid in partition['included_canonical_group_ids'] if gid not in pending]
terminal_rows=[]
for gid in terminal:
    r=ledger['groups'][gid].get('review',{})
    terminal_rows.append({'group_id':gid,'status':r.get('status'),'milestones':r.get('milestones'),'review_scope':r.get('review_scope')})
out = {'schema':'mattersyn.eta-saved-scope-evidence/1','read_at':datetime.now(timezone.utc).isoformat(),
       'source_scan_performed':False,'ledger_last_scan_at':ledger['last_scan_at'],'partition_counts':partition['counts'],
       'pending_cutoff_tier_counts':dict(sorted(tiers.items())), 'tier_unresolved_group_ids':no_tier,
       'pending_cutoff_groups_without_main_candidate':len(missing_main),
       'terminal_scope_counts':dict(Counter(x['status'] for x in terminal_rows)),
       'terminal_scopes':terminal_rows,'pending_tier_rows':rows,
       'selection_policy_keys':list(ledger['selection_policy']),
       'example_ranking':next(iter(rankings.values())), 'bound_files':bound}
assert sum(tiers.values()) == len(pending)
assert len(set(x['group_id'] for x in rows)) == len(pending)
(P/'scope-evidence-current.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k not in ['terminal_scopes','pending_tier_rows','bound_files']},ensure_ascii=False,indent=2))
