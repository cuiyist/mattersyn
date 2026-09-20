"""Capture a read-only pre-integration boundary for the Ghosh delta audit."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
A=Path(__file__).resolve().parent;G=A.parent
S=Path('[local path redacted]')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
records={p.name:sha(p) for p in sorted((S/'data/records').glob('*.json'))}
assert len(records)==546 and not any(k.startswith('ghosh-2012-') for k in records)
shared={}
for rel in [
 'dist/protocol-visuals.mjs','dist/chemical-viewer.mjs','dist/crystal-viewer.mjs',
 'dist/material-guide.mjs','dist/source-evidence.mjs','dist/illustrated-guide.css',
 'dist/assets/chemical-registry/registry.json','dist/assets/chemical-registry/bindings.json',
 'dist/assets/chemical-registry/solution-components.json','dist/assets/chemical-registry/product-contexts.json',
 'data/measurement-display.json','scripts/build_dataset.py','scripts/build_atlas.py','scripts/build_paper_reviews.py','scripts/check_quality.py',
]:
 p=S/rel
 if p.exists():
  target=A/'baseline'/rel;target.parent.mkdir(parents=True,exist_ok=True)
  assert not target.exists(),str(target)
  target.write_bytes(p.read_bytes());shared[rel]={'sha256':sha(p),'snapshot':str(target)}
approved={}
for rel in ['canonical-proposal/v2/package-manifest.json','canonical-proposal/v2/record-manifest.json',
 'canonical-reader-independent-audit/independent-audit-v2.json','source-independent-audit/independent-audit-v2.json',
 'visuals/molecules/metadata-correction-v3/package-freeze.json','visuals/molecules-independent-audit/independent-audit.json',
 'visuals/apparatus/package-freeze.json','visuals/apparatus-independent-audit/independent-audit.json']:
 approved[rel]=sha(G/rel)
records_source={}
for row in read(G/'canonical-proposal/v2/record-manifest.json')['records']:
 d=read(row['path']);records_source[row['record_id']]={'sha256':sha(row['path']),'record_type':d['record_type'],'operations':[x['id'] for x in d['operations']],
 'products':[{'sample_id':x['sample_id'],'composition':x['composition'],'phase':x['phase'],'recipe_link':x['recipe_link']} for x in d['products']],
 'requested_tasks':d['quality']['requested_tasks'],'structure_assets':d['structure_assets']}
out={'schema':'mattersyn.independent_pre_integration_boundary/1','source_id':'ghosh2012','auditor':'/root/peng1998_reader_assets','created_at':datetime.now(timezone.utc).isoformat(),
 'status':'baseline_only_not_proposal_approval','previous_records':records,'shared_file_snapshots':shared,'approved_inputs':approved,'canonical_scope':records_source,'site_modified':False}
p=A/'pre-integration-baseline.json';assert not p.exists();p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'saved','previous_records':len(records),'canonical_records':len(records_source),'shared_snapshots':len(shared),'sha256':sha(p)}))
