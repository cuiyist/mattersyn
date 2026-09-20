"""Read-only task-view check of private Yi records; no Site state is changed."""
from pathlib import Path
from copy import deepcopy
import sys,json,hashlib
B=Path(__file__).resolve().parent;sys.path.insert(0,str(B.parents[3]/'recipe-atlas'/'scripts'))
from dataset_lib import eligibility,training_view,synthesis_precursors
rows=[]
for key in ['anneal-600','anneal-700','anneal-800','anneal-900','anneal-1000','bulk']:
 p=B/'canonical-drafts'/('yi-2002-'+key+'.json');r=json.loads(p.read_text(encoding='utf8'));v=deepcopy(r);v['quality']['review_status']='source_reviewed'
 gates=eligibility(v);prec=training_view(v,'precursor_selection');protocol=training_view(v,'partial_protocol')
 assert gates['precursor_selection']['eligible'] and gates['partial_protocol']['eligible']
 assert not any(gates[t]['eligible']for t in ['size_conditioned_recipe','exact_structure_recipe','optical_outcome','success_prediction'])
 assert len(protocol['output']['operations'])==(3 if key=='bulk'else 16)
 assert set(m['id']for m in synthesis_precursors(v))==({'lanthanum-oxide','molybdenum-trioxide','ytterbium-oxide','erbium-oxide'}if key=='bulk'else{'lanthanum-oxide','ytterbium-oxide','erbium-oxide','ammonium-molybdate'})
 if key!='bulk':
  mol=next(m for m in v['materials']if m['id']=='ammonium-molybdate');assert mol['formula']=='(NH4)2MoO4'
  assert mol['quantities']['mass']['value']==(1.961 if key=='anneal-800'else None)
  assert mol['quantities']['amount']['value']==(9.37 if key=='anneal-800'else None)
  assert next(o for o in v['operations']if o['id']=='ramp')['parameters']['heating_rate']['value']==(20 if key=='anneal-800'else None)
 assert not any(m['property']=='diameter'for m in v['measurements'])
 rows.append({'record_id':v['record_id'],'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'eligibility_after_review':gates,'precursors':prec['output']['precursors'],'exported_operations':[o['id']for o in protocol['output']['operations']],'limits':['Host/dopant notation is not a refined exact atomic composition.','Printed ammonium molybdate identity/mass/mmol are not repaired; inherited comparison recipes lack independently stated charges.','Crystallite-size, TEM range and instrumental particle distribution are distinct and do not define a common per-recipe diameter target.']})
data={'status':'passed_with_source_limits','scope':'Only in-memory source-reviewed copies tested against actual current export helpers; no Site or review statuses edited.','route_count':len(rows),'results':rows,'excluded_views':['size_conditioned_recipe','exact_structure_recipe','optical_outcome','success_prediction'],'recommendations':['Six synthesis routes may support partial-protocol and nominal precursor selection, not corrected exact dose prediction.','Keep all source-group variants together during splitting; unknown physical batches are not independent demonstrations.','Er-series markers are characterization comparisons, not complete altered-composition recipes.','No quantum-yield labels or synthetic spectra are available.']}
(B/'training-compatibility-check.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'status':data['status'],'routes':len(rows),'operation_counts':[len(x['exported_operations'])for x in rows]}))
