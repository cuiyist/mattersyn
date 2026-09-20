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
  ee.append({'source_id':SID,'document_role':'main','pdf_page':n,'printed_page':408+n if n else None,'locator':e['locator']})
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
 'ctab-silica-host':dict(zip('mix age template dilute spin-coat calcine'.split(),'sol-mixing sol-aging template-addition ethanol-dilution spin-coating calcination'.split())),
 'cadmium-stock':dict(zip('prepare complex adjust-ph'.split(),'cadmium-stock-preparation cadmium-stock-preparation cadmium-stock-preparation'.split())),
 'ctab-cds-loading':dict(zip('impregnate rinse evacuate sulfide repeat'.split(),'impregnation rinsing evacuation gas-precipitation ctab-cycles'.split())),
 'copolymer-cds-loading':dict(zip('impregnate rinse evacuate sulfide repeat'.split(),'impregnation rinsing evacuation gas-precipitation copolymer-cycles'.split())),
 'uv-visible':{'acquire':'uv-acquisition','convert':'uv-acquisition'},
 'xrd':{'align':'xrd-acquisition','acquire':'xrd-acquisition'},
 'hrtem':{'section':'hrtem-acquisition','image':'hrtem-acquisition','fourier':'image-power'},
 'sims':{'profile':'sims-acquisition'},
 'pl-silicon':{'deposit':'pl-acquisition','first-cycle':'pl-first','measure-first':'pl-acquisition','reimpregnate':'pl-reimpregnation','measure-cd':'pl-acquisition','later-cycle':'pl-later','measure-later':'pl-acquisition'},
 'loading-fraction':{'compare':'loading-analysis','estimate':'volume-fractions'},
}
measurement_targets={
 'cadmium-stock':{'solution-purpose':'complexation'},
 'chemical-intuition':{'ph-window':'ph-window','adsorption-threshold':'ph-window','silica-solubility':'ph-window','uniform-adsorption':'impregnation','cadmium-binding':'surface-retention','rinse-rationale':'rinsing','gas-rationale':'gas-diffusion','site-regeneration':'silanol-regeneration','order-rationale':'connected-porosity','contrast-model':'xrd-contrast','template-tuning':'pore-size-control','mesoscopic-v-atomic':'host-vs-crystal','outlook':'generalization'},
 'ctab-cds-loading':{'first-cycle-diameter':'ctab-size','saturated-diameter':'ctab-size','saturation-cycles':'ctab-cycles','template-scope':'host-order','color-sequence':'color-sequence','narrow-size-inference':'ctab-absorption'},
 'copolymer-cds-loading':{'first-cycle-diameter':'copolymer-size','saturated-diameter':'copolymer-size','saturation-cycles':'copolymer-cycles','template-scope':'copolymer-gap','exciton-loss':'copolymer-absorption','weak-confinement-size':'copolymer-absorption'},
 'ctab-silica-host':{'film-thickness':'host-thickness','host-meso-order':'host-order','open-porosity':'connected-porosity','pore-diameter':'pore-estimate','initial-c':'xrd-before-growth'},
 'hrtem':{'filled-scale-bar':'figure3-panels','empty-scale-bar':'figure3-panels','enlargement-scale-bar':'figure3-panels','contrast':'hrtem-filled-empty','contrast-assumptions':'tem-contrast','filling':'hrtem-empty-pores','atomic-fringes':'cds-fringes','orientation-contrast':'tem-orientation','projection':'tem-orientation','power-definition':'image-power','meso-space-group':'image-power','meso-a':'image-power','meso-c':'image-power','meso-c-a':'image-power','power-labels':'figure3-panels'},
 'literature-context':{'complete-source':'coverage','prior-host':'method-dependencies','copolymer-reference':'copolymer-gap','gap-size-reference':'uv-acquisition','prior-single-cycle':'silanol-regeneration','reference-colloid':'loading-analysis','blende-reference':'cds-fringes','luminescence-references':'pl-passivation','historical-context':'film-motivation','historical-nano-scale':'nanoscale-context','historical-pore-range':'template-rationale','applications':'array-motivation'},
 'loading-fraction':{'reference-size':'loading-analysis','cds-volume':'volume-fractions','pore-volume':'volume-fractions','pores-per-cell':'volume-fractions','pore-filling':'volume-fractions','reference-method':'loading-analysis'},
 'pl-silicon':{'first-surface-emission':'pl-first','next-surface-emission':'pl-reimpregnation','bound-exciton':'pl-reimpregnation','surface-band-mechanism':'pl-passivation','passivation-mechanism':'pl-passivation','later-emission':'pl-later','later-mechanism':'pl-quenching','figure-curve-style':'figure4-axes','figure-stage-label':'pl-figure-conflict','figure-wavelength-range':'figure4-axes','measurement-temperature':'pl-acquisition'},
 'sims':{'cadmium-adsorbed-depth':'depth-uniformity','saturated-depth':'depth-uniformity'},
 'uv-visible':{'ctab-series-spectral-range':'figure1-spectra','ctab-series-absorbance-range':'figure1-spectra','copolymer-series-spectral-range':'figure1-spectra','copolymer-series-absorbance-range':'figure1-spectra','ctab-traces':'figure1-spectra','ctab-size-points':'figure1-sizes','copolymer-traces':'figure1-spectra','copolymer-size-points':'figure1-sizes','host-comparison':'copolymer-absorption'},
 'xrd':{'calcined-meso-c':'xrd-before-growth','cadmium-adsorbed-meso-c':'xrd-before-growth','saturated-meso-c':'xrd-filling','adsorbed-relative-intensity':'xrd-before-growth','initial-shift':'xrd-before-growth','contrast-inversion':'xrd-contrast','peak-width':'xrd-width','growth-shift':'xrd-filling','figure-range':'figure2-axes','calcined-scale':'figure2-axes','first-cycle-scale':'figure2-axes','trace-labels':'figure2-axes'},
}
rowlinks={};operationlinks={};parameterlinks={};materiallinks={};stocklinks={}
for rid,d in drafts.items():
 short=rid.removeprefix(P)
 for n,m in enumerate(d.get('measurements',[])):
  target=measurement_targets[short][m['id']]
  f=append_fact(target,rid,f'/measurements/{n}',m['id'],m['property'].replace('_',' ').capitalize(),m['value'],m['evidence'],m['value'].get('status','reported'),m['sample_id'],m.get('conditions'))
  f['canonical_measurement_id']=m['id'];rowlinks[rid+'::'+m['id']]=target
 for n,op in enumerate(d.get('operations',[])):
  target=operation_targets[short][op['id']];ii=items[target];pointer=f'/operations/{n}'
  ii['canonical_links'].append({'record_id':rid,'json_pointer':pointer,'relation':'Reported operation; host/substrate context, qualifiers, bounds and missing conditions remain canonical.'});operationlinks[rid+'::'+op['id']]=target
  for name,q in op.get('parameters',{}).items():
   f=append_fact(target,rid,pointer+'/parameters/'+name,'operation-'+op['id']+'-'+name,op['label']+' · '+name.replace('_',' '),q,q.get('evidence',op['evidence']),'operation_parameter',extra=op.get('description'))
   f['canonical_operation_id']=op['id'];f['canonical_parameter']=name;parameterlinks[rid+'::'+op['id']+'::'+name]=target
 for n,mat in enumerate(d.get('materials',[])):assert not mat.get('quantities'),mat['id']
 for n,stock in enumerate(d.get('stocks',[])):
  for name,q in stock.get('concentrations',{}).items():
   target='citrate' if 'citrate' in name else 'stock-composition' if 'final' in name else 'cadmium-stock-preparation' if name.lower().endswith('ph') else 'cadmium-nitrate'
   f=append_fact(target,rid,f'/stocks/{n}/concentrations/{name}','stock-'+stock['id']+'-'+name,stock['name']+' · '+name.replace('_',' '),q,q.get('evidence',stock['evidence']),'stock_concentration')
   f['canonical_stock_id']=stock['id'];stocklinks[rid+'::'+stock['id']+'::'+name]=target
  for c,component in enumerate(stock.get('components',[])):
   for name,q in component.get('quantities',{}).items():
    target='sol-mixing'
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
out['record_formulation_scope_note']='Sample labels require their record IDs. Host, substrate, treatment stage, reference colloid and measured/derived character retain distinct scopes.'
out['corpus_paper_id']='paper-14e7acf4b7c52acfa008'
out['corpus_document_id']='doc-e1e158f382d446b070ee'
out['material_evidence_records']={'CdS/SiO2':[rid for rid in drafts if rid!=P+'ctab-silica-host'],'SiO2':[P+k for k in ['ctab-silica-host','xrd','hrtem','loading-fraction']],'CdS':[P+k for k in ['ctab-cds-loading','copolymer-cds-loading','uv-visible','hrtem','pl-silicon','loading-fraction']]}
out['material_evidence_scope_notes']={'CdS/SiO2':'CTAB and unnamed-copolymer pore-filled composites, shared analytical contexts and separate silicon-supported PL stages. Host preparation is linked as an upstream record, not mislabeled as CdS.','SiO2':'Explicit CTAB silica-host recipe, empty-host characterization and pore-geometry/loading comparisons. Other states in these comparison records contain CdS and are not bare-silica properties.','CdS':'CdS crystallites confined in silica and one optical reference colloid. Composite properties and host mesolattice symmetry are not bare-CdS atomic lattice constants; no complete standalone comparator recipe is supplied.'}
out['counts'].update({'typed_characterization_rows':len(rowlinks),'linked_operations':len(operationlinks),'operation_parameter_facts':len(parameterlinks),'reagent_quantity_facts':len(materiallinks),'stock_quantity_facts':len(stocklinks)})
(O/'canonical-measurement-coverage.json').write_text(json.dumps({'measurement_count':len(rowlinks),'measurement_to_reader_item':rowlinks,'operation_count':len(operationlinks),'operation_to_reader_item':operationlinks,'operation_parameter_count':len(parameterlinks),'operation_parameter_to_reader_item':parameterlinks,'material_quantity_count':len(materiallinks),'material_quantity_to_reader_item':materiallinks,'stock_quantity_count':len(stocklinks),'stock_quantity_to_reader_item':stocklinks,'draft_sha256':{k:sha(B/'canonical-drafts'/f'{k}.json') for k in drafts}},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
