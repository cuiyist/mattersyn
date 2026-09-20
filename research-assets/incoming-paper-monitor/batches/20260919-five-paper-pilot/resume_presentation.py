"""Resume the existing batch and verify current source bytes before presentation."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import sys

B=Path(__file__).resolve().parent
MON=B.parents[1]
sys.path.insert(0,str(MON))
import monitor

def save(name,data):
    (B/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

scan=monitor.scan(MON/'ledger.json',monitor.DEFAULT_SOURCE)
save('presentation-resume-scan.json',scan)
claimed=monitor.claim_batch(MON/'ledger.json','mattersyn-primary',5)
save('presentation-resume-claim.json',claimed)
state=json.loads((B/'workflow-state.json').read_bytes())
fingerprints=[]
for paper in state['papers']:
    key=paper['group_id']
    stamp=monitor.fingerprint(MON/'ledger.json','mattersyn-primary',group_id=key)
    if stamp.get('reconciliation_requires_refingerprint'):
        stamp=monitor.fingerprint(MON/'ledger.json','mattersyn-primary',group_id=key)
    inventory=json.loads((B/key.split('_')[-1]/'intake-manifest.json').read_bytes())
    for doc in inventory['documents']:
        assert hashlib.sha256(Path(doc['path']).read_bytes()).hexdigest()==doc['sha256'],doc['path']
    expected={doc['sha256'] for doc in inventory['documents']}
    actual=set(stamp['files'].values())
    assert expected==actual,(key,'source content set changed; inspect new scope before reuse',expected,actual)
    assert stamp['generation']==2,(key,'selected source generation changed; refresh pairing/manifest before reuse')
    fingerprints.append(stamp)
save('presentation-resume-fingerprints.json',fingerprints)
ledger=monitor.read_ledger(MON/'ledger.json')
assert len(monitor.active_claims(ledger))==5
print(json.dumps({'at':dt.datetime.now(dt.timezone.utc).isoformat(),'source_bundles_verified':len(fingerprints),'generation_by_group':{v['group_id']:v['generation'] for v in fingerprints},'counts':monitor.summary(ledger)},ensure_ascii=False))
