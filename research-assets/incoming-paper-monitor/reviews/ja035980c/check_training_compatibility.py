"""Read-only training-view verification of the private Banerjee records."""
from pathlib import Path
from copy import deepcopy
import sys,json,hashlib
B=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(B.parents[3]/'recipe-atlas'/'scripts'))
from dataset_lib import eligibility,training_view,synthesis_precursors,build_groups
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records=[json.loads(p.read_text(encoding='utf8'))for p in sorted((B/'canonical-drafts').glob('*.json'))]
rows=[];checks=[]
def ck(test,label):
 checks.append({'label':label,'passed':bool(test)})
 if not test:raise AssertionError(label)
for r in records:
 v=deepcopy(r);v['quality']['review_status']='source_reviewed';gates=eligibility(v)
 route=r['record_id']=='banerjee-2003-growth'
 ck(gates['precursor_selection']['eligible']==route,r['record_id']+' precursor gate')
 ck(gates['partial_protocol']['eligible']==route,r['record_id']+' protocol gate')
 ck(not any(gates[t]['eligible']for t in ['size_conditioned_recipe','exact_structure_recipe','optical_outcome','success_prediction']),r['record_id']+' unsupported targets excluded')
 entry={'record_id':r['record_id'],'sha256':sha(B/'canonical-drafts'/(r['record_id']+'.json')),'eligibility_after_review':gates}
 if route:
  pre=training_view(v,'precursor_selection');pro=training_view(v,'partial_protocol')
  ck({m['id']for m in synthesis_precursors(v)}=={'cadmium-oxide','tellurium-source'},'Only CdO and unresolved tellurium precursor enter precursor identities')
  ck(next(m for m in v['materials']if m['id']=='tellurium-source')['formula']is None,'Tellurium starting form is not fabricated')
  ck('requested_host'in pre['input'],'Nanotube host retained in task input')
  ck(len(pre['output']['process_materials'])==1 and pre['output']['process_materials'][0]['role']=='host_matrix','Host retained in separate process material field')
  ck(len(pro['output']['operations'])==17,'Full upstream oxidation and growth/workup exported')
  ck(not any(m['property']=='diameter'for m in v['measurements']),'No long-axis range relabeled as diameter')
  ck(not v['structure_assets'],'No invented measured atomic coordinates')
  entry.update({'precursor_view':pre,'exported_operations':[o['id']for o in pro['output']['operations']]})
 rows.append(entry)
groups=build_groups(records)
ck(len(set(groups.values()))==1,'All 14 records stay in one source split group')
data={'status':'passed_with_source_limits','scope':'Actual current export helpers used with in-memory source-reviewed copies only. No Site files or review statuses are changed.','source_id':'banerjee2003','record_count':len(records),'route_count':1,'check_count':len(checks),'checks':checks,'results':rows,'split_groups':groups,'recommendations':['One route supports nominal precursor selection and partial-protocol supervision. Tellurium feed identity, all precursor charges and stock molarity remain unresolved.','Preserve oxidized MWNT as the requested host and as a separate process material, not an unreported CdTe dopant.','Keep tube-bound long-axis/aspect ranges, free washings and no-tube comparison particles separate. These do not supply an exact diameter-conditioned recipe target.','XPS and microscopy acquisition settings are not synthesis parameters. Contextual 350 °C surface stability and 170 cm−1 literature Raman comparison remain outside route training.','All records from this study must share the same split group. Missing measurements and absent optical performance are not zero-valued or failed-outcome labels.']}
(B/'training-compatibility-check.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':data['status'],'routes':1,'checks':len(checks),'operation_count':17}))
