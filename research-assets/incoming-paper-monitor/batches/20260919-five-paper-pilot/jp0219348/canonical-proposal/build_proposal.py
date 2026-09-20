"""Private Heo 2003 proposal. Writes only beside this script; no source promotion.

The source inventories remain authoritative inputs, not mutable working files.
All source/refinement contexts and table payloads are retained in bound sidecars.
"""
from pathlib import Path
import sys, json, hashlib, re, copy, datetime, shutil
sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
H = OUT.parent
S = H.parents[4] / 'recipe-atlas'
sys.path.insert(0, str(S/'scripts'))
from record_helpers import record, source, fact, qty, material, operation, product, state, measurement
from dataset_lib import validate_record, eligibility, fmt

V = OUT/'v1'
RDIR=V/'canonical-drafts'; PDIR=V/'public-review-proposal'; DDIR=V/'source-payloads'
for p in [RDIR,PDIR,DDIR]: p.mkdir(parents=True,exist_ok=True)
def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x): Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def pointer(x,p):
    for k in p.strip('/').split('/') if p else []:
        k=k.replace('~1','/').replace('~0','~');x=x[int(k)] if isinstance(x,list) else x[k]
    return x
def esc(s):return str(s).replace('~','~0').replace('/','~1')
def slug(s):return re.sub(r'[^a-z0-9]+','-',str(s).lower()).strip('-')
def human(s):
    s=str(s or '').replace('ref34','reference 34').replace('ref28','reference 28').replace('Table1','Table 1').replace('Table2','Table 2').replace('Table5','Table 5')
    s=re.sub(r'\b(for|at|by|with|is|about|approximately|reference|Table|Figure)(?=\d)', r'\1 ',s)
    s=re.sub(r'(?<=\d)(?=(?:K|h|days|day|mm|mL|s|angstrom)\b)',' ',s)
    s=re.sub(r'([,;])(?=\S)',r'\1 ',s)
    return s
I=load(H/'source-inventory.json'); F=load(H/'source-facts.json'); T=load(H/'main-tables.json'); PLAN=load(H/'canonical-mapping-plan.json')
FCTS=F['facts']; FD={x['id'].removeprefix('heo2003-'):x for x in FCTS}
inputs=['source-inventory.json','source-facts.json','main-tables.json','main-table-assets.json','root-asset-manifest.json','page-coverage.json','source-scientific-audit.json','canonical-mapping-plan.json','canonical-mapping-plan.md','si-complete-candidate/independent-audit.json','si-complete-candidate/package-freeze.json','si-complete-candidate/all-reflections.json','si-complete-candidate/all-reflections.tsv']
input_hashes={n:sha(H/n) for n in inputs}
for n in inputs:
    dp=DDIR/n;dp.parent.mkdir(parents=True,exist_ok=True)
    if n.endswith('.json'):save(dp,load(H/n))
    elif n.endswith('.tsv'):dp.write_bytes((H/n).read_bytes())
AGG=load(H/'si-complete-candidate/independent-audit.json')
assert AGG['status']=='passed_aggregate_reconciliation_with_two_preserved_source_sign_uncertainties'
assert AGG['package_freeze_sha256']==sha(H/'si-complete-candidate/package-freeze.json')
for doc in I['source_documents'].values():
    assert sha(doc['path'])==doc['sha256'], 'Source bytes changed: '+doc['path']
source_hashes={x['path']:sha(x['path']) for x in I['source_documents'].values()}
SID='heo2003'; PREFIX='heo-2003-'; FORMULA='In66Si100Al92O384'
SCOPE_LIMIT='Source-defined analytical or refinement context. These identifiers are curator labels, not independent physical batches. Cited controls, model iterations and partially occupied sites do not create additional synthesis routes.'
def evidence(rows):
    out=[]
    for e in rows:
        p=e.get('pdf_page');role='SI' if e.get('source_role')=='si' or str(e.get('source_id','')).endswith('-si') else 'Main'
        loc=(f'{role} PDF p. {p}'+(f" (printed p. {e['printed_page']})" if e.get('printed_page') else '')+', ' if p else '')+e.get('locator','Source inventory')
        v={'source_id':SID,'locator':loc}
        if v not in out:out.append(v)
    return out or [{'source_id':SID,'locator':'Supplied main paper and matched supporting reflection table'}]
def fe(k):return evidence(FD[k]['evidence'])
def se(p,loc):return evidence([{'pdf_page':p,'printed_page':1119+p,'locator':loc}])
GENERAL=se(2,'Experimental; Table 1 on main PDF p. 4')
def status(s,value=True):
    if not value:return 'not_reported'
    if s in ['not_reported','not_applicable','inherited','inferred','calculated','author_derived']:return s
    if s=='author_model' or any(w in s for w in ['hypothesis','interpretation','outlook','proposed']):return 'inferred'
    return 'reported'
def fq(k):
    f=FD[k];v=f['value'];assert isinstance(v,(int,float)) and not isinstance(v,bool),k
    return qty(v,f['unit'] or '',fe(k),status(f['status']),approximate=f['approximate'],qualifier=human(f['qualifier']),basis='Source scope: '+f['sample_scope']+'. Source status: '+f['status']+'.',raw_text=str(v))
SRC=source(SID,I['doi'],I['title'],'; '.join(I['authors']),I['year'],si='Matched 14-page scanned reflection list. Separate page-chunk and aggregate audits are retained as external evidence; this authoring pass does not independently certify them.')
GAPS=[
'The prose and Table 1 disagree on dehydration temperatures/durations and indium-contact duration. Neither version is selected as a resolved recipe.',
'Absolute host and indium amounts, capillary dimensions, feed-flow rate, indium/crystal temperature difference, redox vacuum, gas amount/flow, final vacuum and cooling rate are unreported.',
'Nominal Si100Al92 differs from the averaged Table 2 model containing 96 Si and 96 Al; fixed and varied occupancies are refinement parameters.',
'Average disorder, fractional site populations and charge-compensation hypotheses do not specify a unique atomistic specimen or a DFT-ready structure.',
'CIF qualification is a separate pending gate. The SI aggregate passed its own audit with two unresolved signs; this canonical proposal does not convert reflection intensities into an exact structure or training label.',
'The approximately 4300 Å XPS depth statement cannot be reconstructed from the displayed approximately 10 s sputter cycles and reported rate.',
'The input Na-X synthesis and cited control preparations are external references, not complete procedures supplied here.'
]
RECORDS={}
for c in PLAN['candidate_scopes']:
    key=c['plan_scope_id'];r=record(PREFIX+key,'Heo et al. (2003) · '+c['title'],FORMULA,'Indium nanoclusters in zeolite X','Dynamic ion exchange, solvent-free redox and H2S treatment' if key=='in66-route' else c['title'],SRC,'Main paper; source scope: '+c['boundary'],kind=c['candidate_record_type'])
    r['schema_version']='1.3.0';r['material'].update(elements=['In','Si','Al','O'],components=['In','aluminosilicate zeolite X'],architecture='composite')
    r['lineage']['recipe_family']='heo2003-in66-zeolite-x';r['quality'].update(review_status='imported_unreviewed',review_scope='Private canonical proposal derived from the separately audited main-source extraction; independent canonical and reader audits pending. '+c['boundary'],missing_fields=GAPS.copy(),conflicts=[human(z['description']) for z in I['evidence_conflicts']],requested_tasks=[],experimental_outcome='reported_product' if key=='in66-route' else 'not_established')
    r['intended_target']['host']=fact('Zeolite X (faujasite-type aluminosilicate)',GENERAL,note='Nominal composition and average Si/Al refinement are distinct.')
    if key=='in66-route':
        r['intended_target']['phase']=fact(evidence=GENERAL,note='No unique ordered atomic target was specified before synthesis. The final average Fd-3m refinement is an outcome, not a recipe input.')
        r['intended_target']['morphology']=fact('Host single-crystal octahedra',fe('host-shape'),note='Host morphology; not the geometry of an isolated colloidal indium particle.')
    RECORDS[key]=r

def add_sample(key,sid,name,formula=None,phase=None,link='general_context',e=None,parent=None,stateid=None,notes=None):
    r=RECORDS[key]
    if any(p['sample_id']==sid for p in r['products']):return sid
    p=product(sid,formula,e or GENERAL,link=link,state=stateid,phase=phase,notes=[name,SCOPE_LIMIT]+(notes or []));p['source_sample_label']=name;p['parent_sample_id']=parent;r['products'].append(p)
    return sid
def addm(key,mid,sample,prop,v,e,tech='Source-reported context',scope=''):
    r=RECORDS[key];n=len(r['measurements']);r['measurements'].append(measurement(mid,sample,prop,v,tech,e,conditions=scope));return {'record_id':r['record_id'],'json_pointer':f'/measurements/{n}/value','sample_id':sample,'relation':'Exact canonical field; source status and sample scope preserved.'}
def link(key,p,relation='Exact canonical field; source scope preserved.'):
    return {'record_id':RECORDS[key]['record_id'],'json_pointer':p,'relation':relation}

# One coherent route. Apparatus is an input role, never an incorporated-state ancestor.
r=RECORDS['in66-route']
mat_specs=[
('na-x','Sodium zeolite X','Na92Si100Al92O384','host_precursor','parent-host','Host preparation is cited as reference 28, not supplied. Absolute charge and crystal count are unknown.'),
('tl-acetate','Thallous acetate','TlC2H3O2','metal_precursor','exchange-reagent','Aldrich, 99.99%. Formula is normalized from the named salt; stock preparation details are not supplied.'),
('feed-water','Water in aqueous thallous acetate feed','H2O','solvent','exchange-stock','Aqueous feed; water grade is not specified. Do not inherit the DI-wash grade.'),
('wash-water','Deionized wash water','H2O','workup_solvent','wash','DI water is explicitly specified for washing the black crystal.'),
('in-metal','Indium metal','In','metal_precursor','indium-metal','Aldrich, 99.999%; the metal charge and contact area are not specified.'),
('h2s','Hydrogen sulfide','H2S','treatment_reagent','h2s-reagent','Aldrich, 99.999%, zeolitically dried. Dryer procedure, delivered amount and flow mode are not specified; a sulfide product is not established.'),
('pyrex','Fine Pyrex capillary',None,'apparatus','capillary','Apparatus only; not included in product-state ancestry.')]
for mid,name,formula,role,fid,note in mat_specs:
    q={}
    if mid in ['na-x','in-metal','tl-acetate']:q['absolute_mass']=qty(unit='g',evidence=fe(fid),qualifier='Absolute charge is not reported.')
    if mid in ['tl-acetate','in-metal','h2s']:q['supplier_purity']=qty({'tl-acetate':99.99,'in-metal':99.999,'h2s':99.999}[mid],'%',fe(fid),qualifier='Supplier specification; assay basis is not stated.')
    r['materials'].append(material(mid,name,formula,role,'workup' if mid=='wash-water' else 'synthesis',fe(fid),quantities=q,notes=[note]))
r['stocks']=[{'id':'tl-acetate-feed','name':'Aqueous thallous acetate feed','components':[{'material_id':'tl-acetate','quantities':{}},{'material_id':'feed-water','quantities':{}}],'concentrations':{'thallous_acetate':fq('exchange-stock'),'pH':fq('exchange-ph')},'preparation_operation_ids':[],'scope':'Reported feed specification only; no separate stock preparation, water grade, absolute salt mass or unambiguous flow-volume basis is supplied.','evidence':fe('exchange-stock')+fe('exchange-ph')}]
OP_TEXT={
'host':('Mount sodium-zeolite-X crystals','Lodge the colorless sodium-zeolite-X octahedra, approximately 0.15 mm in cross-section, in a fine Pyrex capillary. The host preparation is cited as reference 28. The number of crystals and capillary bore are not specified.'),
'exchange':('Exchange Na-X with thallium(I)','Pass 0.1 mol/L aqueous thallous acetate at pH 6.4 through the capillary. Table 1 gives 4 days, 10.0 mL and 298 K. The source does not resolve the flow rate or whether the volume denotes total throughput.'),
'dehydrate':('Dehydrate Tl-X under vacuum','Dehydrate Tl-X under the prose-reported vacuum of 10⁻⁶ Torr. The prose specifies 623 K for 48 h; Table 1 specifies 673 K for 3 days. The discrepancy is unresolved and does not define two verified protocols.'),
'redox':('Contact dehydrated Tl-X with indium','Contact the dehydrated host with indium metal under vacuum in coaxial cylindrical ovens. The reported temperature is 623 K, with the crystal somewhat cooler than the indium. The prose gives 96 h and Table 1 gives 5 days. The numerical reactor pressure, temperature difference and indium charge are unknown.'),
'wash':('Wash the selected black crystal','Expose one black crystal to the atmosphere and wash it with deionized water. Table 1 gives 1 day and 10.0 mL. Retain the crystal; the amount and identity of the removed residue are not quantitatively established.'),
'redehydrate':('Redehydrate the washed crystal','Relodge the washed crystal in a Pyrex capillary and dehydrate it under the prose-reported vacuum of 10⁻⁶ Torr. The prose again gives 623 K for 48 h, whereas Table 1 gives 673 K for 3 days. Neither temperature-duration pair is selected as a resolved condition.'),
'h2s':('Treat the crystal with hydrogen sulfide','Expose the redehydrated crystal to zeolitically dried hydrogen sulfide at 0.5 atm and 673 K for 12 h. The source does not specify the gas charge, delivery mode or dryer preparation. This treatment does not by itself establish a sulfide phase in the crystal.'),
'evacuate':('Evacuate after H2S treatment','Evacuate the treated crystal at 673 K for 10 min, as summarized in Table 1. The final vacuum pressure is not stated.'),
'seal':('Seal the treated crystal','Seal the crystal from the vacuum line at room temperature for single-crystal diffraction. A numerical cooling rate, exact sealing temperature and long-term storage procedure are not supplied.')}
op_parameters={
'host':{'host_cross_section':fq('host-size'),'crystal_count':qty(unit='count',evidence=fe('host-size'),qualifier='Number of host crystals is not specified.')},
'exchange':{'temperature':fq('exchange-temperature'),'duration':fq('exchange-duration'),'feed_volume':fq('exchange-volume'),'pH':fq('exchange-ph'),'flow_rate':qty(unit='mL/min',evidence=fe('exchange-method'),qualifier='The flow rate is not reported; do not divide the tabulated volume by duration as a measured flow rate.')},
'dehydrate':{'temperature':qty(unit='K',evidence=fe('initial-dehydration-prose-t')+fe('initial-dehydration-table-t'),qualifier='Unresolved conflict: prose 623 K versus Table 1 673 K. See source-conflict condition options.'),'duration':qty(unit='h',evidence=fe('initial-dehydration-prose-time')+fe('initial-dehydration-table-time'),qualifier='Unresolved conflict: prose 48 h versus Table 1 3 days.'),'pressure':fq('dehydration-vacuum')},
'redox':{'temperature':fq('redox-t'),'duration':qty(unit='h',evidence=fe('redox-prose-time')+fe('redox-table-time'),qualifier='Unresolved conflict: prose 96 h versus Table 1 5 days.'),'pressure':qty(unit='Torr',evidence=fe('redox-pressure'),qualifier='Reactor vacuum is not quantified. Cited equilibrium vapor pressures of the metals are not reactor pressure.'),'crystal_metal_temperature_difference':qty(unit='K',evidence=fe('redox-ovens'),qualifier='Crystal is described as somewhat cooler than the metal; the difference is not quantified.')},
'wash':{'duration':fq('wash-time'),'wash_volume':fq('wash-volume'),'temperature':qty(unit='K',evidence=fe('wash'),qualifier='Wash temperature is not reported.')},
'redehydrate':{'temperature':qty(unit='K',evidence=fe('redehydrate-prose-t')+fe('redehydrate-table-t'),qualifier='Unresolved conflict: prose 623 K versus Table 1 673 K.'),'duration':qty(unit='h',evidence=fe('redehydrate-prose-time')+fe('redehydrate-table-time'),qualifier='Unresolved conflict: prose 48 h versus Table 1 3 days.'),'pressure':fq('dehydration-vacuum')},
'h2s':{'temperature':fq('h2s-t'),'duration':fq('h2s-time'),'pressure':fq('h2s-pressure'),'gas_volume':qty(unit='mL',evidence=fe('h2s-reagent'),qualifier='Delivered gas amount is not reported.')},
'evacuate':{'temperature':qty(673,'K',fe('evacuate-final')),'duration':fq('evacuate-final'),'pressure':qty(unit='Torr',evidence=fe('evacuate-final'),qualifier='The post-treatment vacuum pressure is not reported.')},
'seal':{'temperature':qty(unit='K',evidence=fe('seal'),qualifier='Room temperature; no numerical value is supplied.'),'cooling_rate':qty(unit='K/min',evidence=fe('seal'),qualifier='Cooling rate is not reported.')}}
states=['host-mounted','tl-x','dehydrated-tl-x','black-in-x','washed-in-x','in87-x','treated-crystal','evacuated-product','sealed-product']
opins=[['na-x','pyrex'],['host-mounted','tl-acetate-feed'],['tl-x'],['dehydrated-tl-x','in-metal'],['black-in-x','wash-water'],['washed-in-x','pyrex'],['in87-x','h2s'],['treated-crystal'],['evacuated-product']]
OP_BIND=[]
for n,(sid,out,inp) in enumerate(zip(OP_TEXT,states,opins)):
    step=I['protocols'][0]['steps'][n];e=evidence(step['evidence']);label,text=OP_TEXT[sid]
    r['material_states'].append(state(out,label+' — retained crystal',[z for z in inp if z!='pyrex'],kind='product' if sid=='seal' else 'reaction_batch'))
    env={'dehydrate':'Vacuum; pressure reported in the experimental prose.','redox':'Vacuum in coaxial cylindrical ovens; numerical pressure unknown.','wash':'Exposure to the atmosphere.','redehydrate':'Vacuum; pressure reported in the experimental prose.','h2s':'Zeolitically dried hydrogen sulfide.','evacuate':'Vacuum; pressure unreported.','seal':'Sealed from the vacuum line at room temperature.'}.get(sid)
    r['operations'].append(operation(sid,step['operation'],label,e,inp,[out],depends=[list(OP_TEXT)[n-1]] if n else [],parameters=op_parameters[sid],stage=PLAN['operation_mapping'][n]['stage_plan'],description=text,environment=fact(env,e),retained_fraction=out))
    OP_BIND.append({'source_file':'source-inventory.json','json_pointer':f'/protocols/0/steps/{n}','canonical_links':[link('in66-route',f'/operations/{n}')]})
for oid,prefix in [('dehydrate','initial-dehydration'),('redehydrate','redehydrate')]:
    for v in ['prose','table']:
        r['condition_options'].append({'id':oid+'-source-'+v,'label':f'Unresolved source conflict for {oid}: '+('experimental prose' if v=='prose' else 'Table 1')+'; not an independently verified alternative protocol','parameters':{'temperature':fq(prefix+'-'+v+'-t'),'duration':fq(prefix+'-'+v+'-time')},'evidence':fe(prefix+'-'+v+'-t')+fe(prefix+'-'+v+'-time')})
for v in ['prose','table']:r['condition_options'].append({'id':'redox-source-'+v,'label':'Unresolved source conflict for redox duration: '+v+'; not a separate route','parameters':{'duration':fq('redox-'+v+'-time')},'evidence':fe('redox-'+v+'-time')})
add_sample('in66-route','final','Final H2S-treated In66-X',FORMULA,link='explicit',e=fe('product-formula'),stateid='sealed-product',notes=['Nominal composition from the paper; distinct from the averaged Table 2 framework and from proposed surface residue identities.'])

# Separate acquisition procedures. No assay conditions are inherited into synthesis.
for key in ['single-crystal-acquisition','epxma-acquisition','xps-acquisition']:
    rr=RECORDS[key];rr['lineage']['parent_record_id']=PREFIX+'in66-route'
    rr['materials'].append(material('final-crystal','Treated In66-X crystal',FORMULA,'specimen','characterization',GENERAL,notes=['Sample preparation links to the source route; numerical XPS, EPXMA and diffraction conditions remain separate.']))
    rr['material_states'].append(state('initial-specimen','Treated crystal',['final-crystal'],kind='product'))
    add_sample(key,'final','Current In66-X analytical specimen',FORMULA,link='general_context',stateid='initial-specimen')
rr=RECORDS['single-crystal-acquisition'];ee=fe('xrd-instrument')
rr['material_states'].append(state('diffraction-data','Single-crystal diffraction data',['initial-specimen'],kind='analysis_data'))
rr['operations'].append(operation('xrd-acquire','single_crystal_diffraction','Collect single-crystal diffraction data',ee,['initial-specimen'],['diffraction-data'],stage='characterization',parameters={'temperature':fq('xrd-t')},description='Collect data on the sealed crystal at 294 K using a CAD4/Turbo diffractometer, rotating-anode source and graphite-monochromated Mo radiation. The Table 1 acquisition settings are retained as separate typed values. A ψ-scan absorption correction was tested but was not used in the adopted refinement.',endpoint=fact('Diffraction intensities for structure refinement',ee)))
xp=rr['operations'][0]['parameters']
xp.update(mo_kalpha1_wavelength=qty(.70930,'Å',se(4,'Table 1, Mo Kα wavelengths'),raw_text='0.70930'),mo_kalpha2_wavelength=qty(.71359,'Å',se(4,'Table 1, Mo Kα wavelengths'),raw_text='0.71359'),scan_speed=qty(.5,'degree 2θ/min',se(4,'Table 1, scan speed')),data_collection_angle=qty(unit='degree 2θ',minimum=2,maximum=70,evidence=se(4,'Table 1, collection 2θ range')),lattice_determination_angle=qty(unit='degree 2θ',minimum=10,maximum=20,evidence=se(4,'Table 1, 2θ range for a0')),monitor_reflections=qty(3,'count',fe('xrd-monitor')),monitor_interval=qty(3,'h',fe('xrd-monitor')),background_fraction_of_scan_time=qty(.5,'dimensionless',fe('background-count'),qualifier='At each scan endpoint, background is counted for half the scan time. This is not an absolute counting duration.'))
rr['operations'][0]['description']+=' The scan is ω–2θ at 0.5 degree 2θ/min, with width 0.51 + 0.61 tan θ degrees. Three monitoring reflections are checked every 3 h; background at each scan endpoint is counted for half the scan time.'
rr=RECORDS['epxma-acquisition'];ee=fe('epxma-instrument')
rr['material_states'] += [state('exposed-crystal','Post-diffraction atmosphere-exposed crystal',['initial-specimen'],kind='product'),state('eds-data','EPXMA/EDS data',['exposed-crystal'],kind='analysis_data')]
rr['operations'] += [operation('epxma-expose','expose','Expose the post-diffraction crystal',GENERAL,['initial-specimen'],['exposed-crystal'],stage='characterization',description='After diffraction, expose the current treated crystal to the atmosphere for surface analysis. This handling is distinct from the earlier DI-water wash.',environment=fact('Atmosphere',GENERAL)),operation('epxma-acquire','energy_dispersive_xray_spectroscopy','Acquire EPXMA/EDS spectra',ee,['exposed-crystal'],['eds-data'],depends=['epxma-expose'],stage='characterization',description='Acquire the current-product elemental spectrum with the EDAX 9100 energy-dispersive system on a Phillips 515 scanning electron microscope. The parent In87-X spectrum reproduced in Figure 1B is from reference 34, not an additional current synthesis run.')]
rr=RECORDS['xps-acquisition'];ee=fe('xps-instrument')
rr['materials'].append(material('argon','Argon','Ar','sputtering_gas','characterization',fe('sputter-voltage'),notes=['XPS depth profiling only; no argon synthesis atmosphere is reported.']))
rr['material_states'] += [state('xps-data','XPS spectral data',['initial-specimen'],kind='analysis_data'),state('depth-profile-data','Sputter/depth-profile data',['initial-specimen'],kind='analysis_data')]
rr['operations'] += [operation('xps-acquire','xray_photoelectron_spectroscopy','Acquire indium 3d XPS spectra',ee,['initial-specimen'],['xps-data'],stage='characterization',parameters={'excitation_energy':fq('xps-excitation'),'source_voltage':fq('xps-power-voltage'),'source_current':fq('xps-current')},description='Acquire XPS with a VG ESCALAB 250 using Al Kα excitation. Figure 2 compares the current product, a parent In87-X specimen and an indium-metal reference; those spectra have distinct contextual sample IDs. The metal trace is displayed at one twentieth of its intensity.'),operation('ar-sputter','argon_sputter_depth_profile','Profile the current crystal with argon sputtering',fe('sputter-voltage')+fe('depth-prose'),['initial-specimen','argon'],['depth-profile-data'],depends=['xps-acquire'],stage='characterization',parameters={'sputter_voltage':fq('sputter-voltage'),'sputter_rate':fq('sputter-rate'),'duration_per_cycle':fq('sputter-step')},description='Repeat spectral measurement and approximately 10 s argon-sputter intervals on the current product. The reported rate is 0.6 Å/s at 3 kV. The prose separately states an approximately 4300 Å depth; the supplied displayed cycles do not provide a complete history from which that depth can be reconstructed.',environment=fact('Argon sputtering during XPS depth profiling',fe('sputter-voltage')))]
OP_BIND.append({'source_file':'source-inventory.json','json_pointer':'/protocols/0/steps/9','canonical_links':[link('epxma-acquisition','/operations/0'),link('epxma-acquisition','/operations/1'),link('xps-acquisition','/operations/0'),link('xps-acquisition','/operations/1')],'note':'Inventory analytical handoff expanded into separate explicit analytical procedures; no new synthesis steps.'})

# Scientific factual payload and exact value pointers.
FACT_BIND=[];TABLE_BIND=[];TABLE_ROWS=[]
scope_for_fact={z['fact_id']:k for k,vs in PLAN['fact_mapping'].items() for z in vs}
def value_leaves(v,path=''):
    if isinstance(v,dict):
        for k,z in v.items():yield from value_leaves(z,path+'/'+esc(k))
    elif isinstance(v,list):
        for k,z in enumerate(v):yield from value_leaves(z,path+'/'+str(k))
    else:yield path,v
def sample_for_fact(key,f,leaf=''):
    suffix=f['id'][8:];name=f['sample_scope'];formula=None;phase=None
    if key=='in66-route':
        if suffix in ['product-formula','seal']:return 'final'
        sid='context-'+slug(name)
        if 'sodium' in name or 'host crystals' in name:formula='Na92Si100Al92O384'
        elif suffix=='tl-product':formula='Tl92Si100Al92O384'
        elif suffix=='washed-parent':formula='In87Si100Al92O384'
    elif key in ['single-crystal-acquisition','epxma-acquisition','xps-acquisition']:
        if suffix in ['xps-instrument','xps-excitation','xps-power-voltage','xps-current','epxma-instrument','xrd-instrument']:sid='acquisition-context'
        elif suffix in ['epxma-parent-control','epxma-background']:sid='parent-reference-context';formula='In87Si100Al92O384'
        elif suffix=='in-metal-xps':sid='indium-reference';formula='In'
        elif suffix in ['atomic-like-xps','xps-cation-pair','xps-parent-difference','epxma-lines','xps-splitting']:sid='comparison-context'
        elif suffix=='xps-reference-ranges':sid='cited-reference-'+slug(leaf.split('/')[1] if leaf else 'range')
        elif suffix in ['weight-model','refinement-method','absorption-correction']:sid='analysis-method-context'
        else:sid='final';formula=FORMULA
    elif key=='refinement-comparison':
        sid='iteration-'+leaf.split('/')[1] if suffix=='refinement-stages' and leaf else 'refinement-context'
    elif key=='average-structure':sid='average-model';formula=FORMULA;phase='Average Fd-3m refinement (No. 227); not an ordered atomistic specimen'
    elif key=='ionic-radius-comparison':sid='author-radius-context'
    elif key=='framework-topology':sid='topology-context'
    elif key=='charge-and-mechanism':sid='source-hypothesis'
    else:sid='cited-or-outlook-context'
    return add_sample(key,sid,name,formula,phase,e=evidence(f['evidence']),notes=['Original sample scope: '+name])
for fi,f in enumerate(FCTS):
    key=scope_for_fact[f['id']];e=evidence(f['evidence']);bindings=[]
    for lp,val in value_leaves(f['value']):
        mid=slug(f['id']+(lp or ''));ss=sample_for_fact(key,f,lp)
        note=human(f['qualifier'])+' Source status: '+f['status']+'. Source scope: '+f['sample_scope']+'.'
        if f['id'].endswith('refinement-stages') and '/occupancies/' in lp:unit='atoms per conventional unit cell'
        elif f['id'].endswith('refinement-stages') and '/fixed_occupancies/' in lp:unit='atoms per conventional unit cell'
        elif f['id'].endswith('refinement-stages') and lp.endswith('/R1'):unit='dimensionless'
        elif f['id'].endswith('table2-fixed-sites'):unit='atoms per conventional unit cell' if lp.endswith('/0') else 'site multiplicity'
        else:unit=f['unit'] or ''
        if f['id'].endswith('table2-fixed-sites'):note+= ' This value is the '+('fixed atom count.' if lp.endswith('/0') else 'Wyckoff-site multiplicity, not an occupied atom count.')
        if f['id'].endswith('prior-parent-sites'):note+= ' Cited parent context: '+('In88-X before washing.' if lp.endswith('/0') else 'washed In87-X.')
        if f['id'].endswith('charge-deficit'):note+= ' This value describes '+('the positive model-charge count.' if lp.endswith('/0') else 'the magnitude of the negative nominal framework charge.')
        if f['id'].endswith('xps-reference-ranges'):note+= ' This value is the '+('lower' if lp.endswith('/0') else 'upper')+' boundary of the cited range, not an additional spectral peak.'
        if isinstance(val,(int,float)) and not isinstance(val,bool):
            q=qty(val,unit,e,status(f['status']),approximate=f['approximate'],qualifier=note,basis=f['property']+'; source value path '+(lp or '/'),raw_text=str(val))
        elif isinstance(val,str) and re.fullmatch(r'[−-]?\d+(?:\.\d+)?\(\d+\)',val):
            nv=float(val.split('(')[0].replace('−','-'));q=qty(nv,unit,e,status(f['status']),qualifier=note+' Parentheses are the source estimated standard deviation in the last digits; exact token retained.',basis=f['property'],raw_text=val)
        else:q=fact(val,e,status(f['status'],val is not None),note=note)
        lk=addm(key,mid,ss,slug(f['property']+(lp or '')),q,e,tech='Source '+f['status'].replace('_',' '),scope=f['sample_scope'])
        bindings.append(dict(lk,source_value_pointer='/facts/'+str(fi)+'/value'+lp,source_value=copy.deepcopy(val)))
    FACT_BIND.append({'source_fact_id':f['id'],'source_file':'source-facts.json','json_pointer':f'/facts/{fi}','source_payload':f,'canonical_links':bindings})

def quantities(node,p=''):
    if isinstance(node,dict):
        if {'raw','value','unit','status'}<=set(node):yield p,node;return
        for k,v in node.items():yield from quantities(v,p+'/'+esc(k))
    elif isinstance(node,list):
        for k,v in enumerate(node):yield from quantities(v,p+'/'+str(k))
def table_rows(t):
    for coll in ['shared_rows','model_rows','rows']:
        for n,row in enumerate(t.get(coll,[])):yield '/'+coll+'/'+str(n),row
    for bi,b in enumerate(t.get('blocks',[])):
        for ri,row in enumerate(b.get('rows',[])):yield f'/blocks/{bi}/rows/{ri}',row
for ti,t in enumerate(T['tables']):
    for rp,row in table_rows(t):
        rowid=row['row_id'];key={0:'refinement-comparison',1:'average-structure',2:'average-structure',3:'average-structure',4:'ionic-radius-comparison'}[ti]
        if ti==0 and rp.startswith('/shared_rows'):key='single-crystal-acquisition' if int(rp.rsplit('/',1)[1])>=8 else 'in66-route'
        if ti==0 and rowid=='lattice-a':key='average-structure'
        e=evidence([row.get('source',t['source'])]);rl=[]
        for qp,q in quantities(row):
            scope=t['scope']+' Row '+rowid+'. '+str(row.get('source_scope',''))
            if row.get('cited_reference_number'):scope+=' Cited comparison from reference '+str(row['cited_reference_number'])+'; external full text uninspected.'
            model='fd3m' if 'Fd3̄m' in qp else 'fd3' if 'Fd3̄' in qp else None
            sid=('model-'+model if model else 'table-'+str(ti+1)+'-'+rowid)
            form=FORMULA if key=='average-structure' else None
            add_sample(key,sid,'Table '+str(ti+1)+', '+rowid+((', '+model) if model else ''),form,e=e,notes=[scope,'Tabular refined, fixed and varied values are not separate synthesis outcomes.'])
            extra=[]
            if q.get('uncertainty'):extra.append('Estimated standard deviation: '+str(q['uncertainty']['value'])+' '+str(q['uncertainty'].get('unit') or '')+'.')
            if 'source_to_value_multiplier' in q:extra.append('Source-to-value multiplier '+str(q['source_to_value_multiplier'])+'.')
            if q.get('footnote_markers'):extra.append('Source footnotes: '+', '.join(q['footnote_markers'])+'.')
            if q.get('reason'):extra.append(q['reason'])
            ss='author_derived' if ti==4 and q['value'] is not None else status(q['status'],q['value'] is not None)
            cq=qty(q['value'],q['unit'] or '',e,ss,qualifier=' '.join(extra)+' Source status: '+q['status']+'. '+scope,basis=q.get('basis',''),raw_text=str(q.get('raw_cell') or q.get('raw') or ''))
            lk=addm(key,'table-'+str(ti+1)+'-'+rowid+'-'+slug(qp),sid,'table_'+str(ti+1)+'_'+rowid+'_'+slug(qp),cq,e,tech='Tabulated source refinement' if ti in [1,2,3] else 'Tabulated source value',scope=scope)
            binding=dict(lk,source_file='main-tables.json',source_quantity_pointer=f'/tables/{ti}'+rp+qp,source_quantity=copy.deepcopy(q));TABLE_BIND.append(binding);rl.append(lk)
        if not rl:
            sid=add_sample(key,'table-'+str(ti+1)+'-'+rowid,'Table '+str(ti+1)+', '+rowid,e=e)
            val=' | '.join('Source blank' if z is None else str(z) for z in row['raw_cells'])
            rl.append(addm(key,'table-'+str(ti+1)+'-'+rowid,sid,'table_'+str(ti+1)+'_'+rowid,fact(val,e,note=t['scope']),e,tech='Tabulated context',scope=t['scope']))
        # Explicit bounded acquisition ranges are typed in addition to the original raw row.
        if row.get('range'):
            g=row['range'];rl.append(addm(key,'table-'+str(ti+1)+'-'+rowid+'-range',sid,'table_'+str(ti+1)+'_'+rowid+'_range',qty(unit=g['unit'],evidence=e,minimum=g['min'],maximum=g['max'],raw_text=g['raw'],qualifier='Acquisition angle range, not a synthesis condition.'),e,tech='Single-crystal X-ray diffraction'))
        TABLE_ROWS.append({'source_file':'main-tables.json','json_pointer':f'/tables/{ti}'+rp,'table_number':ti+1,'row_id':rowid,'row_payload':row,'scope':t['scope'],'canonical_links':rl})

# Exact chemical equations and references remain source hypotheses/context.
EQUATION_BIND=[];REFERENCE_BIND=[]
for n,eq in enumerate(I['chemical_equations']):
    e=evidence(eq.get('evidence',[]));key='charge-and-mechanism';sid=add_sample(key,'source-hypothesis','Author-proposed reactions and charge compensation',e=e)
    text=eq.get('expression') or eq.get('equation') or eq.get('text') or eq.get('raw') or eq.get('formula')
    if text is None:raise ValueError('Equation shape requires explicit mapping '+str(eq))
    lk=addm(key,'source-equation-'+str(n+1),sid,'author_proposed_chemical_equation_'+str(n+1),fact(text,e,'inferred',note='Author-proposed mechanism; not an independently demonstrated reaction, a distinct synthesis recipe, or a measured sulfide product.'),e,tech='Author-proposed chemical equation')
    EQUATION_BIND.append({'source_file':'source-inventory.json','json_pointer':f'/chemical_equations/{n}','source_payload':eq,'canonical_links':[lk]})
for n,ref in enumerate(I['references']):
    e=evidence(ref['evidence']);key='reference-and-outlook';sid=add_sample(key,'reference-'+str(ref['number']),'Cited reference '+str(ref['number']),e=e)
    lk=addm(key,'reference-'+str(ref['number']),sid,'bibliographic_reference',fact(ref['raw_bibliographic_text'],e,note='Bibliographic entry transcribed from this paper. External full text has not been inspected for this proposal.'),e,tech='Source bibliography')
    REFERENCE_BIND.append({'source_file':'source-inventory.json','json_pointer':f'/references/{n}','source_payload':ref,'canonical_links':[lk]})

# Named comparison specimens are explicit identities, not extra executed routes.
for key in ['epxma-acquisition','xps-acquisition']:
    rr=RECORDS[key]
    rr['materials'].append(material('parent-reference','Parent In87-X comparison','In87Si100Al92O384','reference_specimen','characterization',se(3,'Figures 1 and 2'),notes=['Reference/control context; Figure 1B is copied from reference 34. This entry is not a second current synthesis run.']))
    add_sample(key,'parent-reference-context','Parent In87-X comparison','In87Si100Al92O384',e=se(3,'Figures 1 and 2'),notes=['Separate reference/control specimen; no assumed physical-batch identity with the final current crystal.'])
rr=RECORDS['xps-acquisition'];rr['materials'].append(material('indium-reference','Indium-metal XPS reference','In','reference_specimen','characterization',se(3,'Figure 2A'),notes=['Figure 2A intensity is scaled to 1/20; not a synthesis precursor charge.']))
add_sample('xps-acquisition','indium-reference','Indium-metal reference','In',e=se(3,'Figure 2A'))

# Explicit availability record fields; no atomic-coordinate asset is admitted.
for r in RECORDS.values():
    assert not r['structure_assets'] and not r['quality']['requested_tasks']
    r['context_links']=[{'label':'Source paper','url':'https://doi.org/10.1021/jp0219348','relation':'Primary source; current proposal is private and not promoted.'}]
    errs=validate_record(r)
    if errs:raise ValueError('\n'.join(errs))
    assert not any(z['eligible'] for z in eligibility(r).values())
    save(RDIR/(r['record_id']+'.json'),r)

# Reader prose is source-specific; the tables and quantified facts come from the records.
SECTIONS={k:{'id':k,'title':title,'items':[]} for k,title in [('precursors','Precursors'),('protocol','Synthesis protocol'),('structures','Final structures'),('properties','Properties'),('intuition','Chemical intuition'),('sources','Sources and evidence') ]}
ITEMS={};UNIT_ROWS=[];TYPED_BIND=[]
def display(q):
    if 'unit' in q:
        if q['value'] is not None:return q['value']
        if q['minimum'] is not None or q['maximum'] is not None:return fmt(q).split(' · ')[0]
        return 'Not reported' if q['status']=='not_reported' else q['status'].replace('_',' ').capitalize()
    return q['value'] if q['value'] is not None else 'Not reported'
def item(section,id,title,text,links=None,e=None,notes=None,claim='source_report',facts=None,assets=None,sourcefacts=None):
    links=links or [];e=e or GENERAL
    x={'id':id,'title':title,'text':text,'claim_type':claim,'sample_scope':{'formulations':[],'physical_batch_id':None,'scope_kind':'source_context','state':title,'link_limit':SCOPE_LIMIT,'canonical_sample_links':[{'record_id':lk['record_id'],'sample_id':lk['sample_id']} for lk in links if 'sample_id' in lk]},'evidence':[dict(z,document_role='main') for z in e],'source_locators':[z['locator'] for z in e],'canonical_links':links,'notes':notes or [],'facts':facts or [],'source_audit_unit_ids':[],'source_fact_ids':sourcefacts or [],'original_assets':assets or [],'training_eligible':False}
    assert id not in ITEMS;SECTIONS[section]['items'].append(x);ITEMS[id]=x;return x
def typed_for(lk):
    rr=next(r for r in RECORDS.values() if r['record_id']==lk['record_id']);q=pointer(rr,lk['json_pointer'])
    if not isinstance(q,dict) or not {'value','status','evidence'}<=q.keys():return None
    label=lk.get('label') or human(lk['json_pointer'].split('/')[-2 if lk['json_pointer'].endswith('/value') else -1].replace('_',' '))
    if lk['json_pointer'].startswith('/measurements/'):label=rr['measurements'][int(lk['json_pointer'].split('/')[2])]['property'].replace('_',' ').replace('-',' ')
    return {'id':lk['record_id']+'::'+lk['json_pointer'],'label':label,'value':display(q),'unit':q.get('unit',''),'status':q['status'],'approximate':q.get('approximate',False),'qualifier':q.get('qualifier',q.get('note','')),'basis':q.get('basis',''),'canonical_record_id':lk['record_id'],'json_pointer':lk['json_pointer'],'canonical_quantity':copy.deepcopy(q),'evidence':q['evidence'],'training_eligible':False}
def add_typed(x,links):
    for lk in links:
        q=typed_for(lk)
        if q:
            x['facts'].append(q);TYPED_BIND.append({'item_id':x['id'],'fact_id':q['id'],'record_id':lk['record_id'],'json_pointer':lk['json_pointer'],'canonical_quantity':q['canonical_quantity']})
def unit(id,file,p,items,links,payload=None,disposition='reader_and_canonical'):
    v={'source_unit_id':id,'source_file':file,'source_json_pointer':p,'item_ids':items,'canonical_links':links,'disposition':disposition}
    if payload is not None:v['source_payload']=payload
    UNIT_ROWS.append(v)
    for it in items:
        if id not in ITEMS[it]['source_audit_unit_ids']:ITEMS[it]['source_audit_unit_ids'].append(id)

for key,r in RECORDS.items():
    for mi,m in enumerate(r['materials']):
        lk=link(key,f'/materials/{mi}');i=item('precursors','material-'+slug(r['record_id']+'-'+m['id']),m['name'],m['name']+'. '+('Formula: '+m['formula']+'. ' if m['formula'] else 'No single molecular formula is assigned. ')+' '.join(m['notes']),[lk],m['evidence'],claim='source_material_inventory')
        qlinks=[link(key,f'/materials/{mi}/quantities/{esc(k)}') for k in m['quantities']];i['canonical_links']+=qlinks;add_typed(i,qlinks)
    for oi,o in enumerate(r['operations']):
        i=item('protocol' if key=='in66-route' else 'properties','operation-'+key+'-'+o['id'],o['label'],o['description'],[link(key,f'/operations/{oi}')],o['evidence'],notes=[o['environment'].get('value') or 'Atmosphere is not numerically or chemically specified for this step.'],claim='synthesis_operation' if key=='in66-route' else 'acquisition_procedure')
        qlinks=[link(key,f'/operations/{oi}/parameters/{esc(k)}') for k in o['parameters']];i['canonical_links']+=qlinks;add_typed(i,qlinks)
    for ci,c in enumerate(r['condition_options']):
        i=item('protocol','conflict-option-'+c['id'],c['label'],'This entry preserves one printed side of an unresolved source conflict. It is not a recommended setting or a verified alternative recipe.',[link(key,f'/condition_options/{ci}')],c['evidence'],claim='unresolved_source_conflict')
        qlinks=[link(key,f'/condition_options/{ci}/parameters/{esc(k)}') for k in c['parameters']];i['canonical_links']+=qlinks;add_typed(i,qlinks)
i=item('precursors','stock-tl-acetate-feed','Aqueous thallous acetate feed','The reported feed is 0.1 mol/L aqueous thallous acetate at pH 6.4. Its preparation, water grade and absolute salt charge are not supplied. The 10.0 mL Table 1 value is retained without assuming a total-throughput or flow-rate interpretation.',[link('in66-route','/stocks/0')],fe('exchange-stock')+fe('exchange-ph'),claim='source_stock_specification')
add_typed(i,[link('in66-route','/stocks/0/concentrations/'+esc(k)) for k in RECORDS['in66-route']['stocks'][0]['concentrations']])

PROSE={
'parent-host':'The starting host is sodium zeolite X, nominally Na92Si100Al92O384. Its preparation is cited to reference 28 rather than reproduced in this paper.',
'host-shape':'The starting host crystals are colorless octahedra. This description applies to the zeolite host and does not identify the morphology of an isolated indium nanocrystal.',
'host-size':'The starting zeolite crystals have an approximate cross-section of 0.15 mm. This is a host-crystal dimension, not the size of the confined indium cluster.',
'product-formula':'The treated crystal is described nominally as In66Si100Al92O384. Table 2 instead refines an averaged (Si,Al) framework corresponding to 96 Si and 96 Al; the two representations are retained without forced reconciliation.',
'surface-powder':'A metallic-gray surface powder is reported. The authors discuss possible indium oxide, sulfide or metallic species, but its phase composition is not established.',
'xps-reference-ranges':'The authors compare the observed binding energies with reported ranges for InCl, InCl3 and other In(III) compounds. These are cited reference ranges, not additional measurements on the current crystal.',
'atomic-like-xps':'The lower-energy indium 3d pair is discussed for both the current In66-X product and its In87-X comparison. The atomic-like assignment is an interpretation and does not independently establish a metallic indium phase.',
'xps-cation-pair':'The higher-energy indium 3d pair is discussed in both zeolite spectra. The source assigns it to cationic indium and compares several oxidation-state references; a unique measured oxidation number is not implied.',
'xps-parent-difference':'The low-energy doublet is relatively stronger for the treated crystal than for the parent, although the treated crystal contains fewer indium atoms overall. The source presents this as a qualitative comparison.',
'epxma-lines':'The source labels oxygen, aluminum, silicon, indium and sulfur features across the EPXMA spectra. The listed line energies preserve the source annotations; they do not provide an elemental stoichiometry or a common peak fit.',
'epxma-tlabsence':'The authors favor the sulfur assignment near 2.31 keV over a possible thallium overlap because the higher-energy thallium L features are absent. This is the authors’ spectral interpretation.',
'epxma-surface':'Sulfur is detected by surface-sensitive elemental analysis, while no sulfur atom is included in the refined crystal structure. The authors therefore discuss a surface contribution rather than proving an internal sulfide phase.',
'epxma-background':'The parent reference spectrum used a beryllium window, affecting oxygen detection. The source also discusses carbon and possible low-energy ghost features. These detector and background comments are not additional composition measurements.',
'depth-prose':'The prose states an approximate profiling depth of 4300 Å. The displayed sequence, approximately 10 s sputter intervals and 0.6 Å/s rate do not provide a complete history that reproduces that depth; no unreported total sputter time is inferred.',
'absorption-correction':'A ψ-scan absorption correction was evaluated using μ = 2.20 mm⁻¹. It was not used in the adopted final refinement; the trial is not silently treated as the final data-processing method.',
'space-group':'The authors adopt Fd-3m (No. 227) after comparison with an Fd-3 (No. 203) trial. These are alternative descriptions of one diffraction study, not separately synthesized polymorphs.',
'si-al-order':'The average structural analysis is interpreted as loss of long-range Si/Al ordering. The schematic framework illustration does not establish an ordered Si/Al arrangement in the treated specimen.',
'alternative-si-al-distance':'The Fd-3 trial produced nearly equal Si–O and Al–O distances. The authors compare these with cited characteristic distances and use the result when favoring the averaged Fd-3m model.',
'refinement-method':'The adopted structure was refined by full-matrix least squares on F² in SHELXL-97 using all reflections without an nσ cutoff. Starting coordinates were taken from reference 34; that reference does not supply a new synthesis route here.',
'refinement-stages':'The source describes successive refinements as additional indium sites are introduced, followed by a final fixed-occupancy refinement. These five iterations belong to one structural analysis. The occupancies are atoms per conventional unit cell, not occupancy fractions or five synthesis outcomes.',
'unrefined-peaks':'Additional residual density opposite four-membered rings could not be stably refined as indium or sulfur. No corresponding atom is added to the proposed product structure.',
'weight-model':'The weighting function and its P definition belong to the diffraction refinement. The max(Fo²,0) term appears within the weighting expression; it does not authorize replacing negative observed reflection intensities in the retained SI table.',
'scattering-model':'The scattering factors use source-described averages of formal ionic and atomic factors for indium and the mixed Si/Al framework. These modeling choices are not a unique experimental assignment of charge to every atomic site.',
'table2-scales':'Table 2 prints coordinates and displacement parameters with different scale factors. The exact printed tokens, scale factors, estimated standard deviations, column order and footnotes are retained beside the normalized values.',
'table2-si-al':'The Table 2 mixed framework site gives 192 positions and is interpreted as 96 Si plus 96 Al. This differs from the paper’s nominal Si100Al92 composition; neither is overwritten.',
'table2-fixed-sites':'The final indium site counts and site multiplicities are distinct quantities. Fixed and varied values in Table 2 describe refinement choices, not separate physical samples.',
'data-ratio-mismatch':'The printed data/parameter ratios match the strong-reflection counts divided by parameter counts, while the table heading and footnote define m using unique reflections. This source inconsistency is retained.',
'zeolite-description':'The host has the faujasite framework topology with sodalite cages and supercages. The structural context describes the host and does not establish a free-standing quantum-dot lattice outside the zeolite.',
'site-definitions':'The source defines conventional extraframework sites I, I′, II′, II, III, III′ and U. These site labels describe crystallographic locations, not distinct reagent or product identities.',
'oxidation-assignment':'The source discusses formal-charge assignments for indium at the refined sites, including a tentative intermediate average charge at I′. These assignments depend on structural and charge-balance arguments.',
'cluster-count':'The structural model contains eight sodalite-centered indium clusters per conventional unit cell. This count is a model population, not the number of crystals prepared.',
'supercage-filling':'The authors discuss an approximately 87.5% supercage arrangement involving three In(I) ions and a minor IIa population. Illustrating the possible sites does not fix a unique local occupancy pattern.',
'ellipsoid-probability':'The crystallographic stereoviews use 50% probability displacement ellipsoids. This is a visualization convention and is not a particle-size distribution.',
'cluster-bond':'The reported In(U)–In(I′) separation is a refined interatomic distance. It does not by itself specify the size or complete coordinates of an independently measured nanocrystal.',
'cluster-oxygen':'The In(I′)–O(3) value is a refined coordination distance with an estimated standard deviation, retained in its printed notation.',
'inIIa-radius':'The authors derive an ionic radius by subtracting an assumed oxygen radius from a coordination distance. This ionic-radius estimate is not the radius of an indium quantum dot.',
'extra-ligand':'The local geometry motivates discussion of an additional ligand. The ligand identity and occupancy are not experimentally established and are not added to a coordinate model.',
'inU-density':'The source uses residual-density and special-position arguments in discussing the central indium assignment. The reasoning is retained as structural interpretation rather than an independent elemental assay.',
'prior-parent-sites':'The comparison with the parent structure uses indium-site populations reported in reference 34. These cited populations are distinct from the current fixed-occupancy refinement.',
'h2s-site-increase':'The reported population increases are differences between the current interpretation and a cited parent model. They are not independent elemental-yield measurements.',
'cluster-stability':'The authors discuss the chemical stability and organization of the confined indium cluster using its coordination and charge model. The proposed mechanism is not a time-resolved reaction measurement.',
'cluster-charge':'The approximately 7+ cluster charge is an author interpretation based on the proposed structural and chemical model, not an individually measured cluster charge.',
'charge-deficit':'The source’s formal-charge accounting gives 83 positive charges against 92 framework negative charges. The unresolved deficit is preserved rather than forcing a neutral atomistic model.',
'oxygen-loss-hypothesis':'Loss of approximately 4.5 framework oxygen atoms per unit cell is proposed as one charge-compensation mechanism. Oxygen removal is not experimentally quantified, and no oxygen coordinates are deleted.',
'proton-hypothesis':'Nine protons per unit cell are proposed as an alternative charge-compensation description. Their positions are not measured and no hydrogen atoms are invented.',
'cluster-size':'The approximately 3.5 Å cluster radius is an author-derived estimate using a refined separation and an assumed ionic radius. It is not a TEM-derived particle diameter.',
'cluster-spacing':'The approximately 10.8 Å spacing refers to the authors’ model of a diamond-type array of cluster centers in the host. It is not a separate real-space microscopy measurement.',
'dot-count':'The source estimates approximately 3 × 10¹⁴ dots in a host crystal of the stated size. This is a model-based count, not a direct particle-count measurement.',
'outlook':'Very high density information storage is proposed as a possible application if the individual clusters could be addressed. No memory device, optical response or transport performance is demonstrated in this paper.',
'motivation':'Hydrogen sulfide treatment is used to investigate indium disproportionation and fuller occupation of the host cavities. The motivation is distinct from proving every proposed charge-compensation pathway.',
'prior-exchange-failure':'Earlier exchange difficulties and high-pressure experiments are cited as background. Their conditions and outcomes are not current failed runs and do not become training labels for this route.',
'in-vapor-pressure':'The indium vapor pressure is a cited equilibrium reference value at 623 K. It is not the measured pressure of the reaction chamber.',
'tl-vapor-pressure':'The thallium vapor pressure is a cited equilibrium reference value at 623 K. It is not the measured pressure of the reaction chamber.'}
for fb in FACT_BIND:
    f=fb['source_payload'];suffix=f['id'].removeprefix('heo2003-');key=scope_for_fact[f['id']]
    section={'in66-route':'protocol','single-crystal-acquisition':'structures','epxma-acquisition':'properties','xps-acquisition':'properties','average-structure':'structures','refinement-comparison':'structures','ionic-radius-comparison':'structures','framework-topology':'structures','charge-and-mechanism':'intuition','reference-and-outlook':'sources'}[key]
    if suffix in ['parent-host','host-shape','host-size','exchange-reagent','exchange-stock','exchange-ph','indium-metal','h2s-reagent']:section='precursors'
    text=PROSE.get(suffix)
    if text is None:
        if suffix.startswith('equation-'):text='The authors propose the reaction shown below as part of their redox or charge-compensation interpretation. It is not an independently established pathway or a separate synthesis recipe.'
        else:
            vals=[fmt(pointer(RECORDS[key],lk['json_pointer'])).split(' · ')[0] for lk in fb['canonical_links']]
            text=human(f['property']).capitalize()+' is reported for '+human(f['sample_scope'])+': '+'; '.join(vals)+'. '+human(f['qualifier'])
    i=item(section,'fact-'+suffix,human(f['property']).capitalize(),text,fb['canonical_links'],evidence(f['evidence']),sourcefacts=[f['id']],claim=f['status']);add_typed(i,fb['canonical_links']);unit(f['id'],'source-facts.json',fb['json_pointer'],[i['id']],fb['canonical_links'],f)
for tr in TABLE_ROWS:
    row=tr['row_payload'];n=tr['table_number'];cells=row['raw_cells'];label=str(row.get('atom_label') or cells[0]);section='protocol' if tr['canonical_links'][0]['record_id'].endswith('in66-route') else 'structures'
    text='Table '+str(n)+' reports '+label+'. Printed cells: '+' | '.join('blank (not zero)' if z is None else str(z) for z in cells[1:])+'. '+tr['scope']
    i=item(section,'table-'+str(n)+'-'+tr['row_id'],'Table '+str(n)+' · '+label,text,tr['canonical_links'],evidence([row.get('source',T['tables'][n-1]['source'])]),claim='tabulated_refinement' if n>1 else 'tabulated_source_value',assets=['heo2003-main-table-'+str(n)]);add_typed(i,tr['canonical_links']);unit('table-'+str(n)+'-'+tr['row_id'],'main-tables.json',tr['json_pointer'],[i['id']],tr['canonical_links'],row)
for ti,t in enumerate(T['tables']):
    its=[x['id'] for x in ITEMS.values() if x['id'].startswith('table-'+str(ti+1)+'-')]
    metadata={k:v for k,v in t.items() if k not in ['shared_rows','model_rows','rows','blocks']}
    i=item('structures','table-'+str(ti+1)+'-scope',t['title'],t['scope'],e=evidence([t['source']]),notes=[t.get('normalization_note',''),t.get('source_literal_caution','')],claim='table_scope_and_footnotes',assets=[t['original_asset_id']])
    for ni,note in enumerate(t.get('footnotes',[])):
        raw=note.get('raw') or note.get('text') or str(note)
        i['notes'].append('Footnote '+str(note.get('marker',ni+1))+': '+raw)
    unit('table-'+str(ti+1)+'-metadata','main-tables.json',f'/tables/{ti}',[i['id']]+its,[],metadata,'reader_table_payload_with_exact_raw_cells_and_footnotes')
for eb in EQUATION_BIND:
    n=eb['json_pointer'].rsplit('/',1)[1];i=item('intuition','chemical-equation-'+n,'Proposed reaction '+str(int(n)+1),'The source proposes this equation as a redox, cluster-formation or charge-compensation mechanism. It does not establish a distinct product phase or a separately executed recipe.',eb['canonical_links'],pointer(RECORDS['charge-and-mechanism'],eb['canonical_links'][0]['json_pointer'])['evidence'],claim='author_hypothesis');add_typed(i,eb['canonical_links']);unit('chemical-equation-'+n,'source-inventory.json',eb['json_pointer'],[i['id']],eb['canonical_links'],eb['source_payload'])
for rb in REFERENCE_BIND:
    ref=rb['source_payload'];i=item('sources','reference-'+str(ref['number']),'Reference '+str(ref['number']),ref['raw_bibliographic_text'],rb['canonical_links'],evidence(ref['evidence']),notes=['External full text was not inspected for this proposal.'],claim='source_bibliography');add_typed(i,rb['canonical_links']);unit('reference-'+str(ref['number']),'source-inventory.json',rb['json_pointer'],[i['id']],rb['canonical_links'],ref)

# Retained originals: all main figures, table crops, useful excerpts and 23 page views.
ASSETS=[];ASSET_MAP={}
fgscopes={1:['epxma-acquisition'],2:['xps-acquisition'],3:['xps-acquisition'],4:['framework-topology'],5:['average-structure'],6:['average-structure','charge-and-mechanism'],7:['average-structure']}
for a in load(H/'root-asset-manifest.json')['assets']+load(H/'main-table-assets.json')['assets']:
    aid=a.get('id',a.get('asset_id'));ap=Path(a['path']);ap=ap if ap.is_absolute() else H/ap
    assert ap.exists() and sha(ap)==a['sha256'],aid
    ASSET_MAP[aid]={'path':str(ap),'sha256':sha(ap),'source_payload':a}
    page=a.get('pdf_page') or a.get('evidence',[{}])[0].get('pdf_page');role=a.get('source_role') or ('si' if 'si-' in ap.name else 'main')
    num=int(aid.rsplit('-',1)[1]) if re.fullmatch('heo2003-figure-[1-7]',aid) else None
    keys=fgscopes[num] if num else ['refinement-comparison'] if role=='si' else ['in66-route'] if any(z in aid for z in ['experimental','preparation']) else list(RECORDS)
    original_figure=next((z for z in I['figures'] if z['id']==aid),None)
    caption=human(original_figure['scope']) if original_figure else a.get('title') or 'Original source page or excerpt; scientific scope is determined by the linked reader items and source locator.'
    rec={'id':aid,'label':original_figure['title'] if original_figure else a.get('title') or ap.stem.replace('-',' ').capitalize(),'document_role':role,'page':page,'caption_paraphrase':caption,'sample_scope':caption,'sample_links':[PREFIX+k for k in keys],'sample_linkage':'Source-context links only. Mixed reference/current panels and model images retain their explicit caption scopes.','evidence_class':'original_refinement_illustration' if num and num>=4 else 'original_experimental_figure' if num else 'original_source_table' if 'main-table' in aid else 'original_source_excerpt','public_asset':'assets/figures/heo2003/'+ap.name,'private_asset':str(ap),'public_asset_sha256':sha(ap),'asset_provenance':copy.deepcopy(a),'source_unit_ids':['asset-'+aid],'notes':['Private proposal only; original-asset integration and reader rendering remain pending.'],'text_reviewed':False,'visual_reviewed':False,'reviewed':False,'reader_render_verified':False,'training_eligible':False}
    ASSETS.append(rec)
    i=item('structures' if num and num>=4 else 'properties' if num else 'sources','asset-'+aid,rec['label'],caption,e=evidence(a.get('evidence') or [{'pdf_page':page,'source_role':role,'locator':aid}]),claim=rec['evidence_class'],assets=[aid]);unit('asset-'+aid,'root-asset-manifest.json' if 'id' in a else 'main-table-assets.json','/assets/'+str(next(j for j,z in enumerate(load(H/('root-asset-manifest.json' if 'id' in a else 'main-table-assets.json'))['assets']) if z.get('id',z.get('asset_id'))==aid)),[i['id']],[],a,'original_source_payload_and_private_asset')

# Bind remaining inventory objects to human-readable context cards, rather than omit metadata.
for key in ['materials','protocols','figures','supporting_tables','chemical_equations','mathematical_models','references','evidence_conflicts','remaining_gaps']:
    for n,obj in enumerate(I[key]):
        if key=='chemical_equations':its=['chemical-equation-'+str(n)]
        elif key=='references':its=['reference-'+str(obj['number'])]
        elif key=='figures':its=['asset-'+obj['asset_id']]
        elif key=='materials':
            mid=obj['id'].removeprefix('heo2003-');its=[z for z in ITEMS if z.startswith('material-') and z.endswith('-'+mid)]
            if mid=='water':its=[z for z in ITEMS if z.startswith('material-') and z.endswith(('feed-water','wash-water'))]
        elif key=='protocols':its=['operation-in66-route-'+k for k in OP_TEXT]
        else:its=[]
        if not its:
            title={'supporting_tables':'Supporting reflection table','mathematical_models':'Refinement mathematical context','evidence_conflicts':'Unresolved source conflict','remaining_gaps':'Unresolved source information','materials':'Contextual material or intermediate'}.get(key,key.replace('_',' ').capitalize())+' '+str(n+1)
            if isinstance(obj,str):text=human(obj)
            elif key=='materials':text=human(obj.get('name',''))+'. '+human(obj.get('notes',''))+' This inventory identity is contextual and does not add a separate synthesis route.'
            else:text='The complete source object is retained in the bound inventory payload. '+human(obj.get('scope') or obj.get('description') or obj.get('conflict') or obj.get('note') or '')
            if key=='supporting_tables':text='The matched 14-page SI contains 1209 reflection rows, with indices, calculated and observed squared structure factors, uncertainties and unexplained o-like markers. A separate aggregate audit reconciled all seven independently read page-pair chunks. Of 7254 numeric positions, 7252 signed values are resolved; two signs on pages 11–12 remain unresolved. The retained table includes 137 definite negative Fobs² values and one zero. This authoring proposal reuses that audit and does not independently recertify the scan or infer a structure from the intensities.'
            i=item('sources','inventory-'+key+'-'+str(n),title,text,e=evidence(obj.get('evidence',[])) if isinstance(obj,dict) else GENERAL,claim='source_context');its=[i['id']]
        unit('inventory-'+key+'-'+str(n),'source-inventory.json','/'+key+'/'+str(n),its,[],obj,'full_inventory_payload_and_reader_context')
meta={k:v for k,v in I.items() if k not in ['materials','protocols','figures','supporting_tables','chemical_equations','mathematical_models','references','evidence_conflicts','remaining_gaps','assets','main_tables']}
i=item('sources','source-identity',I['title'],'Heo and coauthors report one indium-treatment route in zeolite X, its single-crystal structural refinement and surface spectroscopy. The supplied source bundle comprises the nine-page main article and fourteen-page scanned supporting reflection list. Independent main-source, page-chunk and SI aggregate audits remain distinct from this unaudited canonical/reader proposal.',claim='source_identity',notes=GAPS)
unit('inventory-identity','source-inventory.json','',['source-identity'],[],meta,'metadata_and_status_payload')
unit('inventory-main-tables','source-inventory.json','/main_tables',['table-'+str(n)+'-scope' for n in range(1,6)],[],I['main_tables'],'linked_exact_table_payload')
unit('inventory-assets','source-inventory.json','/assets',['asset-'+a['id'] for a in I['assets']],[],I['assets'],'all_original_assets_mapped')

# SI is linked to fixed, separately audited chunks; no moving aggregate artifact is imported.
SI=[]
for ab in ['01-02','03-04','05-06','07-08','09-10','11-12','13-14']:
    a,b=[int(z) for z in ab.split('-')]
    candidates=list(H.glob(f'si-pages{a:02d}-{b:02d}-manifest.json'))+list(H.glob(f'si-pages-{a}-{b}-manifest.json'))
    if not candidates:
        candidates=list(H.glob(f'si-pages{a}-{b}-*manifest*.json'))+list(H.glob(f'si-pages-{a}-{b}-*manifest*.json'))
    files=sorted(set(candidates))
    # Older page pairs may use checkpoint/manifest names with a different zero convention.
    if not files:files=sorted(p for p in H.glob('si-*manifest*.json') if re.search(rf'pages-?0?{a}-0?{b}(?:-|\.)',p.name))
    if not files:
        cp=H/('si-numerical-verification-checkpoint.json' if a==1 else f'si-pages{a:02d}-{b:02d}-author-checkpoint.json')
        if cp.exists():files=[cp]
    audits=sorted(H.glob(f'si-pages-{a}-{b}-independent-audit.json'))
    SI.append({'pages':[a,b],'chunk_manifests':[{'path':str(p),'sha256':sha(p)} for p in files],'independent_audits':[{'path':str(p),'sha256':sha(p)} for p in audits],'aggregate_certification_claimed':False})
save(V/'si-chunk-dependencies.json',{'schema':'mattersyn.private_si_dependencies.v1','source_id':SID,'source_sha256':I['source_documents']['si']['sha256'],'chunks':SI,'preserved_uncertainties':['SI page 11 right row 35 Fobs²: magnitude 1965.46; signed value unresolved.','SI page 12 left row 12 Fcal²: magnitude 3757.09; signed value unresolved.'],'scope':'Dependency snapshot only. No aggregate table, CIF or exact-structure admission is created.'})

# The existing reader renderer expects actual asset objects, not unresolved ID strings.
for it in ITEMS.values():
    it['original_assets']=[{'id':aid,'label':next(a['label'] for a in ASSETS if a['id']==aid),'public_asset':next(a['public_asset'] for a in ASSETS if a['id']==aid),'public_asset_sha256':ASSET_MAP[aid]['sha256'],'private_asset':ASSET_MAP[aid]['path'],'reviewed':False} for aid in it['original_assets']]

reader={'schema_version':'1.3','paper_id':SID,'doi':I['doi'],'title':I['title'],'paper':{k:I[k] for k in ['authors','journal','year','volume','issue','pages','published_online']},'source_group':SID,'corpus_paper_id':None,'corpus_document_id':None,'corpus_document_ids':[],'review_scope':'private_main_and_matched_si_proposal','supporting_information':'Matched 14-page reflection list. All separately audited numerical chunks are linked; whole-SI reconciliation is not certified by this proposal. Two unresolved signs remain.','documents':[{'role':role,'filename':d['filename'],'sha256':d['sha256'],'page_count':d['page_count']} for role,d in I['source_documents'].items()],'document_identity_verification':{'status':'reuse_of_hash_verified_intake','source_bundle_generation':2,'source_hashes':source_hashes},'coverage_status':{'main':'Audited extraction reused; canonical and reader audit pending.','si':'Individual numerical chunks retained; aggregate certification separate.'},'independent_audit':{'status':'pending','note':'This is an authoring proposal, not an independent audit.'},'publication_status':'private_proposal','source_review_promoted':False,'training_eligible':False,'training_note':'All requested_tasks are empty. No exact atomic or DFT structure is admitted.','recipe_inventory':[{'id':r['record_id'],'label':r['title'],'record_ids':[r['record_id']],'record_type':r['record_type'],'status':'private_canonical_and_reader_audit_pending','scope':PLAN['candidate_scopes'][n]['boundary'],'gaps':r['quality']['missing_fields'],'canonical_draft_present':True} for n,r in enumerate(RECORDS.values())],'characterization_inventory':['Single-crystal X-ray diffraction','EPXMA/EDS','XPS and argon depth profiling'],'chemical_intuition':'Author-proposed disproportionation, cluster charge and charge-compensation hypotheses are separated from measured evidence.','reader_contract':{'version':'1.0','section_ids':list(SECTIONS),'item_fields':['id','title','text','claim_type','sample_scope','evidence','source_locators','canonical_links','notes','facts','training_eligible']},'reader_sections':list(SECTIONS.values()),'figures':[a for a in ASSETS if re.fullmatch('heo2003-figure-[1-7]',a['id'])],'tables':[a for a in ASSETS if 'main-table' in a['id']],'schemes':[],'equations':[{'id':'chemical-equation-'+str(n+1),'source_payload':b['source_payload'],'sample_links':[PREFIX+'charge-and-mechanism'],'interpretation_status':'author_hypothesis','training_eligible':False} for n,b in enumerate(EQUATION_BIND)],'source_notes':[a for a in ASSETS if not re.fullmatch('heo2003-figure-[1-7]',a['id']) and 'main-table' not in a['id']],'referenced_methods':[{'reference_number':z['number'],'citation':z['raw_bibliographic_text'],'external_full_text_inspected':False} for z in I['references']],'remaining_gaps':GAPS,'evidence_conflicts':I['evidence_conflicts'],'record_formulation_labels':{r['record_id']:r['title'] for r in RECORDS.values()},'record_formulation_scope_note':SCOPE_LIMIT,'material_evidence_records':{FORMULA:[r['record_id'] for r in RECORDS.values()]},'material_evidence_scope_notes':{FORMULA:'One zeolite-hosted indium route. Reference spectra, alternative refinements, formal ionic radii and mechanism hypotheses remain explicitly contextual.'},'material_original_asset_ids':{FORMULA:[a['id'] for a in ASSETS]},'material_asset_scope_note':'Main figures include copied reference data and structural drawings; none is TEM or SAED. Original captions and scopes must remain visible.','route_evidence_contexts':{PREFIX+'in66-route':'One source route with unresolved prose/Table 1 conditions; characterization and model evidence are contextual. No alternative conditions have been independently selected.'},'presentation_gates':{'canonical_source_audit':False,'reader_source_audit':False,'molecular_bindings':False,'apparatus_bindings':False,'atomic_structure_binding':False,'browser_render':False,'site_integration':False},'counts':{}}
reader['review_scope']='supplied_main_and_matched_si'
reader['review_state']='private_canonical_and_reader_proposal_pending_independent_review'
reader['supporting_information']='Matched 14-page reflection list. A separate independent aggregate audit reconciles 1209 rows from all seven independently read page-pair chunks. Two source signs remain unresolved. This proposal reuses the audit; it does not independently certify the aggregate or derive coordinates.'
reader['coverage_status']['si']='Matched SI and independently audited aggregate, with two preserved sign uncertainties; external audit authority is hash-bound.'
reader['si_aggregate_evidence']={'audit_path':'../../source-payloads/si-complete-candidate/independent-audit.json','audit_sha256':input_hashes['si-complete-candidate/independent-audit.json'],'original_freeze_sha256':input_hashes['si-complete-candidate/package-freeze.json'],'counts':AGG['counts'],'independent_auditor':AGG['auditor'],'author_recertification':False}
PC=load(H/'page-coverage.json')
for d in reader['documents']:
    orig=next(x for x in PC['documents'] if x['role']==d['role'])
    d['pages']=[{'page':p['pdf_page'],'printed_page':1119+p['pdf_page'] if d['role']=='main' else 40+p['pdf_page'],'text_read':True,'visual_review':True,'review_basis':'Inherited from the separately audited main extraction and frozen page coverage.' if d['role']=='main' else 'Native scan cells independently read in the page-pair audit; the separate complete aggregate audit reconciles those fixed chunks. This authoring pass does not claim a fresh independent reread.'} for p in orig['pages']]
conflict_texts=[
'The experimental prose gives both dehydration stages as 623 K for 48 h at 10⁻⁶ Torr, while Table 1 gives 673 K for 3 days. Indium contact is 96 h in the prose and 5 days in Table 1. These discrepancies remain unresolved within one study.',
'The nominal framework is Si100Al92, whereas the averaged Table 2 model corresponds to 96 Si and 96 Al. The two representations are preserved separately; neither composition is silently substituted for the other.',
'The proposed indium charge model provides 83 positive charges against 92 negative framework charges. Oxygen loss and proton compensation are hypotheses, not measured defects or atom positions.',
'Figure 1B reproduces a parent In87-X spectrum from reference 34. Figure 2A scales the indium-metal intensity to one twentieth. These references and display conventions remain distinct from current-product measurements.',
'The Figure 3 caption gives approximately 10 s sputter intervals at 0.6 Å/s, while the prose mentions an approximately 4300 Å depth. The displayed cycle sequence does not establish the full sputtering history.',
'The reported data/parameter ratios use the strong-reflection counts numerically, while the table heading and footnote define the numerator using all unique reflections. The printed ratios and both count definitions are retained.',
'One subsection heading refers to sites I′ and II′, while the body and final table place the minor In(IIa) population at site II. The exact atom labels are retained without silently correcting the heading.'
]
for n,text in enumerate(conflict_texts):ITEMS['inventory-evidence_conflicts-'+str(n)]['text']=text
figure_texts={
1:'EPXMA/EDS spectra compare the current H2S-treated In66-X crystal in panel A with a parent In87-X spectrum copied from reference 34 in panel B. The detector/window context and elemental line assignments are retained; the figure is not a powder diffraction pattern.',
2:'Indium 3d XPS compares an indium-metal reference (A), the current In66-X crystal (B) and an In87-X parent comparison (C). The metal trace is displayed at one twentieth of its original intensity. The figure does not imply identical specimens across the three panels.',
3:'The XPS depth-profile sequence belongs to the current treated crystal. The caption reports approximately 10 s sputter intervals at 0.6 Å/s; the separate approximately 4300 Å prose depth cannot be reconstructed from the supplied displayed sequence.',
4:'The source illustrates the zeolite-X framework and conventional extraframework site labels. This is a topology schematic, not evidence of long-range Si/Al ordering in the treated crystal.',
5:'The supercage stereoview illustrates the refined average model with 50% displacement ellipsoids and partial indium-site populations. It is not a TEM image or a uniquely ordered local configuration.',
6:'The source shows the modeled sodalite-centered In5 cluster and its coordination. The centered-tetrahedron geometry comes from the refinement; the proposed 7+ charge is a chemical interpretation.',
7:'The stereoview shows two adjacent sodalite cages within the average structural model. The cluster-center arrangement is model-based and is not a direct real-space microscopy image.'
}
panels={1:[('A','epxma-acquisition','final','Current H2S-treated In66-X'),('B','epxma-acquisition','parent-reference-context','Parent In87-X spectrum copied from reference 34')],2:[('A','xps-acquisition','indium-reference','Indium-metal reference; displayed intensity multiplied by 1/20'),('B','xps-acquisition','final','Current In66-X'),('C','xps-acquisition','parent-reference-context','Parent In87-X comparison')],3:[('profile','xps-acquisition','final','Current product; total sputter history unresolved')],4:[('schematic','framework-topology','topology-context','Host topology/site convention; no measured ordered Si/Al arrangement')],5:[('stereoview','average-structure','average-model','Partial-site supercage model; 50% displacement ellipsoids')],6:[('stereoview','average-structure','average-model','Sodalite-centered In5 model; proposed cluster charge is interpretive')],7:[('stereoview','average-structure','average-model','Adjacent cages in the average structure; not microscopy')]}
for a in reader['figures']:
    num=int(a['id'].rsplit('-',1)[1]);a['panels']=[];a['canonical_sample_links']=[]
    a['caption_paraphrase']=figure_texts[num];a['sample_scope']=figure_texts[num];ITEMS['asset-'+a['id']]['text']=figure_texts[num]
    for label,key,sid,scope in panels[num]:
        rr=RECORDS[key];pi=next(n for n,p in enumerate(rr['products']) if p['sample_id']==sid)
        lk={'record_id':rr['record_id'],'sample_id':sid,'json_pointer':f'/products/{pi}','relation':scope}
        a['canonical_sample_links'].append(lk);a['panels'].append({'label':label,'scope':scope,'canonical_sample_links':[lk]})
        ITEMS['asset-'+a['id']]['canonical_links'].append(lk)
aggregate_payload=load(H/'si-complete-candidate/all-reflections.json')
si_rows=[{'source_row_id':z['row_id'],'source_file':'si-complete-candidate/all-reflections.json','source_json_pointer':f'/rows/{n}','source_hkl':z['hkl'],'cell_ids':[c['cell_id'] for c in z['cells']],'reader_item_id':'inventory-supporting_tables-0','canonical_context_record_id':PREFIX+'refinement-comparison','mapping_role':'Supporting reflection data for source-defined In66-X; no per-row synthesis sample or exact-coordinate training label.'} for n,z in enumerate(aggregate_payload['rows'])]
save(V/'si-row-coverage.json',{'schema':'mattersyn.private_si_row_coverage.v1','source_sha256':input_hashes['si-complete-candidate/all-reflections.json'],'independent_aggregate_audit_sha256':input_hashes['si-complete-candidate/independent-audit.json'],'counts':AGG['counts'],'rows':si_rows,'exact_payload':'source-payloads/si-complete-candidate/all-reflections.json','unresolved_cells':aggregate_payload['unresolved_cells']})
unit('si-aggregate-reflections','si-complete-candidate/all-reflections.json','',['inventory-supporting_tables-0'],[],{'exact_payload_path':'source-payloads/si-complete-candidate/all-reflections.json','counts':AGG['counts'],'row_coverage_sidecar':'si-row-coverage.json'},'exact_scan_transcription_sidecar_with_separate_independent_audit')
counts={'records':len(RECORDS),'routes':sum(r['record_type']=='literature_protocol' for r in RECORDS.values()),'procedures':sum(r['record_type']=='procedure' for r in RECORDS.values()),'observations':sum(r['record_type']=='observation' for r in RECORDS.values()),'operations':sum(len(r['operations']) for r in RECORDS.values()),'measurements':sum(len(r['measurements']) for r in RECORDS.values()),'materials':sum(len(r['materials']) for r in RECORDS.values()),'stocks':sum(len(r['stocks']) for r in RECORDS.values()),'products_and_contexts':sum(len(r['products']) for r in RECORDS.values()),'source_facts':len(FACT_BIND),'source_units':len(UNIT_ROWS),'table_quantities':len(TABLE_BIND),'table_numeric_values':sum(b['source_quantity']['value'] is not None for b in TABLE_BIND),'table_blank_quantity_objects':sum(b['source_quantity']['value'] is None for b in TABLE_BIND),'main_tables':5,'main_figures':7,'chemical_equations':8,'references':71,'si_reflection_rows':len(si_rows),'original_assets':len(ASSETS),'reader_items':len(ITEMS),'reader_typed_facts':len(TYPED_BIND),'training_eligible_records':0}
reader['counts']=counts
save(PDIR/'heo2003.json',reader)
save(V/'source-fact-coverage.json',{'schema':'mattersyn.private_source_fact_coverage.v1','source_sha256':input_hashes['source-facts.json'],'bindings':FACT_BIND})
save(V/'table-field-coverage.json',{'schema':'mattersyn.private_table_coverage.v1','source_sha256':input_hashes['main-tables.json'],'quantity_bindings':TABLE_BIND,'rows':TABLE_ROWS,'exact_payload_path':'source-payloads/main-tables.json','scope':'All printed rows, blanks, footnotes, scales, uncertainties and conflicts remain in the exact table payload. Canonical quantities are not a CIF.'})
save(V/'source-inventory-coverage.json',{'schema':'mattersyn.private_source_inventory_coverage.v1','source_hashes':input_hashes,'units':UNIT_ROWS,'operation_bindings':OP_BIND,'equation_bindings':EQUATION_BIND,'reference_bindings':REFERENCE_BIND})
save(PDIR/'source-item-coverage.json',{'schema':'mattersyn.source_item_coverage.v1','source_id':SID,'units':UNIT_ROWS,'source_inventory_sha256':input_hashes['source-inventory.json']})
save(PDIR/'canonical-measurement-coverage.json',{'schema':'mattersyn.private_canonical_reader_binding.v1','bindings':TYPED_BIND,'canonical_hashes':{r['record_id']:sha(RDIR/(r['record_id']+'.json')) for r in RECORDS.values()}})
save(PDIR/'reader-original-assets-manifest.json',{'schema':'mattersyn.private_original_assets.v1','assets':ASSET_MAP,'source_files_unchanged':True,'integration_approved':False})

# Author validation: exact values and source coverage, not independent science approval.
checks=[]
def ck(name,result):checks.append({'check':name,'passed':bool(result)});assert result,name
for r in RECORDS.values():
    ck(r['record_id']+' schema and semantic validation',not validate_record(r));ck(r['record_id']+' no training eligibility',not any(z['eligible'] for z in eligibility(r).values()))
    ck(r['record_id']+' private status',r['quality']['review_status']=='imported_unreviewed' and not r['quality']['requested_tasks'] and not r['structure_assets'])
for b in FACT_BIND:
    ck(b['source_fact_id']+' payload exact',pointer(F,b['json_pointer'])==b['source_payload'])
    for lk in b['canonical_links']:
        r=next(r for r in RECORDS.values() if r['record_id']==lk['record_id']);q=pointer(r,lk['json_pointer']);sv=pointer(F,lk['source_value_pointer'])
        if isinstance(sv,(int,float)):ck(lk['record_id']+lk['json_pointer']+' exact scalar',q['value']==sv)
        elif isinstance(sv,str) and re.fullmatch(r'[−-]?\d+(?:\.\d+)?\(\d+\)',sv):ck(lk['record_id']+lk['json_pointer']+' ESD raw token',q['raw_text']==sv)
        else:ck(lk['record_id']+lk['json_pointer']+' exact categorical',q['value']==sv)
for b in TABLE_BIND:
    ck(b['source_quantity_pointer']+' exact table object',pointer(T,b['source_quantity_pointer'])==b['source_quantity']);r=next(r for r in RECORDS.values() if r['record_id']==b['record_id']);ck(b['source_quantity_pointer']+' normalized scalar unchanged',pointer(r,b['json_pointer'])['value']==b['source_quantity']['value'])
for b in TYPED_BIND:
    r=next(r for r in RECORDS.values() if r['record_id']==b['record_id']);ck(b['item_id']+b['json_pointer']+' reader exact canonical object',pointer(r,b['json_pointer'])==b['canonical_quantity'])
for u in UNIT_ROWS:
    ck(u['source_unit_id']+' reachable reader',bool(u['item_ids']) and all(i in ITEMS for i in u['item_ids']))
for n,h in input_hashes.items():ck(n+' unchanged',sha(H/n)==h)
for n in inputs:
    if n.endswith('.json'):ck(n+' exact source-payload copy',load(DDIR/n)==load(H/n))
    elif n.endswith('.tsv'):ck(n+' byte-identical table payload',sha(DDIR/n)==sha(H/n))
ck('all source-unit identifiers unique',len(UNIT_ROWS)==len({x['source_unit_id'] for x in UNIT_ROWS}))
ck('all reader-item identifiers unique',len(ITEMS)==sum(len(s['items']) for s in SECTIONS.values()))
for a in reader['figures']:
    for lk in a['canonical_sample_links']:
        rr=next(r for r in RECORDS.values() if r['record_id']==lk['record_id']);ck(a['id']+lk['sample_id']+' explicit panel context',pointer(rr,lk['json_pointer'])['sample_id']==lk['sample_id'])
ck('exact114 source facts',len(FACT_BIND)==114);ck('one synthesis route',counts['routes']==1);ck('eight proposed chemical equations',len(EQUATION_BIND)==8);ck('all71 bibliographic entries',len(REFERENCE_BIND)==71)
ck('all209 table quantity objects including11 source blanks',len(TABLE_BIND)==209 and sum(b['source_quantity']['value'] is None for b in TABLE_BIND)==11)
ck('seven SI chunk dependency entries',len(SI)==7)
ck('all seven SI chunks have a frozen manifest or checkpoint and a separate audit',all(x['chunk_manifests'] and x['independent_audits'] for x in SI))
ck('all1209 SI reflection rows mapped without reinterpretation',len(si_rows)==1209 and len(set(z['source_row_id'] for z in si_rows))==1209)
ck('all raw table row objects covered',len(TABLE_ROWS)==sum(1 for t in T['tables'] for _ in table_rows(t)))
for r in RECORDS.values():
    for st in r['material_states']:ck(r['record_id']+'/'+st['id']+' vessel excluded from lineage','pyrex' not in st['parent_ids'])
# Run the actual Site reader validator against an isolated private projection.
# No shared Site data/module is changed and no public review status is promoted.
import build_paper_reviews as current_reader_builder
PROJ=V/'reader-compatibility-projection'
for a in ASSETS:
    dst=PROJ/'dist'/a['public_asset'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a['private_asset'],dst)
for r in RECORDS.values():savepath=PROJ/'data/records'/(r['record_id']+'.json');savepath.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(RDIR/(r['record_id']+'.json'),savepath)
old_root=current_reader_builder.ROOT
try:
    current_reader_builder.ROOT=PROJ
    reader_errors=current_reader_builder.validate(reader)
finally:current_reader_builder.ROOT=old_root
ck('actual Site full-paper reader validator, private projection only',not reader_errors)
save(V/'reader-compatibility-check.json',{'schema':'mattersyn.private_reader_compatibility.v1','status':'passed' if not reader_errors else 'failed','errors':reader_errors,'validator_path':str(S/'scripts/build_paper_reviews.py'),'validator_sha256':sha(S/'scripts/build_paper_reviews.py'),'reader_sha256':sha(PDIR/'heo2003.json'),'projection_path':str(PROJ),'limits':['Structural validation and exact private original-asset hashes only. This does not approve scientific mappings, visuals, browser rendering or publication.','Reader review_scope describes the supplied-document coverage reused from independent source audits; the canonical/reader proposal itself remains unreviewed.']})
validation={'schema':'mattersyn.private_proposal_author_validation.v1','status':'passed_author_checks_pending_independent_review','author':'/root/peng1998_reader_assets','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'counts':counts,'check_count':len(checks),'failures':[],'checks':checks,'schema_path':str(S/'dist/data/record.schema.json'),'schema_sha256':sha(S/'dist/data/record.schema.json'),'source_hashes':source_hashes,'bound_input_files':input_hashes,'limits':['Checks establish internal source-pointer consistency and schema conformance; they are not independent scientific review.','Actual page-by-page source inspections, numerical chunk audits and the passed SI aggregate audit are separately documented frozen inputs.','Exact-structure/CIF qualification, visual bindings, browser validation, training and publication remain separate gates.']}
save(PDIR/'proposal-validation.json',validation)
save(V/'canonical-record-manifest.json',{'schema':'mattersyn.private_canonical_manifest.v1','source_id':SID,'version':1,'status':'draft_pending_independent_canonical_review','counts':counts,'record_hashes':{r['record_id']:sha(RDIR/(r['record_id']+'.json')) for r in RECORDS.values()},'records':[{'record_id':r['record_id'],'record_type':r['record_type'],'path':str(RDIR/(r['record_id']+'.json')),'operation_ids':[o['id'] for o in r['operations']],'material_ids':[m['id'] for m in r['materials']],'sample_ids':[p['sample_id'] for p in r['products']]} for r in RECORDS.values()]})
readme='''# Heo 2003 private canonical and reader proposal\n\nOne source route is represented by nine preparation/treatment operations. Three analytical procedures are separate, and six observation/context records preserve average refinement, model comparisons, ionic radii, host topology, mechanisms and external references. Prose/Table 1 discrepancies remain unresolved rather than becoming extra recipes.\n\nThe five main tables are preserved in exact, hash-bound payloads, including blank cells, uncertainty tokens, literal tensor column order, scale factors, fixed/varied counts and footnotes. The canonical scalar schema cannot natively encode crystallographic estimated standard deviations, tensor conventions or all raw table metadata; these remain in the sidecars and display qualifiers. Occupancy counts are not normalized into an ordered atomistic model.\n\nAll 114 source facts, original figures, 71 references and eight proposed chemical equations are linked. SI page-pair dependencies retain their separate audits and the two unresolved signs. This proposal does not assert aggregate SI certification and does not bind the separately prepared average CIF. No training tasks, structure assets, publication or visual-binding approvals are enabled.\n\nThis is an authoring proposal. A distinct reviewer must audit the canonical and reader mappings before any promotion. Source extraction, prior audits, source images and SI chunks were not modified.\n'''
(V/'README.md').write_text(readme,encoding='utf-8')
with (V/'README.md').open('a',encoding='utf-8') as out:
    out.write('\nThe separately passed SI aggregate audit is now included as an external hash-bound dependency: 1209 reflection rows, 7254 numeric positions, 7252 resolved signed values and two unresolved signs. The earlier planning snapshot is preserved unchanged; it is not the current SI status authority. The original aggregate payload may retain a pre-audit author flag, so the independent audit file and its exact freeze binding provide the status authority.\n\nThe current Site reader validator passes against an isolated private projection. Corpus IDs, source-specific molecular/apparatus bindings, average-CIF qualification, removal of private provenance paths from any eventual public export, final reader scientific audit and browser QA are still required before integration. The renderer does not yet provide an interactive crystallographic reflection-table widget; exact raw SI data and every original page remain available in the proposed sidecars and source links.\n')
save(V/'schema-gaps.json',{'schema':'mattersyn.private_schema_gap_report.v1','source_id':SID,'gaps':[{'topic':'Crystallographic table semantics','preservation':'Exact raw cells, source blank values, uncertainties, fixed/varied occupancies, scale factors, literal U-column order and mathematical footnotes remain in main-tables.json and table-field-coverage.json. Scalar schema fields retain values plus explicit qualifiers.','not_performed':'No unique ordered atomic structure or DFT-ready transformation.'},{'topic':'Conflicting process conditions','preservation':'Primary operation quantities remain unresolved, and both printed versions are retained in operation descriptions and explicitly conflict-labeled condition_options.','not_performed':'No source version selected and no extra route created.'},{'topic':'Reflection-table display','preservation':'Exact all-reflections JSON/TSV and source-page images are retained with separate passed aggregate audit and cell locators; all1209 row mappings are enumerated.','not_performed':'No interactive reflection-table component, symmetry expansion, negative-intensity clipping, sign imputation or coordinate inference.'},{'topic':'Promotion and viewer binding','preservation':'All record tasks empty, imported_unreviewed; all viewer/browser/publication approvals false.','not_performed':'No public paths/private provenance sanitization, corpus ID activation, molecule/apparatus/CIF approval or Site modification.'}]})
files={str(p.relative_to(V)):sha(p) for p in sorted(V.rglob('*')) if p.is_file() and p.name!='proposal-package-manifest.json'}
save(V/'proposal-package-manifest.json',{'schema':'mattersyn.private_proposal_package.v1','version':1,'source_id':SID,'author':'/root/peng1998_reader_assets','status':'frozen_author_proposal_pending_independent_review','counts':counts,'files':files,'external_input_hashes':input_hashes,'builder_sha256':sha(__file__)})
print(json.dumps({'status':validation['status'],'counts':counts,'check_count':len(checks),'manifest_sha256':sha(V/'proposal-package-manifest.json'),'reader_sha256':sha(PDIR/'heo2003.json')},indent=2))
