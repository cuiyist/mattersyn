"""Private read-only compatibility check; no premature review-status promotion on disk."""
from pathlib import Path
from copy import deepcopy
import json,sys,hashlib
B=Path(__file__).resolve().parent;sys.path.insert(0,str(B.parents[3]/'recipe-atlas'/'scripts'))
from dataset_lib import synthesis_precursors,eligibility,training_view
out=[]
for suffix in ['ctab-silica-host','ctab-cds-loading','copolymer-cds-loading']:
 p=B/'canonical-drafts'/('besson-2002-'+suffix+'.json');r=json.loads(p.read_text(encoding='utf8'));v=deepcopy(r);v['quality']['review_status']='source_reviewed'
 expected=['teos'] if suffix=='ctab-silica-host' else ['cadmium-nitrate','h2s']
 assert [x['id'] for x in synthesis_precursors(v)]==expected
 gates=eligibility(v);assert gates['precursor_selection']['eligible'] and gates['partial_protocol']['eligible']
 assert not gates['size_conditioned_recipe']['eligible'] and not gates['exact_structure_recipe']['eligible']
 train=training_view(v,'precursor_selection')
 if suffix!='ctab-silica-host':
  assert train['input']['requested_host']['value']==r['intended_target']['host']['value']
  assert len(train['output']['process_materials'])==1 and train['output']['process_materials'][0]['role']=='host_matrix'
 out.append({'record_id':r['record_id'],'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'recognized_precursor_ids':expected,'eligibility_after_completed_review':gates,'precursor_selection_view':train})
report={'status':'passed','scope':'Actual export helpers tested using in-memory source_reviewed copies only. Private canonical review status and Site remain unchanged.','route_count':3,'limits':['Cd nitrate hydration, sodium citrate form and absolute charges remain unknown.','Two optical endpoint outcomes per loading trajectory are preserved, but no arbitrary first-endpoint size-conditioned export is enabled.','No measured atomic coordinates; exact-structure task remains excluded.'],'routes':out}
(B/'training-compatibility-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':'passed','route_count':3,'host_distinctions_preserved':True,'exact_structure_excluded':True}))
