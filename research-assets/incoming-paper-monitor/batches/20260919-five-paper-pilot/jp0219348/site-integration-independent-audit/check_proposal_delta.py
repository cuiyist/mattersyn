"""Independent bounded promotion/public-reader overlay checks; no Site writes."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,copy,re,sys,collections
A=Path(__file__).resolve().parent;H=A.parent;V=H/'canonical-proposal/v2';O=H/'site-integration-proposal';S=H.parents[4]/'recipe-atlas'
bound={};checks=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):p=Path(p).resolve();bound[str(p)]=sha(p);return p
def read(p):return json.loads(bind(p).read_bytes())
def ck(label,ok):checks.append({'check':label,'passed':bool(ok)})
def ptr(x,p):
    for k in p.lstrip('/').split('/') if p else []:
        k=k.replace('~1','/').replace('~0','~');x=x[int(k)] if isinstance(x,list) else x[k]
    return x
def remove(x,p):
    before,k=p.rsplit('/',1);node=ptr(x,before);k=k.replace('~1','/').replace('~0','~')
    if isinstance(node,list):node.pop(int(k))
    else:del node[k]
def walk(x,p=''):
    yield p,x
    if isinstance(x,dict):
        for k,v in x.items():yield from walk(v,p+'/'+k)
    elif isinstance(x,list):
        for i,v in enumerate(x):yield from walk(v,p+'/'+str(i))
pm=read(O/'promotion-proposal-manifest.json');xm=read(O/'projection-manifest.json');plan=read(H/'publication-projection-audit/publication-projection-proposal.json')
prior=read(H/'canonical-proposal/audit-v2/independent-audit.json');productaudit=read(H/'visuals/products-independent-audit/product-si-source-audit.json');appaudit=read(H/'visuals/apparatus/audit-v1/apparatus-source-audit.json')
ck('Independent prerequisites passed',prior['status']=='passed_bounded_canonical_reader_scope' and productaudit['status']=='passed_scientific_projection_and_function_scope' and appaudit['status']=='passed_source_scientific_svg_scope')
for name,digest in pm['audits'].items():ck('Promotion bound audit '+name,sha(bind(H/name))==digest)
oldgap='CIF qualification is a separate pending gate. The SI aggregate passed its own audit with two unresolved signs; this canonical proposal does not convert reflection intensities into an exact structure or training label.'
newgap='A curator reconstruction of the reported average positions and occupancies is qualified for source interpretation. It omits unresolved ADPs, preserves mixed and alternative sites, and is not a full refinement, ordered DFT model or exact-structure training label. Two SI signs remain unresolved.'
qualified={'heo-2003-in66-route':'final','heo-2003-single-crystal-acquisition':'final','heo-2003-average-structure':'average-model'}
records={};original={}
for row in pm['records']:
    rid=row['record_id'];p=V/'canonical-drafts'/(rid+'.json');q=O/'records'/(rid+'.json');b=read(p);r=read(q);records[rid]=r;original[rid]=b
    ck(rid+' baseline/proposal hashes',sha(p)==row['before_sha256'] and sha(q)==row['proposal_sha256'])
    expected=copy.deepcopy(b);expected['collection']='reviewed_literature'
    expected['quality']['review_status']='source_reviewed';expected['quality']['review_scope']=r['quality']['review_scope'];expected['quality']['missing_fields']=[newgap if s==oldgap else s for s in b['quality']['missing_fields']]
    for before,after in zip(expected['sources'],r['sources']):
        before['main_status']=after['main_status'];before['si_status']=after['si_status']
        ck(rid+' source status keeps2unknown signs','two signed values' in after['si_status'] and 'unresolved nulls' in after['si_status'])
    if rid=='heo-2003-in66-route':expected['reader_role']='synthesis_route'
    if rid in qualified:
        ck(rid+' exactly one computed reference',len(r['structure_assets'])==1)
        asset=r['structure_assets'][0]
        ck(rid+' qualified reference fields',asset['id']=='heo2003-average-position-occupancy' and asset['role']=='computed_reference' and asset['sample_id']==qualified[rid] and asset['eligible_as_measured_label'] is False and asset['url']=='/assets/crystal-references/heo2003-average-position-occupancy.cif')
        ck(rid+' clear source-average limitations',all(s in asset['description'] for s in ['ADPs omitted','Not an author-supplied CIF','DFT-ready']))
        expected['structure_assets']=r['structure_assets']
    ck(rid+' only explicit reviewed-metadata/reference/reader-role delta',r==expected)
    ck(rid+' no tasks',r['quality']['requested_tasks']==[])
ck('10records/473measurements/3qualified references',len(records)==10 and sum(len(r['measurements']) for r in records.values())==473 and sum(len(r['structure_assets']) for r in records.values())==3)
ck('Reader role only actual synthesis route',[(rid,r['reader_role']) for rid,r in records.items() if 'reader_role' in r]==[('heo-2003-in66-route','synthesis_route')] and records['heo-2003-in66-route']['record_type']=='literature_protocol' and any(o['stage']=='synthesis' for o in records['heo-2003-in66-route']['operations']))
base=read(V/'public-review-proposal/heo2003.json');projected=read(O/'reader/heo2003.json');promoted=read(O/'promoted-reader/heo2003.json')
ck('Projection input/current bytes bound',sha(V/'public-review-proposal/heo2003.json')==xm['input_sha256'] and sha(O/'reader/heo2003.json')==xm['public_reader_sha256'])
expected=copy.deepcopy(base)
for entry in plan['private_path_removals']:
    ck(entry['pointer']+' expected private value',ptr(expected,entry['pointer'])==entry['value']);remove(expected,entry['pointer'])
for entry in plan['source_role_corrections']:
    p,k=entry['pointer'].rsplit('/',1);node=ptr(expected,p);ck(entry['pointer']+' original role',node[k]==entry['before']);node[k]=entry['after']
for entry in plan['whole_page_attachment_removals']:
    obj=ptr(expected,entry['object_pointer']);ck(entry['object_pointer']+' expected whole-page URL',obj['public_asset']==entry['public_asset'])
    if '/original_assets/' in entry['object_pointer']:remove(expected,entry['object_pointer'])
    else:
        for key in entry['remove_keys']:obj.pop(key)
remove(expected,'/si_aggregate_evidence/audit_path')
expected['document_identity_verification']['source_hashes']={Path(k).name:v for k,v in expected['document_identity_verification']['source_hashes'].items()}
pageids={x['asset_id'] for x in plan['binary_exclusions']}
for formula,ids in expected['material_original_asset_ids'].items():expected['material_original_asset_ids'][formula]=[x for x in ids if x not in pageids]
expected['counts']['original_assets']=16;expected['counts']['source_page_identities_retained_without_images']=23
for sec in expected['reader_sections']:
    for item in sec['items']:
        if item['id'] in {'asset-'+p for p in pageids}:item['notes'].append('Source-page identity and extracted evidence are retained; complete page images remain local. Selected figures and tables are available separately.')
ck('Exact public projection equals approved removals plus stated navigation/count metadata',projected==expected)
for row in plan['retained_selected_assets']:
    p=O/'dist'/row['public_path'];ck(row['asset_id']+' exact retained original bytes',p.is_file() and sha(bind(p))==row['sha256'])
for row in plan['binary_exclusions']:ck(row['asset_id']+' whole-page binary absent',not (O/'dist'/row['proposed_public_path']).exists())
exp=copy.deepcopy(projected)
display_meta=['coverage_status','independent_audit','source_review_promoted','publication_status','review_state','training_note','supporting_information','presentation_gates','audit_details']
for key in display_meta:exp[key]=promoted[key]
exp['remaining_gaps']=[newgap if s==oldgap else s for s in exp['remaining_gaps']]
for item in exp['recipe_inventory']:item['status']='source_reviewed';item['gaps']=[newgap if s==oldgap else s for s in item['gaps']]
for category in ['figures','tables','schemes','equations','source_notes']:
    for item in exp.get(category,[]):item['reviewed']=True
exp['route_evidence_scope_notes']=copy.deepcopy(exp['route_evidence_contexts']);exp['route_evidence_contexts']={'heo-2003-in66-route':sorted(set(records)-{'heo-2003-in66-route'})}
exp['characterization_inventory']=[{'technique':x} if isinstance(x,str) else x for x in exp['characterization_inventory']]
ck('Exact promoted reader delta is stated status/navigation overlay',promoted==exp)
ck('All372 reader items and535typed facts exactly retained after public attachment projection',promoted['reader_sections']==projected['reader_sections'] and sum(len(s['items']) for s in promoted['reader_sections'])==372 and sum(len(i['facts']) for s in promoted['reader_sections'] for i in s['items'])==535)
ck('All473 canonical measurements unchanged',all(r['measurements']==original[rid]['measurements'] for rid,r in records.items()))
ck('All original document locators and hashes unchanged',promoted['documents']==base['documents'])
ck('SI1209rows/2nulls unchanged',promoted['si_aggregate_evidence']==projected['si_aggregate_evidence'] and promoted['si_aggregate_evidence']['counts']['rows']==1209 and promoted['si_aggregate_evidence']['counts']['unresolved_sign_cells']==2)
ck('New route navigation never changes samples',promoted['route_evidence_scope_notes']==base['route_evidence_contexts'] and set(promoted['route_evidence_contexts']['heo-2003-in66-route'])==set(records)-{'heo-2003-in66-route'})
ck('Three technique labels preserved',promoted['characterization_inventory']==[{'technique':s} for s in base['characterization_inventory']])
ck('No training/exact-structure approval',promoted['training_eligible'] is False and promoted['presentation_gates']['exact_ordered_atomic_structure_binding'] is False and promoted['audit_details']['training_promotions']==0 and promoted['audit_details']['source_conflicts_resolved'] is False)
ck('Pending final delivery gates remain explicit',promoted['presentation_gates']['browser_render'] is False and promoted['presentation_gates']['site_integration'] is False)
for name,digest in promoted['audit_details']['audit_sha256'].items():ck('Reader audit metadata '+name,sha(bind(H/name))==digest)
for p,x in walk(promoted):
    if isinstance(x,str):ck('Public value path hygiene '+p,not re.search(r'(?<![A-Za-z])[A-Za-z]:[\\/]',x))
    if isinstance(x,dict):ck('Public key path hygiene '+p,not any(re.match(r'^[A-Za-z]:[\\/]',k) for k in x))
sourceurls={x['proposed_public_path'] for x in plan['binary_exclusions']};ck('No whole-page URL in promoted reader',not any(isinstance(x,str) and x in sourceurls for p,x in walk(promoted)))
sys.path.insert(0,str(S/'scripts'));import dataset_lib
# Validate the declared optional enum in memory only: the import script has not
# modified Site yet. All pre-existing schema constraints remain unchanged.
original_schema=dataset_lib.SCHEMA;dataset_lib.SCHEMA=copy.deepcopy(original_schema)
dataset_lib.SCHEMA['properties']['reader_role']={'enum':['synthesis_route','supporting_procedure','contextual_observation']}
for rid,r in records.items():
    errors=dataset_lib.validate_record(r);ck(rid+' full schema/semantics with declared optional reader_role',not errors)
    ck(rid+' all six task admissions false',all(not x['eligible'] for x in dataset_lib.eligibility(r).values()))
dataset_lib.SCHEMA=original_schema
for p in [H/'prepare_promotion.py',H/'prepare_public_projection.py',H/'import_reviewed_heo.py',S/'scripts/dataset_lib.py',S/'scripts/schema_definition.py',Path(__file__)]:bind(p)
failure=[x for x in checks if not x['passed']]
report={'schema':'mattersyn.heo_private_promotion_projection_delta_audit/1','at':datetime.now(timezone.utc).isoformat(),'author':'/root','auditor':'/root/backlog_eta','reviewer':'/root/backlog_eta','status':'passed_private_staged_promotion_and_projection_scope' if not failure else 'findings','counts':{'checks':len(checks),'failed':len(failure),'records':10,'reader_items':372,'typed_reader_facts':535,'canonical_measurements':473,'qualified_average_references':3,'reader_role_additions':1,'selected_original_crops':16,'public_whole_page_images':0,'new_training_tasks':0,'exact_structure_pairs':0},'record_hashes':{rid:sha(O/'records'/(rid+'.json')) for rid in records},'promoted_reader_sha256':sha(O/'promoted-reader/heo2003.json'),'projection_reader_sha256':sha(O/'reader/heo2003.json'),'promotion_manifest_sha256':sha(O/'promotion-proposal-manifest.json'),'checks':checks,'findings':failure,'manual_findings':['All ten records preserve complete scientific content. Only collection/review metadata, the narrowly qualified average-reference links and one reader navigation role change. The source-conflict fields, operations, conditions, quantities and specimen identities are identical.','Exactly three computed_reference CIF links target the previously approved final/diffraction/average-model samples and keep eligible_as_measured_label=false. All requested_tasks remain empty; actual eligibility returns no tasks.','The full-page projection exactly applies the approved removals, fourteen main→si source-role corrections and documented source-hash-key/gallery metadata. All372 reader objects remain; all16 selected original crops are byte-exact.','The route context string is preserved as a scope note, while nine contextual record IDs populate navigation. Technique strings become technique objects without losing labels or creating source/sample links.','Current schema plus the declared optional reader_role enum was validated in memory without editing Site. Renderer/display classification and old470record behavior are being independently checked by the separate renderer reviewer.'],'limits':['This is a private staging audit, not a verification of Site import, runtime rendering, public URLs or release.','Final integrated browser and anonymous publication checks remain pending.','A later metadata refresh that adds these passed audits must remain a separately documented status/hash delta; all science must stay unchanged.'],'mutations':'Only this private audit folder written; no Site, proposal, source or shared ledger edits.','bound_files':bound}
(A/'promotion-projection-delta-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=['# Heo private promotion and reader-projection audit','',f"**{report['status']}** — {len(checks):,} checks, {len(failure)} findings.",'','Ten proposed records retain every scientific field. The only new navigation role is synthesis_route on the actual synthesis record. Three qualified computed-reference CIF links preserve the approved sample scopes and remain ineligible as measured labels. All requested training tasks and exact-pair admissions remain empty.','','The public reader projection retains all 372 items, 535 typed fact attachments, 473 canonical measurements and the 1,209-row SI context with two null signs. It excludes 23 whole-page image files and retains 16 exact original crops; fourteen SI evidence roles are corrected without changing their locators. The route navigation overlay retains its original prose scope note, and the three characterization technique labels are preserved.','','The ten proposed record hashes and final promoted-reader hash are bound in the JSON report. Current schema validation, with only the declared optional reader_role enum added in memory, passes for all ten records; actual training eligibility remains false for every task.','','This is a private staged-delta audit. Actual Site import, browser rendering, the separate navigation-code regression review and anonymous publication verification remain separate gates. No source, frozen proposal, Site or shared-state file was edited.','']
(A/'promotion-projection-delta-audit.md').write_text('\n'.join(md),encoding='utf-8')
print(json.dumps({'status':report['status'],'checks':len(checks),'findings':failure[:15],'finding_count':len(failure),'sha256':sha(A/'promotion-projection-delta-audit.json'),'reader_sha256':report['promoted_reader_sha256']},ensure_ascii=False))
