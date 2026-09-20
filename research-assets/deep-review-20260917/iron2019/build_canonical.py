"""Source-grounded authoring; writes only the assigned research directory."""
import json,sys,copy
from pathlib import Path
sys.dont_write_bytecode=True
OUT=Path(__file__).parent
BASE=OUT.parents[2]
SITE=BASE/'recipe-atlas'
sys.path.insert(0,str(SITE/'scripts'))
from record_helpers import ev,fact,qty,source,record,material,operation,product,state,measurement
SID='feld2019'
DOI='10.1021/acsnano.8b05032'
TITLE='Chemistry of Shape-Controlled Iron Oxide Nanocrystal Formation'
AUTHORS='Artur Feld; Agnes Weimer; Andreas Kornowski; Naomi Winckelmans; Jan-Philip Merkl; Hauke Kloust; Robert Zierold; Christian Schmidtke; Theo Schotten; Maria Riedner; Sara Bals; Horst Weller'
SRC=source(SID,DOI,TITLE,AUTHORS,2019,si='All 19 pages read in full and visually reviewed; title/authors match the 11-page main article and its Associated Content statement.')
SRC['main_status']='All 11 pages read in full and visually reviewed, including all figures, methods and references. Online publication 12 December 2018; journal year 2019.'
def E(loc):return ev(SID,loc)
G=E('Main PDF p.8 (printed p.159), Materials and Synthesis of the Iron Sources')
T=E('Main PDF p.9 (printed p.160), Nanocrystal Synthesis; SI p.5 Figure S5')
P=E('Main PDF pp.4-7 (printed pp.155-158), Figures 3c,6,7; SI pp.9-10 Figure S12')
def Q(v=None,u='',e=None,**kw):return qty(v,u,e or G,**kw)
def F(v=None,e=None,**kw):return fact(v,e or G,**kw)
def base(rid,title,kind='protocol_variant',formula='Fe–O',family='Iron oxides',loc='Main Methods pp.159-160 and SI section 8'):
    r=record(rid,title,formula,family,'Thermal decomposition of carbonate-derived iron oleate',SRC,loc,kind)
    r['collection']='reviewed_literature';r['material'].update(elements=['Fe','O'] if formula=='Fe–O' else ['Fe','C','H','O'],components=[formula],architecture='unresolved')
    r['lineage']['recipe_family']='feld2019-iron-carbonate-oleate-thermolysis'
    r['intended_target']['composition']=F(formula,E(loc),note='Elemental system only; a unique molecular or nanocrystal stoichiometry is not asserted.')
    r['intended_target']['phase']=F(e=E(loc),note='No uniquely specified final isolated phase.')
    r['quality']['review_scope']='Complete 11-page main and 19-page matching SI review. Literature protocols/condition families only; no physical batch or independent replication is invented. Numeric image labels retain their original dimensional meaning.'
    r['context_links']=[{'label':'Primary article and associated SI','url':'https://doi.org/'+DOI,'relation':'primary_source'}]
    return r
def save(r):
    d=OUT/'canonical';d.mkdir(exist_ok=True)
    (d/(r['record_id']+'.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    return r
def op(r,i,a,label,e,ins,outs,params=None,desc='',stage='synthesis',env='nitrogen / Schlenk',ret=None,endpoint=None,depends=None):
    deps=depends if depends is not None else ([r['operations'][-1]['id']] if r['operations'] else [])
    r['operations'].append(operation(i,a,label,e,ins,outs,deps,params or {},stage=stage,description=desc,environment=F(env,e),retained_fraction=ret,endpoint=endpoint or F(e=e)))
def st(r,i,name,parents,kind='mixture'):r['material_states'].append(state(i,name,parents,kind))

def precursor(valence):
    iii=valence==3;roman='III' if iii else 'II';tag='ferric' if iii else 'ferrous'
    rid=f'feld-2019-fe{valence}-carbonate-to-oleate-preparation'
    C=E('Main PDF p.9 (printed p.160), Synthesis of Fe2(CO3)3–Iron(III) Source; SI pp.2-3 eq2/Figure S2' if iii else 'Main PDF p.8 (printed p.159), Synthesis of FeCO3–Iron(II) Source; SI p.2 eq1/Figure S1')
    O=E(f'Main PDF p.9 (printed p.160), Synthesis of Fe({roman}) Oleate; SI '+('pp.4-5 eq4-6/Figure S4' if iii else 'pp.3-4 eq3/Figure S3'))
    r=base(rid,f'Fe({roman}) source: aqueous carbonate precipitation and oleate preparation','procedure','Fe–C–H–O','Iron oleate precursor mixtures')
    r['method']=f'Prepare carbonate-derived Fe({roman})-source oleate mixture'
    r['quality']['requested_tasks']=['partial_protocol']
    r['materials']=[material('iron-sulfate',f'iron({roman}) sulfate '+('hydrate' if iii else 'heptahydrate'),'Fe2(SO4)3·H2O' if iii else 'FeSO4·7H2O','metal_source','precursor_preparation',C,notes=['Main prints monohydrate; SI eq2 uses xH2O; hydration state and mass/mmol conflict unresolved. 97%, Sigma-Aldrich.' if iii else '99%, Sigma-Aldrich.','Degassed and stored under nitrogen.']),material('sodium-carbonate','sodium carbonate','Na2CO3','precipitating_reagent','precursor_preparation',G,notes=['99.95–100.05% dry basis, Sigma-Aldrich; degassed and stored under nitrogen.']),material('water','Milli-Q water','H2O','solvent','precursor_preparation',G,notes=['18.2 MOhm/cm as printed; nitrogen saturated for 24 h.']),material('nitrogen','nitrogen','N2','protective_gas','precursor_preparation',G),material('prepared-carbonate',f'prepared iron({roman}) carbonate source',None if iii else 'FeCO3','precursor_intermediate','precursor_preparation',C,notes=['Mixture: CO2 assay gives 16% nominal Fe2(CO3)3; remainder probably Fe(OH)3/FeO(OH). Percentage basis not specified.' if iii else 'Wet precipitate used directly.','No recovered dry mass or yield reported; do not equate this preparation batch with the later charged mass.']),material('oleic-acid','oleic acid','C18H34O2','ligand_and_reaction_medium','precursor_preparation',G,notes=['Technical 90% Sigma-Aldrich and pure 99% TCI are listed. Pure OA is explicitly specified for analytical MALDI reactions; selected nanocrystal conditions are not grade/lot assigned.'])]
    salt=(15.90,39.76) if iii else (14.30,51.44);soda=(13.60,128.3) if iii else (16.40,157.7);carbonate=(11.6,39.8) if iii else (5.69,51.4);oa=(158.5,561.2) if iii else (102.4,362.4)
    def stock(i,name,comps,preps,scope,e):r['stocks'].append({'id':i,'name':name,'components':[{'material_id':m,'quantities':q} for m,q in comps],'concentrations':{},'preparation_operation_ids':preps,'scope':scope,'evidence':e})
    stock('sulfate-solution',f'Fe({roman}) sulfate aqueous solution',[('iron-sulfate',{'mass':Q(salt[0],'g',C),'amount':Q(salt[1],'mmol',C,qualifier='Source values retained; hydration basis unresolved.' if iii else '')}),('water',{'volume':Q(180,'mL',C)})],['dissolve-sulfate'],'Carbonate precursor preparation only.',C)
    stock('carbonate-solution','Sodium carbonate aqueous solution',[('sodium-carbonate',{'mass':Q(soda[0],'g',C),'amount':Q(soda[1],'mmol',C,qualifier='As printed; mass/mmol conflict.' if not iii else '')}),('water',{'volume':Q(180,'mL',C)})],['dissolve-carbonate'],'Carbonate precursor preparation only.',C)
    stock('prepared-oleate-stock',f'Fe({roman})-source oleate in excess oleic acid',[('prepared-carbonate',{'mass':Q(carbonate[0],'g',O),'amount':Q(carbonate[1],'mmol',O,qualifier='Nominal carbonate amount as printed; actual composition unresolved.' if iii else 'As printed; mass/mmol conflict.')}),('oleic-acid',{'mass':Q(oa[0],'g',O),'amount':Q(oa[1],'mmol',O)})],['mix-oleate','form-oleate','cool-oleate','age-oleate','dry60','dry120'],'Full quantified precursor preparation, not an assumed nanocrystal reactor charge; concentration/yield not supplied.',O)
    for i,n,parents,kind in [('conditioned-water','Nitrogen-saturated water',['water','nitrogen'],'mixture'),('conditioned-salts','Separately conditioned salts',['iron-sulfate','sodium-carbonate','nitrogen'],'mixture'),('degassed-oa','Degassed OA',['oleic-acid'],'mixture'),('conditioned-oa','Nitrogen-saturated OA',['degassed-oa','nitrogen'],'mixture'),('carbonate-slurry','Precipitation mixture',['sulfate-solution','carbonate-solution'],'mixture'),('wet-carbonate','Filtered carbonate source',['carbonate-slurry'],'fraction'),('mother-liquor','Filtrate',['carbonate-slurry'],'waste'),('washed-carbonate','Washed wet source',['wet-carbonate','conditioned-water'],'fraction'),('wash-waste','Wash filtrate',['wet-carbonate','conditioned-water'],'waste'),('oleate-charge','Carbonate/OA charge',['washed-carbonate','conditioned-oa'],'mixture'),('warm-oleate','60 C emulsion',['oleate-charge'],'mixture'),('cooled-oleate','Room-temperature emulsion',['warm-oleate'],'mixture'),('aged-oleate','24 h emulsion',['cooled-oleate'],'mixture'),('dried60','Partly dried oleate',['aged-oleate'],'mixture'),('oleate-product','Prepared oleate stock',['prepared-oleate-stock'],'product')]:st(r,i,n,parents,kind)
    def add(*args,**kw):kw['stage']='precursor_preparation';op(r,*args,**kw)
    add('condition-apparatus','evacuate_refill','Condition apparatus',G,['nitrogen'],[],{'cycles':Q(4,'count',G),'pressure':Q(u='mbar',e=G)})
    add('condition-water','gas_saturate','Nitrogen-saturate water',G,['water','nitrogen'],['conditioned-water'],{'duration':Q(24,'h',G),'gas_flow':Q(u='mL/min',e=G)})
    add('condition-salts','degas_store','Condition salts separately',G,['iron-sulfate','sodium-carbonate','nitrogen'],['conditioned-salts'],{'duration':Q(u='h',e=G)},desc='State groups separate conditioned reagent containers; salts are not mixed here.')
    add('degas-oa','degas','Degas oleic acid',G,['oleic-acid'],['degassed-oa'],{'temperature':Q(25,'degC',G),'duration':Q(1,'h',G),'pressure':Q(0.5,'mbar',G)},env='vacuum')
    add('saturate-oa','gas_saturate','Nitrogen-saturate oleic acid',G,['degassed-oa','nitrogen'],['conditioned-oa'],{'duration':Q(u='h',e=G)})
    # Replace the temporary grouped reagent state with two physically separate states.
    r['material_states']=[s for s in r['material_states'] if s['id']!='conditioned-salts']
    st(r,'conditioned-iron-sulfate','Separately conditioned iron sulfate',['iron-sulfate','nitrogen'])
    st(r,'conditioned-sodium-carbonate','Separately conditioned sodium carbonate',['sodium-carbonate','nitrogen'])
    next(o for o in r['operations'] if o['id']=='condition-salts')['outputs']=['conditioned-iron-sulfate','conditioned-sodium-carbonate']
    add('dissolve-sulfate','dissolve','Dissolve iron sulfate',C,['conditioned-iron-sulfate','conditioned-water'],['sulfate-solution'],desc='Dissolve iron sulfate in 180 mL water.')
    add('dissolve-carbonate','dissolve','Dissolve sodium carbonate',C,['conditioned-sodium-carbonate','conditioned-water'],['carbonate-solution'],desc='Dissolve sodium carbonate in a separate 180 mL portion of water.')
    add('precipitate','add_stir','Slowly add sulfate solution into carbonate solution',C,['sulfate-solution','carbonate-solution'],['carbonate-slurry'],{'duration':Q(30,'min',C),'stirring_speed':Q(800,'rpm',C),'temperature':Q(u='degC',e=C,qualifier='Room temperature.'),'addition_rate':Q(u='mL/min',e=C,qualifier='Slowly; no numeric rate.')})
    add('filter','filter','Filter through a Schlenk frit',C,['carbonate-slurry'],['wet-carbonate','mother-liquor'],ret='wet-carbonate')
    add('wash','wash','Wash four times with water',C,['wet-carbonate','conditioned-water'],['washed-carbonate','wash-waste'],{'wash_count':Q(4,'count',C),'wash_volume_each':Q(120,'mL',C)},desc='Keep wet precipitate; no drying or further purification.',ret='washed-carbonate')
    add('mix-oleate','mix','Mix reported carbonate charge and oleic acid',O,['washed-carbonate','conditioned-oa'],['oleate-charge'],{'oleic_acid_to_fe_molar_ratio':Q(7,'mol/mol',O,basis='Stated OA equivalents per Fe atom.'),'temperature':Q(u='degC',e=O,qualifier='Room temperature.')},desc='Quantities in prepared-oleate-stock; transferred fraction of preceding wet precipitation batch is not supplied.')
    add('form-oleate','heat_stir','Form oleate emulsion',O,['oleate-charge'],['warm-oleate'],{'temperature':Q(60,'degC',O),'duration':Q(1,'h',O),'stirring_speed':Q(u='rpm',e=O)})
    add('cool-oleate','cool','Cool to room temperature',O,['warm-oleate'],['cooled-oleate'],{'temperature':Q(u='degC',e=O,qualifier='Room temperature.'),'cooling_rate':Q(u='degC/min',e=O)})
    add('age-oleate','stir','Stir at room temperature',O,['cooled-oleate'],['aged-oleate'],{'duration':Q(24,'h',O),'temperature':Q(u='degC',e=O,qualifier='Room temperature.')},endpoint=F('reddish-brown emulsion after initially red coloration' if iii else 'milky gray emulsion',O))
    add('dry60','vacuum_heat','Remove water and CO2',O,['aged-oleate'],['dried60'],{'temperature':Q(60,'degC',O),'duration':Q(2,'h',O),'pressure':Q(u='mbar',e=O)},env='vacuum',endpoint=F('brownish-black mixture',O))
    add('dry120','vacuum_heat','Remove residual water',O,['dried60'],['prepared-oleate-stock'],{'temperature':Q(120,'degC',O),'duration':Q(u='h',e=O,minimum=1,maximum=2),'pressure':Q(u='mbar',e=O)},env='vacuum')
    p=product('prepared-oleate','Fe–C–H–O',O,link='explicit',state='oleate-product',notes=['Precursor mixture, not a nanocrystal. Source oxidation state denotes the starting source, not a pure-valence molecular product. Multiple Fe(II)/Fe(III) complexes observed by MALDI.','No single molecular formula or concentration assigned.'])
    p['source_sample_label']=f'Synthesis of Fe({roman}) Oleate (method heading; not a physical batch label)';r['products']=[p]
    r['quality']['experimental_outcome']='reported_product'
    r['condition_options']=[{'id':'reported-scale-up-capability','label':'Scale-up claim; no separately documented batch','parameters':{'scale_factor':Q(4 if iii else 7,'fold',O,basis='Same concentrations, larger volumes; capability claim only.')},'evidence':O}]
    r['quality']['missing_fields']=['Actual vacuum pressures during 60/120 C drying, numeric room temperature, addition rate, stirring speed in oleate stages.','Recovered carbonate wet/dry mass, preparation yield, fraction transferred to oleate preparation, stock final volume/concentration.','Exact grade/lot for each NC-associated oleate preparation and storage duration.','Single stock molecular composition and oxidation-state population are not established.']
    r['quality']['conflicts']=['15.90 g/39.76 mmol Fe2(SO4)3·H2O is inconsistent with the printed monohydrate; SI eq2 instead gives xH2O.','Prepared Fe(III) source is only 16% nominal carbonate by authors CO2 assay; its 39.8 mmol charge is a nominal formula-based amount, not verified pure carbonate.'] if iii else ['Na2CO3 16.40 g / 157.7 mmol is inconsistent for the anhydrous formula.','FeCO3 5.69 g / 51.4 mmol is inconsistent for the nominal formula.']
    return save(r)

COMMON_MISSING=['Exact Fe(II)-source versus Fe(III)-source oleate branch for the individual condition/figure specimen.','Oleate charge amount, final stock concentration, ODE/OA absolute volumes and nanocrystal reactor scale.','Selected sample quench, withdrawal aliquot amount, purification solvents/amounts/cycles, centrifugation conditions, yield and storage history.','Bound surface ligand identity/coverage, exact final atomic stoichiometry and quantitative phase fractions.','No measured sample coordinates/CIF; reported image size is not explicitly a diameter.']
COMMON_CONFLICTS=['Pristine inert sealed-capillary XRD supports wustite for Figure 3c samples; this does not establish phase purity of air-dried TEM or stored EELS specimens.','General Methods gives 330–350 C and a 3–5 h hold; early growth aliquots/condition windows are not automatically followed by that full hold.','Main Figure 3a uses 34 vol% ODE; SI dilution grid uses 30 vol%. They are distinct source conditions.']
GENID='feld-2019-iron-oleate-general-thermolysis'
def nc(rid,title,ode=None,ratio=7,generic=False):
    e=E('Main Methods pp.159–160; SI pp.11–15 section 8')
    r=base(rid,title,'literature_protocol' if generic else 'protocol_variant')
    if not generic:r['lineage']['parent_record_id']=GENID
    r['materials']=[material('iron-oleate','carbonate-derived iron oleate mixture',None,'metal_precursor','synthesis',T,notes=['Choose an Fe(II)-source or Fe(III)-source upstream preparation; the source does not assign that choice to every figure. Multiple iron complexes are present, not a single molecular species.']),material('oleic-acid','oleic acid','C18H34O2','ligand_and_reaction_medium','synthesis',G,notes=['Already present in the precursor mixture; not an additional quantified charge. Technical 90% and pure 99% are listed; specimen-specific grade unresolved.']),material('nitrogen','nitrogen','N2','protective_gas','synthesis',G)]
    if ode!=0:r['materials'].append(material('ode','1-octadecene','C18H36','diluent','synthesis',G,notes=['90%, Sigma-Aldrich. Optional in generic method; explicitly present in nonzero dilution variants.']))
    r['stocks']=[{'id':'iron-oleate-input','name':'Prepared iron oleate in oleic acid','components':[{'material_id':'iron-oleate','quantities':{'mass':Q(u='g',e=T)}},{'material_id':'oleic-acid','quantities':{'volume':Q(u='mL',e=T)}}],'concentrations':{},'preparation_operation_ids':[],'scope':'Prepared upstream using one of the two separately documented precursor procedures; charged fraction and source branch unspecified. This imported stock does not assert both alternatives were mixed.','evidence':T}]
    st(r,'reaction-charge','Unspecified amount of iron oleate and selected medium',['iron-oleate-input']+(['ode'] if ode not in (None,0) else []),'reaction_batch')
    st(r,'heated-reaction','Heated reaction mixture',['reaction-charge'],'reaction_batch')
    op(r,'condition-apparatus','evacuate_refill','Condition apparatus with nitrogen',G,['nitrogen'],[],{'cycles':Q(4,'count',G),'pressure':Q(u='mbar',e=G)},desc='Three-neck flask with Vigreux and distillation columns. Apparatus photo is illustrative of setup, not a calibrated batch volume.')
    if ode!=0:
        st(r,'degassed-ode','Degassed ODE',['ode']);st(r,'conditioned-ode','Nitrogen-saturated ODE',['degassed-ode','nitrogen'])
        op(r,'degas-ode','degas','Degas ODE before use',G,['ode'],['degassed-ode'],{'temperature':Q(25,'degC',G),'duration':Q(1,'h',G),'pressure':Q(0.5,'mbar',G)},env='vacuum',desc='Applies if ODE is used; precursor OA was conditioned in its upstream preparation.')
        r['operations'][-1]['optional']=generic
        op(r,'saturate-ode','gas_saturate','Nitrogen-saturate ODE',G,['degassed-ode','nitrogen'],['conditioned-ode'],{'duration':Q(u='h',e=G)});r['operations'][-1]['optional']=generic
    ins=['iron-oleate-input']+(['conditioned-ode'] if ode not in (None,0) else [])
    params={'stock_mass':Q(u='g',e=T),'stock_volume':Q(u='mL',e=T),'oleic_acid_to_fe_molar_ratio':Q(ratio,'mol/mol',e,basis='OA per Fe atom as reported') if ratio is not None else Q(u='mol/mol',e=e),'ode_volume_fraction':Q(ode,'vol%',e,qualifier='Explicit no ODE.' if ode==0 else '') if ode is not None else Q(u='vol%',e=e)}
    op(r,'charge','charge','Charge prepared oleate and selected diluent',e,ins,['reaction-charge'],params,desc='Nanocrystal charge is not the entire upstream precursor batch. Selection of Fe(II) or Fe(III) source is unresolved for figure-linked variants.')
    if generic:r['operations'][-1]['optional_inputs']=['conditioned-ode']
    op(r,'heat','heat','Heat toward nucleation',T,['reaction-charge'],['heated-reaction'],{'heating_rate':Q(6,'degC/min',T),'nucleation_temperature':Q(u='degC',e=T),'pressure':Q(u='mbar',e=T)},endpoint=F('nucleation',e))
    r['quality']['missing_fields']=list(COMMON_MISSING);r['quality']['conflicts']=list(COMMON_CONFLICTS)
    r['quality']['experimental_outcome']='reported_partial'
    if generic:
        st(r,'held-reaction','Generic high-temperature reaction endpoint',['heated-reaction'],'reaction_batch')
        op(r,'hold','heat_hold','Hold at the dilution-dependent plateau',T,['heated-reaction'],['held-reaction'],{'temperature':Q(u='degC',e=T,minimum=330,maximum=350),'duration':Q(u='h',e=T,minimum=3,maximum=5)},desc='Generic Methods range. Exact relationship of each plateau/duration to a specific figure is not reported.')
        r['condition_options']=[{'id':'feii-source','label':'Fe(II)-carbonate-derived oleate (alternative)','parameters':{},'evidence':E('Main p.160, Synthesis of Fe(II) Oleate')},{'id':'feiii-source','label':'Fe(III)-carbonate-derived oleate (alternative)','parameters':{},'evidence':E('Main p.160, Synthesis of Fe(III) Oleate')}]
    return r

records=[precursor(2),precursor(3)]
records.append(save(nc(GENID,'General carbonate-derived iron-oleate thermolysis; exact dilution unspecified',ode=None,ratio=None,generic=True)))
windows=[(2,6),(3,10),(5,15),(40,60)]
grid={0:[82,75,45,60],8:[45,38,37,40],30:[37,32,31,28],56:[21,22,21,23]}
for ode,sizes in grid.items():
    rid='feld-2019-iron-oxide-undiluted-cubic-condition' if ode==0 else f'feld-2019-iron-oxide-ode{ode}-growth-family'
    r=nc(rid,('Undiluted iron oxide: cubic condition and related growth observations' if ode==0 else f'Iron oxide shape-evolution family: {ode} vol% ODE, Fe:OA 1:7'),ode)
    if ode==0:r['revision']=2
    CE=E(f'SI pp.11–14, Figure S14 {"no ODE" if ode==0 else str(ode)+" vol% ODE"} row; Figures S15–S16 corresponding time windows')
    r['operations'][-2]['parameters']['ode_volume_fraction']=Q(ode,'vol%',CE,qualifier='Explicit no ODE.' if ode==0 else '')
    st(r,'growth-series','Growth-condition family; sampling details unspecified',['heated-reaction'],'reaction_batch')
    op(r,'growth','grow_and_sample','Observe morphology across post-nucleation windows',CE,['heated-reaction'],['growth-series'],{'temperature':Q(u='degC',e=CE),'sampling_volume':Q(u='mL',e=CE)},desc='Condition-map windows are observations, not four invented independent batches. Exact sample withdrawal/quench protocol and run identity are not specified.')
    for k,((lo,hi),sz) in enumerate(zip(windows,sizes),1):
        fig='S15' if k==1 else 'S16' if k==4 else 'S14'
        qe=E(f'SI p.12 Figure S14, {ode} vol% ODE row, {lo}–{hi} min column'+('; SI p.'+('13' if k==1 else '14')+' Figure '+fig if k in (1,4) else ''))
        r['condition_options'].append({'id':f'window-{k}','label':f'Observed post-nucleation window {lo}–{hi} min; related observations, not independent batch claims','parameters':{'time_after_nucleation':Q(u='min',e=qe,minimum=lo,maximum=hi)},'evidence':qe})
        p=product(f'condition-window-{k}','Fe–O',qe,link='general_context',notes=['Curator observation key, not an experimental batch ID. Reported condition linkage is explicit, but exact iron-source branch/stock/run identity is unknown.','S14 is a schematic summary; dimensional definition and measurement count are absent. No phase assignment transferred from other figures.'])
        p['source_sample_label']=f'Figure S14: {ode} vol% ODE, {lo}–{hi} min'+(f'; Figure {fig}: {sz} nm panel' if k in (1,4) else '')
        p['morphology']=F(['octapod-star shaped','evolving star-like (schematic)','truncated/smoothed star-like (schematic)','cubic shaped'][k-1],qe)
        p['phase']=F(e=P,note='Sample-specific phase unresolved; handling can induce oxidation.')
        r['products'].append(p);r['measurements'].append(measurement(f'window-{k}-size',p['sample_id'],'characteristic_size',Q(sz,'nm',qe,qualifier='Source size label; diameter/edge/tip-to-tip definition and spread not supplied.'),'TEM / authors condition-map summary',qe,conditions=f'Fe:OA 1:7; {ode} vol% ODE; {lo}–{hi} min after nucleation.'))
    if ode==8:
        for k,(tm,temp) in enumerate([(0.5,331),(2,331),(8,339),(56,341)],1):
            e=E(f'Main p.158 Figure 8, phase {k} time/temperature label')
            r['condition_options'].append({'id':f'figure8-point-{k}','label':f'Figure 8 trajectory point {k}; separate from S14 interval summary','parameters':{'time_after_nucleation':Q(tm,'min',e),'temperature':Q(temp,'degC',e)},'evidence':e})
        e=E('SI p.15 Figure S18; main p.158 Figure 8')
        r['quality']['missing_fields'].append('Figure S18 additional 4,13,19 min aliquot temperatures; relationship of exact Figure 8/S18 trajectory to S14 grid specimens is not a physical-batch identifier.')
        for tm in [0.5,2,4,8,13,19,56]:
            p=product('s18-'+str(tm).replace('.','p'),'Fe–O',e,link='general_context',notes=['Timepoint observation from a source trajectory; no independent batch count. No quantitative size assigned.'])
            p['source_sample_label']=f'Figure S18 {tm} min column';r['products'].append(p)
            r['measurements'].append(measurement(p['sample_id']+'-time',p['sample_id'],'time_after_nucleation',Q(tm,'min',e),'TEM sampling series',e,conditions='8 vol% ODE, Fe:OA 1:7.'))
    r['quality']['experimental_outcome']='reported_product'
    r['quality']['missing_fields'].append('Exact growth temperature for each S14 condition; general range 330–350 C is not a sample-level setpoint.')
    records.append(save(r))

r=nc('feld-2019-iron-oxide-high-dilution-fe-oa-series','High-ODE cubic iron oxide family: Fe:OA stoichiometry series',ode=None,ratio=None)
e=E('SI p.14 text and p.15 Figure S17')
r['operations'][-2]['parameters']['ode_volume_fraction']=Q(u='vol%',e=e,qualifier='Greater than 66 vol%; exact value not reported (strict inequality not converted to a closed range).')
r['operations'][-2]['inputs'].append('conditioned-ode')
next(s for s in r['material_states'] if s['id']=='reaction-charge')['parent_ids'].append('conditioned-ode')
r['quality']['conflicts'].append('Main p.159 says highest ODE dilution of 66 vol% suppresses stars; SI p.14 states over 66 vol% for the Fe:OA series. Preserve strict-bound wording and do not equate the protocols.')
st(r,'cubic-series','Cubic products of independently varied Fe:OA conditions',['heated-reaction'],'reaction_batch')
op(r,'grow','grow','Obtain cubes in the high-dilution regime',e,['heated-reaction'],['cubic-series'],{'temperature':Q(u='degC',e=e),'duration':Q(u='min',e=e)},desc='No exact duration is given for this alternative series; do not import the S16 40–60 min window.')
for i,(ratio,size,spread) in enumerate([(2.5,7.5,10.2),(4,8.5,9.0),(5,13.3,4.8),(7,21.5,6.0)],1):
    r['condition_options'].append({'id':f'ratio-{i}','label':f'Fe:OA 1:{ratio}; alternative condition','parameters':{'oleic_acid_to_fe_molar_ratio':Q(ratio,'mol/mol',e,basis='OA per Fe atom')},'evidence':e})
    p=product(f's17-ratio-{i}','Fe–O',e,link='general_context',notes=['Condition map links ratio and size, but exact batch/iron-source branch, dilution and growth temperature/time remain unresolved.'])
    p['source_sample_label']=f'Figure S17 Fe:OA 1:{ratio} panel';p['morphology']=F('cubic shaped',e);r['products'].append(p)
    r['measurements']+=[measurement(f'ratio-{i}-size',p['sample_id'],'characteristic_size',Q(size,'nm',e,qualifier='Reported size; geometrical definition not explicit.'),'TEM',e),measurement(f'ratio-{i}-spread',p['sample_id'],'relative_size_spread',Q(spread,'%',e,qualifier='Reported ± percentage; spread definition and count not reported.'),'TEM',e)]
r['quality']['experimental_outcome']='reported_product';records.append(save(r))

r=nc('feld-2019-iron-oxide-ode34-star-condition','Iron oxide star morphology at 34 vol% ODE (Figure 3a)',ode=34,ratio=7)
e=E('Main p.155 Figure 3a caption: 66 vol% OA, 34 vol% ODE, Fe:OA 1:7')
r['operations'][-2]['parameters']['ode_volume_fraction']=Q(34,'vol%',e)
st(r,'star-condition','Figure 3a condition, sampling time unspecified',['heated-reaction'],'reaction_batch')
op(r,'observe-star','grow','Obtain the Figure 3a star condition',e,['heated-reaction'],['star-condition'],{'time_after_nucleation':Q(u='min',e=e),'temperature':Q(u='degC',e=e)},desc='Do not substitute the 30 vol% SI series or its size labels.')
p=product('figure3a-stars','Fe–O',e,link='general_context');p['source_sample_label']='Figure 3a';p['morphology']=F('star / octapod shaped',e);r['products']=[p];r['quality']['experimental_outcome']='reported_product';records.append(save(r))
(OUT/'canonical-summary.json').write_text(json.dumps({'record_count':len(records),'record_ids':[r['record_id'] for r in records],'supersession':{'record_id':'feld-2019-iron-oxide-undiluted-cubic-condition','revision':2,'changes':['Removed falsely selected Fe(II) upstream branch from NC condition; two upstream precursor procedures now separate.','Preserved selected 60 nm cubic observation and added other no-ODE growth observations with condition-map scope.','No diameter, final-phase or independent batch assignment.']},'counting_policy':'Records represent 2 precursor procedures and 7 partial NC method/condition families, not nine new experiments. All share one DOI/source/family split group.'},indent=2),encoding='utf-8')
print('Wrote',len(records),'canonical records to',OUT/'canonical')
