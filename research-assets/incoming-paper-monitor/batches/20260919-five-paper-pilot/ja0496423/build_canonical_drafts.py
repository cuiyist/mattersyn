"""Private Gu 2004 canonical authoring from the independently audited extraction.

Only this batch directory is written. Site schema/helpers are read-only imports.
No Site builders, downloads, publication, or training exports are invoked.
"""
from pathlib import Path
from copy import deepcopy
from collections import Counter
from datetime import datetime, timezone
import sys, json, hashlib
sys.dont_write_bytecode = True
B = Path(__file__).resolve().parent
S = Path(r'[local path redacted]')
sys.path.insert(0,str(S/'scripts'))
from record_helpers import record, source, fact, qty, material, operation, state, product, measurement
from dataset_lib import validate_record, eligibility

SID='gu2004'; PRE='gu-2004-'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d): Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
inventory=read(B/'source-inventory.json'); facts_file=read(B/'source-facts.json')
audit=read(B/'source-scientific-audit.json')
assert audit['status']=='passed' and not audit['open_findings']
for name,digest in audit['bound_files'].items():
    assert sha(B/name)==digest, f'Audited extraction changed: {name}'
for d in inventory['source_documents'].values():
    assert sha(d['path'])==d['sha256'], 'Source bytes changed'
U={u['id']:u for u in inventory['units']}
F={f['id']:f for f in facts_file['facts']}
assert len(U)==126 and len(F)==95
unit_links={uid:[] for uid in U}; fact_links={fid:[] for fid in F}

def evidence(items):
    return [{'source_id':SID,'locator':f"{'Main' if e['source_role']=='main' else 'SI'} PDF p. {e['pdf_page']}, {e['locator']}"} for e in items]
def E(uid):
    u=U[uid if uid.startswith(SID+'-') else SID+'-'+uid]
    return evidence([u])
def fq(fid):
    f=F[fid if fid.startswith(SID+'-fact-') else SID+'-fact-'+fid]
    assert not isinstance(f['value'],(list,dict)), f['id']
    status={'unreported':'not_reported','author_model_input':'reported'}.get(f['status'],f['status'])
    if isinstance(f['value'],str):
        return fact(f['value'],evidence(f['evidence']),status,note=f['qualifier'])
    basis='Source sample scope: '+f['sample_scope']+'.'
    if f['status']=='author_model_input': basis+=' Reported author-model input, not an independently measured experimental quantity.'
    if f['unit'] is None: basis+=' Unit is not supplied in the extraction/source; empty unit is not a dimensionless assignment.'
    return qty(f['value'],f['unit'] or '',evidence(f['evidence']),status=status,
        minimum=f['minimum'],maximum=f['maximum'],approximate=f['approximate'],
        qualifier=f['qualifier'],basis=basis,raw_text=f['raw_text'] or '',
        minimum_exclusive=f['minimum_exclusive'],maximum_exclusive=f['maximum_exclusive'])
def fl(r,fid,pointer,array_index=None):
    fid=fid if fid.startswith(SID+'-fact-') else SID+'-fact-'+fid
    fact_links[fid].append({'record_id':r['record_id'],'pointer':pointer,'source_array_index':array_index})
def ul(r,uid,pointer):
    uid=uid if uid.startswith(SID+'-') else SID+'-'+uid
    unit_links[uid].append({'record_id':r['record_id'],'pointer':pointer})

SRC=source(SID,inventory['doi'],inventory['title'],
    'Hongwei Gu; Rongkun Zheng; XiXiang Zhang; Bing Xu',2004,
    si='Matched three-page supporting information verified by title/authors/content and unchanged source hashes. All three pages text-read and visually inspected in the independently passed extraction audit.')
SRC['main_status']='Complete two-page main article text-read and visually inspected in the independently passed source extraction audit. These private canonical drafts await a separate canonical scientific audit.'
SRC['reuse_status']='Private bibliographic/factual extraction; original source and figure rights remain separate. No publication or reuse license is inferred.'
MATERIAL_INFO={m['id'].removeprefix(SID+'-'):m for m in inventory['materials']}
FORMULAS={'oleylamine':'C18H37N','oleic-acid':'C18H34O2','diol':None,
    'dioctyl-ether':'C16H34O','topo':None,'triethylamine':'C6H15N','sulfur':'S',
    'iron-pentacarbonyl':'Fe(CO)5','platinum-acac':'C10H14O4Pt','cadmium-chloride':'CdCl2',
    'acetylacetone':'C5H8O2','water':'H2O','ethanol':'C2H6O','hexane':'C6H14',
    'cadmium-acac':'C10H14CdO4','dibromoanthracene':'C14H8Br2','nitrogen':'N2'}
ROLES={'oleylamine':'ligand','oleic-acid':'ligand','diol':'reducing_agent','dioctyl-ether':'solvent',
    'topo':'reaction_additive','triethylamine':'precipitation_reagent','sulfur':'chalcogen_precursor',
    'iron-pentacarbonyl':'metal_precursor','platinum-acac':'metal_precursor','cadmium-chloride':'metal_precursor',
    'acetylacetone':'chelating_reagent','water':'solvent','ethanol':'antisolvent','hexane':'solvent',
    'cadmium-acac':'metal_precursor','dibromoanthracene':'quantum_yield_reference','nitrogen':'storage_gas'}
MISSING=[U[i]['claim'] for i in U if i.startswith('gu2004-gap-')]
CONFLICT=U['gu2004-xrf-table-ratio-gap']['claim']
records={}
def base(suffix,title,kind='observation',formula='FePt/CdS',method='Source-scoped observation and interpretation'):
    r=record(PRE+suffix,'Gu et al. (2004) · '+title,formula,
        'FePt–CdS heterodimers and source-linked precursor/control contexts',method,deepcopy(SRC),
        'Complete two-page main article and matched three-page supporting information',kind)
    r['schema_version']='1.3.0';r['collection']='reviewed_literature'
    if formula=='FePt/CdS':
        r['material'].update(elements=['Fe','Pt','Cd','S'],components=['FePt','CdS'],architecture='heterostructure')
    elif formula=='FePt':
        r['material'].update(elements=['Fe','Pt'],components=['FePt'],architecture='alloy')
    else:
        r['material'].update(elements=['C','H','Cd','O'],components=[formula],architecture='single_material')
    r['lineage'].update(source_group=SID,recipe_family='gu2004-one-pot-fept-cds')
    r['quality'].update(review_status='imported_unreviewed',requested_tasks=[],
        review_scope='Private canonical draft from independently audited complete main+SI extraction; canonical scientific review, reader mapping and publication are pending. No independently reproduced laboratory batch is claimed.',
        missing_fields=deepcopy(MISSING),conflicts=[CONFLICT],
        experimental_outcome='reported_product' if kind=='literature_protocol' else 'not_established')
    if kind!='literature_protocol':
        r['intended_target']['composition']=fact(None,E('identity-title'),note='Context/procedure record; not a separately quantified target-synthesis experiment.')
    records[suffix]=r
    return r
def mat(r,key,stage='synthesis',role=None):
    if any(x['id']==key for x in r['materials']): return
    d=MATERIAL_INFO[key];e=E(d['source_unit_id']);notes=[U[d['source_unit_id']]['claim']]
    if d['identity_notes']:notes.append(d['identity_notes'])
    if key in ['diol','topo']:
        notes.append('Technical-grade reagent is a mixture; no complete molecular formula or molecular coordinates are assigned to the dosed reagent.')
    elif key in ['cadmium-chloride','cadmium-acac']:
        notes.append('Formula denotes the source-named salt/chelate only; hydration and assay basis are unresolved, and the formula is not a measured full reagent composition.')
    else:notes.append('Formula denotes the source-named chemical identity; no connectivity or atomic-coordinate asset has been generated or verified in this canonical subtask.')
    m=material(key,d['name_as_reported'],FORMULAS[key],role or ROLES[key],stage,e,
        quantities={'purity':fq(d['purity_fact_id'])},notes=notes)
    idx=len(r['materials']);r['materials'].append(m)
    fl(r,d['purity_fact_id'],f'/materials/{idx}/quantities/purity');ul(r,d['source_unit_id'],f'/materials/{idx}')
def specimen(r,key,name,formula,euid):
    r['materials'].append(material(key,name,formula,'specimen','characterization',E(euid),
        notes=['Nominal source specimen identity; a shared label does not establish an identical physical batch across measurement techniques.']))
def sample(r,sid,label,formula,euid,state_id=None,parent=None,explicit=False,notes=None):
    p=product(sid,formula,E(euid),link='explicit' if explicit else 'general_context',state=state_id,
        notes=notes or ['Physical batch/aliquot identity relative to other analytical records is not established.'])
    p['source_sample_label']=label;p['parent_sample_id']=parent;r['products'].append(p);return p
def link(r,target,label,relation):
    r['context_links'].append({'label':label,'url':'../records/'+PRE+target+'.html','relation':relation})
def unit_measure(r,uid,sid,status=None):
    u=U[uid if uid.startswith(SID+'-') else SID+'-'+uid]
    if status is None:
        status='author_derived' if u['kind'] in ['author_interpretation','author_model','author_outlook'] else 'reported'
    note='Source scope: '+u['sample_scope']+'. Source kind: '+u['kind']+'.'
    if u['kind']=='reference':note+=' Bibliographic context only; external cited full text not inspected. The source SI reference is separately matched.'
    if u['kind']=='missingness':note+=' This is a report of the inspected source gap, not a missing quantity filled with a value.'
    m=measurement('source-'+u['id'].removeprefix(SID+'-'),sid,'source_'+u['kind'],
        fact(u['claim'],E(u['id']),status,note),
        'Source text / original figure or table context',E(u['id']),conditions=u['sample_scope'])
    index=len(r['measurements']);r['measurements'].append(m);ul(r,u['id'],f'/measurements/{index}/value')
def measure_fact(r,short,sid,tech):
    fid=short if short.startswith(SID+'-fact-') else SID+'-fact-'+short;f=F[fid]
    if isinstance(f['value'],list):
        if f['unit']=='ratio':
            labels=['Fe','Pt','Cd','S'] if short=='reported-fe-pt-cd-s-ratio' else ['FePt','CdS']
            for j,(label,value) in enumerate(zip(labels,f['value'])):
                q=qty(value,'relative atom parts' if len(labels)==4 else 'relative component parts',
                    evidence(f['evidence']),approximate=f['approximate'],
                    qualifier='Main-text reported ratio; uncorrected SI mol% remains separate.',
                    basis=f['sample_scope']+'; ordered components '+':'.join(labels),raw_text=f['raw_text'] or '')
                m=measurement(f['property']+'-'+label.lower(),sid,f['property'].replace('-','_')+'_'+label.lower(),q,tech,evidence(f['evidence']),f['sample_scope'])
                index=len(r['measurements']);r['measurements'].append(m);fl(r,fid,f'/measurements/{index}/value',j)
        else:
            m=measurement(f['property'],sid,f['property'].replace('-','_'),
                fact(', '.join('{'+v+'}' for v in f['value']),evidence(f['evidence']),note='Ordered source index list; raw list preserved in canonical-source-coverage.json.'),tech,evidence(f['evidence']),f['sample_scope'])
            index=len(r['measurements']);r['measurements'].append(m);fl(r,fid,f'/measurements/{index}/value')
    else:
        m=measurement(f['property'],sid,f['property'].replace('-','_'),fq(fid),tech,evidence(f['evidence']),f['sample_scope'])
        index=len(r['measurements']);r['measurements'].append(m);fl(r,fid,f'/measurements/{index}/value')
def add_analysis(r,oid,label,action,inputs,euid,parameters=None):
    e=E(euid);out=oid+'-data';r['material_states'].append(state(out,label+' data',inputs,'analysis_data'))
    r['operations'].append(operation(oid,action,label,e,inputs,[out],parameters=parameters or {},stage='characterization',
        description='Only source-supported acquisition context is retained. Instrument settings and specimen preparation absent from the paper remain unknown.'))
    return len(r['operations'])-1
def op_fact(r,idx,key,short):
    r['operations'][idx]['parameters'][key]=fq(short);fl(r,short,f'/operations/{idx}/parameters/{key}')

up=base('cdacac-preparation','Cadmium acetylacetonate precursor preparation','procedure','C10H14CdO4','Chelation, precipitation and recrystallization')
for key in ['cadmium-chloride','water','acetylacetone','triethylamine','ethanol']:
    mat(up,key,'precursor_preparation',role='recrystallization_solvent' if key=='ethanol' else None)
route=base('heterodimer','One-pot FePt–CdS heterodimer synthesis','literature_protocol',method='Staged colloidal growth and thermally induced dewetting')
for key in ['platinum-acac','diol','dioctyl-ether','oleylamine','oleic-acid','iron-pentacarbonyl','sulfur','topo','cadmium-acac']:
    mat(route,key)
for key in ['ethanol','hexane']:mat(route,key,'workup')
mat(route,'nitrogen','storage')
PARAM_KEYS={
 'cdcl2-mass':'cadmium_chloride_mass','cdcl2-amount':'cadmium_chloride_amount','water-volume':'water_volume',
 'acetylacetone-volume':'acetylacetone_volume','acetylacetone-amount':'acetylacetone_amount','stir-duration':'duration',
 'triethylamine-volume':'triethylamine_volume','isolated-cdacac-mass':'isolated_precursor_mass','dry-temperature':'temperature',
 'ptacac-mass':'platinum_precursor_mass','first-diol-mass':'first_diol_mass','dioctyl-ether-volume':'dioctyl_ether_volume',
 'solution-temperature':'temperature','thermal-duration':'duration','oleylamine-volume':'oleylamine_volume',
 'oleic-acid-volume':'oleic_acid_volume','feco5-volume':'iron_pentacarbonyl_volume','hold-duration':'duration',
 'sulfur-mass':'sulfur_mass','topo-mass':'topo_mass','second-diol-mass':'second_diol_mass','cdacac-mass':'cadmium_precursor_mass',
 'duration':'duration','ethanol-volume':'ethanol_volume','hexane-volume':'hexane_volume'}
UNKNOWN_UNITS={'temperature':'°C','duration':'min','ramp-rate':'°C/min','cooling-rate':'°C/min','cooling-duration':'min',
    'ramp-duration':'min','stir-speed':'rpm','stirring-rate':'rpm','drying-duration':'min','storage-temperature':'°C',
    'storage-duration':'day','vacuum-pressure':'Torr','pressure':'Torr','filtration-pressure':'Torr','aging-duration':'min',
    'centrifuge-duration':'min','isolated-product-mass':'mg','particle-concentration':'mg/mL','addition-duration':'s'}
OP_LABELS={
 'cdacac-dissolve':'Dissolve cadmium chloride in DI water',
 'cdacac-chelate':'Add acetylacetone and stir for 15 minutes',
 'cdacac-precipitate':'Add triethylamine to form a white precipitate',
 'cdacac-filter':'Filter and retain the crude chelate',
 'cdacac-recrystallize':'Recrystallize cadmium acetylacetonate from ethanol and water',
 'cdacac-dry':'Dry the precursor at 80 °C under vacuum',
 'hetero-charge':'Combine platinum precursor and the first diol charge in dioctyl ether',
 'hetero-preheat':'Heat to 100 °C until the solution becomes light brown',
 'hetero-metal-addition':'Add oleylamine, oleic acid and iron pentacarbonyl',
 'hetero-fept-growth':'Grow FePt at the boiling point of dioctyl ether',
 'hetero-cool':'Cool the in-pot FePt dispersion to 100 °C',
 'hetero-sulfur':'Add sulfur and stir to form source stage 2',
 'hetero-cadmium-addition':'Add TOPO, the second diol charge and cadmium acetylacetonate',
 'hetero-shell-hold':'Hold at 100 °C for source stage 3',
 'hetero-crystallize':'Heat to 280 °C for heterodimer formation',
 'hetero-cool-workup':'Cool the crude product to room temperature',
 'hetero-first-precipitation':'Precipitate with ethanol and retain the product pellet',
 'hetero-hexane-redispersion':'Redisperse the first pellet in hexane',
 'hetero-insoluble-removal':'Remove insoluble material and retain the clarified dispersion',
 'hetero-reprecipitation':'Reprecipitate with ethanol and retain the product pellet',
 'hetero-storage':'Redisperse the final product in hexane and store under nitrogen',
}
for r,pid in [(up,'gu2004-cdacac-preparation'),(route,'gu2004-heterodimer')]:
    ops=[o for o in inventory['operations'] if o['protocol_id']==pid]
    for o in ops:
        oid=o['id'].removeprefix('gu2004-');e=E(o['source_unit_id']);out=o['output']
        stage='precursor_preparation' if r is up else 'synthesis'
        if oid in ['hetero-cool-workup','hetero-first-precipitation','hetero-hexane-redispersion','hetero-insoluble-removal','hetero-reprecipitation']:stage='workup'
        if oid=='hetero-storage':stage='storage'
        parents=[x for x in o['inputs'] if x!='nitrogen']
        kind='fraction' if o['retained_fraction'] else 'reaction_batch'
        if oid in ['cdacac-dry','hetero-storage']:kind='product'
        r['material_states'].append(state(out,OP_LABELS[oid]+' output',parents,kind))
        env=fact(None,e,note='No operation-specific atmosphere is stated; SI general reaction atmosphere is not automatically a workup setting.')
        if stage in ['precursor_preparation','synthesis']:
            env=fact('Inert atmosphere; gas identity and pressure unspecified',E('reaction-atmosphere'),note='SI general statement for reactions unless otherwise stated.')
        if oid=='cdacac-dry':env=fact('Vacuum',e,note='Drying pressure is not supplied.')
        if oid=='hetero-storage':env=fact('Nitrogen',e,note='Only final storage explicitly identifies nitrogen.')
        params={}; idx=len(r['operations'])
        for fid in o['quantity_fact_ids']:
            if fid=='gu2004-fact-cdacac-recrystallize-isolated-cdacac-mass':continue
            tail=fid.removeprefix('gu2004-fact-'+oid+'-');key=PARAM_KEYS[tail]
            params[key]=fq(fid);fl(r,fid,f'/operations/{idx}/parameters/{key}')
        for field in o['unreported_fields']:
            if field in UNKNOWN_UNITS:
                key=field.replace('-','_')
                if key not in params:
                    params[key]=qty(unit=UNKNOWN_UNITS[field],evidence=e,qualifier='Unreported: '+field+'.')
        desc=o['description']+' Unreported fields: '+', '.join(o['unreported_fields'])+'.'
        endpoint=fact(None,e)
        if oid=='hetero-preheat':endpoint=fact('Solution becomes light brown',e)
        if oid=='cdacac-precipitate':endpoint=fact('White precipitates appear',e)
        op=operation(oid,o['action'],OP_LABELS[oid],e,o['inputs'],[out],
            depends=[r['operations'][-1]['id']] if r['operations'] else [],parameters=params,stage=stage,
            description=desc,environment=env,endpoint=endpoint,retained_fraction=o['retained_fraction'])
        r['operations'].append(op);ul(r,o['source_unit_id'],f'/operations/{idx}')
    ul(r,'reaction-atmosphere','/operations/0/environment')
sample(up,'cdacac-isolate','Prepared Cd(acac)2; weighing state relative to drying unresolved','C10H14CdO4','cdacac-recrystallize',state_id='recrystallized-cdacac',explicit=True)
sample(up,'cdacac-dried','Vacuum-dried Cd(acac)2 before use','C10H14CdO4','cdacac-dry',state_id='cadmium-acac',parent='cdacac-isolate',explicit=True)
measure_fact(up,'cdacac-recrystallize-isolated-cdacac-mass','cdacac-isolate','Reported upstream isolated mass')
for sid,label,formula,euid,st,par in [
 ('stage-1','1: in-pot FePt before sulfur addition','FePt','hetero-fept-growth','fept-1-in-pot',None),
 ('stage-2','2: proposed sulfur-covered FePt; not an intact isolated shell product','FePt/S','hetero-sulfur','intermediate-2-in-pot','stage-1'),
 ('stage-3','3: proposed metastable FePt@CdS; intact shell not established','FePt/CdS','hetero-shell-hold','intermediate-3-in-pot','stage-2'),
 ('stage-4','4: FePt–CdS heterodimer in stored hexane dispersion','FePt/CdS','hetero-storage','product-4-hexane','stage-3')]:
    p=sample(route,sid,label,formula,euid,st,par,True,
        ['Same-pot source stage identity; detailed sampling/isolation linkage to figures is unreported.',
         'Component notation is not an exact stoichiometric formula or proof of an intact intermediate shell.'])
    if sid in ['stage-2','stage-3']:
        p['morphology']=fact('Proposed shell-like intermediate; isolation damage prevents treating it as a demonstrated intact uniform shell.',E('intermediate-isolation-failure'),'author_derived')
idx=next(i for i,o in enumerate(route['operations']) if o['id']=='hetero-fept-growth');op_fact(route,idx,'temperature','fept-growth-temperature')
idx=next(i for i,o in enumerate(route['operations']) if o['id']=='hetero-cool-workup');op_fact(route,idx,'temperature','workup-temperature')
link(route,'cdacac-preparation','Upstream Cd(acac)2 preparation','Complete chelate preparation is a separate source procedure; the 50 mg main-reaction charge is not its 2.8 g isolated mass.')
link(up,'heterodimer','Use in FePt–CdS synthesis','The chelate is a precursor for the one-pot route; exact precursor-batch identity is not established.')

mic=base('microscopy','Source-stage TEM, HRTEM and diffraction','procedure',method='Electron microscopy and selected-area electron diffraction')
for key,label,formula,euid in [('precursor-1','FePt 1 microscopy specimen','FePt','figure-1a'),
    ('isolated-2','Isolated intermediate 2 microscopy specimen','FePt/S','figure-s4'),
    ('isolated-3','Isolated intermediate 3 microscopy specimen','FePt/CdS','figure-s5'),
    ('product-4','Product 4 microscopy/diffraction context','FePt/CdS','figure-1b')]:specimen(mic,key,label,formula,euid)
for sid,label,formula,euid in [('tem-1','Figure 1A / source FePt 1','FePt','figure-1a'),
    ('tem-2','SI Figure S-4 / isolated 2','FePt/S','figure-s4'),('tem-3','SI Figure S-5 / isolated 3','FePt/CdS','figure-s5'),
    ('tem-4','Figure 1B / final 4 TEM','FePt/CdS','figure-1b'),('hrtem-4','Figure 1C / final 4 HRTEM','FePt/CdS','figure-1c'),
    ('saed-4','Figure 1D / final 4 SAED','FePt/CdS','figure-1d'),
    ('study-size','Study-wide product-size description','FePt/CdS','overview-size')]:sample(mic,sid,label,formula,euid)
add_analysis(mic,'tem','Image source-stage specimens by TEM','transmission_electron_microscopy',
    ['precursor-1','isolated-2','isolated-3','product-4'],'figure-1a',{'accelerating_voltage':qty(unit='kV',evidence=E('gap-measurement-missingness'))})
mic['operations'][-1]['description']+=' Inputs identify a set of separate analytical specimens, not a physically mixed specimen.'
add_analysis(mic,'hrtem','Inspect final-product CdS crystallinity by HRTEM','high_resolution_tem',['product-4'],'final-cds-crystallinity')
add_analysis(mic,'saed','Acquire the final-product diffraction pattern','selected_area_electron_diffraction',['product-4'],'final-saed-phases')
for f,s in [('overall-size-description','study-size'),('overall-size-upper-description','study-size'),('fept-1-average-diameter','tem-1'),
 ('final-fept-component-diameter','tem-4'),('final-cds-component-diameter','tem-4'),('final-cds-phase','saed-4'),('final-fept-phase','saed-4'),
 ('cds-saed-reflections','saed-4'),('fept-saed-reflections','saed-4'),('figure-1a-scale-bar','tem-1'),('figure-1b-scale-bar','tem-4'),
 ('figure-1c-scale-bar','hrtem-4'),('intermediate-2-tem-scale','tem-2'),('intermediate-3-tem-scale','tem-3')]:measure_fact(mic,f,s,'TEM / HRTEM / SAED or source overview, as individually cited')

xrf=base('xrf','Final-product XRF and unresolved quantitative representations','procedure',method='X-ray fluorescence')
specimen(xrf,'product-4','Product 4 XRF specimen','FePt/CdS','figure-s1')
sample(xrf,'main-ratio','Main-text approximate composition relation','FePt/CdS','final-xrf-ratio')
sample(xrf,'si-software','SI Figure S-1 software output; substrate/source contributions unresolved','FePt/CdS','figure-s1')
add_analysis(xrf,'xrf','Measure product 4 by X-ray fluorescence','xray_fluorescence',['product-4'],'figure-s1',
    {'excitation_energy':qty(unit='keV',evidence=E('gap-measurement-missingness'))})
for fid in ['reported-fe-pt-cd-s-ratio','reported-fept-cds-ratio']:measure_fact(xrf,fid,'main-ratio','Author-reported main-text XRF relation')
for f in F.values():
    if f['property'].startswith('xrf-'):measure_fact(xrf,f['id'],'si-software','Original XRF software output')

mag=base('magnetometry','Magnetism of final heterodimer 4','procedure',method='ZFC/FC and field-dependent magnetometry')
specimen(mag,'product-4','Final-product magnetic specimen','FePt/CdS','magnetic-timing')
sample(mag,'zfc-fc-4','Figure 2A / product 4 ZFC–FC','FePt/CdS','magnetic-zfc-fc')
sample(mag,'hysteresis-4','Figure 2B / product 4 at 5 K','FePt/CdS','hysteresis')
i=add_analysis(mag,'zfc-fc','Record ZFC/FC magnetic response of 4','zfc_fc_magnetometry',['product-4'],'magnetic-zfc-fc');op_fact(mag,i,'applied_field','zfc-fc-applied-field')
i=add_analysis(mag,'hysteresis','Record the 5 K field-dependent moment of 4','field_dependent_magnetometry',['product-4'],'hysteresis');op_fact(mag,i,'temperature','hysteresis-temperature')
measure_fact(mag,'blocking-temperature','zfc-fc-4','ZFC/FC magnetometry');measure_fact(mag,'coercivity','hysteresis-4','Field-dependent magnetometry')

opt=base('optical','Optical absorption, photoluminescence and quantum yield of 4','procedure',method='UV–visible absorption and fluorescence')
specimen(opt,'product-4','Product 4 optical specimen','FePt/CdS','photoluminescence-result')
mat(opt,'hexane','characterization');mat(opt,'dibromoanthracene','characterization')
for sid,label,formula,euid in [('absorption-4','Figure 2C / absorption of 4 in hexane','FePt/CdS','optical-fept-band'),
 ('fluorescence-4','Figure 2C / fluorescence of 4 in hexane','FePt/CdS','photoluminescence-result'),
 ('yield-4','Reported quantum yield of 4','FePt/CdS','quantum-yield-standard'),
 ('standard','9,10-Dibromoanthracene fluorescence reference','C14H8Br2','quantum-yield-standard'),
 ('photograph-4','Figure 2D / hand-held UV lamp photograph','FePt/CdS','blue-photograph')]:sample(opt,sid,label,formula,euid)
add_analysis(opt,'absorption','Measure absorption of 4 in hexane','uv_visible_absorption',['product-4','hexane'],'optical-fept-band')
i=add_analysis(opt,'fluorescence','Measure fluorescence of 4 in hexane','photoluminescence',['product-4','hexane'],'photoluminescence-result');op_fact(opt,i,'excitation_wavelength','fluorescence-excitation')
add_analysis(opt,'quantum-yield','Compare 4 fluorescence with the reported reference standard','relative_quantum_yield',['product-4','hexane','dibromoanthracene'],'quantum-yield-standard')
opt['operations'][-1]['description']+=' Product and standard are separate comparison samples; no physical co-addition of standard to product is asserted.'
add_analysis(opt,'uv-photograph','Photograph 4 under a hand-held UV lamp','qualitative_fluorescence_photograph',['product-4','hexane'],'blue-photograph',
    {'lamp_wavelength':qty(unit='nm',evidence=E('blue-photograph'),qualifier='Lamp wavelength is unreported; the separate spectrometer excitation is not inherited.')})
for f,s in [('fept-assigned-absorption','absorption-4'),('cds-assigned-absorption-shoulder','absorption-4'),('emission-maximum','fluorescence-4'),
    ('fluorescence-quantum-yield','yield-4'),('standard-quantum-yield','standard')]:measure_fact(opt,f,s,'UV–visible absorption / fluorescence; individually cited')

control=base('fept-control','As-prepared FePt 1 optical and magnetic comparisons','procedure','FePt','Source-stage optical and magnetic controls')
specimen(control,'fept-1','FePt 1 control specimens','FePt','figure-s2');mat(control,'hexane','characterization')
sample(control,'absorption-1','SI Figure S-2 / FePt 1 in hexane','FePt','figure-s2')
sample(control,'zfc-fc-1','SI Figure S-3 / as-synthesized FePt 1','FePt','figure-s3')
add_analysis(control,'absorption','Measure the as-prepared FePt 1 absorption comparison','uv_visible_absorption',['fept-1','hexane'],'figure-s2',
    {'absorption_peak':qty(unit='nm',evidence=E('figure-s2'),qualifier='No numerical precursor peak is assigned from the unlabelled broad curve.')})
add_analysis(control,'zfc-fc','Record the FePt 1 magnetic comparison','zfc_fc_magnetometry',['fept-1'],'figure-s3',
    {'applied_field':qty(unit='Oe',evidence=E('figure-s3'),qualifier='The 100 Oe final-product condition is not inherited.')})
link(control,'heterodimer','In-pot FePt 1 stage','These controls do not establish a separate complete purified-FePt synthesis or an independent reaction run.')

model=base('magnetic-model','Author estimate of FePt magnetic anisotropy',method='Author relaxation-time model')
sample(model,'model-context','Author-model FePt component in 4','FePt','magnetic-equation',
       notes=['Model context, not a newly prepared specimen or independent fitted raw-data series.'])
for f in ['magnetic-observation-time','magnetic-attempt-time','magnetic-anisotropy','model-fept-diameter']:
    measure_fact(model,f,'model-context','Author relaxation-time model')
mechanism=base('mechanism','Proposed intermediates, dewetting and component-function interpretation',method='Author mechanistic interpretation and outlook')
sample(mechanism,'source-model','Source proposed stage/assembly mechanism',None,'one-pot-mechanism',
       notes=['Proposed mechanism and outlook are not experimental target structures or additional recipe examples.'])
lit=base('literature-context','Source identity, references and study limitations',method='Bibliographic and source-scope context')
sample(lit,'references','Source/reference context',None,'identity-title')

# Explicit assignment of every non-operation/non-material source unit to its source context.
ASSIGN={
 'overview-size':('microscopy','study-size'),'fept-tem-size':('microscopy','tem-1'),
 'fept-saed-claim':('microscopy','tem-1'),'final-tem-dimensions':('microscopy','tem-4'),
 'final-cds-crystallinity':('microscopy','hrtem-4'),'final-saed-phases':('microscopy','saed-4'),
 'figure-1a':('microscopy','tem-1'),'figure-1b':('microscopy','tem-4'),'figure-1c':('microscopy','hrtem-4'),
 'figure-1d':('microscopy','saed-4'),'figure-s4':('microscopy','tem-2'),'figure-s5':('microscopy','tem-3'),
 'intermediate-isolation-failure':('mechanism','source-model'),
 'final-xrf-ratio':('xrf','main-ratio'),'figure-s1':('xrf','si-software'),
 'xrf-table-ratio-gap':('xrf','si-software'),
 'magnetic-timing':('magnetometry','zfc-fc-4'),'magnetic-zfc-fc':('magnetometry','zfc-fc-4'),
 'magnetic-weak-interactions':('magnetometry','zfc-fc-4'),'hysteresis':('magnetometry','hysteresis-4'),
 'figure-2a':('magnetometry','zfc-fc-4'),'figure-2b':('magnetometry','hysteresis-4'),
 'magnetic-equation':('magnetic-model','model-context'),'anisotropy-comparison':('magnetic-model','model-context'),
 'optical-fept-band':('optical','absorption-4'),'optical-cds-shoulder':('optical','absorption-4'),
 'photoluminescence-result':('optical','fluorescence-4'),'quantum-yield-standard':('optical','yield-4'),
 'blue-photograph':('optical','photograph-4'),'figure-2c':('optical','fluorescence-4'),'figure-2d':('optical','photograph-4'),
 'figure-s2':('fept-control','absorption-1'),'figure-s3':('fept-control','zfc-fc-1'),
 'one-pot-mechanism':('mechanism','source-model'),'scheme-stages':('mechanism','source-model'),
 'sulfur-junction':('mechanism','source-model'),'property-conservation-rationale':('mechanism','source-model'),
 'outlook':('mechanism','source-model'),'no-intermediate-isolation':('heterodimer','stage-1'),
 'upstream-cited-fept':('heterodimer','stage-1'),
}
for element in ['si','s','fe','rh','cd','pt']:ASSIGN['xrf-table-'+element]=('xrf','si-software')
for uid,u in U.items():
    if unit_links[uid]:continue
    key=uid.removeprefix(SID+'-')
    if key in ASSIGN:
        rkey,sid=ASSIGN[key];unit_measure(records[rkey],uid,sid)
    elif u['kind'] in ['metadata','source_scope','reference','missingness','literature_context']:
        unit_measure(lit,uid,'references')
    else:raise AssertionError('Unmapped source unit: '+uid)

for r in records.values():
    if r is not route and r is not up:
        link(r,'heterodimer','Source synthesis context','Nominal stage/product context only; no unproven same-batch linkage is implied.')
for target,label in [('microscopy','TEM, HRTEM and diffraction'),('xrf','Both XRF representations'),
    ('magnetometry','Final-product magnetism'),('optical','Optical properties'),('fept-control','FePt 1 controls'),
    ('magnetic-model','Author magnetic model'),('mechanism','Chemical intuition'),('literature-context','References and source gaps')]:
    link(route,target,label,'Related source evidence; analytical specimens and author-model contexts retain their own scope.')

# Integrity validation binds every extracted fact and source unit to real draft fields.
def resolve(obj,pointer):
    node=obj
    for token in pointer.lstrip('/').split('/'):
        node=node[int(token)] if isinstance(node,list) else node[token]
    return node
errors=[];checks=0
by_id={r['record_id']:r for r in records.values()}
for r in records.values():
    errors.extend(validate_record(r))
    assert r['quality']['review_status']=='imported_unreviewed' and r['quality']['requested_tasks']==[]
    assert not r['structure_assets'] and all(not v['eligible'] for v in eligibility(r).values())
    checks+=3
for fid,links in fact_links.items():
    assert links,'Unmapped source fact: '+fid
    f=F[fid]
    for binding in links:
        q=resolve(by_id[binding['record_id']],binding['pointer']);checks+=1
        if binding['source_array_index'] is not None:
            assert q['value']==f['value'][binding['source_array_index']]
        elif isinstance(f['value'],list):
            assert q['value']==', '.join('{'+v+'}' for v in f['value'])
        else:
            assert q==fq(fid), 'Source fact conversion changed: '+fid
for uid,links in unit_links.items():
    assert links,'Unmapped source unit: '+uid
    for binding in links: resolve(by_id[binding['record_id']],binding['pointer']);checks+=1
assert len(records)==10
assert sum(r['record_type']=='literature_protocol' for r in records.values())==1
assert len(up['operations'])==6 and len(route['operations'])==15
assert len(OP_LABELS)==21 and all(o['label']==OP_LABELS[o['id']] for r in [up,route] for o in r['operations'])
assert next(o for o in route['operations'] if o['id']=='hetero-preheat')['parameters']['duration']['approximate'] is True
assert not any(p['batch_id'] for r in records.values() for p in r['products'])
assert [o['retained_fraction'] for o in route['operations'] if o['retained_fraction']]==[
    'first-product-pellet','clarified-hexane-dispersion','final-product-4-pellet','product-4-hexane']
assert not any('Si'==m['formula'] or 'Rh'==m['formula'] for r in records.values() for m in r['materials'])
checks+=8
assert not errors,'\n'.join(errors)
outdir=B/'canonical-drafts';outdir.mkdir(exist_ok=True)
for r in records.values():write(outdir/(r['record_id']+'.json'),r)
counts={'records':len(records),'record_types':dict(Counter(r['record_type'] for r in records.values())),
    'operations':sum(len(r['operations']) for r in records.values()),
    'source_synthesis_preparation_operations':21,
    'measurements':sum(len(r['measurements']) for r in records.values()),
    'material_slots':sum(len(r['materials']) for r in records.values()),
    'products_and_contexts':sum(len(r['products']) for r in records.values()),
    'source_facts':len(F),'source_fact_bindings':sum(len(v) for v in fact_links.values()),
    'source_units':len(U),'source_unit_bindings':sum(len(v) for v in unit_links.values())}
pending=['Independent canonical scientific audit against the passed source package.',
    'Reader item/figure/sample links and original-asset integration have not been authored here.',
    'Molecular identity/structure visuals, source-specific apparatus scenes and material hub links await the site-owning workflow.',
    'Cross-record source-stage relations are contextual links; actual physical batch/aliquot joins are unresolved.',
    'No exact experimental atomic structure or CIF exists in this source package.',
    'Publication and all training task eligibility remain disabled.']
manifest={'schema':'mattersyn-canonical-draft-manifest/1','source_id':SID,'created_at':datetime.now(timezone.utc).isoformat(),
    'status':'private_draft_schema_valid_pending_canonical_scientific_audit','published':False,'training_eligible':False,
    'counts':counts,'source_extraction_audit_sha256':sha(B/'source-scientific-audit.json'),
    'source_inventory_sha256':sha(B/'source-inventory.json'),'source_facts_sha256':sha(B/'source-facts.json'),
    'build_script_sha256':sha(__file__),'dataset_validator_sha256':sha(S/'scripts/dataset_lib.py'),
    'schema_definition_sha256':sha(S/'scripts/schema_definition.py'),'record_helpers_sha256':sha(S/'scripts/record_helpers.py'),
    'records':[{'record_id':r['record_id'],'record_type':r['record_type'],'path':str(outdir/(r['record_id']+'.json')),
        'sha256':sha(outdir/(r['record_id']+'.json')),'operations':[o['id'] for o in r['operations']],
        'samples':[p['sample_id'] for p in r['products']],'measurements':[m['id'] for m in r['measurements']],
        'training_tasks':eligibility(r)} for r in records.values()], 'pending_links_and_gates':pending}
write(B/'canonical-record-manifest.json',manifest)
write(B/'canonical-source-coverage.json',{'schema':'mattersyn-canonical-source-coverage/1','source_id':SID,
    'source_facts_sha256':sha(B/'source-facts.json'),'source_inventory_sha256':sha(B/'source-inventory.json'),
    'status':'author_mapping_not_independent_audit','facts':[{'source_fact_id':fid,'source_fact':F[fid],'canonical_bindings':links} for fid,links in fact_links.items()],
    'source_units':[{'source_unit_id':uid,'canonical_bindings':links} for uid,links in unit_links.items()],
    'status_normalizations':{'unreported':'not_reported','author_model_input':'reported with explicit author-model-input basis; original status retained here'},
    'list_normalizations':'SAED lists use bracketed string labels in schema facts; main XRF ratios become exact ordered scalar components. Original arrays remain preserved in this sidecar.'})
write(B/'canonical-draft-validation.json',{'schema':'mattersyn-private-draft-validation/1','status':'passed',
    'validation_scope':'Existing Site Draft2020-12 schema and semantic validator; source-field coverage/lineage integrity checks. Not an independent canonical scientific audit.',
    'created_at':datetime.now(timezone.utc).isoformat(),'counts':counts,'author_integrity_checks':checks,'schema_errors':errors,
    'record_hashes':{r['record_id']:sha(outdir/(r['record_id']+'.json')) for r in records.values()},
    'canonical_manifest_sha256':sha(B/'canonical-record-manifest.json'),
    'coverage_sha256':sha(B/'canonical-source-coverage.json'),'published':False,'training_eligible':False,
    'pending_links_and_gates':pending})
print(json.dumps(counts,ensure_ascii=False))
