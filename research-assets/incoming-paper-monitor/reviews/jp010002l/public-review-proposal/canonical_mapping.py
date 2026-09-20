"""Read-only links to audited canonical quantities and specimen scopes."""
drafts=records
def quantity_display(q):
 if q.get('value') is not None:return q['value']
 lo=q.get('minimum');hi=q.get('maximum')
 if lo is not None and hi is not None:
  return f'{"(" if q.get("minimum_exclusive") else "["}{lo:g}, {hi:g}{")" if q.get("maximum_exclusive") else "]"}' if q.get('minimum_exclusive') or q.get('maximum_exclusive') else f'{lo:g}–{hi:g}'
 if lo is not None:return ('> ' if q.get('minimum_exclusive') else '≥ ')+f'{lo:g}'
 if hi is not None:return ('< ' if q.get('maximum_exclusive') else '≤ ')+f'{hi:g}'
 return 'Not reported' if q.get('status')=='not_reported' else q.get('raw_text') or q.get('status','Unspecified')
def canon_evidence(es):
 ee=[]
 for e in es:
  match=re.search(r'Main PDF p\. (\d+)',e['locator']);n=int(match.group(1)) if match else None
  ee.append({'source_id':SID,'document_role':'main','pdf_page':n,'printed_page':5547+n if n else None,'locator':e['locator']})
 return ee
def append_fact(target,rid,pointer,identifier,label,q,es,basis,sample=None,extra=None):
 ii=items[target];ee=canon_evidence(es)
 f={'id':rid+'::'+identifier,'label':label,'value':quantity_display(q),'unit':q.get('unit'),'approximate':q.get('approximate',False),'basis':basis,'qualifier':' '.join(str(x) for x in [q.get('basis'),q.get('qualifier'),q.get('note'),extra] if x),'evidence':ee,'canonical_record_id':rid,'json_pointer':pointer,'canonical_quantity':q,'training_eligible':False}
 if sample:f['sample_id']=sample
 ii['facts'].append(f);ii['canonical_links'].append({'record_id':rid,'json_pointer':pointer,'relation':SCOPE[ii['sample_scope']['scope_kind']]})
 for e in ee:
  if e not in ii['evidence']:ii['evidence'].append(e)
  if e['locator'] not in ii['source_locators']:ii['source_locators'].append(e['locator'])
 return f
def op_target(short,op):
 if short=='absorption-acquisition':return 'absorption-method'
 if short=='photoluminescence-acquisition':return 'pl-method'
 if short=='transient-absorption-acquisition':return 'ta-delay' if op['id'] in ['delay-scan','analyze'] else 'ta-excitation'
 oid=op['id']
 if oid in ['a-prepare','a-inject']:return 'step-a-charge'
 if oid=='a-grow':return 'step-a-grow'
 if oid=='a-purge':return 'step-a-purge'
 if oid.endswith('-exchange'):return 'step-b'
 if oid.endswith('-add-cd'):return 'step-c-cadmium'
 if oid.endswith(('-grow','-purge')):return 'step-c-feed'
 raise ValueError((short,oid))

def measurement_target(short,m):
 mid=m['id']
 if short in ROUTES:
  r=short.removeprefix('system-')
  if mid=='a-core-preparation-size':return 'core-size-conflict'
  if mid=='a-core-absorption':return 'absorption-stages-'+r
  if mid=='step-sequence':return short+'-sequence'
  if mid in ['system-core-size','well-count','well-layer-count','well-thickness','cap-layer-count','cap-thickness','barrier-layer-count','barrier-thickness']:return short+'-structure'
  if mid=='absorption-transition':return 'absorption-'+r
  if mid in ['pl-maximum','estimated-qy-bound']:return 'emission-'+r
  if mid in ['relaxation-crossover','short-lived-component']:return 'dynamics-'+r
  if mid in ['inset-short-probe','inset-long-probe']:return 'figure4-insets'
 if short=='absorption-acquisition':return 'absorption-method' if mid=='stage-series' else 'absorption-comparison'
 if short=='photoluminescence-acquisition':return 'pl-method'
 if short=='transient-absorption-acquisition':return 'bleach-vs-emission' if mid=='negative-signal' else 'figure4-decays'
 maps={
 'chemical-interpretation':{'nucleation-ph':'nucleation-ph','solubility-contrast':'exchange-driving-force','exchange-mass-balance':'cadmium-recycling','conditional-cd':'step-c-cadmium','two-well-construction':'barrier-design','morphology-context':'morphology-scope','wavefunction-scope':'figure1-scope','future-barriers':'coupling-outlook'},
 'optical-comparison':{'oscillator-ratio':'absorption-comparison','atom-count-ratio':'oscillator-interpretation','hg-content':'oscillator-interpretation','energy-order':'absorption-comparison','trap-interpretation':'trap-location','well-interaction':'coupling-outlook','structural-evidence-scope':'structural-inference'},
 'literature-context':{'cited-preparation':'sequence-framework','cited-structure':'morphology-scope','cited-theory':'theory-context','source-completeness':'coverage','historical-motivation':'motivation'}}
 return maps[short][mid]

rowlinks={};operationlinks={};parameterlinks={};materiallinks={};stocklinks={}
for rid,d in drafts.items():
 short=rid.removeprefix(P)
 for n,m in enumerate(d.get('measurements',[])):
  target=measurement_target(short,m)
  f=append_fact(target,rid,f'/measurements/{n}',m['id'],m['property'].replace('_',' ').capitalize(),m['value'],m['evidence'],m['value'].get('status','reported'),m['sample_id'],m.get('conditions'))
  f['canonical_measurement_id']=m['id'];rowlinks[rid+'::'+m['id']]=target
 for n,op in enumerate(d.get('operations',[])):
  target=op_target(short,op);ii=items[target];pointer=f'/operations/{n}'
  ii['canonical_links'].append({'record_id':rid,'json_pointer':pointer,'relation':'Reported operation; branch, repeated-step identity, bounds, optionality and source scope remain canonical.'});operationlinks[rid+'::'+op['id']]=target
  for name,q in op.get('parameters',{}).items():
   f=append_fact(target,rid,pointer+'/parameters/'+name,'operation-'+op['id']+'-'+name,op['label']+' · '+name.replace('_',' '),q,q.get('evidence',op['evidence']),'operation_parameter',extra=op.get('description'))
   f['canonical_operation_id']=op['id'];f['canonical_parameter']=name;parameterlinks[rid+'::'+op['id']+'::'+name]=target
 for n,mat in enumerate(d.get('materials',[])):
  assert not mat.get('quantities'),mat['id']
 for n,stock in enumerate(d.get('stocks',[])):
  target={'cd-stock':'cadmium-stock','hg-stock':'mercury-stock','h2s-water-stock':'h2s-water'}[stock['id']]
  for name,q in stock.get('concentrations',{}).items():
   f=append_fact(target,rid,f'/stocks/{n}/concentrations/{name}','stock-'+stock['id']+'-'+name,stock['name']+' · '+name.replace('_',' '),q,q.get('evidence',stock['evidence']),'stock_concentration')
   f['canonical_stock_id']=stock['id'];stocklinks[rid+'::'+stock['id']+'::'+name]=target
  for component in stock.get('components',[]):assert not component.get('quantities'),component
for ii in items.values():
 joins=[]
 for f in ii['facts']:
  if not f.get('sample_id'):continue
  rid=f['canonical_record_id'];sample=f['sample_id'];n=next(n for n,p in enumerate(drafts[rid].get('products',[])) if p['sample_id']==sample)
  join={'record_id':rid,'sample_id':sample,'json_pointer':f'/products/{n}','relation':SCOPE[ii['sample_scope']['scope_kind']]}
  if join not in joins:joins.append(join)
 if ii['id'].startswith('absorption-stages-'):
  rid=P+'system-'+ii['id'].removeprefix('absorption-stages-')
  for n,p in enumerate(drafts[rid]['products']):
   join={'record_id':rid,'sample_id':p['sample_id'],'json_pointer':f'/products/{n}','relation':'Figure 2 source-labeled sequential stage within this system; no cross-system physical batch identity.'}
   if not any(j['record_id']==rid and j['sample_id']==p['sample_id'] for j in joins):joins.append(join)
 ii['sample_scope']['formulations']=list(dict.fromkeys(x['sample_id'] for x in joins))
 if joins:ii['sample_scope']['canonical_sample_links']=joins
 ii['canonical_links']=list({json.dumps(x,sort_keys=True):x for x in ii['canonical_links']}.values())
out['record_formulation_labels']={rid:[p['sample_id'] for p in d.get('products',[])] for rid,d in drafts.items()}
out['record_formulation_scope_note']='System and stage labels require their canonical record ID. No unique physical batch identity is asserted from repeated spectra.'
out['corpus_paper_id']='paper-fbd268bbd6f324abc0eb'
out['corpus_document_id']='doc-b8689ed110c272852502'
out['material_evidence_records']={'CdS/HgS/CdS':list(drafts),'CdS':[P+r for r in ROUTES],'HgS':[]}
out['material_evidence_scope_notes']={'CdS/HgS/CdS':'Three source layer architectures and shared analytical or interpretive records; procedures and observation contexts are not additional synthesis routes.','CdS':'Initial core size and 470 nm absorption feature are scoped to each route’s a-cds-core sample. Other properties in these records describe the composite, not bare CdS.','HgS':'No isolated HgS material sample or independently characterized pure HgS synthesis is supplied; HgS is a component layer in the composite routes.'}
out['counts'].update({'typed_characterization_rows':len(rowlinks),'linked_operations':len(operationlinks),'operation_parameter_facts':len(parameterlinks),'reagent_quantity_facts':len(materiallinks),'stock_quantity_facts':len(stocklinks)})
(O/'canonical-measurement-coverage.json').write_text(json.dumps({'measurement_count':len(rowlinks),'measurement_to_reader_item':rowlinks,'operation_count':len(operationlinks),'operation_to_reader_item':operationlinks,'operation_parameter_count':len(parameterlinks),'operation_parameter_to_reader_item':parameterlinks,'material_quantity_count':len(materiallinks),'material_quantity_to_reader_item':materiallinks,'stock_quantity_count':len(stocklinks),'stock_quantity_to_reader_item':stocklinks,'draft_sha256':{k:sha(B/'canonical-drafts'/f'{k}.json') for k in drafts}},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
