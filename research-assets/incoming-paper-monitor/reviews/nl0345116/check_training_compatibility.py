"""Read-only task-view validation of the private Sashchiuk literature records."""
from pathlib import Path
from copy import deepcopy
import sys,json,hashlib
B=Path(__file__).resolve().parent;sys.dont_write_bytecode=True
sys.path.insert(0,str(B.parents[3]/'recipe-atlas'/'scripts'))
from dataset_lib import eligibility,training_view,synthesis_precursors,build_groups
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records=[json.loads(p.read_text(encoding='utf8'))for p in sorted((B/'canonical-drafts').glob('*.json'))]
routes={'sashchiuk-2004-'+x for x in ['individual-low','sphere-intermediate','wire-intermediate','wire-high']};checks=[];rows=[]
def ck(test,label):
 checks.append({'label':label,'passed':bool(test)})
 if not test:raise AssertionError(label)
for r in records:
 v=deepcopy(r);v['quality']['review_status']='source_reviewed';g=eligibility(v);rid=r['record_id'];route=rid in routes
 ck(g['precursor_selection']['eligible']==route,rid+' precursor gate')
 ck(g['partial_protocol']['eligible']==route,rid+' partial-protocol gate')
 ck(not any(g[t]['eligible']for t in ['size_conditioned_recipe','exact_structure_recipe','optical_outcome','success_prediction']),rid+' unsupported outcomes excluded')
 result={'record_id':rid,'sha256':sha(B/'canonical-drafts'/(rid+'.json')),'eligibility_after_review':g}
 if route:
  pre=training_view(v,'precursor_selection');p=training_view(v,'partial_protocol')
  ck({m['id']for m in synthesis_precursors(v)}=={'lead-chxbu','selenium'},rid+' source-named Pb and Se precursors only')
  ck(next(m for m in v['materials']if m['id']=='lead-chxbu')['formula']is None,rid+' unresolved lead salt formula retained')
  ck(len(p['output']['operations'])==5,rid+' five source-specific preparative operations')
  ck(not any(o['stage']=='characterization'for o in p['output']['operations']),rid+' characterization excluded')
  ck(len(p['output']['condition_options'])==2,rid+' alternative TOPO grades preserved')
  ck(all(q['quantities']['relative_mass']['unit']=='mass parts'for q in v['stocks'][0]['components']),rid+' mass proportions not molar or absolute charges')
  ck(not v['structure_assets'],rid+' no supplied measured coordinate label')
  ck(all(o['environment']['status']=='not_reported'for o in v['operations']if o['id']not in ['prepare-stock','heat-topo']),rid+' unstated later atmosphere remains unknown')
  ck(any('aliquot-workup'in x['url']for x in v['context_links']),rid+' aliquot workup stays separately linked')
  ck(not any(m['property']=='diameter'for m in v['measurements']),rid+' no unrelated aggregate or primary diameter substituted')
  result.update(precursor_view=pre,exported_operations=[o['id']for o in p['output']['operations']])
 rows.append(result)
groups=build_groups(records);ck(len(set(groups.values()))==1,'All main-paper routes, aliquots and models share one split group')
data={'status':'passed_with_source_limits','source_id':'sashchiuk2004','scope':'Actual current Site export helpers called read-only with source-reviewed copies in memory; no review status or Site file changed.','record_count':len(records),'route_count':4,'check_count':len(checks),'checks':checks,'results':rows,'split_groups':groups,'recommendations':['Four literature routes support source-named precursor selection and partial-protocol supervision. Pb-cHxBu exact formula/identity remains unresolved; outputs must not be interpreted as unambiguous purchasable salts.','The mass-part ratios are not absolute charges, molar ratios or final stock concentrations. Missing stock-injection amount prevents a complete reconstruction of precursor inventory.','Spherical trajectory windows, intermediate-stock90min wires and high-stock40min wires are separate source claims. Caption/body stock conflicts and unknown image-to-batch joins preclude exact specimen-outcome supervision.','Removed aliquots are quenched in1mL methanol and purified separately; this does not establish whole-batch workup. Partial route exports retain the evidence-linked workup procedure through the reader context, not an invented whole-batch step.','No size-conditioned, measured-CIF, optical-outcome or success target is admitted. Assembly diameters and wire widths are not individual-crystal diameters.','Electrical-device conditions and author dipole/transport calculations are not synthesis parameters or independently measured material labels.','Keep the entire source group, duplicate source copies and linked aliquots together across data splits.']}
(B/'training-compatibility-check.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':data['status'],'routes':4,'checks':len(checks),'synthesis_operations':20}))
