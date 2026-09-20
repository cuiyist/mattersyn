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
  match=re.search(r'(Main|SI) PDF p\. (\d+)',e['locator'],re.I);n=int(match.group(2)) if match else None;role='si' if match and match.group(1).lower()=='si' else 'main'
  ee.append({'source_id':SID,'document_role':role,'pdf_page':n,'printed_page':158+n if n and role=='main' else None,'locator':e['locator']})
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
exec((O/'canonical_targets.py').read_text(encoding='utf8'))
rowlinks={};operationlinks={};parameterlinks={};materiallinks={};stocklinks={}
for rid,d in drafts.items():
 short=rid.removeprefix(P)
 for n,m in enumerate(d.get('measurements',[])):
  target=measurement_targets[short][m['id']];f=append_fact(target,rid,f'/measurements/{n}',m['id'],m['property'].replace('_',' ').capitalize(),m['value'],m['evidence'],m['value'].get('status','reported'),m['sample_id'],m.get('conditions'));f['canonical_measurement_id']=m['id'];rowlinks[rid+'::'+m['id']]=target
 for n,op in enumerate(d.get('operations',[])):
  target=operation_targets[short][op['id']];pointer=f'/operations/{n}';items[target]['canonical_links'].append({'record_id':rid,'json_pointer':pointer,'relation':'Source-defined operation. Aliquot quenching is distinct from bulk termination; common study identity does not resolve caption/body conflicts or unreported batch identity.'});operationlinks[rid+'::'+op['id']]=target
  for name,q in op.get('parameters',{}).items():
   f=append_fact(target,rid,pointer+'/parameters/'+name,'operation-'+op['id']+'-'+name,op['label']+' · '+name.replace('_',' '),q,q.get('evidence',op['evidence']),'operation_parameter',extra=op.get('description'));f['canonical_operation_id']=op['id'];f['canonical_parameter']=name;parameterlinks[rid+'::'+op['id']+'::'+name]=target
 for n,mat in enumerate(d.get('materials',[])):
  for name,q in mat.get('quantities',{}).items():
   target=material_targets[mat['id']];f=append_fact(target,rid,f'/materials/{n}/quantities/{name}','material-'+mat['id']+'-'+name,mat['name']+' · '+name.replace('_',' '),q,q.get('evidence',mat['evidence']),'material_quantity');f['canonical_material_id']=mat['id'];materiallinks[rid+'::'+mat['id']+'::'+name]=target
 for n,stock in enumerate(d.get('stocks',[])):
  for name,q in stock.get('concentrations',{}).items():
   target=(route_stock.get(short) or stock_targets[stock['id']]);f=append_fact(target,rid,f'/stocks/{n}/concentrations/{name}','stock-'+stock['id']+'-'+name,stock['name']+' · '+name.replace('_',' '),q,q.get('evidence',stock['evidence']),'stock_concentration',extra=('Inherited stock condition: '+stock.get('scope','source-defined shared framework')) if q.get('status')=='inherited' else None);f['canonical_stock_id']=stock['id'];stocklinks[rid+'::'+stock['id']+'::'+name]=target
  for c,component in enumerate(stock.get('components',[])):
   for name,q in component.get('quantities',{}).items():
    target=route_stock.get(short) or material_targets[component['material_id']];f=append_fact(target,rid,f'/stocks/{n}/components/{c}/quantities/{name}','stock-'+stock['id']+'-'+component['material_id']+'-'+name,stock['name']+' · '+component['material_id']+' '+name.replace('_',' '),q,q.get('evidence',stock['evidence']),'stock_component');f['canonical_stock_id']=stock['id'];f['canonical_material_id']=component['material_id'];stocklinks[rid+'::'+stock['id']+'::'+component['material_id']+'::'+name]=target
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
out['record_formulation_scope_note']='Always pair record and sample IDs. Individual particles, spherical assemblies, wires, optical aliquots, electrical devices and models remain separate contexts. Common study identity does not establish a single physical batch or resolve source-ratio conflicts.'
out['counts'].update({'typed_characterization_rows':len(rowlinks),'linked_operations':len(operationlinks),'operation_parameter_facts':len(parameterlinks),'reagent_quantity_facts':len(materiallinks),'stock_quantity_facts':len(stocklinks)})
(O/'canonical-measurement-coverage.json').write_text(json.dumps({'measurement_count':len(rowlinks),'measurement_to_reader_item':rowlinks,'operation_count':len(operationlinks),'operation_to_reader_item':operationlinks,'operation_parameter_count':len(parameterlinks),'operation_parameter_to_reader_item':parameterlinks,'material_quantity_count':len(materiallinks),'material_quantity_to_reader_item':materiallinks,'stock_quantity_count':len(stocklinks),'stock_quantity_to_reader_item':stocklinks,'draft_sha256':{k:sha(B/'canonical-drafts'/f'{k}.json') for k in drafts}},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
