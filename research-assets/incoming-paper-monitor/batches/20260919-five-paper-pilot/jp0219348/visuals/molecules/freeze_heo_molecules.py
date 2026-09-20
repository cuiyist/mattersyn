"""Freeze a passed author proposal, never grant independent or binding approval."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json
O=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_bytes())
assert not (O/'package-freeze.json').exists(),'Preserve a revision before any authorized rebuild.'
v=load(O/'author-validation.json');g=load(O/'generation-manifest.json')
assert v['mechanical_checks']['failed']==0 and v['independent_audit'] is False
assert len(v['manual_preview_scope'])==11 and all(x['actually_viewed'] for x in v['manual_preview_scope'])
for p,h in g['input_hashes'].items():assert sha(p)==h,p
for p,h in v['bound_package_files'].items():assert sha(O/p)==h,p
files={str(p.resolve()):sha(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name!='package-freeze.json'}
out={'schema':'mattersyn-private-molecular-package-freeze/1','source_id':'heo2003','author':'/root/backlog_eta','reviewer':None,'frozen_at':datetime.now(timezone.utc).isoformat(),'status':'author_frozen_pending_distinct_independent_audit_and_canonical_binding','counts':g['counts'],'author_validation_sha256':sha(O/'author-validation.json'),'bound_files':files,'bound_source_and_baseline_inputs':g['input_hashes'],'final_canonical_bindings':False,'binding_approved':False,'independent_scientific_audit':'pending','published':False,'scope':'Local reference identity drawings and source-qualified component/material proposals only; no Site import or independent approval.','remaining_gates':v['remaining_gates']}
(O/'package-freeze.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'freeze':str(O/'package-freeze.json'),'sha256':sha(O/'package-freeze.json'),'files':len(files),'checks':v['mechanical_checks'],'previews_actually_viewed':len(v['manual_preview_scope']),'counts':g['counts']}))
