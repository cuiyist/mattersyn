import sys,json,re
from pathlib import Path
from copy import deepcopy
ROOT=Path('[local path redacted]')
sys.path.insert(0,str(ROOT/'scripts'))
from record_helpers import *
from dataset_lib import validate_record
HERE=Path(__file__).parent
OUT=ROOT/'data/records';OUT.mkdir(parents=True,exist_ok=True)
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(r):
    errors=validate_record(r)
    if errors:raise ValueError('\n'.join(errors))
    (OUT/(r['record_id']+'.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

d=load(HERE/'murray-audit.json')
src=source('murray1993','10.1021/ja00072a025','Synthesis and Characterization of Nearly Monodisperse CdE (E = S, Se, Te) Semiconductor Nanocrystallites','C. B. Murray; D. J. Norris; M. G. Bawendi',1993)
def me(loc):
    x=d['source_locators'][loc]
    return ev('murray1993','Main pp. '+', '.join(map(str,x['printed_pages']))+'; '+x['section'])
def mq(key):
    x=d['quantities'][key];v=x.get('value');ra=x.get('range',{});status=x.get('status','')
    if status.startswith('reported'):status='reported'
    elif status.startswith('calculated'):status='calculated'
    elif status=='missing':status='not_reported'
    if status not in ['reported','calculated','inherited','inferred','not_reported','author_derived']:status='reported' if v is not None or ra else 'not_reported'
    if v is None and not ra:status='not_reported'
    deriv=x.get('derivation') or x.get('calculation') or x.get('formula')
    if deriv is not None and not isinstance(deriv,str):deriv=json.dumps(deriv)
    if status=='calculated' and not deriv:deriv=x.get('note','Additive liquid-volume assumption; see original input quantities.')
    return qty(v,x.get('unit') or '',me(x['source_locator_id']),status,ra.get('minimum'),ra.get('maximum'),x.get('approximate',False),x.get('qualifier',''),x.get('basis',''),x.get('raw_text',''),deriv)
ids={
 'murray1993.protocol.cdse.method1':'murray-1993-cdse-method1',
 'murray1993.protocol.cdse.method2':'murray-1993-cdse-method2',
 'murray1993.protocol.cdse.method2.small100c':'murray-1993-cdse-small-species',
 'murray1993.procedure.cdse.isolation':'murray-1993-cdse-isolation',
 'murray1993.procedure.cdse.size_selection':'murray-1993-cdse-size-selection',
 'murray1993.procedure.cdse.pyridine_exchange':'murray-1993-cdse-surface-exchange'}
chemical={x['id']:x for x in d['chemical_entities']};states={x['id']:x for x in d['material_state_templates']};ops={x['id']:x for x in d['operations']}
roles={'chemical.dimethylcadmium':'metal_precursor','chemical.topse':'chalcogen_precursor','chemical.tms2se':'chalcogen_precursor','chemical.argon':'process_gas','chemical.topo':'coordinating_medium','chemical.top':'coordinating_solvent','chemical.selenium':'upstream_starting_material'}
for c in d['canonical_records']:
    rid=ids[c['id']];e=me(c['source_locator_id']);isproc='.procedure.' in c['id'];small='small100c' in c['id'];m2='method2' in c['id']
    r=record(rid,c['label'],'CdSe','II–VI chalcogenide','Post-synthesis procedure' if isproc else 'Hot injection',src,e[0]['locator'],'procedure' if isproc else 'protocol_variant' if m2 else 'literature_protocol')
    r['lineage']['parent_record_id']=ids.get(c.get('variant_of'))
    selected=[ops[k] for k in c['operation_ids']]
    used={v for o in selected for v in o['inputs']+o['outputs']}
    if m2:used|={'chemical.dimethylcadmium','chemical.tms2se','chemical.top','chemical.topo'}
    if rid.endswith('method1'):used.add('chemical.topse')
    for mid in sorted(used&chemical.keys()):
        ch=chemical[mid];role=roles.get(mid,'workup_solvent');stage='precursor_preparation' if mid=='chemical.selenium' else 'workup' if isproc else 'synthesis'
        notes=[f"{k.replace('_',' ').capitalize()}: {ch[k]}" for k in ['supplier','grade','purity_reported','preparation'] if ch.get(k)]
        if m2 and mid!='chemical.tms2se':notes.append('Material context inherited from the referenced Method 1 framework; independent charge unreported.')
        r['materials'].append(material(mid,ch['name'],ch['formula'],role,stage,me(ch['source_locator_id']),notes=notes))
    for o in selected:
        stage='precursor_preparation' if o['id'].startswith('prep.') or o['id']=='m2.prepare_precursor' else 'storage' if o['id']=='m2.store_precursor' else 'workup' if o['id'].startswith('workup.') else 'fractionation' if o['id'].startswith('selection.') else 'surface_exchange' if o['id'].startswith('exchange.') else 'synthesis'
        oe=me(o['source_locator_id']);conditions=o.get('conditions',{});env=conditions.get('environment') or conditions.get('gas');endpoint=conditions.get('endpoint')
        text=o.get('note','')
        extra={k:v for k,v in conditions.items() if v is not None and k not in ['environment','gas','endpoint']}
        if extra:text+=' '+ '; '.join(k.replace('_',' ')+': '+str(v) for k,v in extra.items())
        r['operations'].append(operation(o['id'],o['action'],o['action'].replace('_',' ').capitalize(),oe,o['inputs'],o['outputs'],o.get('depends_on',[]),{k:mq(k) for k in o.get('quantity_ids',[])},stage,optional=stage=='surface_exchange',description=text.strip(),environment=fact(env,oe),endpoint=fact(endpoint,oe),retained_fraction=conditions.get('retain') or conditions.get('retained_fraction')))
    for sid in sorted(used-chemical.keys()):
        name=states.get(sid,{}).get('label',sid.replace('state.','').replace('.',' '));parents=[]
        for o in selected:
            if sid in o['outputs']:parents+=o['inputs']
        # A repeated/updated state is not its own ancestral batch.
        parents=list(dict.fromkeys(p for p in parents if p!=sid))
        r['material_states'].append(state(sid,name,parents,'aliquot' if 'aliquot' in sid or 'portion' in sid else 'waste' if 'gray' in sid else 'product' if 'product' in sid or 'powder' in sid else 'mixture'))
    if rid.endswith('method1'):
        charges={'chemical.dimethylcadmium':['m1.A.me2cd.volume','m1.A.me2cd.amount'],'chemical.topo':['m1.topo.mass'],'chemical.top':['m1.A.top.volume','m1.B.top.volume'],'chemical.topse':['m1.B.topse.amount','m1.B.topse_stock.volume'],'chemical.selenium':['topse.stock.se_mass','selenium.purity']}
        for m in r['materials']:m['quantities']={key:mq(key) for key in charges.get(m['id'],[])}
        def stock(id,name,comp,concentrations,prep):return dict(id=id,name=name,components=[{'material_id':mid,'quantities':{k:mq(k) for k in qids}} for mid,qids in comp],concentrations={k:mq(k) for k in concentrations},preparation_operation_ids=prep,scope='Stock component quantities; do not sum prepared stock and transferred aliquots as separate reaction inputs.',evidence=e)
        r['stocks']=[stock('stock-topse','TOPSe stock',[('chemical.selenium',['topse.stock.se_mass']),('chemical.top',['topse.stock.top_volume'])],['topse.stock.concentration'],['prep.topse.stock']),stock('stock-a','Solution A',[('chemical.dimethylcadmium',charges['chemical.dimethylcadmium']),('chemical.top',['m1.A.top.volume'])],[],['m1.prepare.A']),stock('stock-b','Solution B',[('chemical.topse',['m1.B.topse_stock.volume','m1.B.topse.amount']),('chemical.top',['m1.B.top.volume'])],[],['m1.prepare.B'])]
        r['quality']['conflicts']=['Listed liquid components sum nominally to 51 mL, but the source describes a 50-mL syringe. Measured injection volume remains unknown.']
    elif m2:
        for m in r['materials']:m['quantities']={'amount':qty(unit='mmol',evidence=e)}
    # Product identity is a protocol-level observation, not an invented physical batch.
    p=product(rid+'-product','CdSe',e,'explicit' if small else 'general_context',notes=['Source-defined protocol context; independent batch identity is not supplied.'])
    r['products']=[p]
    if small:
        r['measurements']=[measurement('small-species-size',p['sample_id'],'diameter',mq('m2.small.product.size'),'Reported approximate small-species size; not an atomic-coordinate reconstruction',e)]
        r['quality']['requested_tasks']=['precursor_selection','partial_protocol']
    if isproc:r['quality']['requested_tasks']=['partial_protocol']
    r['quality']['missing_fields']=c.get('critical_missing') or (['Starting batch identity, source-specific timing and a complete numerical sample history remain unreported.'] if isproc else ['Independent precursor amounts, stock composition, growth duration and batch-specific characterization remain unreported.'])
    r['quality']['experimental_outcome']='reported_product'
    r['context_links']=[{'label':'Original interactive evidence guide','url':'../murray-1993-method-'+('2' if m2 else '1')+'.html','relation':'Source context; shared figures do not establish recipe-specific sample links.'},{'label':'Chemical intuition','url':'../index.html#intuition','relation':'Separate literature interpretation, excluded from training inputs.'}]
    for branch in c.get('branch_record_ids',[]):r['context_links'].append({'label':'Shared '+branch.split('.')[-1].replace('_',' ')+' procedure','url':ids[branch]+'.html','relation':'Reusable procedure; not evidence that every sample underwent this branch.'})
    if not small and not isproc:r['structure_assets']=[{'id':'cod-9016056','role':'external_reference','sample_id':None,'url':'../assets/cdse-structures/cdse-wurtzite-cod-9016056-original.cif','description':'1977 experimental bulk wurtzite reference; not measured coordinates of a Murray batch.','eligible_as_measured_label':False},{'id':'illustrative-582-atoms','role':'illustrative','sample_id':None,'url':'../assets/cdse-structures/cdse-3p5-by-3p0-nm-illustrative-cluster.xyz','description':'Geometric model displayed in the paper guide; figure-to-recipe assignment unresolved.','eligible_as_measured_label':False}]
    write(r)

# Peng: paired temperature alternatives remain in one protocol-family record.
p=load(ROOT/'dist/assets/peng2000-recipe.json')
ps=source('peng2000','10.1038/35003535','Shape control of CdSe nanocrystals','X. Peng; L. Manna; W. Yang; J. Wickham; E. Scher; A. Kadavanich; A. P. Alivisatos',2000,'No matching SI verified for this extraction')
for best in [False,True]:
    rid='peng-2000-cdse-'+('high-aspect' if best else 'typical');e=ev('peng2000','Main p. 60; '+('best high-aspect-ratio conditions paragraph' if best else 'typical synthesis paragraph'))
    r=record(rid,'Peng et al. (2000) · '+('High-aspect-ratio variant' if best else 'Typical synthesis family'),'CdSe','II–VI chalcogenide','Hot injection',ps,e[0]['locator'],'protocol_variant' if best else 'literature_protocol')
    if best:r['lineage']['parent_record_id']='peng-2000-cdse-typical'
    ratios=[1,2.6,48] if best else [1,2,38]
    for mid,name,formula,role,ratio in [('selenium','Selenium','Se','chalcogen_precursor',ratios[0]),('dimethylcadmium','Dimethylcadmium','C2H6Cd','metal_precursor',ratios[1]),('tbp','Tributylphosphine','C12H27P','coordinating_solvent',ratios[2]),('topo','Trioctylphosphine oxide','C24H51OP','coordinating_medium',None),('hpa','Hexylphosphonic acid','C6H15O3P','ligand',None)]:
        q={'stock_mass_ratio_component':qty(ratio,'relative mass',e,basis='Se:dimethylcadmium:TBP by weight')} if ratio is not None else {'mass':qty(unit='g',evidence=e)}
        if best and mid=='hpa':q['fraction']=qty(8,'percent',e,status='inferred',basis='HPA in TOPO; weight basis from context, denominator not explicitly defined')
        r['materials'].append(material(mid,name,formula,role,'synthesis',e,q,notes=['Absolute prepared stock masses are not reported.'] if ratio is not None else []))
    r['stocks']=[{'id':'precursor-stock','name':'Se / dimethylcadmium / TBP stock','components':[{'material_id':mid,'quantities':{'mass_ratio_component':qty(v,'relative mass',e,basis='Se:dimethylcadmium:TBP by weight')}} for mid,v in zip(['selenium','dimethylcadmium','tbp'],ratios)],'concentrations':{'molarity':qty(unit='mol/L',evidence=e)},'preparation_operation_ids':['prepare-stock'],'scope':'Mass ratio only; no total prepared amount or numerical concentration.','evidence':e}]
    r['material_states']=[state('hot-medium','Heated coordinating medium',['topo','hpa']),state('reaction','Growth mixture',['precursor-stock','hot-medium'],'reaction_batch'),state('collected','Collected nanocrystals',['reaction'],'product')]
    r['operations']=[operation('prepare-stock','prepare_stock','Precursor-stock preparation',e,['selenium','dimethylcadmium','tbp'],['precursor-stock'],description='Composition reported; dissolution order, duration and preparation temperature unreported.'),operation('heat','heat','Prepare heated coordinating medium',e,['topo','hpa'],['hot-medium'],parameters={'medium_mass':qty(None if best else 4,'g',e,basis='Total TOPO or TOPO/HPA charge'),'before_injection_temperature':qty(360 if best else None,'degC',e)},description='Select one paired thermal alternative for the typical family; HPA amount varies across the study.'),operation('inject','inject','Inject precursor stock',e,['precursor-stock','hot-medium'],['reaction'],['prepare-stock','heat'],{'stock_volume':qty(2,'mL',e),'injection_duration':qty(None if best else 1,'s',e,qualifier='' if best else 'much less than')},description='The typical-family duration is much less than 1 s; it is not independently restated for the high-aspect variant.'),operation('grow','grow','Growth and optical monitoring',e,['reaction'],['reaction'],['inject'],{'duration':qty(unit='min',evidence=e),'growth_temperature':qty(unit='degC',evidence=e)},description='Paired post-injection temperatures are alternatives, not a time trace. UV-visible and photoluminescence aliquot monitoring is described for the typical family.'),operation('reinject','inject','Optional monomer replenishment',e,['precursor-stock','reaction'],['reaction'],['grow'],{'additional_volume_fraction':qty(None if best else 40,'percent',e,qualifier='' if best else 'less than',basis='Relative to previously injected stock volume')},optional=True,branch='optional-reinjection',description='Number, timing and exact reinjection amounts unreported; general context for the high-aspect variant.'),operation('stop','remove_heat','Stop heating',e,['reaction'],['collected'],['grow'],description='Heating-mantle removal is described; purification and isolated yield are not supplied.')]
    if not best:
        r['condition_options']=[{'id':v['id'],'label':f"Injection {v['before_injection_c']} °C / after injection {v['after_injection_c']} °C",'parameters':{'before_injection_temperature':qty(v['before_injection_c'],'degC',e),'after_injection_temperature':qty(v['after_injection_c'],'degC',e)},'evidence':e} for v in p['reported_protocols'][0]['thermal_variants']]
    r['products']=[product(rid+'-product','CdSe',e,'general_context',notes=['Study-wide rod phase and figure-specific dimensions are not linked to this complete recipe.'])]
    r['quality']['missing_fields']=['Growth duration','Prepared stock amount and concentration','Atmosphere and thermal trajectory','Workup and isolated yield','Exact recipe-to-characterization mapping']+(['Independent medium mass and post-injection temperature'] if best else [])
    r['quality']['experimental_outcome']='reported_product';r['context_links']=[{'label':'Original interactive evidence guide','url':'../alivisatos-2000.html','relation':'Study-wide characterization and HPA comparisons remain contextual.'}]
    write(r)

# The 2017 core protocol already has typed extraction; retain its exact scope.
n=load(ROOT/'dist/assets/recipe.json');ns=source('nakonechnyi2017',n['source']['doi'],n['source']['title'],n['source']['authors'],2017,'Verified main (9 pages) and matching SI (7 pages); listed omissions remain')
e=ev('nakonechnyi2017','Main p. 4720; Zinc Blende CdSe Core QDs')
r=record('nakonechnyi-2017-zb-cdse-core','Nakonechnyi et al. (2017) · Zinc-blende CdSe cores','CdSe','II–VI chalcogenide','Hot addition',ns,e[0]['locator'])
roles={'cadmium_oxide':'metal_precursor','myristic_acid':'ligand','ode_reactor':'solvent','selenium_dispersion':'chalcogen_precursor'}
for m in n['materials']:
    q=m.get('amount',{});v=q.get('value');unit=q.get('unit','')
    r['materials'].append(material(m['id'],m['name'],m.get('formula'),roles.get(m['id'],'workup_solvent'),'synthesis' if m['id'] in roles else 'workup',e,{'amount':qty(v,unit,e,basis=q.get('basis',''))},notes=[m.get('role','')]))
    if m.get('components'):
        for c in m['components']:
            q=c['amount'];r['materials'][-1]['quantities'][c['name'].lower().replace(' ','_')]=qty(q.get('value'),q.get('unit',''),e,basis='Component of selenium dispersion')
states_ids={}
material_ids={m['id'] for m in r['materials']}
previous=None
for o in n['steps']:
    ins=([o['input']] if isinstance(o.get('input'),str) else o.get('inputs',[]))+o.get('additional_inputs',[]);outs=[o['output']] if o.get('output') else ins[:1]
    if not ins:ins=[m['id'] for m in r['materials'][:3]]
    for sid in ins+outs:
        if sid not in material_ids:states_ids[sid]=state(sid,sid.replace('_',' '),[], 'product' if 'capped' in sid or 'purified' in sid else 'mixture')
    params={}
    for key in ['temperature','duration','pressure']:
        if key in o and isinstance(o[key],dict):q=o[key];params[key]=qty(q.get('value'),q.get('unit',''),e,approximate=q.get('approximate',False))
    if o.get('centrifugation'):
        for key,q in o['centrifugation'].items():params['centrifugation_'+key]=qty(q.get('value'),q.get('unit',''),e)
    if o.get('repeat_count'):params['cycles']=qty(o['repeat_count'],'count',e)
    env=o.get('atmosphere');env=env.get('value') if isinstance(env,dict) else env
    r['operations'].append(operation(o['id'],o['action'],o['title'],e,ins,outs,[previous] if previous else [],params,'workup' if int(o['id'][1:])>=5 else 'synthesis',description=o['text'],environment=fact(env,e),retained_fraction=o.get('retained_fraction')));previous=o['id']
r['material_states']=list(states_ids.values())
p=product('nakonechnyi-core-product','CdSe',e,'explicit',phase='zinc blende',surface='Oleate-capped after ligand replacement',notes=['Product linked to the selected protocol paragraph; exact measurement/purification stage not stated. Approximate size is author-derived from absorption.'])
r['products']=[p];r['measurements']=[measurement('core-absorption',p['sample_id'],'first_exciton_absorption',qty(537,'nm',e),'Absorption spectroscopy',e),measurement('core-diameter',p['sample_id'],'diameter',qty(3,'nm',e,status='author_derived',approximate=True),'Author sizing relation applied to first-exciton absorption',e,derives=['core-absorption'])]
r['quality']['experimental_outcome']='reported_product';r['quality']['missing_fields']=n['critical_missing_fields'];r['quality']['conflicts']=n['anti_mixing_notes'];r['context_links']=[{'label':'Original interactive evidence guide','url':'../nakonechnyi-2017.html','relation':'Same core-only source scope; subsequent shell growth excluded.'}]
write(r)
print('Wrote',len(list(OUT.glob('*.json'))),'validated source records')
