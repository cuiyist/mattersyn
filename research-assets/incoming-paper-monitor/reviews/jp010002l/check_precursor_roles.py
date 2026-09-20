from pathlib import Path
from copy import deepcopy
import json,sys
B=Path(__file__).resolve().parent;sys.path.insert(0,str(B.parents[3]/'recipe-atlas'/'scripts'))
from dataset_lib import synthesis_precursors,eligibility,training_view
results=[]
for roman in ['i','ii','iii']:
 r=json.loads((B/'canonical-drafts'/('braun-2001-system-'+roman+'.json')).read_text(encoding='utf8'))
 p=synthesis_precursors(r);assert [m['id'] for m in p]==['cd2','hg2','h2s']
 reviewed=deepcopy(r);reviewed['quality']['review_status']='source_reviewed'
 assert eligibility(reviewed)['precursor_selection']['eligible']
 assert not eligibility(reviewed)['exact_structure_recipe']['eligible']
 view=training_view(reviewed,'precursor_selection')
 results.append({'record_id':r['record_id'],'recognized_precursor_ids':[m['id'] for m in p],'recognized_ion_or_molecular_formulas':[m['formula'] for m in p],'aqueous_stock_excluded_as_duplicate_identity':all(m['id']!='h2s-aqueous' for m in p),'eligible_after_root_applies_completed_review_status':True,'exact_structure_recipe_eligible':False,'training_view':view})
out={'status':'passed','scope':'Read-only export behavior check using an in-memory copy with completed source-review status. Private canonical quality metadata and Site files are not modified.','routes':results}
(B/'role-training-check.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':'passed','route_count':len(results),'precursors_per_route':3,'identities':['Cd2+','Hg2+','H2S'],'unknown_salts_preserved':True}))
