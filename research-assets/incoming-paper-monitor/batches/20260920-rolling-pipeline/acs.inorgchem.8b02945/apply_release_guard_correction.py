"""Preserve the initial release preparation and bind the independently reviewed guard fix."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,copy
F=Path(__file__).resolve().parent;O=F/'site-integration-proposal'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
audit=F/'site-integration-independent-audit/release-helper-correction-audit.json'
assert read(audit)['status']=='passed'
p=O/'release-preparation.json';before=read(p);assert before['publication_gate'] is False
old=O/'release-preparation-v1.json';assert not old.exists();old.write_bytes(p.read_bytes())
assert before['release_support_sha256']==sha(F/'delivery-helper-proposal/release_support.py')
after=copy.deepcopy(before);after['release_support_sha256']=sha(F/'release_support.py')
save(p,after)
save(O/'release-preparation-correction.json',{'at':datetime.now(timezone.utc).isoformat(),'status':'applied_after_independent_review','audit_sha256':sha(audit),'before_sha256':sha(old),'after_sha256':sha(p),'only_changed_field':'release_support_sha256','reason':'Reader renderer adds the reviewed-scope display label. Corrected guard permits only that exact derived field while preserving all scientific comparisons and deployed-byte checks.','scientific_data_changed':False,'initial_failed_attempt_closed_no_premature_ledger_completion':True})
print('Preserved initial preparation; bound the independently reviewed display-projection guard.')
