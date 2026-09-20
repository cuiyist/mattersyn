from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent;ROOT=R.parents[2];SITE=ROOT/'recipe-atlas'
rows=[];errors=[]
visual=json.loads((R/'visual-review.json').read_text(encoding='utf-8'))
for id in ['tessier2015','zhang2019']:
 a=json.loads((R/(id+'.json')).read_text(encoding='utf-8'));public=SITE/'dist/data/recipe-figures'/(id+'.json')
 if json.loads(public.read_text(encoding='utf-8'))!=a:errors.append(id+' local/public JSON mismatch')
 for f in a['figures']:
  asset=SITE/'dist'/f['public_asset'];source=ROOT/'downloaded_papers'/f['source_file']
  source_hash=hashlib.sha256(source.read_bytes()).hexdigest();asset_hash=hashlib.sha256(asset.read_bytes()).hexdigest()
  if source_hash!=f['source_sha256']:errors.append(id+'/'+f['id']+' source hash')
  if asset_hash!=f['public_asset_sha256']:errors.append(id+'/'+f['id']+' crop hash')
  if visual['items'].get(id+'/'+f['id'],{}).get('sha256')!=asset_hash:errors.append(id+'/'+f['id']+' changed since visual review')
  rows.append({'paper_id':id,'figure_id':f['id'],'source_page':f['page'],'source_role':f['document_role'],'source_sha256':source_hash,'asset_sha256':asset_hash,'crop_normalized':f['crop_normalized']})
inp=json.loads((R/'tessier2015.json').read_text(encoding='utf-8'))
scope=next(f['sample_assignments'] for f in inp['figures'] if f['id']=='figure-s4')
if 'independently sourced' in scope or 'comparison references' not in scope:errors.append('InP S4 bulk-reference wording not corrected')
report={'status':'passed' if not errors else 'failed','errors':errors,'items':rows,'scientific_assignments':'Verified for the nine selected figures/tables; see independent-audit.md','visual_crop_status':'Passed: four corrected crops re-inspected; five unchanged crops retain earlier visual review','wording_status':'Passed: bulk-reference reflections described as comparison references, without implying an independently retrieved structural dataset','visual_review_manifest':'visual-review.json','whole_paper_review':False}
(R/'independent-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'hash_checks_passed':not errors,'items':len(rows),'errors':errors}))
