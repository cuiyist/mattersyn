"""Independent bounded revision audit. Reads author files; writes only this audit directory."""
from pathlib import Path
import json, hashlib, sys, datetime, collections, copy, re
A=Path(__file__).resolve().parent; R=A.parent; C=R/'canonical-proposal'; P=R/'public-review-proposal'
S=Path('[local path redacted]'); sys.path.insert(0,str(S/'scripts'))
from dataset_lib import validate_record, eligibility, build_groups
checks=collections.Counter(); failures=[]; bound={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
 p=Path(p);bound[str(p)]=sha(p);return json.loads(p.read_text(encoding='utf-8-sig'))
def ck(ok,cat,detail):
 checks[cat]+=1
 if not ok:failures.append({'category':cat,'detail':detail})
def diff(a,b,p=''):
 if type(a)!=type(b):return [(p,a,b)]
 if isinstance(a,dict):return sum([diff(a[k],b[k],p+'/'+k) if k in a and k in b else [(p+'/'+k,a.get(k),b.get(k))] for k in sorted(set(a)|set(b))],[])
 if isinstance(a,list):return [(p,a,b)] if len(a)!=len(b) else sum([diff(x,y,p+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))],[])
 return [] if a==b else [(p,a,b)]
def ptr(o,p):
 for k in p.lstrip('/').split('/') if p else []:
  k=k.replace('~1','/').replace('~0','~');o=o[int(k)] if isinstance(o,list) else o[k]
 return o
old=read(A/'independent-audit-v1.json'); freeze=read(C/'v2/package-manifest.json')
ck(sha(C/'v2/package-manifest.json')=='871dd6e962bbb75b51d802a034d023af6343868a1a75a9da90cdf131c7cb9103','expected_freeze','v2')
for p,h in freeze['bound_files'].items():
 ck(Path(p).exists() and sha(Path(p))==h,'v2_frozen_hash',p);bound[p]=sha(Path(p))
for p,h in old['bound_files'].items():
 ck(Path(p).exists() and sha(Path(p))==h,'v1_preserved_hash',p);bound[p]=sha(Path(p))
ck(sha(R/'source-independent-audit/independent-audit-v2.json')==old['source_audit_sha256'],'passed_source_unchanged','source audit')
note='The preparation label and intended ZnAl2O4 target do not establish the observed product composition. Sample-specific phase and result observations remain in their separate source contexts; no pure-target product composition is assigned here.'
waternote='SCF solvent-water context; grade is not separately reported. No in situ nitrate-stock preparation, salt charge or solution volume is inherited by this material slot.'
routes={'sommer-2020-acs-route','sommer-2020-mw-route','sommer-2020-scf-route'}
records={}; record_deltas=[]; changed_products=set(); unchanged=0
for p in sorted((C/'v1').glob('sommer-2020-*.json')):
 before=read(p); after=read(C/'v2'/p.name);rid=after['record_id']; records[rid]=after
 expected=copy.deepcopy(before)
 if rid in routes:
  expected['revision']=2
  for ix,prod in enumerate(expected['products']):
   if not re.fullmatch(r'(?:a[1-6]|m[1-9]|s[12])',prod['sample_id']):continue
   ck(prod['composition']['value']=='ZnAl2O4' and prod['composition']['status']=='reported','prior_nominal_assignment',rid+'/'+str(ix))
   prod['composition'].update(value=None,status='not_reported',note=note);changed_products.add((rid,'/products/'+str(ix)+'/composition'))
  if rid=='sommer-2020-scf-route':
   ck(expected['materials'][3]['id']=='insitu-water','scf_slot_identity',rid)
   expected['materials'][3]['name']='Aqueous SCF solvent';expected['materials'][3]['notes'][0]=waternote
 else:
  unchanged+=1;ck(sha(p)==sha(C/'v2'/p.name),'16_records_byte_identical',rid)
 ck(expected==after,'exact_requested_record_delta',rid)
 dd=diff(before,after);record_deltas.append({'record_id':rid,'deltas':dd})
 for k in ['operations','stock_solutions','condition_options','measurements','material_states','intended_target','evidence']:
  if k in before:ck(before[k]==after[k],'science_field_preserved',rid+'/'+k)
 ck(not validate_record(after),'current_schema',{'record_id':rid,'errors':validate_record(after)})
 ck(not any(v['eligible'] for v in eligibility(after).values()),'zero_training_tasks',rid)
 ck(after['quality']['review_status']=='imported_unreviewed' and not after['quality']['requested_tasks'] and 'collection' not in after,'unpromoted_review',rid)
 ck(not after['structure_assets'],'no_coordinate_claim',rid)
ck(len(records)==19 and unchanged==16 and len(changed_products)==17,'record_counts','19/16/17')
ck(sum(len(d['deltas']) for d in record_deltas)==56,'canonical_leaf_count','56')
ck(len(set(build_groups(list(records.values())).values()))==1,'single_source_split','19 records')
for name in ['source-to-field-coverage.json','lossless-source-map.json','operation-quantity-scope.json']:
 ck(sha(C/'v1'/name)==sha(C/'v2'/name),'source_maps_byte_identical',name);read(C/'v2'/name)
rb=read(P/'v1/sommer2020.json');ra=read(P/'v2/sommer2020.json');rd=diff(rb,ra)
expected=copy.deepcopy(rb);updated=0;field_count=0
for si,sec in enumerate(expected['reader_sections']):
 for ii,item in enumerate(sec['items']):
  for fi,f in enumerate(item['facts']):
   key=(f['canonical_record_id'],f['json_pointer'])
   if key in changed_products:
    f['canonical_quantity']=copy.deepcopy(ptr(records[key[0]],key[1]));f['value']='Not reported';f['status']='not_reported';f['qualifier']=note;updated+=1
expected['reader_sections'][0]['items'][17]['material_identities'][0]['name']='Aqueous SCF solvent'
identity=ra['reader_sections'][0]['items'][17]['material_identities'][0]
ck(identity['canonical_record_id']=='sommer-2020-scf-route' and identity['json_pointer']=='/materials/3','scf_reader_exact_identity',identity)
expected['reader_sections'][0]['items'][17]['text']+=' The separate SCF material slot is an aqueous solvent reference with unreported grade; no in situ stock charges or preparation volume are transferred.'
other_deltas=[d for d in rd if '/canonical_quantity/' not in d[0] and not any(d[0].endswith('/'+s) for s in ['value','status','qualifier'])]
scfnotes=[];scflabels=[]
for si,sec in enumerate(expected['reader_sections']):
 for ii,item in enumerate(sec['items']):
  context=item.get('operation_context',{})
  labels=context.get('material_flow_labels',{})
  if labels.get('insitu-water')=='Water-based nitrate-stock solvent' and any(l.get('record_id')=='sommer-2020-scf-route' for l in item.get('canonical_links',[])):
   labels['insitu-water']='Aqueous SCF solvent';scflabels.append(item['id'])
   # The corrected operation-note repeats the actual slot name and scope.
   actual=ra['reader_sections'][si]['items'][ii]
   changes=diff(item.get('notes',[]),actual.get('notes',[]))
   ck(len(changes)==1 and changes[0][0]=='/0' and 'Aqueous SCF solvent' in changes[0][2],'scf_input_note_delta',changes)
   item['notes']=copy.deepcopy(actual['notes']);scfnotes.append(item['id'])
expected['figures'][11]['label']='Figure 11 · Autoclave impurity phase fractions versus duration'
fig=expected['reader_sections'][2]['items'][31]
fig['title']='Autoclave impurity phase fractions versus duration'
fig['original_assets'][0]['label']='Open original Figure 11 · Autoclave impurity phase fractions versus duration'
fig['notes'].insert(0,'The inherited source-title label in the typed context is historical extraction metadata. Figure 11 shows impurity phase fractions versus duration and has no diffraction panel.')
ck(len(scflabels)==1 and len(scfnotes)==1,'one_scf_operation_note','scope')
ck(expected==ra,'exact_requested_reader_delta',[d[0] for d in diff(expected,ra)])
ck(updated==17 and len(rd)==110,'reader_delta_counts','17 fields/110 leaves')
for item in [i for sec in ra['reader_sections'] for i in sec['items']]:
 ck(not item['training_eligible'],'reader_unpromoted',item['id'])
 for b in item.get('canonical_links',[]):ck(ptr(records[b['record_id']],b['json_pointer']) is not None,'reader_link',item['id'])
 for b in item.get('sample_scope',{}).get('canonical_sample_links',[]):ck(ptr(records[b['record_id']],b['json_pointer'])['sample_id']==b['sample_id'],'reader_sample_link',item['id'])
 for f in item['facts']:
  q=ptr(records[f['canonical_record_id']],f['json_pointer']);field_count+=1
  ck(f['canonical_quantity']==q,'1515_exact_reader_fields',f['id'])
  for k in ['status','unit','approximate']:ck(f.get(k)==q.get(k,False if k=='approximate' else None),'reader_field_semantics',f['id']+'/'+k)
 for identity in item.get('material_identities',[]):
  q=ptr(records[identity['canonical_record_id']],identity['json_pointer'])
  for key in ['name','formula','role']:ck(identity[key]==q[key],'reader_material_identity',item['id']+'/'+key)
ck(field_count==1515,'typed_field_count','1515')
for name in ['source-item-coverage.json','reader-bindings-proposal.json']:
 before=read(P/'v1'/name);after=read(P/'v2'/name)
 # Coverage metadata may rebind record/reader hashes; every source mapping remains separately tested by exact content delta.
 if name=='source-item-coverage.json':ck(before==after,'reader_coverage_unchanged',name)
 else:
  for key in ['molecular_apparatus_bindings_approved','publication_approved']:ck(after[key] is False,'downstream_gates_pending',key)
ck(ra['training_eligible'] is False and ra['source_review_promoted'] is False,'reader_admission_unchanged','reader')
for p in [Path(__file__),S/'scripts/dataset_lib.py',S/'scripts/schema_definition.py']:
 bound[str(p)]=sha(p)
report={'schema':'mattersyn-independent-canonical-reader-audit/1','source_id':'sommer2020','doi':'10.1021/acs.cgd.9b01519','reviewer':'/root/norberg2004_extract','author':'/root/backlog_eta','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'passed' if not failures else 'open_findings','audited_revision':2,'proposal_freeze_sha256':sha(C/'v2/package-manifest.json'),'prior_audit_sha256':sha(A/'independent-audit-v1.json'),'source_audit_sha256':old['source_audit_sha256'],'reader_sha256':sha(P/'v2/sommer2020.json'),'counts':old['counts'],'prior_full_review_checks':old['independent_mechanical_checks'],'delta_checks':sum(checks.values()),'delta_checks_by_category':dict(checks),'failures':failures,'manual_scopes':old['manual_scopes']+['Independently inspected all 56 canonical and 110 reader leaf changes; verified 17 unknown route-product compositions retain their nominal targets and separately reported phase observations, SCF-specific solvent identity and corrected Figure11 title. No fresh full-source rereading is claimed for this bounded delta.'],'findings':[dict(f,status='resolved',resolution={'SOMMER-PROP-01':'All17 route-product compositions now not_reported/null with explicit target-versus-result qualifier; targets and all result observations unchanged.','SOMMER-PROP-02':'Only SCF solvent slot/name/scope and its linked reader identity/input labels changed; no stock quantities or chemical identity changed.','SOMMER-PROP-03':'Curated Figure11 title and asset-link label corrected; unchanged inherited title payload explicitly marked historical.'}[f['id']]) for f in old['findings']],'record_deltas':record_deltas,'reader_deltas':rd,'limits':old['limits'],'bound_files':dict(sorted(bound.items()))}
(A/'revision-2-independent-checks.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
if not failures:
 for name in ['independent-audit-v2.json','independent-audit.json']:(A/name).write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 md='# Sommer 2020 canonical/reader independent audit — revision 2\n\nStatus: passed. All three findings are resolved. The 17 route-product compositions now remain unknown, the SCF solvent is scoped independently, and Figure 11 is correctly described as impurity phase fractions versus duration.\n\nThe preserved complete review covered 19 records, 31 operations, 39 condition options, 357 prose cards, 1,515 typed fields, 65 facts, 332 source units and 222 table cells. Its 66,405 supporting checks passed; this bounded delta adds '+str(sum(checks.values()))+' checks. Exactly 56 canonical and 110 reader leaves changed; 16 other records remain byte-identical. All recipe operations, quantities, stocks, source claims, sample links, tables and crop bytes are retained.\n\nMain-paper scope only: the declared SI remains locally unlocated and unverified. Source conflicts remain explicit. This audit does not approve molecular/apparatus science, coordinate models, browser delivery, Site integration, publication or training. Exact inputs and manual scope are in the JSON.\n'
 for name in ['independent-audit-v2.md','independent-audit.md']:(A/name).write_text(md,encoding='utf-8')
print(json.dumps({'status':report['status'],'checks':report['delta_checks'],'failures':failures,'bound_files':len(bound),'audit_sha256':sha(A/'independent-audit-v2.json') if not failures else None},ensure_ascii=False,indent=2))
