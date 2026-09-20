"""Exact canonical links and typed quantities, executed after source prose is authored."""
drafts={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')}
measurement_targets={
'ag-structure':{'crystallinity':'ag-lattice','assembly':'ag-packing','elemental_identification':'ag-eds','polycrystallinity':'ag-polycrystals','population_scope':'ag-majority-single','interparticle-separation':'ag-tem','fig2-a-scale':'ag-tem','fig2-b-scale':'ag-packing','fig2-c-scale':'ag-lattice',**{'fig11-'+k+'-scale':'ag-polycrystals' for k in 'abcd'}},
'ag-typical-framework':{'cell-internal-diameter':'apparatus','darkest-time':'reaction-dwell','apparatus':'apparatus'},
'ir':{'crystalline-core':'ir-tem','tem-scale':'ir-tem','tem-inset-scale':'ir-tem'},
'pt':{'crystalline-core':'pt-tem','tem-scale':'pt-tem'},
'optical-comparison':{'spectrum-i-scope':'optical-current','spectrum-ii-scope':'optical-c10','spectrum-iii-scope':'optical-hydrocarbon','i-peak':'optical-current','i-diameter-context':'optical-current','ii-diameter-context':'optical-c10','iii-relative-size':'optical-hydrocarbon','width-comparison':'optical-width-interpretation','electron-path':'optical-width-interpretation'},
'recovery':{'alternative-solvents':'chemical-other-solvents','unreported-drying':'redisperse'},
'solvation':{'synthesis-stability':'dispersibility','co2-redispersion':'dispersibility','repeated-dispersion':'dispersibility','c10-dispersion':'chain-length','tail-solvation':'chain-length','polar-solvents':'polar-solvation','rigidity':'ligand-rigidity','short-hydrocarbon':'polar-solvation','ligand-excess':'thiol-excess','outlook':'outlook','hydrocarbon-spacing':'spacing-comparison','fluorinated-shortening':'conflict-chain'},
'growth-model':{'equation-1':'equation-1','equation-2':'equation-2','equation-3':'equation-3','force-model-assumptions':'equation-1','psi1':'scaled-distributions','radius-definitions':'moment-ratios','psi2':'cumulative-distribution','self-similarity':'scaled-distributions','coagulation':'coagulation-condensation','unit-sticking':'cumulative-distribution','nonunit-sticking':'cumulative-distribution','three-stages':'nucleation-growth','polycrystals':'coagulation-structure','gold-realignment':'coagulation-structure','parameter-effects':'thiol-excess','cited-thiol-ratios':'note32-context','cited-supercritical-nanowires':'reference-22','frequency':'equation-2','silver-vacuum':'equation-2','silver-co2':'equation-3','silver-acetone':'equation-3','hamaker-temperature':'conflict-temperature','critical-temperature':'conflict-temperature','critical-pressure':'conflict-temperature','mu1':'moment-ratios','mu3':'moment-ratios','model-sticking':'cumulative-distribution','mu1-threshold':'moment-ratios','mu3-threshold':'moment-ratios','global-spread':'ag-diameter-range','stronger-attraction':'equation-3'}}
op_targets={
'ag-typical-framework':{'load':'charge-ag','fill':'fill-co2','condition':'heat','inject':'simultaneous-injection','hold':'reaction-dwell'},
'recovery':{'cool':'cool-vent','depressurize':'cool-vent','vent':'cool-vent','collect':'collect','precipitate':'precipitate','redisperse':'redisperse'},
'tem-eds':{'deposit':'tem-acquisition','image':'tem-acquisition','size':'size-analysis','eds':'eds-acquisition'},
'growth-analysis':{'volume':'size-analysis','normalize':'scaled-distributions','moments':'moment-ratios','cumulative':'cumulative-distribution'}}
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
  match=re.search(r'Main PDF p\. (\d+)',e['locator'])
  x={'source_id':SID,'document_role':'main','pdf_page':int(match.group(1)) if match else None,'printed_page':9432+int(match.group(1)) if match else None,'locator':e['locator']}
  if not match:x['scope']='Complete supplied main PDF pages 1–8'
  ee.append(x)
 return ee
def append_fact(target,rid,pointer,identifier,label,q,es,basis,sample=None,extra=None):
 ii=items[target];ee=canon_evidence(es)
 f={'id':rid+'::'+identifier,'label':label,'value':quantity_display(q),'unit':q.get('unit'),'approximate':q.get('approximate',False),'basis':basis,'qualifier':' '.join(x for x in [q.get('basis'),q.get('qualifier'),q.get('note'),extra] if x),'evidence':ee,'canonical_record_id':rid,'json_pointer':pointer,'canonical_quantity':q,'training_eligible':False}
 if sample:f['sample_id']=sample
 ii['facts'].append(f);ii['canonical_links'].append({'record_id':rid,'json_pointer':pointer,'relation':SCOPE[ii['sample_scope']['scope_kind']]})
 for e in ee:
  if e not in ii['evidence']:ii['evidence'].append(e)
  if e['locator'] not in ii['source_locators']:ii['source_locators'].append(e['locator'])
 return f
rowlinks={};operationlinks={};parameterlinks={};materiallinks={}
for rid,d in drafts.items():
 short=rid.removeprefix(P)
 for n,m in enumerate(d.get('measurements',[])):
  target='table1-'+short[-1] if short in AG else measurement_targets[short][m['id']]
  basis='author_theory_or_interpretation' if short=='growth-model' else ('cited_comparison' if m['property'].startswith('cited_') else m['value'].get('status','reported'))
  f=append_fact(target,rid,f'/measurements/{n}',m['id'],m['property'].replace('_',' ').capitalize(),m['value'],m['evidence'],basis,m['sample_id'],m.get('conditions'))
  f['canonical_measurement_id']=m['id'];rowlinks[rid+'::'+m['id']]=target
 for n,op in enumerate(d.get('operations',[])):
  target='table1-'+short[-1] if short in AG else short+'-route' if short in ['ir','pt'] else op_targets[short][op['id']]
  ii=items[target];pointer=f'/operations/{n}';ii['canonical_links'].append({'record_id':rid,'json_pointer':pointer,'relation':'Reported operation; retain any explicitly marked common-method inheritance and original source scope.'})
  operationlinks[rid+'::'+op['id']]=target
  for name,q in op.get('parameters',{}).items():
   qp=pointer+'/parameters/'+name
   f=append_fact(target,rid,qp,'operation-'+op['id']+'-'+name,op['label']+' · '+name.replace('_',' '),q,q.get('evidence',op['evidence']),'operation_parameter',extra=op.get('description'))
   f['canonical_operation_id']=op['id'];f['canonical_parameter']=name
   parameterlinks[rid+'::'+op['id']+'::'+name]=target
 for n,mat in enumerate(d.get('materials',[])):
  for name,q in mat.get('quantities',{}).items():
   target={'co2':'chemical-co2','hydrogen':'chemical-h2'}[mat['id']]
   pointer=f'/materials/{n}/quantities/{name}'
   f=append_fact(target,rid,pointer,'material-'+mat['id']+'-'+name,mat['name']+' · '+name.replace('_',' '),q,q.get('evidence',mat['evidence']),'reagent_specification')
   f['canonical_material_id']=mat['id'];materiallinks[rid+'::'+mat['id']+'::'+name]=target
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
out['record_formulation_scope_note']='Curator context/sample IDs require their record ID. No physical batch identity or unreported cross-figure join is asserted.'
out['counts'].update({'typed_characterization_rows':len(rowlinks),'linked_operations':len(operationlinks),'operation_parameter_facts':len(parameterlinks),'reagent_quantity_facts':len(materiallinks)})
(O/'canonical-measurement-coverage.json').write_text(json.dumps({'measurement_count':len(rowlinks),'measurement_to_reader_item':rowlinks,'operation_count':len(operationlinks),'operation_to_reader_item':operationlinks,'operation_parameter_count':len(parameterlinks),'operation_parameter_to_reader_item':parameterlinks,'material_quantity_count':len(materiallinks),'material_quantity_to_reader_item':materiallinks,'draft_sha256':{k:sha(B/'canonical-drafts'/f'{k}.json') for k in drafts}},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
