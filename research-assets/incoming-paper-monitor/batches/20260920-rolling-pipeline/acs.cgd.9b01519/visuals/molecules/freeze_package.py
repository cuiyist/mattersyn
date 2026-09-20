"""Freeze only an already validated, source-bound private author proposal."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
O=Path(__file__).resolve().parent;P=O.parents[1]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assert not(O/'package-freeze.json').exists()
inputs=read(O/'input-bindings.json');source=read(P/'package-freeze.json')
assert source['revision']==2 and inputs['source_freeze_sha256']==sha(P/'package-freeze.json')
audit=inputs['source_audit'];assert audit and sha(audit['path'])==audit['sha256']
assert read(audit['path'])['status'].startswith('passed')
cm=inputs['canonical_record_manifest'];assert cm and sha(cm['path'])==cm['sha256']
canonical_package=Path(cm['path']).parent/'package-manifest.json';assert canonical_package.exists(),'Final canonical author package not frozen.'
for p,h in inputs['canonical_records'].items():assert sha(p)==h
for p,h in inputs['inputs'].items():assert sha(p)==h
for p,h in source['source_hashes'].items():assert sha(p)==h
assert read(O/'author-validation.json')['status']=='passed_author_checks'
assert read(O/'viewer-function-checks.json')['status']=='passed_author_execution_checks'
assert read(O/'author-visual-review.json')['status']=='passed_author_visual_review'
reg=read(O/'registry-additions.json');reg['status']='private_author_proposal_pending_independent_molecular_audit';save('registry-additions.json',reg)
qual=read(O/'reference-qualification.json');qual['status']='author_qualified_pending_independent_molecular_audit';qual.pop('source_and_canonical_audits_pending',None);qual['independent_source_audit']=audit;qual['canonical_author_package']={'path':str(canonical_package),'sha256':sha(canonical_package)};qual['independent_canonical_approval']='not asserted by this molecular author package';save('reference-qualification.json',qual)
binding=read(O/'binding-author-checks.json');binding['status']='passed_author_checks';binding['canonical_freeze_confirmed']=True;save('binding-author-checks.json',binding)
checkpoint=read(O/'working-checkpoint.json');checkpoint['status']='author_complete_pending_independent_molecular_audit';checkpoint['pending']=['Independent molecule/source-slot audit','Root-owned integration and actual mounted-browser checks','Publication, if later authorized'];checkpoint['canonical_manifest_sha256']=cm['sha256'];checkpoint['registry_sha256']=sha(O/'registry-additions.json');save('working-checkpoint.json',checkpoint)
bound={str(p):sha(p)for p in sorted(O.rglob('*'))if p.is_file()and p.name!='package-freeze.json'and '__pycache__'not in p.parts}
for p,h in inputs['inputs'].items():bound[p]=h
bound.update(inputs['canonical_records']);bound[audit['path']]=audit['sha256'];bound[cm['path']]=cm['sha256'];bound[str(canonical_package)]=sha(canonical_package)
freeze={'schema':'mattersyn-chemical-proposal-freeze/1','source_id':'sommer2020','author':'/root/peng1998_reader_assets','created_at':datetime.now(timezone.utc).isoformat(),'status':'private_author_frozen_pending_independent_molecular_audit','counts':{'identities':28,'material_slots':62,'stocks':7,'stock_components':23,'distinct_2d_models':6,'unchanged_cached_3d_models':2,'symbolic_identity_cards':17,'static_previews_viewed':37,'public_asset_candidates':36},'source_freeze_sha256':sha(P/'package-freeze.json'),'source_audit':audit,'canonical_record_manifest':cm,'bound_files':bound,'binding_approved':False,'published':False,'eligible_training':False,'no_product_atomic_binding':True,'no_browser_approval':True}
save('package-freeze.json',freeze);print(json.dumps({'status':freeze['status'],'files':len(bound),'freeze_sha256':sha(O/'package-freeze.json')}))
