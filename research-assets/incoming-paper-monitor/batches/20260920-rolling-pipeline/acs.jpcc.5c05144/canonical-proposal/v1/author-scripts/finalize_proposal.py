"""Freeze the bounded private Sasongko conversion after author transport checks."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,shutil,re
sys.dont_write_bytecode=True
C=Path(__file__).resolve().parent;J=C.parent;O=C/'v1'
assert not (O/'package-freeze.json').exists(),'Existing immutable freeze must be preserved.'
S=Path('[local path redacted]');sys.path.insert(0,str(S/'scripts'))
from dataset_lib import validate_record,eligibility,build_groups
import build_paper_reviews as consumer
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def resolve(x,p):
 for k in p.strip('/').split('/')if p else[]:
  k=k.replace('~1','/').replace('~0','~');x=x[int(k)]if isinstance(x,list)else x[k]
 return x
checks=[]
def ck(n,v):
 checks.append({'check':n,'passed':bool(v)})
 assert v,n
CM=read(O/'record-manifest.json');CV=read(O/'source-to-field-coverage.json');R={x['record_id']:read(x['path'])for x in CM['records']}
RV=read(O/'reader/sasongko2025.json');RB=read(O/'reader/reader-bindings-proposal.json');RC=read(O/'reader/source-item-coverage.json')
ITEM={i['id']:i for s in RV['reader_sections']for i in s['items']}
EFF=CM['effective_source_files'];D=read(EFF['source-facts.json']['path']);T=read(EFF['source-tables.json']['path']);I=read(EFF['source-inventory.json']['path']);A=read(EFF['original-assets-manifest.json']['path'])
SID='sasongko2025';PRE='sasongko-2025-'
source_inputs={}
for f in [J/'package-freeze.json',J/'source-extraction-revision-2/package-freeze.json',J/'source-independent-audit/independent-audit-v2.json']:
 source_inputs[str(f)]=sha(f)
 for p,h in read(f).get('bound_files',{}).items():
  pp=Path(p)if Path(p).is_absolute()else J/p;want=h['sha256']if isinstance(h,dict)else h
  ck('Retained upstream bytes '+str(pp),sha(pp)==want)
ck('Effective source audited',source_inputs[str(J/'source-extraction-revision-2/package-freeze.json')]=='d34778349e9942a73a1d275536af354e93d52739692e689fe2f12d394db7fddc'and read(J/'source-independent-audit/independent-audit-v2.json')['status']=='passed')
for n,x in EFF.items():ck('Effective source '+n,sha(x['path'])==x['sha256']);source_inputs[x['path']]=x['sha256']
intake=read(J/'intake-identity.json')
for x in intake['file_copies']:
 ck('Actual original '+x['role'],sha(x['source_path'])==x['sha256']);source_inputs[x['source_path']]=x['sha256']
ck('Generation remains scoped to admitted source',CM['source_generation']==intake['source_generation']==1)
source_inputs[str(J/'intake-identity.json')]=sha(J/'intake-identity.json')
for x in CM['records']:
 r=R[x['record_id']];ck('Frozen candidate byte '+x['record_id'],sha(x['path'])==x['sha256']);ck('Schema '+x['record_id'],not validate_record(r))
 ck('No task admission '+x['record_id'],not r['quality']['requested_tasks']and not any(v['eligible']for v in eligibility(r).values()))
 ck('Unreviewed record '+x['record_id'],r['quality']['review_status']=='imported_unreviewed')
 ck('No exact atomic assets '+x['record_id'],not any(p.get('structure_assets')for p in r['products']))
ck('One leakage split',len(set(build_groups(list(R.values())).values()))==1)
ck('Bounded record counts',len(R)==19 and sum(r['record_type']=='literature_protocol'for r in R.values())==1 and sum(r['record_type']=='procedure'for r in R.values())==7 and sum(r['record_type']=='observation'for r in R.values())==11)
def converted(q,out,label):
 ck(label+' original evidence',all(any(e['source_sha256']in o['locator']and e['locator']in o['locator']and 'PDF p. '+str(e['pdf_page'])in o['locator']for o in out['evidence'])for e in q['evidence']))
 if q['status']=='reported_text':ck(label+' literal text',out['value']==q['raw_text']);return
 ck(label+' raw token',out['raw_text']==q['raw_text'])
 ck(label+' unit',out['unit']==(q.get('unit')or''))
 ck(label+' approximate',out['approximate']==q.get('approximate',False))
 v=q['value'];lo=(q.get('range')or{}).get('min');hi=(q.get('range')or{}).get('max');cmp=q.get('comparison')
 if cmp in['<','<=']:hi=v;v=None
 if cmp in['>','>=']:lo=v;v=None
 ck(label+' value and bounds',(out['value'],out['minimum'],out['maximum'])==(v,lo,hi))
 if cmp in['<','<=']:ck(label+' upper inclusivity',out['maximum_exclusive']==(cmp=='<'))
 if cmp in['>','>=']:ck(label+' lower inclusivity',out['minimum_exclusive']==(cmp=='>'))
 if v is None and lo is None and hi is None:ck(label+' missingness',out['status']=='not_reported')
 if q.get('uncertainty')is not None:ck(label+' uncertainty retained',json.dumps(q['uncertainty'],ensure_ascii=False,separators=(',',':'))in out['qualifier'])
 ck(label+' source status preserved',q['status']in out['qualifier'])
FM={f['id']:f for f in D['facts']}
ck('Every fact represented',set(FM)=={x['source_fact_id']for x in CV['facts']})
for x in CV['facts']:
 f=FM[x['source_fact_id']];ck('Every fact field '+f['id'],len(x['canonical_bindings'])==1+len(f['quantities']))
 for b in x['canonical_bindings']:
  val=resolve(R[b['record_id']],b['pointer']);src=resolve(f,b['source_pointer'])
  if b['source_pointer']=='/claim':ck('Literal claim '+f['id'],val['value']==src)
  else:converted(src,val,f['id']+b['source_pointer'])
ck('100 fact quantities',sum(len(f['quantities'])for f in FM.values())==100)
ck('Every table field',len(CV['table_cells'])==127 and sum(b['cell_kind']=='cells'for b in CV['table_cells'])==121)
for b in CV['table_cells']:converted(resolve(T,b['source_pointer']),resolve(R[b['record_id']],b['pointer']),b['source_pointer'])
payload_count=0
for b in CV['source_objects']:
 if b.get('source_pointer')and b['pointer'].startswith('/measurements/'):
  source=T if b['category']=='table'else D
  ck('Complete payload '+b['category']+' '+b['source_id'],json.loads(resolve(R[b['record_id']],b['pointer'])['value'])==resolve(source,b['source_pointer']));payload_count+=1
ck('All source units represented',len(CV['source_units'])==157 and {u['id']for u in I['units']}=={x['source_unit_id']for x in CV['source_units']})
for b in CV['source_units']:
 ck('Nonempty unit '+b['source_unit_id'],bool(b['canonical_bindings']))
 for t in b['canonical_bindings']:ck('Unit pointer '+b['source_unit_id'],resolve(R[t['record_id']],t['pointer'])is not None)
for x in CV['operation_quantities']:converted(resolve(D,x['source_pointer']),resolve(R[x['record_id']],x['pointer']),x['source_pointer'])
ops={op['id']:(r,op)for r in R.values()for op in r['operations']};srcops={op['id']:op for p in D['protocols']for op in p['operations']}
ck('All 21 operations once',len(ops)==21 and set(ops)==set(srcops))
for oid,(r,op)in ops.items():
 src=srcops[oid];ck('Inputs preserve source '+oid,op['inputs']==src['inputs'])
 ck('Outputs preserve source '+oid,op['outputs']==[x+'-prepared-state'if x=='fa-oleate-stock'else x for x in src['outputs']])
 known={m['id']for m in r['materials']}|{s['id']for s in r['stocks']}|{s['id']for s in r['material_states']}
 ck('Resolvable graph '+oid,set(op['inputs']+op['outputs'])<=known)
 if op['stage']=='characterization':
  states={s['id']:s for s in r['material_states']};ck('Separate acquisition inputs '+oid,all(states[x]['kind']=='sample_set'for x in op['inputs']))
  ck('No inherited synthesis atmosphere '+oid,op['environment']['value']is None)
ck('First retained fraction',ops['first-spin'][1]['retained_fraction']=='first-precipitate')
ck('Second retained fraction',ops['second-spin'][1]['retained_fraction']=='final-supernatant')
ck('Second product from hexane',ops['second-spin'][1]['inputs']==['hexane-redispersion'])
ck('Aliquot quantity only',set(ops['inject-fa'][1]['parameters'])=={'fa_precursor_aliquot'}and ops['inject-fa'][1]['parameters']['fa_precursor_aliquot']['value']==.51)
ck('No made-up stock concentration',all(not s['concentrations']for r in R.values()for s in r['stocks']))
ck('Selected wash not pooled',ops['add-wash'][1]['inputs']==['crude','selected-wash'])
hot=R[PRE+'hot-injection'];SC={s['id']:s for s in D['sample_contexts']}
ck('Nine paired conditions',len(hot['condition_options'])==9)
for c in hot['condition_options']:
 s=SC[c['id']]['condition_scope'];p=c['parameters'];ck('Source-paired option '+c['id'],p['growth_temperature']['value']==s['growth_temperature_C']and p['oam_volume']['value']==.2 and p['oa_volume']['value']=={2:.4,3:.6,4:.8}[s['OAm_OA_volume_parts'][1]]and [p['wash_acetonitrile_parts']['value'],p['wash_toluene_parts']['value']]==s['acetonitrile_toluene_volume_parts'])
for oid,banned in {'temperature-pl-acquire':['gamma_beta_transition','beta_alpha_transition'],'temperature-raman-acquire':['overlap_threshold'],'thermal-aging-acquire':['reference_temperature_label','normalized_slope','normalized_intercept']}.items():ck('Outcomes not setpoints '+oid,not(set(banned)&set(ops[oid][1]['parameters'])))
for r in R.values():
 for p in r['products']:
  if p['sample_id']in SC:ck('Source composition scope '+r['record_id']+'/'+p['sample_id'],p['composition']['value']==SC[p['sample_id']]['reported_whole_composition'])
ck('Source references complete',len(D['references'])==89 and all(any(b['category']=='references'and b['source_id']==x['id']for b in CV['source_objects'])for x in D['references']))
source_named=0
for s in D['sample_contexts']:
 it=ITEM['source-sample_contexts-'+s['id']];ck('Named sample '+s['id'],any(x['sample_id']==s['id']and resolve(R[x['record_id']],x['json_pointer'])['sample_id']==s['id']for x in it['sample_scope']['canonical_sample_links']));source_named+=1
for f in D['figures']:
 it=ITEM['source-figures-'+f['id']];ck('Figure links '+f['id'],set(f['sample_context_ids'])<=set(x['sample_id']for x in it['sample_scope']['canonical_sample_links']))
fieldkeys=set()
for x in RC['canonical_field_map']:
 it=ITEM[x['reader_item_id']];q=next(q for q in it['facts']if q['id']==x['reader_fact_id']);ck('Exact typed reader field '+x['record_id']+x['json_pointer'],q['canonical_quantity']==resolve(R[x['record_id']],x['json_pointer']));fieldkeys.add((x['record_id'],x['json_pointer']))
ck('1197 distinct typed reader fields',len(fieldkeys)==1197)
ck('Semantic units reach reader',set(RC['source_units'])=={x['id']for x in I['units']}and all(RC['source_units'].values()))
ck('Supported reader scope',RV['review_scope']=='supplied_main_and_matched_si')
ck('False presentation gates',not any(RV['presentation_gates'].values())and not RV['source_review_promoted'])
ck('Real route-context IDs',all(isinstance(v,list)and all(x in R for x in v)for v in RV['route_evidence_contexts'].values()))
ck('Typed characterization inventory',isinstance(RV['characterization_inventory'],dict))
for it in ITEM.values():
 ck('Readable scalar prose '+it['id'],isinstance(it['title'],str)and isinstance(it['text'],str)and 'Source panel assignments: {'not in it['text']and 'Unreported details: .'not in it['text'])
 ck('No public local path in prose '+it['id'],not any(v in it['title']+' '+it['text']for v in['C:/Users/','C:\\Users\\']))
allowed=[]
for a in RB['original_assets']:
 src=next(z for z in A['assets']if z['id']==a['id']);ck('Selected original crop '+a['id'],not src['contains_complete_source_page']and sha(a['private_path'])==a['sha256']==src['sha256'])
 ck('Public asset path '+a['id'],a['public_asset'].startswith('assets/figures/sasongko2025/')and not any(t in a['public_asset']for t in['source-render','audit-pages','.pdf','.txt']))
 allowed.append(a);source_inputs[a['private_path']]=a['sha256']
ck('All 17 selected crops',len(allowed)==17)
old=consumer.ROOT
try:consumer.ROOT=O/'isolated-reader-fixture';errs=consumer.validate(RV)
finally:consumer.ROOT=old
ck('Actual current isolated reader consumer',not errs)
for x in CM['records']:ck('Exact fixture record '+x['record_id'],sha(O/'isolated-reader-fixture/data/records'/Path(x['path']).name)==x['sha256'])
source_inputs[str(S/'scripts/build_paper_reviews.py')]=sha(S/'scripts/build_paper_reviews.py')
source_inputs[str(S/'scripts/dataset_lib.py')]=sha(S/'scripts/dataset_lib.py')
source_inputs[str(S/'scripts/record_helpers.py')]=sha(S/'scripts/record_helpers.py')
for p in sorted((S/'data/schema').glob('*.json')):source_inputs[str(p)]=sha(p)
manual={
 'author':'/root/norberg2004_extract','scope':'Canonical/reader conversion author review; does not repeat or replace distinct full source audit.',
 'source_pages_viewed':{'main':[2,3,4,6],'si':[3,5,8]},'additional_source_text_read':['SI analysis/characterization p4'],
 'structured_content_read':{'facts':48,'fact_quantities':100,'source_operations':21,'sample_contexts':33,'stocks':4,'source_materials':13,'table_cells':121,'additional_table_quantities':6},
 'crop_contacts_actually_viewed':[{'path':str(p),'sha256':sha(p)}for p in sorted((J/'source-render/crop-contacts').glob('contact-*.png'))],
 'selected_crops_viewed_in_contacts':17,'operation_display_texts_read':21,'nonreference_reader_display_prose_read':184,
 'reference_handling':'All 89 literal reference payloads retained and exact-tested; whitespace-normalized citation text; no cited paper newly retrieved.',
 'scientific_scope_notes':['Nine paired condition contexts retain fixed companion parameters; no Cartesian design or replicate assertion.','Whole FA stock and 0.51 mL aliquot remain separate.','Sequential spins retain first precipitate then final supernatant.','Acquisition inputs are separate sample sets, even where IDs match washing-formulation IDs.','Current optical and phase observations are distinct from cited reference cells and author hypotheses.','All 33 named source contexts have direct existing product pointers.','Source conflicts, table blanks and undefined ± statistics remain explicit.'],
 'downstream_gates':{'distinct_canonical_reader_audit':False,'molecules':False,'apparatus':False,'products':False,'browser':False,'publication':False,'training':False}}
for x in manual['crop_contacts_actually_viewed']:source_inputs[x['path']]=x['sha256']
save('author-reading-receipt.json',manual)
save('public-assets-proposal.json',{'status':'private_unapproved','selected_original_assets':allowed,'count':17,'full_page_assets':0,'raw_source_text_assets':0})
save('author-validation.json',{'status':'passed_author_checks_pending_distinct_review','author':manual['author'],'check_count':len(checks),'checks':checks,'counts':{**RV['counts'],'named_source_contexts':source_named,'structured_payloads':payload_count},'actual_reader_consumer_errors':errs,'upstream_source_audit_passed':True,'independent_canonical_audit':False,'browser_validation':False,'source_inputs':source_inputs})
notes='''# Sasongko 2025 canonical and source reader proposal

This private author proposal is ready for distinct canonical/reader review. It contains 19 records: one hot-injection route, seven preparation/acquisition procedures and eleven observations. Twenty-one operations preserve all source preparation, workup and measurement stages. The route holds nine paired condition options from three comparison families; neither a Cartesian matrix nor identified physical replicates are inferred.

The whole FA-oleate stock formulation is separate from the 0.51 mL injection. Washing options are alternatives, not pooled solvents. The first centrifugation retains its precipitate; the second retains the supernatant. Measurement input IDs are explicit sample sets even when a label resembles a stock ID. Missing pressures, ramps, wash quantities, concentrations and storage remain missing.

All 48 source facts, 100 fact quantities, 157 inventory units, 121 table cells and six specimen-label quantities reach exact canonical fields. The 273 reader items include 1,197 exact typed fields and all 33 named source context links. Eight figures, one scheme, two equations, 89 references and 17 selected original crops are retained. No full source pages or raw full-text assets are proposed for publication. Literal structured source objects remain preserved separately from readable academic display prose.

Current sample phase assignments, quoted reference-cell parameters, literature-table rows and mechanistic interpretations remain distinct. No current QD atomic structure is supplied. The printed fringe/index and quoted cubic cell tension, Raman temperature/figure-label inconsistencies, citation mismatch and instrument/equation typography remain documented. No new atomic geometry, absolute quantum yield, device outcome or exact structure–recipe label is asserted.

The actual current reader validator passes on an isolated fixture with exact candidate records and crop copies. Author transport and semantic checks do not replace independent review. Molecular, apparatus, product, browser, publication and training gates remain false. The original source freeze and revision-2 overlay are unchanged; the converter inspected seven relevant source pages and all selected crop contacts without claiming a second complete source audit.

Entry points: record-manifest.json; source-to-field-coverage.json; reader/sasongko2025.json; reader/source-item-coverage.json; author-validation.json; author-reading-receipt.json. Source and reader builders are retained under author-scripts. Any correction after package-freeze.json must preserve this version.
'''
(O/'proposal-notes.md').write_text(notes,encoding='utf-8')
for name in['build_canonical.py','build_reader.py','finalize_proposal.py']:
 target=O/'author-scripts'/name;target.parent.mkdir(exist_ok=True);shutil.copyfile(C/name,target)
bound={str(p.relative_to(O)).replace('\\','/'):sha(p)for p in sorted(O.rglob('*'))if p.is_file()and 'isolated-reader-fixture'not in p.parts and p.name!='package-freeze.json'}
freeze={'schema':'mattersyn-private-canonical-reader-freeze/1','status':'frozen_author_proposal_pending_distinct_audit','author':manual['author'],'created_at':datetime.now(timezone.utc).isoformat(),'source_id':SID,'source_generation':1,'effective_source_freeze_sha256':CM['source_freeze_sha256'],'source_audit_sha256':CM['source_audit_sha256'],'record_manifest_sha256':sha(O/'record-manifest.json'),'reader_path':'reader/sasongko2025.json','reader_sha256':sha(O/'reader/sasongko2025.json'),'counts':RV['counts'],'bound_files':bound,'external_inputs':source_inputs,'independent_canonical_review':False,'publication_approved':False,'training_approved':False}
save('package-freeze.json',freeze)
(C/'author-progress.md').write_text(notes+'\n## Frozen handoff\n\nFinal author freeze: `v1/package-freeze.json`, SHA256 `'+sha(O/'package-freeze.json')+'`. Next action: a distinct auditor compares this immutable proposal with the passed effective source and actual reader consumer. No author mutation is pending.\n',encoding='utf-8')
print(json.dumps({'status':'frozen_pending_distinct_audit','freeze':str(O/'package-freeze.json'),'sha256':sha(O/'package-freeze.json'),'reader_sha256':sha(O/'reader/sasongko2025.json'),'record_manifest_sha256':sha(O/'record-manifest.json'),'checks':len(checks),'bound_files':len(bound),'external_inputs':len(source_inputs),'counts':RV['counts']},ensure_ascii=False))
