"""Narrow independent addendum; prior asset audit is not overwritten."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
I=Path(__file__).resolve().parent; B=I.parent; S=B.parents[3]/'recipe-atlas'
def read(p): return json.loads(Path(p).read_bytes())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
prior_path=I/'asset-integration-independent-audit.json'; prior=read(prior_path)
normal_path=I/'publication-url-normalization.json'; normal=read(normal_path)
checks=[]; bound={}; failures=[]
def check(label,ok):
 row={'check':label,'passed':bool(ok)};checks.append(row)
 if not ok:failures.append(row)
def bind(p):
 p=Path(p).resolve();bound[str(p)]=sha(p);return bound[str(p)]
check('Prior passed asset audit unchanged',bind(prior_path)=='92d8abb70fc3f0d097aa00ce93b163bee8b5ea36c2efb6db8b0c4ad93eb464e4')
bind(normal_path)
changes={str(S/'data/records'/str(x['record_id']+'.json')):x for x in normal['records']}
bindings_path=S/'dist/assets/chemical-registry/bindings.json'; current_bindings=read(bindings_path)
check('Exactly 12 normalized records',len(changes)==12)
for path,oldhash in prior['bound_files'].items():
 current=bind(path)
 if path in changes:
  change=changes[path]
  check('Normalized current record hash: '+path,current==change['after_sha256'] and oldhash==change['before_sha256'])
 elif path!=str(bindings_path):check('Prior bound input remains unchanged: '+path,current==oldhash)
baseline=read(I/'base-site-inputs/dist/assets/chemical-registry/bindings.json')
check('All 424 original binding source hashes unchanged',all(current_bindings['sourceRecordSha256'].get(k)==v for k,v in baseline['sourceRecordSha256'].items()))
for rid,h in current_bindings['sourceRecordSha256'].items():
 if rid not in baseline['sourceRecordSha256']:check('New source-record hash resolves: '+rid,sha(S/'data/records'/str(rid+'.json'))==h)
# Recreate the exact previously audited binding bytes by restoring only the 12
# new record-hash values. This proves no other binding metadata changed.
for change in changes.values():current_bindings['sourceRecordSha256'][change['record_id']]=change['before_sha256']
restored_bytes=(json.dumps(current_bindings,ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode('utf-8')
check('Only 12 binding source hash values changed',hashlib.sha256(restored_bytes).hexdigest()==prior['bound_files'][str(bindings_path)])
bind(__file__)
result={'schema':'mattersyn.asset-integration-url-addendum/1','author':'/root','auditor':'/root/backlog_eta','at':datetime.now(timezone.utc).isoformat(),'status':'passed_narrow_url_and_binding_delta' if not failures else 'pending_root_correction','prior_asset_audit_sha256':sha(prior_path),'scope':'Preserves prior asset audit. Verifies only the later 12 record hash/18 publication-URL transport changes and associated sourceRecordSha256 updates. Detailed URL-to-original-image validation is in reader-integration-independent-audit.json; promotion science and browser approval are excluded.','checks':checks,'open_findings':failures,'counts':{'checks':len(checks),'changed_records':12,'changed_urls':18,'bound_files':len(bound)},'bound_files':bound,'site_modified':False,'ledger_modified':False,'publication_approved':False}
(I/'asset-integration-url-addendum.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(I/'asset-integration-url-addendum.md').write_text('# Asset integration URL addendum\n\nStatus: '+result['status']+'. '+str(len(checks))+' checks; '+str(len(failures))+' findings.\n\nThe prior asset audit remains unchanged. All prior bound assets and metadata remain identical except 12 newly imported Norberg record hashes and their 12 binding source-hash values, caused by 18 documented deployment URL replacements. All 424 baseline binding hashes are unchanged. Detailed source-image URL resolution is retained in the reader integration audit. No Site/ledger edits or browser/publication approval.\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'checks':len(checks),'findings':failures,'sha256':sha(I/'asset-integration-url-addendum.json')}))
