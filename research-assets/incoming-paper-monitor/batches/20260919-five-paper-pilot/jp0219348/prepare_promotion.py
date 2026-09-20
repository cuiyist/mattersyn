"""Stage metadata-only review promotion for a final independent integration check."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json
H=Path(__file__).resolve().parent
O=H/'site-integration-proposal'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
audits={}
for rel in ['canonical-proposal/audit-v2/independent-audit.json','si-complete-candidate/independent-audit.json','structure-candidate/independent-audit-addendum.json','visuals/molecules-independent-audit/independent-audit.json','visuals/molecules-independent-audit/binding-revision-3-delta-audit.json','publication-projection-audit/publication-projection-audit.json']:
 p=H/rel;assert p.exists(),p;audits[rel]=sha(p)
scope='Complete supplied 9-page main article and matched 14-page SI reviewed. Separate independent source, canonical/reader, reflection-table and molecular-binding audits passed. One synthesis route, three acquisition procedures and six analytical/model contexts retain their own sample identities. Average position/occupancy reconstruction is qualified separately; condition conflicts, two uncertain SI signs and unresolved physical sample links remain explicit. No exact ordered structure or training task is admitted.'
oldgap='CIF qualification is a separate pending gate. The SI aggregate passed its own audit with two unresolved signs; this canonical proposal does not convert reflection intensities into an exact structure or training label.'
newgap='A curator reconstruction of the reported average positions and occupancies is qualified for source interpretation. It omits unresolved ADPs, preserves mixed and alternative sites, and is not a full refinement, ordered DFT model or exact-structure training label. Two SI signs remain unresolved.'
approved_structures={
 'heo-2003-in66-route':'final',
 'heo-2003-single-crystal-acquisition':'final',
 'heo-2003-average-structure':'average-model',
}
changes=[]
for p in sorted((H/'canonical-proposal/v2/canonical-drafts').glob('*.json')):
 r=read(p);before=copy.deepcopy(r)
 r['collection']='reviewed_literature'
 if r['record_id']=='heo-2003-in66-route':r['reader_role']='synthesis_route'
 r['quality']['review_status']='source_reviewed'
 r['quality']['review_scope']=scope
 r['quality']['missing_fields']=[newgap if s==oldgap else s for s in r['quality']['missing_fields']]
 for s in r['sources']:
  s['main_status']='Complete supplied 9-page main article read, extracted and independently audited; source conflicts retained.'
  s['si_status']='Matched 14-page reflection list fully read and independently audited: 1209 rows, with two signed values preserved as unresolved nulls.'
 if r['record_id'] in approved_structures:
  sample=approved_structures[r['record_id']];assert sample in {x['sample_id'] for x in r['products']},sample
  r['structure_assets'].append({'id':'heo2003-average-position-occupancy','role':'computed_reference','sample_id':sample,'url':'/assets/crystal-references/heo2003-average-position-occupancy.cif','description':'Curator reconstruction from the adopted Table 2 average structure: mixed Si/Al sites, fractional indium occupancies and alternative InII/InIIa positions. Geometry/occupancy only; ADPs omitted. Nominal Si100Al92 differs from average Si96Al96. Not an author-supplied CIF, unique ordered specimen, full refinement or DFT-ready input.','eligible_as_measured_label':False})
 assert not r['quality']['requested_tasks']
 for key in ['materials','stocks','operations','condition_options','products','measurements','material_states','intended_target','lineage']:
  assert before[key]==r[key],(p,key)
 target=O/'records'/p.name;write(target,r)
 changes.append({'record_id':r['record_id'],'before_sha256':sha(p),'proposal_sha256':sha(target),'added_qualified_structure_references':len(r['structure_assets'])-len(before['structure_assets']),'science_values_and_sample_links_unchanged':True})
reader=read(O/'reader/heo2003.json')
reader.update(coverage_status='supplied_main_and_matched_si_review_complete',independent_audit=scope,source_review_promoted=True,publication_status='Reviewed contribution staged for integration; release and browser gates are tracked separately.',review_state='source_reviewed',training_note='No training task is admitted. The average position/occupancy CIF is a qualified source reconstruction, not an exact ordered structure or DFT-ready model.')
reader['audit_details']={'scope':scope,'audit_sha256':audits,'source_conflicts_resolved':False,'training_promotions':0}
reader['supporting_information']='Matched 14-page reflection list fully read and independently audited: 1209 rows. Two printed signs remain unresolved and are preserved as numeric nulls with both candidates. Downloadable transcribed rows retain their original page/block/row identities.'
reader['remaining_gaps']=[newgap if s==oldgap else s for s in reader['remaining_gaps']]
for item in reader['recipe_inventory']:
 item['status']='source_reviewed';item['gaps']=[newgap if s==oldgap else s for s in item['gaps']]
for key in ['figures','tables','schemes','equations','source_notes']:
 for item in reader.get(key,[]):item['reviewed']=True
# The published renderer expects record-id arrays. Preserve the prior prose separately.
reader['route_evidence_scope_notes']=copy.deepcopy(reader['route_evidence_contexts'])
reader['route_evidence_contexts']={'heo-2003-in66-route':[x['record_id'] for x in changes if x['record_id']!='heo-2003-in66-route']}
reader['characterization_inventory']=[{'technique':s} if isinstance(s,str) else s for s in reader['characterization_inventory']]
reader['presentation_gates']={'canonical_source_audit':True,'reader_source_audit':True,'molecular_bindings':True,'apparatus_bindings':'pending independent audit','average_position_occupancy_binding':'pending final product viewer audit','exact_ordered_atomic_structure_binding':False,'browser_render':False,'site_integration':False}
write(O/'promoted-reader/heo2003.json',reader)
write(O/'promotion-proposal-manifest.json',{'schema':'mattersyn.heo_promotion_proposal/1','at':datetime.now(timezone.utc).isoformat(),'author':'/root','status':'proposal_requires_remaining_visual_and_independent_promotion_checks','audits':audits,'records':changes,'counts':{'records':10,'measurements':473,'qualified_average_model_references':3,'new_training_tasks':0,'exact_structure_pairs':0},'gates_pending':['apparatus independent source audit','product and reflection reader independent audit','complete integrated browser review','independent final promotion/delta audit','anonymous publication verification']})
print(json.dumps({'proposed_records':len(changes),'source_values_unchanged':True,'training_promotions':0}))
