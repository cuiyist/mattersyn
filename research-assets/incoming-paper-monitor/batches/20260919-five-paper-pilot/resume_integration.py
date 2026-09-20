"""Fingerprint the already-resumed four active contributions without rescanning."""
from pathlib import Path
import datetime as dt
import hashlib,json,sys
B=Path(__file__).resolve().parent
MON=B.parents[1]
sys.path.insert(0,str(MON))
import monitor
stamps=[]
keys=['10.1021_jp0219348','10.1021_la036034c','10.1021_jp0473669','10.1021_ja048427j']
assert {p['group_id'] for p in monitor.active_claims(monitor.read_ledger(MON/'ledger.json'))}==set(keys)
for key in keys:
    stamp=monitor.fingerprint(MON/'ledger.json','mattersyn-primary',group_id=key)
    if stamp.get('reconciliation_requires_refingerprint'):
        stamp=monitor.fingerprint(MON/'ledger.json','mattersyn-primary',group_id=key)
    inventory=json.loads((B/key.split('_')[-1]/'intake-manifest.json').read_bytes())
    for d in inventory['documents']:
        assert hashlib.sha256(Path(d['path']).read_bytes()).hexdigest()==d['sha256'],d['path']
    assert {d['sha256'] for d in inventory['documents']}==set(stamp['files'].values()),key
    assert stamp['generation']==2,key
    stamps.append(stamp)
result={'at':dt.datetime.now(dt.timezone.utc).isoformat(),'source_fingerprints':stamps,'counts':monitor.summary(monitor.read_ledger(MON/'ledger.json'))}
out=B/'integration-resume-20260920T0116.json'
assert not out.exists(),'Dated resume is immutable; use a new filename for later source checks.'
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({'path':str(out),'verified_source_bundles':len(stamps),'counts':result['counts']}))
