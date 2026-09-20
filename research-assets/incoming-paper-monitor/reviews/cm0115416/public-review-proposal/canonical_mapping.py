"""Exact canonical quantities and source-specific sample scopes, read-only."""
drafts=records
def quantity_display(q):
 if q.get('value') is not None:return q['value']
 lo=q.get('minimum');hi=q.get('maximum')
 if lo is not None and hi is not None:return f'{lo:g}–{hi:g}'
 if lo is not None:return ('> ' if q.get('minimum_exclusive') else '≥ ')+f'{lo:g}'
 if hi is not None:return ('< ' if q.get('maximum_exclusive') else '≤ ')+f'{hi:g}'
 return 'Not reported' if q.get('status')=='not_reported' else q.get('raw_text') or q.get('status','Unspecified')
def canon_evidence(es):
 ee=[]
 for e in es:
  match=re.search(r'Main PDF p\. (\d+)',e['locator']);n=int(match.group(1)) if match else None
  ee.append({'source_id':SID,'document_role':'main','pdf_page':n,'printed_page':2909+n if n else None,'locator':e['locator']})
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
operation_targets={
 'stock-a':{'dissolve-a':'acid-dissolution','dry-a':'acid-removal','redissolve-a':'a-redissolution','stir-a':'a-redissolution'},
 'stock-b':{'dissolve-b':'b-dissolution','stir-b':'b-dissolution'},
 'bulk':{'mix':'bulk-mix','press':'bulk-press','fire':'bulk-fire'},
 'bulk-grinding':{'grind':'bulk-grinding','compare':'grinding-result'},
 'xrd':{'acquire':'xrd-method','scherrer':'xrd-widths'},
 'tem':{'acquire':'tem-method','compare':'tem-scales'},
 'particle-size':{'acquire':'sizing-method'},
 'downconversion':{'excite':'fluorescence-method','acquire':'fluorescence-method'},
 'upconversion':{'excite':'upconversion-method','acquire':'fluorescence-method','compare':'bulk-spectrum'},
 'near-ir':{'acquire':'near-ir-method'},
 'erbium-series':{'compare':'erbium-method'},
 'power-response':{'sweep':'power-method','fit':'power-law'},
}
for r in R:operation_targets[r]={**operation_targets['stock-a'],**operation_targets['stock-b'],'combine':'dropwise-addition','stir-suspension':'post-addition','transfer':'autoclave-charge','hydrothermal':'hydrothermal-treatment','centrifuge':'centrifugation','wash':'washing','dry':'drying','ramp':'anneal-800' if r=='anneal-800' else 'annealing-series','anneal':'anneal-800' if r=='anneal-800' else 'annealing-series','cool':'anneal-800' if r=='anneal-800' else 'annealing-series'}
measurement_targets={
 'stock-a':{'supplier':'lanthanum-oxide'},'stock-b':{'supplier':'ammonium-molybdate'},
 'bulk':{'spectral-order':'bulk-spectrum','structural-comparison':'bulk-structure-claim'},
 'bulk-grinding':{'result':'grinding-result','interpretation':'grinding-intuition'},
 'xrd':{'scherrer-size':'scherrer-size','reference':'phase','minor-phase':'phase','figure-scope':'phase','single-crystal-inference':'single-crystal-inference'},
 'tem':{'scale-before':'tem-scales','scale-after':'tem-scales','diameter-range':'tem-morphology','shape':'tem-morphology','unchanged':'anneal-size'},
 'particle-size':{'majority-range':'size-distribution','average':'size-distribution','rounded-summary':'size-distribution','histogram':'size-distribution','comparison':'single-crystal-inference'},
 'downconversion':{'emission-h':'downconversion-peaks','transition-h':'downconversion-peaks','emission-s':'downconversion-peaks','transition-s':'downconversion-peaks','signal-roles':'figure4'},
 'upconversion':{'peak-519':'upconversion-peaks','assignment-519':'upconversion-peaks','peak-541':'upconversion-peaks','assignment-541':'upconversion-peaks','peak-653':'upconversion-peaks','assignment-653':'upconversion-peaks','nano-order':'bulk-spectrum','bulk-order':'bulk-spectrum','enhancement':'bulk-spectrum','temperature-response':'anneal-emission','selected-condition':'annealing-series','temperature-mechanism':'anneal-rationale','figure6-labels':'figure6','figure10-style':'figure10'},
 'near-ir':{'center-wavenumber':'nir-band','center-wavelength':'nir-band','band-wavenumber':'nir-band','band-wavelength':'nir-band','transitions':'nir-assignment','plot-axis':'figure5-axis'},
 'erbium-series':{**{f'fraction-{v}':'erbium-method' for v in [1,2,3,4,5,7]},'text-trend':'erbium-trend','figure-trend':'erbium-conflict','optimum':'erbium-trend','recipe-limit':'erbium-method'},
 'power-response':{**{f'slope-{p}-{w}':'power-slopes' for p in ['prose','figure'] for w in [519,541,653]},'relation':'power-law','photon-count':'power-law','caption-wavelength':'power-label-conflict','figure-axes':'figure8'},
 'mechanisms':{'sensitizer':'sensitizer-emitter','two-steps':'two-photon-model','energy-diagram':'figure9-model','bulk-decay':'bulk-population','surface-sites':'surface-rationale','lifetime':'surface-rationale','emission-location':'surface-bands','size-explanation':'size-context','background':'phosphor-context','applications':'bioassay-context','excitation-definition':'phosphor-context','reference-scope':'reference-scope','source-completeness':'coverage','intensity-efficiency':'bulk-spectrum'},
}
for r in R:measurement_targets[r]={'preanneal-emission':'before-anneal','bulk-like':'anneal-size','emission-order':'anneal-emission','color':'white-powder','crystallite-size':'scherrer-size','phase-reference':'phase','growth':'anneal-size'}
material_targets={'lanthanum-oxide':'lanthanum-oxide','ytterbium-oxide':'ytterbium-oxide','erbium-oxide':'erbium-oxide','nitric-acid':'nitric-acid','water':'water','ammonium-molybdate':'ammonium-molybdate','molybdenum-trioxide':'molybdenum-trioxide'}

rowlinks={};operationlinks={};parameterlinks={};materiallinks={};stocklinks={}
for rid,d in drafts.items():
 short=rid.removeprefix(P)
 for n,m in enumerate(d.get('measurements',[])):
  target=measurement_targets[short][m['id']];f=append_fact(target,rid,f'/measurements/{n}',m['id'],m['property'].replace('_',' ').capitalize(),m['value'],m['evidence'],m['value'].get('status','reported'),m['sample_id'],m.get('conditions'));f['canonical_measurement_id']=m['id'];rowlinks[rid+'::'+m['id']]=target
 for n,op in enumerate(d.get('operations',[])):
  target=operation_targets[short][op['id']];pointer=f'/operations/{n}';items[target]['canonical_links'].append({'record_id':rid,'json_pointer':pointer,'relation':'Source-defined operation. Shared preparation steps retain source-defined applicability; repeated procedure context does not establish separate physical batches or supply missing variant charges.'});operationlinks[rid+'::'+op['id']]=target
  for name,q in op.get('parameters',{}).items():
   f=append_fact(target,rid,pointer+'/parameters/'+name,'operation-'+op['id']+'-'+name,op['label']+' · '+name.replace('_',' '),q,q.get('evidence',op['evidence']),'operation_parameter',extra=op.get('description'));f['canonical_operation_id']=op['id'];f['canonical_parameter']=name;parameterlinks[rid+'::'+op['id']+'::'+name]=target
 for n,mat in enumerate(d.get('materials',[])):
  for name,q in mat.get('quantities',{}).items():
   target=material_targets[mat['id']];f=append_fact(target,rid,f'/materials/{n}/quantities/{name}','material-'+mat['id']+'-'+name,mat['name']+' · '+name.replace('_',' '),q,q.get('evidence',mat['evidence']),'material_quantity');f['canonical_material_id']=mat['id'];materiallinks[rid+'::'+mat['id']+'::'+name]=target
 for n,stock in enumerate(d.get('stocks',[])):
  for name,q in stock.get('concentrations',{}).items():
   target='stock-a-composition' if stock['id']=='solution-a-stock' else 'stock-b-composition';f=append_fact(target,rid,f'/stocks/{n}/concentrations/{name}','stock-'+stock['id']+'-'+name,stock['name']+' · '+name.replace('_',' '),q,q.get('evidence',stock['evidence']),'stock_concentration');f['canonical_stock_id']=stock['id'];stocklinks[rid+'::'+stock['id']+'::'+name]=target
  for c,component in enumerate(stock.get('components',[])):
   for name,q in component.get('quantities',{}).items():
    target=material_targets[component['material_id']];f=append_fact(target,rid,f'/stocks/{n}/components/{c}/quantities/{name}','stock-'+stock['id']+'-'+component['material_id']+'-'+name,stock['name']+' · '+component['material_id']+' '+name.replace('_',' '),q,q.get('evidence',stock['evidence']),'stock_component');f['canonical_stock_id']=stock['id'];f['canonical_material_id']=component['material_id'];stocklinks[rid+'::'+stock['id']+'::'+component['material_id']+'::'+name]=target
for ii in items.values():
 joins=[]
 for f in ii['facts']:
  if not f.get('sample_id'):continue
  rid=f['canonical_record_id'];sample=f['sample_id'];n=next(n for n,p in enumerate(drafts[rid].get('products',[])) if p['sample_id']==sample)
  join={'record_id':rid,'sample_id':sample,'json_pointer':f'/products/{n}','relation':SCOPE[ii['sample_scope']['scope_kind']]}
  if join not in joins:joins.append(join)
 ii['sample_scope']['formulations']=list(dict.fromkeys(x['sample_id'] for x in joins))
 if joins:ii['sample_scope']['canonical_sample_links']=joins
 ii['canonical_links']=list({json.dumps(x,sort_keys=True):x for x in ii['canonical_links']}.values())

out['record_formulation_labels']={rid:[p['sample_id'] for p in d.get('products',[])] for rid,d in drafts.items()}
out['record_formulation_scope_note']='Record IDs are required for sample labels. Source-specific 800 °C XRD/TEM, generic optical/sizing contexts, five temperature endpoints, incomplete Er variants and bulk comparator remain distinct; shared protocols do not establish physical batch identity.'
out['counts'].update({'typed_characterization_rows':len(rowlinks),'linked_operations':len(operationlinks),'operation_parameter_facts':len(parameterlinks),'reagent_quantity_facts':len(materiallinks),'stock_quantity_facts':len(stocklinks)})
(O/'canonical-measurement-coverage.json').write_text(json.dumps({'measurement_count':len(rowlinks),'measurement_to_reader_item':rowlinks,'operation_count':len(operationlinks),'operation_to_reader_item':operationlinks,'operation_parameter_count':len(parameterlinks),'operation_parameter_to_reader_item':parameterlinks,'material_quantity_count':len(materiallinks),'material_quantity_to_reader_item':materiallinks,'stock_quantity_count':len(stocklinks),'stock_quantity_to_reader_item':stocklinks,'draft_sha256':{k:sha(B/'canonical-drafts'/f'{k}.json') for k in drafts}},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
