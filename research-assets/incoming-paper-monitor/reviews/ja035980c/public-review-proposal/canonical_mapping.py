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
  ee.append({'source_id':SID,'document_role':role,'pdf_page':n,'printed_page':10341+n if n and role=='main' else None,'locator':e['locator']})
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
oxidation_ops={'oxidize':'oxidative-treatment','acid-hcl':'hcl-treatment','acid-hf':'hf-treatment','wash-tubes':'water-wash','dry-tubes':'dry-nanotubes'}
operation_targets={
'oxidation':oxidation_ops,
'growth':{**oxidation_ops,'mix-cd':'precursor-mixing','heat':'precursor-heating','adjust':'te-injection','injection':'te-injection','grow':'growth','stop':'cooling','cool':'cooling','solvate':'toluene-addition','precipitate':'precipitation','filter':'filtration','wash':'toluene-washing','final-dry':'product-drying'},
'electron-microscopy':{'disperse':'tem-preparation','deposit':'tem-preparation','image-tem':'tem-acquisition','image-hrtem':'hrtem-acquisition'},
'sem':{'deposit':'sem-preparation','image':'sem-acquisition'},'eds':{'analyze':'eds-acquisition'},
'xps':{'mount':'xps-mounting','evacuate':'xps-mounting','survey':'xps-survey','high-resolution':'xps-high-resolution'},
'xrd':{'acquire':'xrd-acquisition'},'uv-visible':{'dissolve-washings':'uv-preparation','disperse-composite':'uv-preparation','acquire':'uv-acquisition'},
'infrared':{'acquire':'ir-acquisition'},'raman':{'acquire':'raman-acquisition'}}
measurement_targets={
'oxidation':{'oxygen':'oxidation-coverage','cleaning':'purification-evidence','surface-sites':'surface-groups'},
'growth':{'long-axis':'particle-dimensions','aspect':'particle-dimensions','tdpa-role':'tdpa','junctions':'figure4-junction'},
'electron-microscopy':{**{f'scale-1{p}':'figure1' for p in 'abcd'},**{f'scale-2{p}':'figure2-tem' for p in 'cde'},'scale-3a':'figure3-interface','scale-3a-inset':'figure3-interface',**{f'scale-3{p}':'figure3-sites' for p in 'bcd'},**{f'scale-4{p}':'figure4-junction' for p in 'abc'},'pristine':'figure1','oxidation':'oxidation-morphology','figure2':'figure2-tem','figure3':'figure3-sites','figure4':'figure4-junction','phase':'crystal-phase','site-density':'site-selectivity'},
'sem':{'scale-2a':'figure2-sem','scale-2b':'figure2-sem','motifs':'figure2-sem'},
'eds':{'elements':'eds-elements','plotted-elements':'eds-elements','energy-units':'eds-unit-conflict','metal-limit':'purification-evidence'},
'xps':{'cd-binding':'surface-xps','strong-oxygen':'oxidation-coverage','mild-oxygen':'oxidation-coverage','carbon':'surface-xps','tellurium':'teo3','oxygen-curve':'figure5-xps','passivation':'passivation-model','thermal-decomposition':'thermal-context','carboxyl-removal':'thermal-context','integrity':'thermal-context'},
'xrd':{'cdte-indices':'xrd-indexing','mwnt-indices':'xrd-indexing','mixed-phase':'crystal-phase','broadening':'xrd-broadening','axis-range':'xrd-indexing'},
'uv-visible':{'plot-range':'figure7','composite-spectrum':'uv-heterostructure','background':'uv-heterostructure','washings-heterogeneity':'uv-washings','detachment':'detachment-model','signal-type':'figure7'},
'infrared':{'axis':'si-ir','assignments':'si-ir','identity':'si-identity'},
'raman':{'lo':'raman-cdte','bulk-lo':'raman-cdte','g-precursor':'raman-carbon','d-precursor':'raman-carbon','g-composite':'raman-carbon','d-composite':'raman-carbon','lo-absent':'raman-cdte','confinement':'quantum-confinement','plot':'figure6'},
'oxidation-controls':{'strong-oxygen':'oxidation-coverage','mild-oxygen':'oxidation-coverage','strong-result':'oxidation-coverage','mild-result':'oxidation-coverage','pristine-result':'oxidation-coverage','raw-scope':'control-scope','correlation':'oxidation-coverage'},
'free-nanocrystals':{'free-prose-size':'free-particle-size','no-tube-size':'free-particle-size','free-shape':'free-particle-size','later-comparison':'uv-washings','no-tube-recipe':'free-particle-size'},
'mechanisms':{'coordination':'figure8-model','ligand-competition':'tdpa-competition','diffusion':'diffusion-model','site-geometry':'shape-variables','tip-preference':'site-selectivity','junction':'shape-variables','scheme':'figure8-model','passivation':'passivation-model','swnt-limit':'mwnt-swnt','outlook':'outlook'},
'source-context':{'documents':'coverage','external-preparations':'missing-fields','prior-attachment':'prior-cdse','other-nanostructures':'chemistry-context','measurement-limits':'property-limits','matching':'si-identity'},
}
material_targets={'cadmium-oxide':'cdo','tdpa':'tdpa','topo':'topo','te-top-stock':'te-top','hydrochloric-acid':'hcl','hydrofluoric-acid':'hf','tellurium-source':'te-top','top':'te-top'}
stock_targets={'hydrochloric-acid-solution':'hcl','hydrofluoric-acid-solution':'hf','te-in-top':'te-top'}

rowlinks={};operationlinks={};parameterlinks={};materiallinks={};stocklinks={}
for rid,d in drafts.items():
 short=rid.removeprefix(P)
 for n,m in enumerate(d.get('measurements',[])):
  target=measurement_targets[short][m['id']];f=append_fact(target,rid,f'/measurements/{n}',m['id'],m['property'].replace('_',' ').capitalize(),m['value'],m['evidence'],m['value'].get('status','reported'),m['sample_id'],m.get('conditions'));f['canonical_measurement_id']=m['id'];rowlinks[rid+'::'+m['id']]=target
 for n,op in enumerate(d.get('operations',[])):
  target=operation_targets[short][op['id']];pointer=f'/operations/{n}';items[target]['canonical_links'].append({'record_id':rid,'json_pointer':pointer,'relation':'Source-defined operation. Upstream nanotube oxidation may be inherited by the composite route; this does not establish separate experimental batches or fill unreported conditions.'});operationlinks[rid+'::'+op['id']]=target
  for name,q in op.get('parameters',{}).items():
   f=append_fact(target,rid,pointer+'/parameters/'+name,'operation-'+op['id']+'-'+name,op['label']+' · '+name.replace('_',' '),q,q.get('evidence',op['evidence']),'operation_parameter',extra=op.get('description'));f['canonical_operation_id']=op['id'];f['canonical_parameter']=name;parameterlinks[rid+'::'+op['id']+'::'+name]=target
 for n,mat in enumerate(d.get('materials',[])):
  for name,q in mat.get('quantities',{}).items():
   target=material_targets[mat['id']];f=append_fact(target,rid,f'/materials/{n}/quantities/{name}','material-'+mat['id']+'-'+name,mat['name']+' · '+name.replace('_',' '),q,q.get('evidence',mat['evidence']),'material_quantity');f['canonical_material_id']=mat['id'];materiallinks[rid+'::'+mat['id']+'::'+name]=target
 for n,stock in enumerate(d.get('stocks',[])):
  for name,q in stock.get('concentrations',{}).items():
   target=stock_targets[stock['id']];f=append_fact(target,rid,f'/stocks/{n}/concentrations/{name}','stock-'+stock['id']+'-'+name,stock['name']+' · '+name.replace('_',' '),q,q.get('evidence',stock['evidence']),'stock_concentration');f['canonical_stock_id']=stock['id'];stocklinks[rid+'::'+stock['id']+'::'+name]=target
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
out['record_formulation_scope_note']='Always pair record and sample IDs. Pristine/oxidized nanotubes, attached CdTe, free washings, no-tube comparator, control oxidation levels and author models are distinct contexts; common study identity does not establish a single physical batch.'
out['counts'].update({'typed_characterization_rows':len(rowlinks),'linked_operations':len(operationlinks),'operation_parameter_facts':len(parameterlinks),'reagent_quantity_facts':len(materiallinks),'stock_quantity_facts':len(stocklinks)})
(O/'canonical-measurement-coverage.json').write_text(json.dumps({'measurement_count':len(rowlinks),'measurement_to_reader_item':rowlinks,'operation_count':len(operationlinks),'operation_to_reader_item':operationlinks,'operation_parameter_count':len(parameterlinks),'operation_parameter_to_reader_item':parameterlinks,'material_quantity_count':len(materiallinks),'material_quantity_to_reader_item':materiallinks,'stock_quantity_count':len(stocklinks),'stock_quantity_to_reader_item':stocklinks,'draft_sha256':{k:sha(B/'canonical-drafts'/f'{k}.json') for k in drafts}},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
