"""Read-only checks of current training-export behavior with source-scoped labels."""
from pathlib import Path
from copy import deepcopy
import sys,json,hashlib
B=Path(__file__).resolve().parent;sys.path.insert(0,str(B.parents[3]/'recipe-atlas'/'scripts'))
from dataset_lib import eligibility,training_view,synthesis_precursors
results=[]
for key,hours in [('sg1',1),('sg2',3),('sg3',6),('sg4',12),('afm1',5),('afm2',30)]:
 p=B/'canonical-drafts'/('dantas-2002-'+key+'.json');r=json.loads(p.read_text(encoding='utf8'));v=deepcopy(r);v['quality']['review_status']='source_reviewed'
 assert [o['id']for o in v['operations']]==['mix','melt','quench','stress-relief','anneal']
 assert v['operations'][-1]['parameters']['duration']['value']==hours
 assert [m['id']for m in synthesis_precursors(v)]==['lead-dioxide','sulfur-source']
 assert next(m for m in v['materials']if m['id']=='lead-dioxide')['formula']=='PbO2'
 assert next(m for m in v['materials']if m['id']=='sulfur-source')['formula']is None
 gates=eligibility(v);assert gates['precursor_selection']['eligible'] and gates['partial_protocol']['eligible']
 assert not any(gates[t]['eligible']for t in ['size_conditioned_recipe','exact_structure_recipe','optical_outcome','success_prediction'])
 precursor=training_view(v,'precursor_selection');protocol=training_view(v,'partial_protocol')
 assert precursor['input']['composition']=='PbS/glass' and 'requested_host'in precursor['input']
 assert len(precursor['output']['process_materials'])==1
 assert len(protocol['output']['operations'])==5
 assert not any(m['property']=='diameter'for m in v['measurements'])
 results.append({'record_id':r['record_id'],'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'eligibility_after_completed_source_review':gates,'recognized_precursors':precursor['output']['precursors'],'host_preserved':precursor['input']['requested_host'],'full_inherited_protocol_operations':[o['id']for o in protocol['output']['operations']],'limits':['Precursor list remains partial: printed PbO2 plus chemically unidentified sulfur source. Do not score it as a complete exact precursor-set target.','Shared preparation is inherited; six annealing variants do not establish six independent fusion batches.','Source size/radius/height ambiguity intentionally excludes diameter-conditioned training.']})
data={'status':'passed_with_partial_precursor_limit','scope':'Actual helper behavior tested only with in-memory reviewed copies; no review status or Site files changed.','route_count':6,'results':results,'display_recommendations':['Structural category should explicitly include source_reported_optically_inferred_qd_size, source_reported_afm_qd_size, figure_reported_afm_grain_height, figure_reported_afm_substrate_depth, figure4_histogram_displayed_depth_range and reported_afm_size_distribution.','Do not classify optical/theory energies or effective masses as measured atomic crystal data.','Keep size/radius/height labels and different SG/AFM cohorts visible in both reader and machine views.']}
(B/'training-compatibility-check.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':data['status'],'routes':6,'full_operations_per_route':5,'size_exact_optical_success_exports_excluded':True}))
