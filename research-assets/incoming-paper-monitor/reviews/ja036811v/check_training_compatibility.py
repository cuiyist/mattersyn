"""Read-only export validation using reviewed in-memory copies of source drafts."""
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
routes={'schwartz-2003-zno-route':{'zinc-acetate-dihydrate'},'schwartz-2003-co-route':{'zinc-acetate-dihydrate','cobalt-acetate-tetrahydrate'},'schwartz-2003-ni-route':{'zinc-acetate-dihydrate','nickel-perchlorate-hexahydrate'}}
for r in records:
 v=deepcopy(r);v['quality']['review_status']='source_reviewed';gates=eligibility(v);rid=r['record_id'];route=rid in routes
 ck(gates['precursor_selection']['eligible']==route,rid+' precursor gate')
 ck(gates['partial_protocol']['eligible']==route,rid+' protocol gate')
 ck(not any(gates[t]['eligible']for t in ['size_conditioned_recipe','exact_structure_recipe','optical_outcome','success_prediction']),rid+' unsupported targets excluded')
 entry={'record_id':rid,'sha256':sha(B/'canonical-drafts'/(rid+'.json')),'eligibility_after_review':gates}
 if route:
  pre=training_view(v,'precursor_selection');pro=training_view(v,'partial_protocol')
  ck({m['id']for m in synthesis_precursors(v)}==routes[rid],rid+' exact source salts and hydrates')
  ck(len(pro['output']['operations'])==6,rid+' full six-stage preparation and workup')
  ck(len(pro['output']['condition_options'])==4,rid+' mutually exclusive alternative solvents exported')
  states={s['id']:s for s in pro['output']['material_states']}
  ck(states['precipitated']['parent_ids']==['as-grown']and states['colloid']['parent_ids']==['washed'],rid+' alternatives do not become a co-added mixture lineage')
  ck(not any(m['property']=='diameter'for m in v['measurements']),rid+' no unrelated optical or TEM size becomes a route target')
  ck(not v['structure_assets'],rid+' no unverified measured dopant coordinates')
  ops={o['id']:o for o in pro['output']['operations']}
  ck(ops['add-base']['parameters']['temperature']['status']=='not_reported',rid+' numerical room temperature remains unknown')
  ck(ops['prepare-metal']['parameters']['total_metal_concentration']['value']==.101,rid+' total metal stock concentration preserved')
  if rid!='schwartz-2003-zno-route':
   dopant=next(m for m in v['materials']if m['id']in routes[rid]-{'zinc-acetate-dihydrate'})
   ck(dopant['quantities']['initial_dopant_fraction']['status']=='not_reported',rid+' no invented fixed feed loading')
   ck(ops['prepare-metal']['parameters']['solution_volume']['status']=='inherited',rid+' typical framework inheritance preserved')
  entry.update({'precursor_view':pre,'exported_operations':[o['id']for o in pro['output']['operations']]})
 rows.append(entry)
groups=build_groups(records)
ck(len(set(groups.values()))==1,'All 30 records remain in one source split group')
ds=next(r for r in records if r['record_id']=='schwartz-2003-dopant-series')
ck(all(not {'cobalt-acetate-tetrahydrate','nickel-perchlorate-hexahydrate'}<={c['material_id']for c in s['components']}for s in ds['stocks']),'Co and Ni comparison stocks remain separate')
data={'status':'passed_with_source_limits','scope':'Actual current export helpers applied to in-memory source-reviewed copies. No Site files or source statuses are changed.','source_id':'schwartz2003','record_count':len(records),'route_count':3,'check_count':len(checks),'checks':checks,'results':rows,'split_groups':groups,'recommendations':['Three general preparation frameworks support precursor-selection and partial-protocol supervision: pure ZnO, ZnO:Co and ZnO:Ni. Hydrated salt identity is retained.','Doped typical quantities are explicitly inherited; no fixed dopant feed fraction or exact occupancy is invented. Co and Ni are separate doping systems.','Alternatives and unknown workup settings remain explicit. Literature partial protocols are not fully specified experimental SOPs.','Kinetic titrations, nominal-loading studies, postprocessing, TEM populations, low-temperature optical specimens and magnetic aggregates are separate contexts. They must not supply an arbitrary size, field, temperature or dopant percentage to a general synthesis route.','MCD/Zeeman theory parameters, reference-host lattice constants, external bulk comparisons and author ferromagnetism interpretations are not exact-structure or success labels.','All records and matched main/SI evidence stay together when splitting the dataset.']}
(B/'training-compatibility-check.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':data['status'],'routes':3,'checks':len(checks),'exported_synthesis_operations':18}))
