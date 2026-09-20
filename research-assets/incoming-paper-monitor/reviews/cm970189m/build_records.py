"""Private Veinot 1997 extraction; source values remain distinct from model claims."""
from pathlib import Path
from copy import deepcopy
import json,sys
B=Path(__file__).resolve().parent; S=B.parents[3]/'recipe-atlas'
sys.path.insert(0,str(S/'scripts'))
from record_helpers import record,source,ev,fact,qty,material,operation,state,product,measurement
from dataset_lib import validate_record
SID='veinot1997'; PREFIX='veinot-1997-'
SRC=source(SID,'10.1021/cm970189m','Surface Functionalization of Cadmium Sulfide Quantum-Confined Nanoclusters. 3. Formation and Derivatives of a Surface Phenolic Quantum Dot','Jonathan G. C. Veinot; Madlen Ginzburg; William J. Pietro',1997)
SRC['main_status']='All six supplied main pages read and visually inspected; independent canonical audit pending'
def E(p,s):return ev(SID,f'Main PDF p. {p}, printed p. {2116+p}, {s}')
MAT=E(1,'Experimental Section: Materials'); QDOH=E(1,'Surface Phenol Functionalized CdS Quantum Dots')+E(2,'QDOH preparation continuation'); ACYL=E(2,'N-Acylimidazoles'); EST=E(2,'Esterification of Surface Phenol Functionalized CdS Quantum Dots'); SPEC=E(2,'Spectroscopy'); TEM=E(2,'Electron Microscopy'); T1=E(3,'Table 1'); T2=E(3,'Table 2'); T3=E(3,'Table 3')
def Q(v=None,u='',e=EST,**kw):return qty(v,u,deepcopy(e),**kw)
def F(v=None,e=EST,**kw):return fact(v,deepcopy(e),**kw)
def M(i,n,f,role='solvent',stage='synthesis',e=MAT,notes=None,quantities=None):return material(i,n,f,role,stage,deepcopy(e),notes=notes or [],quantities=quantities)
CHEM={
 'water':('Deionized, charcoal-treated water','H2O'), 'acn':('Acetonitrile','C2H3N'), 'methanol':('Methanol','CH4O'), 'acetone':('Acetone','C3H6O'), 'ether':('Diethyl ether','C4H10O'), 'toluene':('Dry toluene','C7H8'), 'dmso':('Dimethyl sulfoxide','C2H6OS'), 'chloroform':('Chloroform','CHCl3'), 'dmso-d6':('Dimethyl sulfoxide-d6','C2D6OS'), 'cdcl3':('Chloroform-d','CDCl3'), 'd2o':('Deuterium oxide','D2O'), 'dmf':('N,N-Dimethylformamide','C3H7NO'), 'ethanol':('Ethanol','C2H6O'), 'hexane':('n-Hexane','C6H14'),
 'na2s':('Sodium sulfide nonahydrate','Na2S·9H2O'), 'hpt':('4-Hydroxythiophenol','C6H6OS'), 'cd-acetate':('Cadmium acetate (hydration unspecified)','Cd(C2H3O2)2'), 'n2':('Nitrogen','N2'), 'imidazole':('Imidazole','C3H4N2'), 'acetic-anhydride':('Acetic anhydride','C4H6O3'), 'butyric-anhydride':('Butyric anhydride','C8H14O3'), 'benzoyl-chloride':('Benzoyl chloride','C7H5ClO'), 'butanoyl-chloride':('n-Butanoyl chloride','C4H7ClO'), 'decanoyl-chloride':('Decanoyl chloride','C10H19ClO'), 'pyrene-acid':('1-Pyrenecarboxylic acid','C17H10O2'), 'socl2':('Thionyl chloride','SOCl2'), 'pyrene-chloride':('1-Pyrenecarboxylic acid chloride','C17H9ClO'), 'acetic-acid':('Glacial acetic acid','C2H4O2'), 'kbr':('Potassium bromide','KBr'), 'sieves':('4 angstrom molecular sieves','Unspecified aluminosilicate'), 'mixed-bed':('Mixed-bed ion-exchange resin, Sybron-Barnstead D8902','Mixture'), 'charcoal':('Activated charcoal, Sybron-Barnstead D8204','C'), 'qdoh':('Surface phenol-functionalized CdS nanoclusters (1, QDOH)','CdS'), 'cluster':('Source-specific functionalized CdS nanocluster specimen','CdS'), 'grid':('JBS-183, 300 mesh carbon-coated copper TEM grid','C/Cu'), 'si-grid':('Precision silicon calibration grid','Si'), 'filter-paper':('Filter paper','Cellulose'), 'tms':('Tetramethylsilane NMR reference','C4H12Si'), 'bare-capped':('Unfunctionalized thiophenolate-capped CdS nanoclusters','CdS'), 'acyl-agent':('Unspecified N-acylimidazole reagent','Variable'), 'acyl-chloride':('Unspecified acyl chloride reagent','Variable')}
ACYL_NAMES={'a':('acetyl','N-Acetylimidazole','C5H6N2O'),'b':('butanoyl','N-Butanoylimidazole','C7H10N2O'),'c':('pyrene-1-carbonyl','N-(Pyrene-1-carbonyl)imidazole','C20H12N2O'),'d':('benzoyl','N-Benzoylimidazole','C10H8N2O'),'e':('decanoyl','N-Decanoylimidazole','C13H22N2O')}
for x,(_,n,f) in ACYL_NAMES.items():CHEM['3'+x]=(n,f)
CHEM['ether']=('Ether (workup identity not further specified)',None)
CHEM['filter-paper']=('Filter paper',None)
def C(i,role='solvent',stage='synthesis',e=MAT,**kw):
 if i=='ether':kw['notes']=kw.get('notes',[])+['Workup text says ether without specifying identity; solubility discussion separately names diethyl ether. No unqualified transfer of that identity into the workup.']
 if role=='surface functionalization reagent':role='surface_functionalization_reagent'
 return M(i,*CHEM[i],role,stage,e,**kw)
def base(key,title,kind='procedure',method='Supporting procedure'):
 r=record(PREFIX+key,'Veinot et al. (1997) · '+title,'CdS','Surface-functionalized II–VI quantum dots',method,deepcopy(SRC),'Main PDF pp. 1–6, printed pp. 2117–2122',kind)
 r['schema_version']='1.1.0';r['collection']='reviewed_literature';r['material'].update(elements=['Cd','S'],components=['CdS'],architecture='single_material');r['lineage']['recipe_family']='veinot1997-phenolic-cds'
 r['quality'].update(review_status='imported_unreviewed',requested_tasks=[],review_scope='Private full supplied-main extraction; independent canonical/reader audit pending. SI not located or verified. Source compound labels do not establish individual physical batches.',missing_fields=['Matching supporting information not located or verified.','No measured atomic coordinates or explicit CdS crystalline phase assignment supplied.'],conflicts=[])
 r['context_links']=[{'label':'Complete source review','url':'../paper-review.html?id=veinot1997','relation':'Six supplied main pages; matching SI unverified.'}]
 return r
def link(r,key,label,relation):r['context_links'].append({'label':label,'url':'../records/'+PREFIX+key+'.html','relation':relation})
def add(r,oid,action,label,ins,out,e=EST,parameters=None,stage='synthesis',description='',depends=None,environment=None,retained=False,kind='mixture'):
 if out:r['material_states'].append(state(out,label+' output',ins,'fraction'if kind=='solid'else kind))
 r['operations'].append(operation(oid,action,label,deepcopy(e),ins,[out]if out else[],depends=depends,parameters=parameters or {},stage=stage,description=description,environment=F(environment,e),retained_fraction=out if retained else None))
def P(r,i,label,f='CdS',e=EST,sid=None,explicit=False,notes=None):
 p=product(i,f,deepcopy(e),link='explicit'if explicit else'general_context',state=sid,notes=notes or[]);p['source_sample_label']=label;r['products'].append(p);return p
def V(r,i,s,prop,v,tech,e,conditions=''):r['measurements'].append(measurement(i,s,prop,v,tech,deepcopy(e),conditions))
def stock(i,n,ids,e,scope,amounts=None,concs=None,ops=None):return dict(id=i,name=n,components=[{'material_id':x,'quantities':(amounts or{}).get(x,{})}for x in ids],concentrations=concs or{},preparation_operation_ids=ops or[],scope=scope,evidence=deepcopy(e))
records=[]

# Route 1: source preparation; do not repair the printed mass/amount mismatch.
r=base('qdoh','Surface phenol-functionalized CdS nanoclusters (1, QDOH)','literature_protocol','Kinetic trapping in mixed solvents')
r['materials']=[C('na2s','chalcogen_precursor',e=QDOH,quantities={'mass':Q(2.53,'g',e=QDOH),'amount':Q(11,'mmol',e=QDOH)}),C('hpt','surface ligand',e=QDOH,quantities={'mass':Q(4.93,'g',e=QDOH),'amount':Q(39,'mmol',e=QDOH)}),C('cd-acetate','metal_precursor',e=QDOH,quantities={'mass':Q(5.05,'g',e=QDOH),'amount':Q(29,'mmol',e=QDOH)},notes=['Both printed quantities retained. The reported mass and amount do not agree with the named salt formula; hydration state is unspecified.']),*[C(i,e=QDOH)for i in ['acn','methanol','water']],*[C(i,stage='workup',e=QDOH)for i in ['acetone','ether']],C('n2','inert atmosphere',e=QDOH),C('dmso',stage='characterization',e=QDOH)]
r['stocks']=[stock('sulfide-stock','Sulfide and capping-thiol solution',['na2s','hpt','acn','methanol','water'],QDOH,'150 mL total 1:1:2 (v/v) acetonitrile/methanol/water solvent mixture. Individual solvent volumes are not separately reported.',concs={'solvent_volume':Q(150,'mL',e=QDOH),'acn_relative_volume':Q(1,'part',e=QDOH,basis='1:1:2 v/v'),'methanol_relative_volume':Q(1,'part',e=QDOH,basis='1:1:2 v/v'),'water_relative_volume':Q(2,'part',e=QDOH,basis='1:1:2 v/v')},ops=['prepare-sulfide']),stock('cadmium-stock','Cadmium acetate solution',['cd-acetate','acn','methanol','water'],QDOH,'Same 1:1:2 solvent system, but volume of this separate solution is not stated. Do not inherit 150 mL.',ops=['prepare-cadmium'])]
add(r,'prepare-sulfide','stock_preparation','Dissolve sulfide and capping thiol',['na2s','hpt','acn','methanol','water'],'sulfide-ready',QDOH,stage='precursor_preparation',parameters={'solvent_volume':Q(150,'mL',e=QDOH)},description='Use 1:1:2 (v/v) acetonitrile/methanol/water. No temperature or dissolution duration stated.')
add(r,'prepare-cadmium','stock_preparation','Prepare cadmium acetate solution',['cd-acetate','acn','methanol','water'],'cadmium-ready',QDOH,stage='precursor_preparation',description='Use the same solvent system. Cadmium-solution volume unreported; printed 5.05 g and 29 mmol are inconsistent.')
add(r,'combine','solution_addition','Add sulfide/thiol solution to cadmium solution',['sulfide-stock','cadmium-stock','n2'],'reaction-mixture',QDOH,depends=['prepare-sulfide','prepare-cadmium'],environment='Nitrogen; protected from light',description='Add to rapidly stirring cadmium solution. Addition rate, apparatus geometry, pressure and temperature are not supplied.')
add(r,'stir','stirring','Stir protected from light',['reaction-mixture'],'yellow-precipitate',QDOH,depends=['combine'],parameters={'duration':Q(12,'h',e=QDOH),'temperature':Q(u='degC',e=QDOH),'pressure':Q(u='Torr',e=QDOH)},environment='Nitrogen; protected from light',description='Bright yellow precipitate forms. Room-temperature drying later in the method does not establish the reaction temperature.')
add(r,'concentrate','rotary_evaporation','Concentrate with a rotary evaporator',['yellow-precipitate'],'concentrated',QDOH,depends=['stir'],stage='workup',parameters={'remaining_volume_fraction':Q(1/3,'',e=QDOH,approximate=True,raw_text='approximately one-third its original volume')},description='Absolute original total volume is unknown because the cadmium solution volume was omitted.')
add(r,'isolate','centrifugation','Isolate the precipitate',['concentrated'],'isolated-solid',QDOH,depends=['concentrate'],stage='workup',description='Retain solid; centrifuge speed and duration are unreported.',retained=True,kind='solid')
last='isolated-solid';dep='isolate'
for i in ['water','acetone','ether']:
 add(r,'wash-'+i,'washing_sonication_centrifugation','Wash, sonicate and centrifuge with '+CHEM[i][0].lower(),[last,i],'washed-'+i,QDOH,depends=[dep],stage='workup',description='Repeated cycles in the stated solvent order; number, volumes, sonication settings and centrifuge settings are not supplied.',retained=True,kind='solid');last='washed-'+i;dep='wash-'+i
add(r,'dry','vacuum_drying','Dry the QDOH powder',[last],'qdoh-powder',QDOH,depends=[dep],stage='workup',parameters={'duration':Q(u='h',e=QDOH,qualifier='overnight'),'temperature':Q(u='degC',e=QDOH,qualifier='room temperature'),'pressure':Q(u='Torr',e=QDOH,qualifier='high vacuum; numerical pressure not reported')},environment='High vacuum',kind='solid')
p=P(r,'compound-1','1 (QDOH)',e=QDOH,sid='qdoh-powder',explicit=True,notes=['Surface phenolic CdS material, not an atomically specified cluster. Characterization links below are at compound-class scope.']);p['surface']=F('4-Hydroxyphenyl thiolate-bound phenolic surface',QDOH+E(4,'NMR and IR interpretation'));p['morphology']=F('Yellow nanocluster powder',QDOH)
V(r,'isolated-mass','compound-1','isolated_product_mass',Q(2.23,'g',e=QDOH),'Gravimetric isolated product',QDOH,'Capped powder mass, not a measured quantitative CdS yield.')
r['quality']['experimental_outcome']='reported_product';r['quality']['conflicts']=['Cadmium acetate 5.05 g and 29 mmol are retained exactly although inconsistent with the named formula; hydration unspecified.','Sodium sulfide nonahydrate 2.53 g and 11 mmol are reported with approximate rounding consistency, not silently recomputed.','Methods p2 attributes 20 mol% of sulfur to thiol; Results p3 gives 34 mol% under the same quantitative-sulfide-yield assumption.']
r['quality']['missing_fields']+=['Cadmium solution volume, reaction temperature, numerical pressure, stirring and centrifugation settings unreported.']
link(r,'reagent-conditioning','Reagent conditioning','Upstream preparation before the reaction.');link(r,'characterization','Compound-resolved characterization','Values identify compound1, not a uniquely identified isolated batch.');records.append(r)

# Five genuine named surface-functionalization variants. Absolute charge reported only for 2a.
for x,(name,agent,formula) in ACYL_NAMES.items():
 key='2'+x;e=EST+T1
 r=base('ester-'+key,f'{name.capitalize()} ester of surface phenolic CdS ({key})','literature_protocol','Surface esterification with N-acylimidazole')
 def aq(v,u):return Q(v if x=='a'else None,u,e=EST,qualifier=''if x=='a'else'Only representative 2a charge reported; variant charge unknown')
 r['materials']=[C('qdoh','seed',e=EST,quantities={'mass':aq(300,'mg')}),C('3'+x,'surface functionalization reagent',e=EST+T1,quantities={'mass':aq(170,'mg')}),C('dmso',e=EST),C('n2','inert atmosphere',e=EST),*[C(i,stage='workup',e=EST)for i in ['water','methanol','acetone','ether']]]
 r['stocks']=[stock('qdoh-dispersion','QDOH suspension in DMSO',['qdoh','dmso'],EST,'Representative 2a: 300 mg QDOH in 5 mL DMSO; other variants share similar conditions but not stated amounts.',amounts={'dmso':{'volume':aq(5,'mL')}},ops=['sonicate-qdoh']),stock('acyl-stock',agent+' in DMSO',['3'+x,'dmso'],EST,'Representative 2a: 5 mL solution containing 170 mg acetylimidazole in DMSO. Total solution volume is not solvent-only volume.',concs={'solution_volume':aq(5,'mL')},ops=['prepare-acyl'])]
 add(r,'sonicate-qdoh','sonication','Prepare the QDOH suspension',['qdoh','dmso'],'qdoh-suspended',EST,stage='precursor_preparation',description='Sonicate the QDOH in DMSO. '+('300 mg in 5 mL.'if x=='a'else'Common-method inheritance; this variant has no independently reported charge or volume.'))
 add(r,'prepare-acyl','stock_preparation','Prepare '+agent+' solution',['3'+x,'dmso'],'acyl-ready',EST,stage='precursor_preparation',description='DMSO solution. '+('170 mg in 5 mL solution.'if x=='a'else'Variant-specific concentration and delivered volume are unreported.'))
 add(r,'add-acyl','dropwise_addition','Add acylating reagent dropwise',['qdoh-dispersion','acyl-stock','n2'],'esterifying-mixture',e,depends=['sonicate-qdoh','prepare-acyl'],environment='Dry nitrogen; dark',description='Rapid stirring; no injection rate or exact vessel geometry. Similar conditions inherited from representative2a only; absolute amounts are not inherited.')
 add(r,'react','stirring','React at room temperature',['esterifying-mixture'],'reacted',e,depends=['add-acyl'],parameters={'duration':Q(30,'min',e=T1+EST),'temperature':Q(u='degC',e=EST,qualifier='room temperature'),'pressure':Q(u='Torr',e=EST)},environment='Dry nitrogen; dark',description='Table1 reports 30 min for this variant. General discussion says usually15–30min; prolonged >12h destroys clusters and is a separate observation.')
 add(r,'cool','ice_bath_cooling','Cool in an ice bath',['reacted'],'cooled',EST,depends=['react'],stage='workup',parameters={'temperature':Q(u='degC',e=EST,qualifier='ice bath; reaction-mixture temperature not quantified')},description='No source duration; do not assign 0°C to the sample.')
 add(r,'quench','water_quench','Quench with water',['cooled','water'],'quenched',EST,depends=['cool'],stage='workup',description='Water quantity and addition rate unreported.')
 add(r,'isolate','centrifugation','Recover the esterified clusters',['quenched'],'recovered',EST,depends=['quench'],stage='workup',retained=True,kind='solid',description='Retain precipitate; centrifuge speed and duration unspecified.')
 last='recovered';dep='isolate'
 for solvent in ['water','methanol','acetone','ether']:
  add(r,'sonicate-'+solvent,'solvent_sonication','Sonicate repeatedly in '+CHEM[solvent][0].lower(),[last,solvent],'washed-'+solvent,EST,depends=[dep],stage='workup',description='Consecutive solvent order is reported. Cycle count, volume, sonication settings and inter-solvent recovery details are unreported; do not invent centrifugation at every wash.',kind='solid');last='washed-'+solvent;dep='sonicate-'+solvent
 add(r,'dry','vacuum_drying','Dry the esterified nanoclusters',[last],'ester-powder',EST,depends=[dep],stage='workup',parameters={'duration':Q(24,'h',e=EST),'temperature':Q(u='degC',e=EST,qualifier='room temperature'),'pressure':Q(u='Torr',e=EST,qualifier='high vacuum; numerical pressure not stated')},environment='High vacuum',kind='solid')
 p=P(r,'compound-'+key,key+' ('+name+' ester)',e=e,sid='ester-powder',explicit=True,notes=['Named compound-class product. Source characterization is not assigned a fabricated run or batch identifier.']);p['surface']=F('Thiolate-bound phenyl '+name+' ester groups',E(2,'Compound structures')+E(3,'Scheme 1'))
 r['quality']['experimental_outcome']='reported_product';r['quality']['missing_fields']+=['Surface-conversion percentage is NMR-derived, not isolated mass yield.','No batch-resolved atomic coordinates, per-variant isolated mass, exact pressure, or centrifugation settings.']
 if x!='a':r['quality']['missing_fields']+=['Absolute QDOH, N-acylimidazole and DMSO charges are not reported for this variant; 2a quantities are not copied.']
 link(r,'qdoh','QDOH preparation','Upstream phenolic CdS substrate.');link(r,'acylimidazole-3'+x,agent+' preparation','Separate upstream molecular synthesis.');link(r,'characterization','Characterization and surface conversion','Tables identify this compound class; exact specimen-to-run mapping unreported.');link(r,'prolonged-degradation','Prolonged-exposure degradation','Contextual >12h observation, not a selectable safe alternative.');records.append(r)

r=base('pyrenecarbonyl-chloride','1-Pyrenecarboxylic acid chloride preparation');e=E(2,'1-Pyrenecarboxylic Acid Chloride')
r['materials']=[C('pyrene-acid','organic precursor','precursor_preparation',e,quantities={'mass':Q(1,'g',e=e),'amount':Q(4.1,'mmol',e=e)}),C('socl2','chlorinating reagent / reaction medium','precursor_preparation',e,quantities={'volume':Q(20,'mL',e=e)}),C('n2','inert atmosphere','precursor_preparation',e)]
add(r,'dissolve','dissolution','Dissolve the pyrenecarboxylic acid',['pyrene-acid','socl2','n2'],'acid-solution',e,stage='precursor_preparation',environment='Dry nitrogen')
add(r,'stir','stirring','Stir until the olive-green precipitate forms',['acid-solution'],'green-precipitate',e,depends=['dissolve'],stage='precursor_preparation',parameters={'duration':Q(u='min',e=e,qualifier='several minutes'),'temperature':Q(u='degC',e=e,qualifier='room temperature')},environment='Dry nitrogen')
add(r,'heat','heating','Heat the mixture',['green-precipitate'],'heated',e,depends=['stir'],stage='precursor_preparation',parameters={'temperature':Q(80,'degC',e=e),'duration':Q(3,'h',e=e)},description='The green precipitate redissolves. Heating-apparatus type is not specified.')
add(r,'cool','cooling','Cool the reaction mixture',['heated'],'cooled',e,depends=['heat'],stage='workup',description='Temperature and duration unreported.')
add(r,'filter','filtration','Filter and retain the filtrate',['cooled'],'filtrate',e,depends=['cool'],stage='workup',retained=True,description='Subsequent product is recovered from filtrate, not the filter solid.')
add(r,'evaporate','vacuum_evaporation','Remove excess thionyl chloride',['filtrate'],'acid-chloride-solid',e,depends=['filter'],stage='workup',environment='In vacuo; pressure unreported',description='Remove excess reagent completely. Highly fluorescent orange-yellow solid is used immediately for3c.',kind='solid')
P(r,'pyrene-chloride-product','1-Pyrenecarboxylic acid chloride','C17H9ClO',e,'acid-chloride-solid',True,notes=['No isolated yield or full spectrum supplied. Qualitative fluorescence is not a quantum-yield measurement.']);link(r,'acylimidazole-3c','Preparation of3c','Use immediately; storage period not reported.');records.append(r)

for x,(name,agent,formula)in ACYL_NAMES.items():
 r=base('acylimidazole-3'+x,agent+' precursor preparation (3'+x+')');e=ACYL;anh=x in'ab';feed={'a':'acetic-anhydride','b':'butyric-anhydride','c':'pyrene-chloride','d':'benzoyl-chloride','e':'decanoyl-chloride'}[x]
 r['materials']=[C('imidazole','organic precursor','precursor_preparation',e,quantities={}if anh else{'equivalents':Q(2.05,'equiv',e=e,basis='Relative to acyl chloride; Results discussion rounds to2equiv')}),C(feed,'acyl donor / reaction medium'if anh else'acyl donor','precursor_preparation',e),C('toluene',stage='workup'if anh else'precursor_preparation',e=e)]
 if anh:
  r['materials'].append(C('n2','inert atmosphere','precursor_preparation',e))
  add(r,'dissolve','dissolution','Dissolve imidazole in excess anhydride',['imidazole',feed,'n2'],'anhydride-mixture',e,stage='precursor_preparation',environment='Dry nitrogen',description='Large excess corresponding acid anhydride; absolute charges and concentration unreported.')
  add(r,'react','stirring','Stir at room temperature',['anhydride-mixture'],'reacted',e,depends=['dissolve'],stage='precursor_preparation',parameters={'duration':Q(30,'min',e=e,basis='Common anhydride-method text'),'temperature':Q(u='degC',e=e,qualifier='room temperature')},environment='Dry nitrogen',description='For3b Table1 reports15min, conflicting with common30min method; retain both as source conflict, not two independent runs.')
  if x=='b':r['operations'][-1]['parameters']['table1_reaction_duration']=Q(15,'min',e=T1,basis='Conflicts with common anhydride-method30min; no resolved operative value')
  add(r,'evaporate','vacuum_evaporation','Remove acid and excess anhydride',['reacted'],'crystals',e,depends=['react'],stage='workup',environment='Reduced pressure; numerical pressure not stated',description='Remove liquid to afford white crystals.',kind='solid')
  dep='evaporate';last='crystals'
 else:
  r['stocks']=[stock('chloride-stock','Acyl chloride in dry toluene',[feed,'toluene'],e,'50% solution; mass/volume/mole basis not stated. Absolute amounts unknown.',concs={'reported_percentage':Q(50,'%',e=e,basis='Concentration basis not supplied')},ops=['prepare-chloride']),stock('imidazole-stock','Imidazole in toluene',['imidazole','toluene'],e,'2.05 equivalents imidazole; absolute charge and solvent volume unreported.',ops=['prepare-imidazole'])]
  add(r,'prepare-chloride','stock_preparation','Prepare 50% acyl chloride solution',[feed,'toluene'],'chloride-ready',e,stage='precursor_preparation',description='Dry toluene; 50% basis unspecified.')
  add(r,'prepare-imidazole','stock_preparation','Prepare imidazole solution',['imidazole','toluene'],'imidazole-ready',e,stage='precursor_preparation',description='2.05 equivalents imidazole. Absolute charge and volume unreported.')
  add(r,'add-chloride','dropwise_addition','Add chloride solution with rapid stirring',['chloride-stock','imidazole-stock'],'reaction-mixture',e,depends=['prepare-chloride','prepare-imidazole'],stage='precursor_preparation',parameters={'temperature':Q(u='degC',e=e,qualifier='room temperature')},description='Addition rate and atmosphere not explicitly specified for this branch. Do not inherit dryN2 from preceding anhydride route.')
  add(r,'heat','heating','Heat the reaction mixture',['reaction-mixture'],'heated',e,depends=['add-chloride'],stage='precursor_preparation',parameters={'temperature':Q(100,'degC',e=e),'duration':Q(u='min',e=e,qualifier='Heating-stage duration not specified')},description='Table1 reaction time is '+str({'c':30,'d':15,'e':30}[x])+'min; no exact stage allocation given. White imidazole hydrochloride precipitates.')
  add(r,'hot-filter','hot_filtration','Hot-filter imidazole hydrochloride',['heated'],'filtrate',e,depends=['heat'],stage='workup',retained=True,description='Retain the toluene filtrate; white precipitate is imidazolium chloride byproduct.')
  add(r,'ice-cool','ice_bath_crystallization','Cool the toluene solution in an ice bath',['filtrate'],'crystals',e,depends=['hot-filter'],stage='workup',description='White N-acylimidazole crystals precipitate; no measured sample temperature or cooling duration.',kind='solid');dep='ice-cool';last='crystals'
 add(r,'recrystallize','recrystallization','Recrystallize from toluene',[last,'toluene'],'purified',e,depends=[dep],stage='workup',description='Recrystallize '+('from toluene; number of cycles not specified.'if anh else'once from toluene before use. Solvent volume unreported.'),kind='solid')
 P(r,'compound-3'+x,'3'+x+' ('+agent+')',formula,e,'purified',True,notes=['Molecular precursor; material-hub context CdS is not the molecular product formula. Slight air sensitivity discussed generally.'])
 if x=='b':r['quality']['conflicts'].append('Table1 3b reaction duration15min versus common anhydride preparation30min.')
 if x=='d':r['quality']['conflicts'].append('Table1 benzoylimidazole3d has an anomalous2.6ppm3H methyl entry; preserved in characterization without assigning it to an impurity.')
 link(r,'ester-2'+x,'CdS ester2'+x,'Downstream surface-functionalization route.');link(r,'characterization','Molecular precursor yields and NMR','Yield and spectra identify compound class, not a unique physical run.');
 if x=='c':link(r,'pyrenecarbonyl-chloride','Pyrene acid-chloride preparation','Upstream precursor used immediately.')
 records.append(r)

# Shared reagent conditioning and explicitly scoped analytical sample preparation.
r=base('reagent-conditioning','Reagent purification and handling');e=MAT
r['materials']=[C('toluene',stage='precursor_preparation'),C('sieves','drying medium','precursor_preparation'),C('water',stage='precursor_preparation'),C('mixed-bed','purification medium','precursor_preparation'),C('charcoal','purification medium','precursor_preparation'),C('cd-acetate','metal_precursor','precursor_preparation'),C('acetic-acid',stage='precursor_preparation'),C('hpt','surface ligand','precursor_preparation')]
add(r,'dry-toluene','solvent_drying','Dry toluene over molecular sieves',['toluene','sieves'],'dried-toluene',e,stage='precursor_preparation',parameters={'sieve_pore_size':Q(4,'angstrom',e=e)},description='Reagent-grade toluene; drying duration unreported.')
add(r,'filter-toluene','filtration','Filter toluene before use',['dried-toluene'],'filtered-toluene',e,depends=['dry-toluene'],stage='precursor_preparation',retained=True)
add(r,'deionize-water','ion_exchange','Deionize water',['water','mixed-bed'],'deionized-water',e,stage='precursor_preparation',description='Sybron-BarnsteadD8902mixed-bed ion exchange.')
add(r,'charcoal-water','charcoal_purification','Remove organic impurities from water',['deionized-water','charcoal'],'purified-water',e,depends=['deionize-water'],stage='precursor_preparation',description='Sybron-BarnsteadD8204activated charcoal treatment follows ion exchange.')
add(r,'recrystallize-cadmium','recrystallization','Recrystallize cadmium acetate',['cd-acetate','acetic-acid'],'cadmium-crystals',e,stage='precursor_preparation',description='Recrystallize from glacial acetic acid; amounts and recovery details unreported.',kind='solid')
add(r,'dry-cadmium','vacuum_drying','Dry cadmium acetate',['cadmium-crystals'],'dry-cadmium',e,depends=['recrystallize-cadmium'],stage='precursor_preparation',parameters={'temperature':Q(100,'degC',e=e),'duration':Q(u='h',e=e),'pressure':Q(u='Torr',e=e,qualifier='in vacuo')},environment='Vacuum',kind='solid')
add(r,'distill-thiol','vacuum_distillation','Distill4-hydroxythiophenol immediately before use',['hpt'],'fresh-thiol',e,stage='precursor_preparation',environment='Reduced pressure; numerical pressure unstated',description='Distillation temperature and duration unreported.')
for i in ['dmso','na2s','imidazole','pyrene-acid','butanoyl-chloride','decanoyl-chloride','socl2','acetic-anhydride','butyric-anhydride','benzoyl-chloride']:
 note='Aldrich ACS spectrophotometric grade, as received.'if i=='dmso'else('BDH reagent grade, as received.'if i in['acetic-anhydride','butyric-anhydride','benzoyl-chloride']else'Aldrich reagent grade, as received.')
 if i=='butanoyl-chloride':note+=' Listed inventory only: reported3b preparation uses butyric anhydride; no extra chloride-route experiment inferred.'
 r['materials'].append(C(i,'reagent as received','precursor_preparation',e,notes=[note]))
for i in ['dmso-d6','cdcl3','d2o']:r['materials'].append(C(i,stage='characterization',e=e,notes=['Cambridge Isotope Laboratories deuterated solvents in sealed ampules; source says used immediately after opening.']))
add(r,'open-deuterated','ampule_opening','Open deuterated solvent ampules immediately before use',['dmso-d6','cdcl3','d2o'],'deuterated-solvents',e,stage='characterization',description='Independent solvent choices for different measurements; not a three-solvent mixture.')
records.append(r)

r=base('nmr','400 MHz proton NMR and D2O exchange');e=SPEC+E(4,'Figures1–3')
r['materials']=[C('cluster','analytical specimen','characterization',e),*[C(i,stage='characterization',e=e)for i in['dmso-d6','cdcl3','d2o']],C('3e','molecular analytical specimen','characterization',E(4,'Figure2')),C('tms','NMR reference','characterization',E(4,'Figure3'))]
add(r,'dissolve','nmr_sample_preparation','Prepare compound-specific NMR specimens',['cluster','dmso-d6','cdcl3'],'nmr-specimens',e,stage='characterization',description='QDOH and2a–d use DMSO-d6;2e usesCDCl3. Separate alternatives, not mixed solvents. Figure2 usesDMSO-d6 for3e; other molecular precursor NMR solvents are not independently specified.')
add(r,'acquire','nmr','Acquire proton NMR',['nmr-specimens'],'nmr-observations',e,depends=['dissolve'],stage='characterization',parameters={'frequency':Q(400,'MHz',e=SPEC)},description='Bruker ARX (printed Brucker); no scan count, concentration, temperature or reference protocol supplied. Figure3 marks residual CHCl3, water and TMS.')
add(r,'d2o-test','deuterium_exchange','Add one drop D2O to the QDOH specimen',['nmr-specimens','d2o'],'exchanged-qdoh',E(4,'Figure1 and discussion'),depends=['dissolve'],stage='characterization',parameters={'d2o_drops':Q(1,'drop',e=E(4,'Figure1'))},description='Repeat NMR for QDOH only.8.6–9.1ppmOH resonance vanishes; not a synthesis step or treatment of all esters.')
add(r,'prepare-3e','nmr_sample_preparation','Prepare the separate3e NMR specimen',['3e','dmso-d6'],'nmr-3e',E(4,'Figure2'),stage='characterization',description='N-Decanoylimidazole3e inDMSO-d6; sourceFigure2. This is a molecular precursor specimen, not a CdS-containing sample.')
add(r,'acquire-3e','nmr','Acquire N-decanoylimidazole proton NMR',['nmr-3e'],'nmr-3e-observation',E(4,'Figure2'),depends=['prepare-3e'],stage='characterization',parameters={'frequency':Q(400,'MHz',e=E(4,'Figure2'))},description='Figure2marks residualDMSO. Concentration, scan count and NMR temperature unreported.')
link(r,'characterization','NMR assignments','Tables and pairedQDOHexchange observations.');records.append(r)

r=base('ftir','FTIR measurements of KBr pellets');e=SPEC+T2+E(5,'Figure4')
r['materials']=[C('cluster','analytical specimen','characterization',e),C('kbr','pellet matrix','characterization',e)]
add(r,'pellet','kbr_pellet_preparation','Prepare KBr pellets',['cluster','kbr'],'kbr-pellets',e,stage='characterization',description='Particle/KBr ratio, pressing force and drying conditions unreported.')
add(r,'acquire','ftir','Acquire Fourier-transform infrared spectra',['kbr-pellets'],'ir-observations',e,depends=['pellet'],stage='characterization',description='Mattson3000spectrometer. Resolution and scan count unreported. Figure4 is2e;Table2 covers1and2a–e.')
link(r,'characterization','Complete IR band inventory','AllTable2positions, intensities and source assignments retained.');records.append(r)

r=base('uv-visible','UV–visible absorption measurements');e=SPEC+E(5,'Figure5')
r['materials']=[C('cluster','analytical specimen','characterization',e),C('methanol',stage='characterization',e=e),C('chloroform',stage='characterization',e=e)]
add(r,'prepare','optical_sample_preparation','Prepare solvent-specific optical specimens',['cluster','methanol','chloroform'],'optical-specimens',e,stage='characterization',description='Methanol forQDOH;chloroform for allesters. These are separate specimens, not a mixed-solvent stock. Figure5QDOH10^-4M has unspecified molarity basis.')
add(r,'acquire','uv_visible','Measure absorption in quartz cuvettes',['optical-specimens'],'uv-observations',e,depends=['prepare'],stage='characterization',parameters={'path_length':Q(1,'cm',e=SPEC)},description='Hewlett-Packard8452diode-array spectrophotometer. Absorption onsets and model-derived diameters must remain distinct.')
link(r,'characterization','Absorption and model-derived sizes','Methods295/305nm versusTable3390nm conflict remains explicit.');records.append(r)

r=base('tem','TEM specimen preparation and size calibration');e=TEM
r['materials']=[C('cluster','analytical specimen','characterization',e,quantities={'mass':Q(2.5,'mg',e=e)}),C('chloroform',stage='characterization',e=e,quantities={'specimen_solvent_volume':Q(3,'mL',e=e,basis='Nanocluster suspension only; separate grid-cleaning volume unspecified')}),C('acetone',stage='characterization',e=e),C('grid','support','characterization',e),C('si-grid','calibration standard','characterization',e),C('filter-paper','wicking support','characterization',e)]
add(r,'sonicate','sonication','Sonicate the chloroform suspension',['cluster','chloroform'],'suspension',e,stage='characterization',description='2.5mg nanocluster per3mL CHCl3. QDOH suspension preparation does not imply the stable colloidal solubility defined by Note10.')
add(r,'centrifuge','centrifugation','Centrifuge the freshly sonicated suspension',['suspension'],'centrifuged-suspension',e,depends=['sonicate'],stage='characterization',description='Speed, duration and retained subfraction are not explicitly identified; do not label pellet or supernatant by assumption.')
add(r,'clean-grid','grid_cleaning','Clean the carbon-coated copper grid',['grid','acetone','chloroform'],'clean-grid',e,stage='characterization',parameters={'mesh':Q(300,'mesh',e=e)},description='JBS183grid:acetone→chloroform→acetone, then air-dry. Cleaning volumes unknown.')
add(r,'deposit','drop_casting','Apply three drops to the grid',['centrifuged-suspension','clean-grid','filter-paper'],'wet-grid',e,depends=['centrifuge','clean-grid'],stage='characterization',parameters={'drops':Q(3,'drop',e=e)},description='Filter paper absorbs solvent through the grid. Individual clusters and aggregates adhere; no spin coating or annealing.')
add(r,'dry-grid','air_drying','Air-dry the specimen grid',['wet-grid'],'dry-grid',e,depends=['deposit'],stage='characterization',parameters={'temperature':Q(u='degC',e=e,qualifier='room temperature')},environment='Air')
add(r,'calibrate','tem_calibration','Calibrate length against silicon grid',['si-grid'],'calibrated-scale',e,stage='characterization',parameters={'line_density':Q(21600,'lines/cm',e=e)})
add(r,'image','tem','Image individual clusters and aggregates',['dry-grid','calibrated-scale'],'tem-observations',e+E(6,'Figure6'),depends=['dry-grid','calibrate'],stage='characterization',parameters={'figure6_magnification':Q(290000,'times',e=E(6,'Figure6')),'accelerating_voltage':Q(u='kV',e=e)},description='PhilipsEM301;Figure6showsQDOH and6nm scale bar. General imaging conditions for every Table3compound are not fully enumerated.')
link(r,'characterization','TEM sizes and Figure6','TEM diameter, tight-binding size and aggregate dimension remain separate.');records.append(r)

r=base('unfunctionalized-control','Unfunctionalized thiophenolate-capped CdS control','protocol_variant','Surface-reactivity control');e=E(5,'Control experiments')
r['materials']=[C('bare-capped','control substrate',e=e),C('acyl-agent','surface functionalization reagent',e=e),C('water',stage='workup',e=e)]
add(r,'expose','control_exposure','Expose unfunctionalized capped CdS to N-acylimidazole',['bare-capped','acyl-agent'],'control-mixture',e,description='Reported control without exact acyl identity, dose, solvent, duration or temperature. Do not copy2a conditions.')
add(r,'workup','aqueous_workup','Perform aqueous workup',['control-mixture','water'],'control-recovery',e,depends=['expose'],stage='workup',description='Only unchanged nanocluster and recovered organic acid reported; no quantified conversion or detection limit.')
P(r,'control-cluster','Unchanged thiophenolate-capped CdS',e=e,sid='control-recovery',explicit=True,notes=['No reaction reported. Conditions incompletely specified; no success-calibration training label.']);r['quality']['experimental_outcome']='reported_failure';records.append(r)

for key,title,kind,desc,e in [('direct-acylchloride-degradation','Initial direct-acyl-chloride esterification attempts','acyl_chloride_exposure','Initial esterification attempts using acyl chlorides destroyed the cluster. Exact reagent, dose, medium, time and temperature are unreported. Fischer–Speier acidic esterification is a separate predicted incompatibility, not a performed experiment.',E(2,'Results and Discussion continuation')),('prolonged-degradation','Prolonged N-acylimidazole exposure','prolonged_surface_reaction','Extending ordinary time did not improve conversion; exposure >12h destroyed the cluster, precipitated bulkCdS and afforded crystalline corresponding O,S-diester. Exact acyl variant and isolated yields unreported.',E(5,'Esterification and prolonged exposure'))]:
 r=base(key,title,'observation','Contextual degradation observation');r['materials']=[C('qdoh','surface-functionalized substrate',e=e),C('acyl-chloride'if key.startswith('direct')else'acyl-agent','reaction reagent',e=e)]
 add(r,'exposure',kind,title,[m['id']for m in r['materials']],'degraded-mixture',e,description=desc,parameters={'duration_threshold':Q(12,'h',e=e,qualifier='greater than; strict lower threshold, not a12h measured run')}if key=='prolonged-degradation'else{})
 p=P(r,'degradation-observation','Unresolved degraded CdS-containing material',e=e,sid='degraded-mixture',notes=[desc]);r['quality']['experimental_outcome']='reported_failure';r['quality']['missing_fields']+=['Incomplete contextual experiment; not a full recipe or negative-example label.'];records.append(r)

# Characterization filled below from complete Tables1–3, plus distinct prose/figure observations.
r=base('characterization','Compound-resolved spectra, morphology and colloidal solubility','observation','NMR, FTIR, UV–visible and TEM characterization')
for c in ['1']+['2'+x for x in'abcde']+['3'+x for x in'abcde']:
 formula='CdS'if not c.startswith('3')else ACYL_NAMES[c[1]][2]
 P(r,'compound-'+c,c+(' (QDOH)'if c=='1'else''),formula,T1+T2+T3,notes=['Compound-class identity explicitly tabulated. Physical batch, replicate identity and specimen-to-route mapping are not individually reported.'])
records.append(r)

def finish():
 OUT=B/'canonical-drafts';OUT.mkdir(exist_ok=True);errors={}
 for rec in records:
  if rec['record_id']==PREFIX+'unfunctionalized-control':
   rec['quality']['experimental_outcome']='not_established'
   V(rec,'no-reaction','control-cluster','reaction_observation',F('No reaction observed; unchanged nanocluster and recovered organic acid',E(5,'Control experiments')),'Reported control observation',E(5,'Control experiments'),'Deliberate unfunctionalized control, not a failed QDOH synthesis or calibrated negative label.')
  if rec['record_id'].startswith(PREFIX+'ester-2') and not rec['record_id'].endswith('2a'):
   for op in rec['operations']:
    op['description']='Inherited common-method framework from representative2a through the source similar-conditions statement; absolute charges not inherited. '+op['description']
    if op['environment']['value'] is not None:op['environment']['status']='inherited'
    for k,v in op['parameters'].items():
     if v['value'] is not None and not(op['id']=='react'and k=='duration'):v['status']='inherited'
  if rec['record_id'].startswith(PREFIX+'acylimidazole-') or rec['record_id']==PREFIX+'pyrenecarbonyl-chloride':
   rec['intended_target']['composition']=deepcopy(rec['products'][0]['composition'])
  if rec['record_id'].startswith(PREFIX+'acylimidazole-'):
   for p in rec['products']:p['composition']['evidence']+=E(3,'Scheme1 and Table1 compound identities')
   rec['intended_target']['composition']=deepcopy(rec['products'][0]['composition'])
  if rec['record_id']==PREFIX+'direct-acylchloride-degradation':
   extra=E(3,'Results and Discussion continuation: initial acyl-chloride attempts')
   for field in ['materials','operations']:
    for item in rec[field]:item['evidence']+=deepcopy(extra)
   for p in rec['products']:
    p['composition']=F(e=extra,note='Clusters destroyed; resulting chemical composition and phase not identified by the source.')
    p['link_evidence']+=deepcopy(extra)
  if rec['record_type']=='literature_protocol' and rec['products']:
   rec['intended_target']['surface']=deepcopy(rec['products'][0]['surface'])
  errs=validate_record(rec)
  if errs:errors[rec['record_id']]=errs
  (OUT/(rec['record_id']+'.json')).write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 report={'status':'failed'if errors else'passed','records':len(records),'measurements':sum(len(x['measurements'])for x in records),'operations':sum(len(x['operations'])for x in records),'source_pages':6,'review_scope':'supplied_main_only_si_unverified','training_eligible':False,'errors':errors}
 (B/'records-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2));return bool(errors)
if __name__=='__main__':
 exec((B/'characterization_rows.py').read_text(encoding='utf-8'))
 sys.exit(finish())
