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
  ee.append({'source_id':SID,'document_role':'main','pdf_page':n,'printed_page':7452+n if n else None,'locator':e['locator']})
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
 'glass-host':{'mix':'batch-preparation','melt':'fusion','quench':'quench','stress-relief':'stress-anneal'},
 'optical-preparation':{'cut':'optical-preparation','polish':'optical-preparation'},
 'optical-absorption':{'acquire':'optical-instrument'},
 'photoluminescence':{'excite':'optical-instrument','acquire':'optical-instrument'},
 'afm-analysis':{'scan':'afm-acquisition','analyze':'afm-panels'},
 'parabolic-model':{'solve':'parabolic-model','compare':'model-comparison'},
 'four-band-model':{'solve':'four-band-model','compare':'model-comparison'},
 'power-response':{'sweep':'power-acquisition','integrate':'power-acquisition','fit':'power-law'},
}
for r in ROUTES:operation_targets[r]={**operation_targets['glass-host'],'anneal':r+'-growth'}
measurement_targets={
 'glass-host':{'component-functions':'glass-composition','purity':'glass-composition'},
 'optical-preparation':{'preparation-scope':'optical-preparation'},
 'optical-absorption':{'prose-spectral-range':'figure1-axes','figure1-scope':'figure1-axes','feature-s':'absorption-assignments','anneal-redshift':'absorption-trend','surface-trend':'absorption-trend','state-merging':'surface-broadening','absorption-controls':'absorption-trend','bulk-comparator':'figure2-axes','figure1-ticks':'figure1-axes','figure2-offsets':'figure2-axes'},
 'photoluminescence':{'source-aspl-range':'pl-range','aspl-presence':'pl-range','aspl-evolution':'pl-trend','figure5-scope':'figure5-window','figure7-dual-axis':'figure7-axes','figure7-axis':'figure7-axes','near-line-mechanism':'near-excitation-line','emission-scope':'passivation-losses'},
 'afm-analysis':{'afm1-scope':'afm-panels','afm2-scope':'afm-panels','afm1-hist-range':'afm-panels','afm2-hist-range':'afm-panels','histogram-axis':'afm-panels','afm-observation':'afm2-size','cross-cohort-comparison':'afm-versus-optical'},
 'parabolic-model':{'radius-axis':'figure3-legend','curve-labels':'figure3-legend','method-limits':'parabolic-model'},
 'four-band-model':{'radius-axis':'figure3-legend','eigenvalue-labels':'figure3-legend','space-i':'figure3-legend','space-ii':'figure3-legend','curve-parities':'figure3-legend','strong-regime':'confinement-regimes','weak-size':'confinement-regimes','level-spacing':'confinement-regimes','comparison-size':'optical-size-sg1','comparison-energy':'optical-size-sg1','rounded-experimental-energy':'optical-size-sg1','size-agreement':'model-comparison'},
 'power-response':{'exponent':'power-law','power-law':'power-law','power-axis':'figure6-context','sublinear-inference':'auger-argument'},
 'mechanisms':{'growth':'anneal-rationale','three-mechanisms':'candidate-mechanisms','phonon-model':'phonon-argument','auger-model':'auger-argument','two-step-first':'two-photon-model','two-step-second':'two-photon-model','localization':'momentum-argument','photon-source':'momentum-argument','saturation':'sublinear-rationale','model-support':'sublinear-rationale','surface-loss':'passivation-losses','raman':'raman-boundary','mechanistic-certainty':'scope-conclusion'},
 'literature-context':{'source-scope':'coverage','six-samples':'sample-boundary','model-references':'four-band-model','size-reference':'model-comparison','prior-aspl':'aspl-context','bohr-radius':'pbs-context','bulk-gap':'pbs-context','small-dot-gap':'pbs-context','telecom-wavelength':'pbs-context','telecom-energy':'pbs-context','lasers-context':'laser-context','missing-reproduction':'missing-recipe'},
}
for r in ROUTES:
 mt={'growth-duration':r+'-growth','sample-cohort':r+'-growth'}
 if r in SG:
  mt.update({'series-color':'color','optical-size':'optical-size-'+r,'absorption-s':'absorption-'+r,'absorption-1':'absorption-'+r,'absorption-2':'absorption-'+r,'absorption-3':'absorption-'+r})
  if r=='sg1':mt.update({'main-aspl':'near-excitation-line','near-excitation-line':'near-excitation-line','power-exponent':'power-law'})
 else:mt.update({k:r+'-size' for k in ['afm-size','afm-grain-height','afm-substrate-depth','distribution']})
 measurement_targets[r]=mt
material_targets={'silica':'silica','sodium-carbonate':'carbonate','zinc-oxide':'zinc-oxide','alumina':'alumina','lead-dioxide':'lead-oxide','boron-oxide':'boron-oxide','sulfur-source':'sulfur-source','aluminum-crucible':'crucible','glass-host':'glass-composition'}
rowlinks={};operationlinks={};parameterlinks={};materiallinks={};stocklinks={}
for rid,d in drafts.items():
 short=rid.removeprefix(P)
 for n,m in enumerate(d.get('measurements',[])):
  target=measurement_targets[short][m['id']];f=append_fact(target,rid,f'/measurements/{n}',m['id'],m['property'].replace('_',' ').capitalize(),m['value'],m['evidence'],m['value'].get('status','reported'),m['sample_id'],m.get('conditions'));f['canonical_measurement_id']=m['id'];rowlinks[rid+'::'+m['id']]=target
 for n,op in enumerate(d.get('operations',[])):
  target=operation_targets[short][op['id']];pointer=f'/operations/{n}';items[target]['canonical_links'].append({'record_id':rid,'json_pointer':pointer,'relation':'Source-defined operation. Repeated common glass steps are inherited context, not evidence of separate physical fusion batches.'});operationlinks[rid+'::'+op['id']]=target
  for name,q in op.get('parameters',{}).items():
   f=append_fact(target,rid,pointer+'/parameters/'+name,'operation-'+op['id']+'-'+name,op['label']+' · '+name.replace('_',' '),q,q.get('evidence',op['evidence']),'operation_parameter',extra=op.get('description'));f['canonical_operation_id']=op['id'];f['canonical_parameter']=name;parameterlinks[rid+'::'+op['id']+'::'+name]=target
 for n,mat in enumerate(d.get('materials',[])):
  for name,q in mat.get('quantities',{}).items():
   target=material_targets[mat['id']];f=append_fact(target,rid,f'/materials/{n}/quantities/{name}','material-'+mat['id']+'-'+name,mat['name']+' · '+name.replace('_',' '),q,q.get('evidence',mat['evidence']),'material_quantity');f['canonical_material_id']=mat['id'];materiallinks[rid+'::'+mat['id']+'::'+name]=target
 for n,stock in enumerate(d.get('stocks',[])):
  for name,q in stock.get('concentrations',{}).items():
   target='sulfur-source';f=append_fact(target,rid,f'/stocks/{n}/concentrations/{name}','stock-'+stock['id']+'-'+name,stock['name']+' · '+name.replace('_',' '),q,q.get('evidence',stock['evidence']),'stock_concentration');f['canonical_stock_id']=stock['id'];stocklinks[rid+'::'+stock['id']+'::'+name]=target
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
out['record_formulation_scope_note']='Labels require record IDs. SG1–SG4 optical specimens, AFM1/AFM2 microscopy specimens, glass framework and model contexts remain distinct. Shared steps are inherited, with no asserted independent melt count.'
out['corpus_paper_id']='paper-93084fec2106e8ad8cef'
out['corpus_document_id']='doc-a0f1bded4adaf7016c04'
out['material_evidence_records']={'PbS/glass':list(drafts),'PbS':[rid for rid in drafts if rid!=P+'glass-host']}
out['material_evidence_scope_notes']={'PbS/glass':'Whole composite: glass-embedded PbS. The glass-host procedure is upstream context, not a claim that unannealed glass already has the final measured nanocrystals. SG and AFM cohorts, optical size inference and electronic models remain separate.','PbS':'Component evidence from PbS embedded in multicomponent glass, not a freestanding PbS synthesis or bare-crystal property. Source models, literature context and shared analytical methods retain their own scope; no glass-composite measurement is silently reclassified as isolated-particle behavior.'}
out['counts'].update({'typed_characterization_rows':len(rowlinks),'linked_operations':len(operationlinks),'operation_parameter_facts':len(parameterlinks),'reagent_quantity_facts':len(materiallinks),'stock_quantity_facts':len(stocklinks)})
(O/'canonical-measurement-coverage.json').write_text(json.dumps({'measurement_count':len(rowlinks),'measurement_to_reader_item':rowlinks,'operation_count':len(operationlinks),'operation_to_reader_item':operationlinks,'operation_parameter_count':len(parameterlinks),'operation_parameter_to_reader_item':parameterlinks,'material_quantity_count':len(materiallinks),'material_quantity_to_reader_item':materiallinks,'stock_quantity_count':len(stocklinks),'stock_quantity_to_reader_item':stocklinks,'draft_sha256':{k:sha(B/'canonical-drafts'/f'{k}.json') for k in drafts}},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
