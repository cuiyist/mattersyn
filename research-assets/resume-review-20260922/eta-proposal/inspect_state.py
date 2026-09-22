"""Read-only ETA evidence inventory. No source scan or shared-state write."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import json,hashlib,importlib.util
P=Path(__file__).resolve().parent;M=P.parents[1]/'incoming-paper-monitor'
bound={}
def read(path):
 path=Path(path);raw=path.read_bytes();bound[str(path)]=hashlib.sha256(raw).hexdigest();return json.loads(raw)
control=read(M/'review-control.json');decision=read(M/'two-month-decision.json');queue=read(M/'queue-status.json');ledger=read(M/'ledger.json');active=read(M/'deadline-20260920/active-cutoff.json')
cutoff=Path(active['cutoff_manifest']['path']).parent
spec=importlib.util.spec_from_file_location('readonly_partition',M/'deadline-20260920/partition_deadline_scope.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
partition=mod.partition(ledger,read(cutoff/'file-inventory.json'),read(cutoff/'last-authoritative-group-mapping.json'))
included=set(partition['included_canonical_group_ids']);pending=set(partition['included_pending_group_ids'])
canonical_groups={k:g for k,g in ledger['groups'].items() if not g.get('alias_of')}
statuses=Counter(g.get('review',{}).get('status') for k,g in canonical_groups.items() if k in included)
terminal=[{'group_id':k,'review':g.get('review'),'generation':g.get('generation'),'history':g.get('history')} for k,g in canonical_groups.items() if k in included and k not in pending]
ranking=read(M/'deadline-20260920/workflow-20260920T0412/screen/ranked-scopes.json')
rank_keys=list(ranking);rank_lists={k:len(v) for k,v in ranking.items() if isinstance(v,list)}
rank_meta={k:v for k,v in ranking.items() if not isinstance(v,list)}
out={'at':datetime.now(timezone.utc).isoformat(),'source_scan_performed':False,'control_status':control['status'],'control_recorded_at':control.get('recorded_at'),
 'decision':decision,'queue_generated_at':queue['generated_at'],'queue_counts':queue['counts'],
 'ledger_created_at':ledger.get('created_at'),'ledger_last_scan_at':ledger['last_scan_at'],'ledger_sha256':bound[str(M/'ledger.json')],
 'queue_ledger_hash_matches':queue['ledger_sha256']==bound[str(M/'ledger.json')],
 'partition_counts':partition['counts'],'included_review_status_counts':dict(statuses),
 'terminal':terminal,'ranking_keys':rank_keys,'ranking_lists':rank_lists,'ranking_metadata':rank_meta,
 'example_group_keys':list(next(iter(canonical_groups.values()))),
 'example_pending_priority':next((g.get('priority') for k,g in canonical_groups.items() if k in pending and g.get('priority')),None),
 'bound_files':bound}
(P/'state-inspection.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({k:v for k,v in out.items() if k not in ['terminal','decision','bound_files','ranking_metadata']},ensure_ascii=False))
print('RANKING_METADATA',json.dumps(rank_meta,ensure_ascii=False)[:12000])
print('TERMINAL_EXAMPLE',json.dumps(terminal[-1],ensure_ascii=False)[:12000])
