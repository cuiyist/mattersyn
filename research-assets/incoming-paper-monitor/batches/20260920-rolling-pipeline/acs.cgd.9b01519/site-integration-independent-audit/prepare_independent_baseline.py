"""Read-only Site boundary; all outputs belong to this private audit directory."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
A=Path(__file__).resolve().parent;G=A.parent;S=Path('[local path redacted]')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
out=A/'pre-integration-baseline.json';assert not out.exists()
records={p.name:sha(p) for p in sorted((S/'data/records').glob('*.json'))}
assert len(records)==567 and not any(k.startswith('sommer-2020-') for k in records)
shared={}
for rel in ['dist/protocol-visuals.mjs','dist/chemical-viewer.mjs','dist/crystal-viewer.mjs','dist/material-guide.mjs','dist/source-evidence.mjs','dist/paper-review.mjs','dist/illustrated-guide.css','dist/assets/chemical-registry/registry.json','dist/assets/chemical-registry/bindings.json','dist/assets/chemical-registry/solution-components.json','dist/assets/chemical-registry/product-contexts.json','data/measurement-display.json','scripts/build_dataset.py','scripts/build_atlas.py','scripts/build_paper_reviews.py','scripts/check_quality.py','dist/data/dataset-manifest.json','dist/data/validation-report.json']:
 p=S/rel
 if p.exists():
  target=A/'baseline'/rel;target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists();target.write_bytes(p.read_bytes());shared[rel]={'sha256':sha(p),'snapshot':str(target)}
training={}
for p in sorted((S/'dist/data/exports').rglob('*')):
 if p.is_file():
  rel=p.relative_to(S).as_posix();target=A/'baseline'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes());training[rel]={'sha256':sha(p),'snapshot':str(target),'bytes':p.stat().st_size}
inputs={}
for rel in ['canonical-proposal/v2/package-manifest.json','canonical-proposal/v2/record-manifest.json','canonical-reader-independent-audit/independent-audit-v2.json','source-independent-audit/independent-audit-v2.json','visuals/molecules/canonical-v2-rebind/package-freeze.json','visuals/apparatus/package-freeze.json','product-context-proposal/package-freeze.json','product-context-independent-audit/independent-audit.json']:
 inputs[rel]=sha(G/rel)
source={}
for row in read(G/'canonical-proposal/v2/record-manifest.json')['records']:
 r=read(row['path']);source[r['record_id']]={'sha256':sha(row['path']),'record_type':r['record_type'],'operations':[x['id']for x in r['operations']],'products':[{'sample_id':x['sample_id'],'composition':x['composition'],'phase':x['phase'],'recipe_link':x['recipe_link']}for x in r['products']],'requested_tasks':r['quality']['requested_tasks'],'structure_assets':r['structure_assets']}
x={'schema':'mattersyn.independent_pre_integration_boundary/1','source_id':'sommer2020','auditor':'/root/peng1998_reader_assets','created_at':datetime.now(timezone.utc).isoformat(),'status':'baseline_only_not_proposal_approval','previous_records':records,'shared_file_snapshots':shared,'training_export_snapshots':training,'approved_inputs':inputs,'canonical_scope':source,'site_modified':False}
out.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'records':len(records),'shared_files':len(shared),'training_exports':len(training),'sha256':sha(out)}))
