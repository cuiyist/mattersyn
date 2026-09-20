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
  ee.append({'source_id':SID,'document_role':role,'pdf_page':n,'printed_page':13204+n if n and role=='main' else None,'locator':e['locator']})
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
growth_ops={'prepare-metal':'zinc-stock','prepare-base':'base-stock','add-base':'alkaline-growth','precipitate':'workup','wash':'workup','redisperse':'workup'}
topo_ops={'remove-excess':'remove-zinc','amine-precipitate':'amine-workup','ethanol-wash':'amine-workup','toluene-resuspend':'amine-workup','ethanol-precipitate':'amine-workup','repeat-cycle':'amine-workup','heat-topo':'topo-heating','cool':'topo-cooling','precipitate':'topo-cooling','wash':'topo-cooling','redisperse':'topo-redispersion'}
operation_targets={**{k:growth_ops for k in ['zno-route','co-route','ni-route']},**{k:topo_ops for k in ['topo-zno','topo-co','topo-ni']},'clarity-restoration':{'add-zinc':'clarity'},'aggregation':{'prepare-ethanol':'aggregation','evaporate':'aggregation'},'pure-kinetics':{'prepare':'pure-kinetics','add-base':'pure-kinetics','measure':'pure-kinetics'},'pure-titration':{'prepare':'pure-titration','titrate':'pure-titration','measure':'pure-titration'},'co-titration':{'prepare':'co-titration','titrate':'co-titration','measure':'co-titration'},'dopant-series':{'prepare':'dopant-series','add-base':'dopant-series','measure':'dopant-series'},'thermal-ripening':{'heat':'thermal-ripening','measure':'thermal-ripening'},'room-aging':{'age':'room-aging'},'surface-cleaning-control':{'treat':'surface-control','measure':'surface-control'},'microscopy':{'precipitate':'microscopy-method','redisperse':'microscopy-method','deposit':'microscopy-method','image':'microscopy-method','diffraction':'microscopy-method','histogram':'microscopy-method'},'diffraction':{'acquire':'xrd-method'},'icp':{'analyze':'icp-method'},'optical-absorption':{'room':'absorption-method','film':'lowtemp-absorption','glass':'lowtemp-absorption','cool':'lowtemp-absorption','acquire':'lowtemp-absorption'},'mcd':{'prepare':'mcd-method','field-scan':'mcd-method','temperature-scan':'mcd-method','normalize':'mcd-definition'},'zeeman':{'acquire':'zeeman-method','extract':'zeeman-method'},'magnetometry':{'mount':'magnetometry-method','measure':'magnetometry-method','subtract':'magnetometry-method'},'luminescence':{'prepare':'luminescence-method','measure':'luminescence-method'}}
measurement_targets={}
def mg(record,target,ids):
 for k in ids.split():measurement_targets.setdefault(record,{})[k]=target
for r in ['zno-route','co-route','ni-route']:mg(r,'colloid-rationale','scale')
for r in ['co-route','ni-route']:mg(r,'dopant-substitution','nominal-vs-incorporated')
for r in ['topo-zno','topo-co','topo-ni']:
 mg(r,'topo-redispersion','concentration stability');mg(r,'cleaning-rationale','cleaning');mg(r,'cleaning-structure','ripening')
mg('aggregation','aggregate-morphology','dopant size-results size-discussion morphology');mg('aggregation','aggregate-phase','phase')
mg('pure-kinetics','pure-formation','metastable evolution')
mg('pure-titration','pure-base-response','initial nucleation strong early-energy early-size later-energy later-size early');mg('pure-titration','pure-intensity','linear');mg('pure-titration','pure-titration','endpoint')
mg('co-titration','co-color','precursor final color');mg('co-titration','co-intermediate','nochange intermediate-onset intermediate intermediate-discussion intermediate-max internal-onset internal');mg('co-titration','co-isosbestic','iso1 iso2 deconvolution');mg('co-titration','nucleation-threshold','intercept')
for r in ['co','ni']:
 mg('dopant-series','dopant-series',' '.join(r+'-nominal-'+str(n) for n in [0,2,4,6,8]));mg('dopant-series','dopant-number',r+'-slope '+r+'-two-percent');mg('dopant-series','dopant-energy',r+'-trend');mg('dopant-series','si-kinetics',r+'-kinetic-feed')
mg('dopant-series','si-kinetic-results','s1');mg('dopant-series','dopant-number','base-control')
mg('thermal-ripening','thermal-ripening',' '.join('time-'+str(n) for n in [2,5,20,40,120]));mg('thermal-ripening','thermal-response','trend')
mg('room-aging','pure-tem','bandgap tem-diameter distribution optical-size')
mg('surface-cleaning-control','surface-control','time-0 time-30 time-120');mg('surface-cleaning-control','si-cleaning-results','decrease')
for prefix,target in [('pure','pure-tem'),('co5','co-tem')]:
 mg('microscopy',target,' '.join(prefix+'-'+s for s in ['mean','width','optical','count']));mg('microscopy','pure-diffraction' if prefix=='pure' else 'co-diffraction',' '.join(prefix+'-'+s for s in ['overview-scale','hrtem-scale','diffraction']))
mg('microscopy','co-tem','co5-dopant co-overview-count');mg('microscopy','ni-tem','ni-scale ni-diffraction');mg('microscopy','aggregate-morphology','aggregate-scale')
mg('diffraction','xrd-method','scherrer phase');mg('diffraction','aggregate-phase','aggregate');mg('icp','icp-method','scope')
mg('optical-absorption','co-spectra','co17-doping co17-diameter co-lf co-oscillator bulk-oscillator co-lines');mg('optical-absorption','ni-spectra','ni15-doping ni15-diameter ni-region-ligand-field ni-region-charge-transfer ni-region-bandgap ni-lines');mg('optical-absorption','ni-fine','ni-origin-a1 ni-origin-e ni-linewidth');mg('optical-absorption','fine-structure','co-fine-agreement');mg('optical-absorption','fano','co-fano');mg('optical-absorption','co-ct-band','co-tail')
for prefix,target in [('co17','table1-co'),('ni15','table1-ni')]:mg('mcd',target,' '.join(prefix+'-'+t+'-'+f for t in ['ligand-field','charge-transfer','band-gap'] for f in ['ratio','energy']))
mg('mcd','co-ct-band','co-ct-observed co-ct-bound');mg('mcd','field-co','co-lf-caption co-lf-prose co-bg co17-T5 co17-T10 co-saturation');mg('mcd','field-ni','ni-caption ni-prose ni15-T5 ni15-T10 ni15-T20 ni15-T40 ni15-T80 ni-flat ni-response');mg('mcd','mcd-relative','co-ratio ni-relative');mg('mcd','mcd-definition','normalization')
mg('zeeman','zeeman-results','average high-field turning plot')
mg('magnetometry','magnetic-loop','coercivity remanence saturation');mg('magnetometry','curie-bound','tc');mg('magnetometry','aggregation-interpretation','hysteresis isolated');mg('magnetometry','magnetic-fractions','ferro-fraction per-co reference-per-co')
mg('luminescence','quenching','dopant quenching pure co')
mg('topo-optical-comparisons','si-lf-comparison','co-topo-fraction s5 ics');mg('topo-optical-comparisons','si-bandgap-comparison','zno-before-diameter zno-after-diameter toluene s6')
mg('nucleation-model','equation3','eq3');mg('nucleation-model','basic-acetate','cluster');mg('nucleation-model','nucleation-threshold','exclusion');mg('nucleation-model','intermediate-model','scheme surface-intermediate');mg('nucleation-model','geometry-barrier','geometry');mg('nucleation-model','solubility-model','strain');mg('nucleation-model','co-isosbestic','linearity');mg('nucleation-model','dopant-homogeneity','scope')
mg('mcd-intensity-model','equation1','eq1 k beta');mg('mcd-intensity-model','equation2','eq2');mg('mcd-intensity-model','co-ground-state','co-spin co-zfs co-ground');mg('mcd-intensity-model','ni-ground-state','ni-first ni-second ni-level-accuracy ni-ground');mg('mcd-intensity-model','sum-rule','sumrules ni-sumrule')
for n in ['4','5','6a','6b','7a','7b']:mg('charge-transfer-model','equation'+n[0],'eq'+n)
for x in ['co','ni']:mg('charge-transfer-model','ct-parameters',x+'-dq '+x+'-racah-b '+x+'-c-over-b '+x+'-delta-spe');mg('charge-transfer-model','electronegativity-parameters',x+'-chi-opt')
mg('charge-transfer-model','electronegativity-parameters','halide-gap chi-difference oxide-range');mg('charge-transfer-model','ct-prediction','calculated-gap ni-onset co-predicted');mg('charge-transfer-model','oxide-electronegativity','bound-oxide molecular-oxide pure-oxide oxidation-ease');mg('charge-transfer-model','confinement-electronegativity','confinement');mg('charge-transfer-model','ni-ct','ni-ct-context');mg('charge-transfer-model','co-ct-assignment','co-assignment');mg('charge-transfer-model','ct-intensity','weak-mlct weak-relative covalency')
mg('exchange-model','equation8','eq8a eq8b alpha-ev alpha-cm');mg('exchange-model','equation9','eq9');mg('exchange-model','valence-model','valence-split');mg('exchange-model','co-exchange','beta-co beta-co-width beta-co-cm beta-co-cm-width geff model-limits');mg('exchange-model','ni-exchange','beta-ni beta-ni-width beta-ni-cm ratio ni-contrast');mg('exchange-model','volume-scaling','scaling scaling-cm');mg('exchange-model','lattice-context','a c');mg('exchange-model','table2-comparators','ref-co-cdte ref-co-cdse ref-co-znte ref-mn-cdte ref-mn-cdse ref-mn-znte ref-mn-zno');mg('exchange-model','equation9','beta')
mg('magnetization-model','equation10','eq10 attempt-time');mg('magnetization-model','domain-estimate','domain-spin domain-co co-per-dot dots-per-domain domains');mg('magnetization-model','interface-hypothesis','interface');mg('magnetization-model','aggregation-interpretation','intrinsic')
mg('source-context','coverage','coverage');mg('source-context','si-identity','si-match');mg('source-context','dmso','prior');mg('source-context','structure-boundary','structures');mg('source-context','outlook','outlook');mg('source-context','missing-fields','unreconciled')
material_targets={'zinc-acetate-dihydrate':'zinc-stock','tetramethylammonium-hydroxide-pentahydrate':'base-stock','dmso':'dmso','ethanol':'ethanol','ethyl-acetate':'antisolvents','heptane':'antisolvents','cobalt-acetate-tetrahydrate':'cobalt-source','nickel-perchlorate-hexahydrate':'nickel-source','zinc-acetate-additive':'clarity-reagent','dodecylamine':'dodecylamine','toluene':'toluene','topo-technical':'topo','topo-component':'topo','quartz':'analysis-materials','helium':'analysis-materials'}
stock_targets={'metal-stock':'zinc-stock','base-stock':'base-stock','metal-series':'dopant-series'}

rowlinks={};operationlinks={};parameterlinks={};materiallinks={};stocklinks={}
for rid,d in drafts.items():
 short=rid.removeprefix(P)
 for n,m in enumerate(d.get('measurements',[])):
  target=measurement_targets[short][m['id']];f=append_fact(target,rid,f'/measurements/{n}',m['id'],m['property'].replace('_',' ').capitalize(),m['value'],m['evidence'],m['value'].get('status','reported'),m['sample_id'],m.get('conditions'));f['canonical_measurement_id']=m['id'];rowlinks[rid+'::'+m['id']]=target
 for n,op in enumerate(d.get('operations',[])):
  target=operation_targets[short][op['id']];pointer=f'/operations/{n}';items[target]['canonical_links'].append({'record_id':rid,'json_pointer':pointer,'relation':'Source-defined operation. Shared frameworks retain their source applicability; this does not establish independent batches, exact retained dopant concentrations or unreported conditions.'});operationlinks[rid+'::'+op['id']]=target
  for name,q in op.get('parameters',{}).items():
   f=append_fact(target,rid,pointer+'/parameters/'+name,'operation-'+op['id']+'-'+name,op['label']+' · '+name.replace('_',' '),q,q.get('evidence',op['evidence']),'operation_parameter',extra=op.get('description'));f['canonical_operation_id']=op['id'];f['canonical_parameter']=name;parameterlinks[rid+'::'+op['id']+'::'+name]=target
 for n,mat in enumerate(d.get('materials',[])):
  for name,q in mat.get('quantities',{}).items():
   target=material_targets[mat['id']];f=append_fact(target,rid,f'/materials/{n}/quantities/{name}','material-'+mat['id']+'-'+name,mat['name']+' · '+name.replace('_',' '),q,q.get('evidence',mat['evidence']),'material_quantity');f['canonical_material_id']=mat['id'];materiallinks[rid+'::'+mat['id']+'::'+name]=target
 for n,stock in enumerate(d.get('stocks',[])):
  for name,q in stock.get('concentrations',{}).items():
   target=({'pure-kinetics':'pure-kinetics','pure-titration':'pure-titration','co-titration':'co-titration','dopant-series':'dopant-series'}.get(short) or stock_targets[stock['id']]);f=append_fact(target,rid,f'/stocks/{n}/concentrations/{name}','stock-'+stock['id']+'-'+name,stock['name']+' · '+name.replace('_',' '),q,q.get('evidence',stock['evidence']),'stock_concentration',extra=('Inherited stock condition: '+stock.get('scope','source-defined shared framework')) if q.get('status')=='inherited' else None);f['canonical_stock_id']=stock['id'];stocklinks[rid+'::'+stock['id']+'::'+name]=target
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
out['record_formulation_scope_note']='Always pair record and sample IDs. Undoped/doped ZnO, initial feed, internal/surface dopants, cleaned optical specimens, aggregates and author models are distinct contexts; common study identity does not establish a single physical batch.'
out['counts'].update({'typed_characterization_rows':len(rowlinks),'linked_operations':len(operationlinks),'operation_parameter_facts':len(parameterlinks),'reagent_quantity_facts':len(materiallinks),'stock_quantity_facts':len(stocklinks)})
(O/'canonical-measurement-coverage.json').write_text(json.dumps({'measurement_count':len(rowlinks),'measurement_to_reader_item':rowlinks,'operation_count':len(operationlinks),'operation_to_reader_item':operationlinks,'operation_parameter_count':len(parameterlinks),'operation_parameter_to_reader_item':parameterlinks,'material_quantity_count':len(materiallinks),'material_quantity_to_reader_item':materiallinks,'stock_quantity_count':len(stocklinks),'stock_quantity_to_reader_item':stocklinks,'draft_sha256':{k:sha(B/'canonical-drafts'/f'{k}.json') for k in drafts}},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
