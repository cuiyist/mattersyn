"""Canonical facts are bound without changing values, units, missingness or cohort IDs."""
drafts=records
default_targets={'afm-acquisition':'afm-acquisition','aps-functionalization':'aps-variant','buffer-exchange':'buffer-exchange','core-shell-stock':'core-shell-stock','cw-photostability':'cw-acquisition','eels-acquisition':'eels-acquisition','ellman-assay':'ellman-acquisition','gel-band-narrowing':'gel-narrowing','gel-electrophoresis':'gel-acquisition','gel-ph-stability':'gel-ph','gel-salt-stability':'gel-salt','hplc-acquisition':'hplc-acquisition','hplc-purification':'hplc-purification','optical-acquisition':'optical-acquisition','storage-photostability':'storage-acquisition','tem-acquisition':'tem-acquisition'}
op_targets={
'silica-silanization':dict(zip('precipitate mps basify dilute stir1 heat1 cool1 feed2 stir2 heat2 cool2 prepare-quench quench stir3 heat3 age rotovap rest24 dialyze-methanol filter045 centrifugal-concentrate rest12 column rest-aqueous filter022 optional-dialysis optional-filter optional-vacufuge clear store'.split(),'silica-prime silica-prime silica-prime silica-primary silica-primary silica-primary silica-primary silica-secondary silica-secondary silica-secondary silica-secondary silica-quench silica-quench silica-quench silica-quench silica-quench silica-dialysis silica-dialysis silica-dialysis silica-dialysis silica-concentrate silica-concentrate silica-exchange silica-exchange silica-exchange silica-optional silica-optional silica-optional silica-finish silica-finish'.split())),
'mpa-exchange':dict(zip('precipitate resuspend sonicate age prepare-dmap add-dmap collect dry dissolve clear optional-nap'.split(),'mpa-exchange mpa-exchange mpa-exchange mpa-exchange chemical-dmap mpa-recovery mpa-recovery mpa-recovery mpa-recovery mpa-recovery mpa-optional'.split()))}
measurement_targets={
'afm-acquisition':{'small-feature-range':'afm-exclusions','histogram-filter':'afm-exclusions'},
'cw-photostability':{'nc-stability':'cw-result','brightening-level':'cw-result','dye-bleaching':'cw-result','plotted-end':'cw-result','mechanism':'brightening-mechanism'},
'eels-acquisition':{'preliminary-shell':'eels-result'},'ellman-assay':{'accessible-thiols':'thiol-result','stable-time':'thiol-result'},
'gel-band-narrowing':{'yield-upper':'narrowing-result','panel-pH':'gel-conflicts','narrowing':'narrowing-result'},
'gel-ph-stability':{'silica-migration':'gel-charge','mpa-migration':'gel-charge','image-scale':'gel-ph'},
'gel-salt-stability':{k:'salt-result' for k in ['silica-constant-through','mpa-retardation-above','other-nacl','other-duration','other-outcome']},
'hplc-acquisition':{**{k:'hplc-three' for k in ['void-time','void-area','fluorescent-time','fluorescent-area','late-time','late-area']},**{k:'hplc-purified' for k in ['purified-result','gel-comparison','gel_agarose','gel_pb','gel_pH','gel_duration','gel_voltage','gel_scale_bar']},**{k:'hplc-size-limit' for k in ['small-size-fraction','pore-limit-context','size-limit']}},
'literature-context':{**{k:'background-quantitative' for k in ['prior-size','prior-qy','dye-lifetime','nc-lifetime']},'prior-silica':'silica-literature','prior-qy-loss':'silica-literature','scope':'prior-coatings','biocompatibility':'why-shell','source-summary':'study-summary'},
'silanization-mechanism':{'primer':'mps-binding','slow-hydrolysis':'methanol-choice','consolidation':'primary-network','secondary-growth':'secondary-network','quench':'quench-rationale','phosphonate-identity':'chemical-phosphonate','equilibration':'equilibration','purification':'column-chemistry','amine-binding':'aps-control','priming-pH':'mps-binding','growth-pH':'methanol-choice','hydrolysis-pH':'methanol-choice','base-water':'chemical-base','fresh-water':'secondary-network','postfeed-pH':'secondary-network','silica-reduction':'column-chemistry','column-perturbation':'column-chemistry'},
'silica-silanization':{'applicability-size':'silica-prime','workup-hardware':'purification-materials','column-water-option':'column-chemistry'},
'surface-interpretation':{'functional-groups':'surface-chemistry','charge':'gel-charge','bioconjugation':'surface-chemistry','silica-first-peak':'size-ambiguity','silica-second-peak':'afm-results','mpa-green':'size-ambiguity','mpa-large':'size-ambiguity','afm-limit':'size-ambiguity','partial-shell-selection':'hplc-outlook','future-qy':'future-qy','future-separation':'hplc-outlook','dna':'future-bioconjugation','negative-pH':'gel-charge','first-height':'afm-results','rare-large':'afm-results','shell-height-bound':'shell-thickness','shell-bound':'shell-thickness','mpa-small-increase':'size-ambiguity'},
'synthesis-controls':{'toluene-outcome':'methanol-choice','no-base-outcome':'mps-binding','excess-base-outcome':'mps-binding','overheat-outcome':'thermal-control','partial-shell-methanol-outcome':'thermal-control','partial-shell-water-outcome':'thermal-control','unquenched-outcome':'quench-rationale','no-phosphonate-outcome':'quench-rationale','overconcentrated-outcome':'equilibration','short-aging-outcome':'equilibration','aps-priming-outcome':'aps-control','overheat-temperature':'thermal-control','overheat-duration':'thermal-control','partial-dialysis-lag':'thermal-control','aps-scattering':'aps-control','postquench-rest-context':'equilibration','discussion-intermediate-rest':'purification-conflicts'},
'tem-acquisition':{'shell-visibility':'si-microscopy','si-shell-claim':'si-microscopy','coreshell-size-context':'si-microscopy'},
'upstream-controls':{'no-cdse-test':'upstream-zns','stored-test':'upstream-zns','scatter-method':'note34-scattering','detection-angle':'note34-scattering','methanol-scatter-ratio':'note34-scattering','mps-scatter':'note34-scattering'},
}
def measurement_target(short,m):
 mid=m['id']
 if short.startswith('size-'):
  return 'figure5-yellow' if mid=='histogram' else 'shell-thickness' if mid=='shell-estimate' else 'size-ambiguity' if mid=='structure-limit' else 'afm-results' if mid=='source-height-increase' else 'table2-'+short.removeprefix('size-')
 if short=='optical-properties':
  if mid in ['green-body-emission','yellow-body-emission']:return 'optical-conflicts'
  if mid.startswith(('blue-','green-','yellow-','orange-','red-')):return 'table1-'+mid.split('-')[0]
  return {'absorption-comparison-window':'optical-overview','fwhm-results':'optical-width','fwhm-abstract':'optical-width','water-redshift':'optical-overview','stokes-shift':'optical-width','qy-retention-summary':'optical-width','shape':'optical-overview'}[mid]
 if short=='storage-photostability':return 'ph-optical' if mid.startswith('pH-') else 'storage-result'
 if short in measurement_targets:return measurement_targets[short][mid]
 return default_targets[short]
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
  ee.append({'source_id':SID,'document_role':'main','pdf_page':n,'printed_page':8860+n if n else None,'locator':e['locator']})
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
rowlinks={};operationlinks={};parameterlinks={};materiallinks={};stocklinks={}
for rid,d in drafts.items():
 short=rid.removeprefix(P)
 for n,m in enumerate(d.get('measurements',[])):
  target=measurement_target(short,m);basis=m['value'].get('status','reported')
  f=append_fact(target,rid,f'/measurements/{n}',m['id'],m['property'].replace('_',' ').capitalize(),m['value'],m['evidence'],basis,m['sample_id'],m.get('conditions'))
  f['canonical_measurement_id']=m['id'];rowlinks[rid+'::'+m['id']]=target
 for n,op in enumerate(d.get('operations',[])):
  target=op_targets[short][op['id']] if short in op_targets else default_targets[short];ii=items[target];pointer=f'/operations/{n}'
  ii['canonical_links'].append({'record_id':rid,'json_pointer':pointer,'relation':'Reported operation; optionality, retained fraction, branch and source scope remain canonical.'});operationlinks[rid+'::'+op['id']]=target
  for name,q in op.get('parameters',{}).items():
   f=append_fact(target,rid,pointer+'/parameters/'+name,'operation-'+op['id']+'-'+name,op['label']+' · '+name.replace('_',' '),q,q.get('evidence',op['evidence']),'operation_parameter',extra=op.get('description'))
   f['canonical_operation_id']=op['id'];f['canonical_parameter']=name;parameterlinks[rid+'::'+op['id']+'::'+name]=target
 for n,mat in enumerate(d.get('materials',[])):
  for name,q in mat.get('quantities',{}).items():
   assert mat['id']=='phosphonate-stock',mat['id'];target='chemical-phosphonate';pointer=f'/materials/{n}/quantities/{name}'
   f=append_fact(target,rid,pointer,'material-'+mat['id']+'-'+name,mat['name']+' · '+name.replace('_',' '),q,q.get('evidence',mat.get('evidence',[])),'reagent_specification')
   f['canonical_material_id']=mat['id'];materiallinks[rid+'::'+mat['id']+'::'+name]=target
 for n,stock in enumerate(d.get('stocks',[])):
  for name,q in stock.get('concentrations',{}).items():
   target='chemical-phosphonate' if 'phosphonate' in stock['id'] else 'chemical-dmap' if 'dmap' in stock['id'] else 'core-shell-stock' if 'upstream' in stock['id'] else 'buffers'
   f=append_fact(target,rid,f'/stocks/{n}/concentrations/{name}','stock-'+stock['id']+'-'+name,stock['name']+' · '+name.replace('_',' '),q,q.get('evidence',stock['evidence']),'stock_concentration')
   f['canonical_stock_id']=stock['id'];stocklinks[rid+'::'+stock['id']+'::'+name]=target
  for c,component in enumerate(stock.get('components',[])):
   for name,q in component.get('quantities',{}).items():
    target='chemical-dmap' if 'dmap' in stock['id'] else 'core-shell-stock'
    f=append_fact(target,rid,f'/stocks/{n}/components/{c}/quantities/{name}','stock-'+stock['id']+'-'+component['material_id']+'-'+name,stock['name']+' · '+component['material_id']+' '+name.replace('_',' '),q,q.get('evidence',stock['evidence']),'stock_component')
    f['canonical_stock_id']=stock['id'];f['canonical_material_id']=component['material_id'];stocklinks[rid+'::'+stock['id']+'::'+component['material_id']+'::'+name]=target
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
out['record_formulation_scope_note']='Sample labels require their canonical record ID. No physical batch identity is asserted from a reused color name.'
out['review_scope']='supplied_main_only_si_unverified'
out['corpus_paper_id']='paper-d3cbbb38be2025d1cbe1'
out['corpus_document_id']='doc-4a098734749b2dd6a6a2'
out['evidence_conflicts'].extend({'id':k,'text':items[k]['text'],'source_locators':items[k]['source_locators']} for k in ['chemical-phosphonate','afm-cross-reference-conflict'])
out['material_evidence_records']={
 'CdSe/ZnS/siloxane':[rid for rid in drafts if rid!=P+'mpa-exchange'],
 'CdSe/ZnS':list(drafts),
 'CdSe':[P+'size-'+c for c in ['green','yellow','red','dark-red']],
 'ZnS':[P+'upstream-controls'],
}
out['material_evidence_scope_notes']={
 'CdSe/ZnS/siloxane':'Primary silica-coating route and characterization, with explicitly scoped MPA comparison cohorts. The standalone MPA coating route is not the silica route; shared assays are not new synthesis routes.',
 'CdSe/ZnS':'Starting core/shell stock, silica/MPA downstream coatings and their explicitly labeled comparisons; no complete upstream core/shell recipe is reproduced in this source.',
 'CdSe':'Only Table 2 CdSe core TEM diameters within paired core/shell/coating size cohorts. Shared size records also contain other coating states; those are not properties of bare CdSe. No bare-CdSe recipe or independent bare-core crystal structure is supplied.',
 'ZnS':'Incomplete upstream residual-ZnS diagnostic context only, including a no-CdSe hot-TOPO comparison and aged shell stock. This does not establish a fully specified ZnS synthesis or a new material page.',
}
from collections import Counter
out['counts'].update({'record_types':dict(Counter(d['record_type'] for d in drafts.values())),'typed_characterization_rows':len(rowlinks),'linked_operations':len(operationlinks),'operation_parameter_facts':len(parameterlinks),'reagent_quantity_facts':len(materiallinks),'stock_quantity_facts':len(stocklinks)})
(O/'canonical-measurement-coverage.json').write_text(json.dumps({'measurement_count':len(rowlinks),'measurement_to_reader_item':rowlinks,'operation_count':len(operationlinks),'operation_to_reader_item':operationlinks,'operation_parameter_count':len(parameterlinks),'operation_parameter_to_reader_item':parameterlinks,'material_quantity_count':len(materiallinks),'material_quantity_to_reader_item':materiallinks,'stock_quantity_count':len(stocklinks),'stock_quantity_to_reader_item':stocklinks,'draft_sha256':{k:sha(B/'canonical-drafts'/f'{k}.json') for k in drafts}},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
