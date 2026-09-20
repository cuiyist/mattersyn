"""Root-owned rolling admission through existing audited cutoff/queue gates."""
from pathlib import Path
from datetime import datetime,timezone
import json,sys,subprocess,hashlib
import monitor,activate_screened_cutoff
R=Path(__file__).resolve().parent;D=R/'deadline-20260920';a=json.loads((D/'active-cutoff.json').read_text(encoding='utf8'))
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');out=D/('admission-'+stamp);out.mkdir()
ledger=R/'ledger.json';manifest=Path(a['cutoff_manifest']['path']);partition=out/'scope-partition.json'
subprocess.run([sys.executable,str(D/'partition_deadline_scope.py'),'--cutoff-manifest',str(manifest),'--ledger',str(ledger),'--output',str(partition)],check=True,capture_output=True)
report=Path(monitor.read_ledger(ledger)['selection_policy']['source_report'])
proof=activate_screened_cutoff.activate(ledger,report,partition,out/'activation')
before={x['group_id'] for x in monitor.active_claims(monitor.read_ledger(ledger))}
result=monitor.claim_batch(ledger,'mattersyn-primary',size=2,refill=True)
added=[x['group_id'] for x in result['active_papers'] if x['group_id'] not in before]
part=json.loads(partition.read_text(encoding='utf8'))
assert len(added)<=1 and all(g in part['included_pending_group_ids'] for g in added)
fingerprints={g:monitor.fingerprint(ledger,'mattersyn-primary',group_id=g) for g in added}
for g in added:
 current=monitor.read_ledger(ledger)['groups'][g]
 if current.get('fingerprint',{}).get('generation')!=current['generation']:
  # Hash-confirmed alias reconciliation can add sibling source copies and
  # advance generation. Bind the combined unchanged evidence before manifesting.
  fingerprints[g]=monitor.fingerprint(ledger,'mattersyn-primary',group_id=g)
 current=monitor.read_ledger(ledger)['groups'][g]
 assert current.get('fingerprint',{}).get('generation')==current['generation']
batch=R/'batches/20260920-rolling-pipeline'/('intake-'+stamp)
subprocess.run([sys.executable,str(R/'build_batch_manifest.py'),'--output-dir',str(batch)],check=True,capture_output=True)
row={'at':datetime.now(timezone.utc).isoformat(),'new_groups':added,'active_claims':result['active_review_claims'],'cutoff_partition':str(partition),'activation_proof':str(out/'activation/activation-proof.json'),'intake_manifest':str(batch/'intake-manifest.json'),'fingerprints':fingerprints,'source_files_changed':False}
(out/'admission.json').write_text(json.dumps(row,indent=2)+'\n',encoding='utf8')
a['current_activation']={'path':str(out/'activation/activation-proof.json'),'sha256':hashlib.sha256((out/'activation/activation-proof.json').read_bytes()).hexdigest()};a['counts']=part['counts'];a['recorded_at']=row['at'];a['author']='/root'
(D/'active-cutoff.json').write_text(json.dumps(a,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:row[k] for k in ['new_groups','active_claims','cutoff_partition','intake_manifest']},indent=2))
