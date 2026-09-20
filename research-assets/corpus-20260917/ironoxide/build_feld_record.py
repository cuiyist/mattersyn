import hashlib
import json
import sys
from pathlib import Path
sys.dont_write_bytecode=True
BASE=Path('[local path redacted]')
SITE=BASE/'recipe-atlas'
OUT=BASE/'research-assets/corpus-20260917'
sys.path.insert(0,str(SITE/'scripts'))
from record_helpers import ev,fact,qty,source,record,material,operation,product,state,measurement

SID='feld2019'
ID='feld-2019-iron-oxide-undiluted-cubic-condition'
def E(loc):return ev(SID,loc)
GENERAL=E('Main PDF p. 8, printed p. 159, Materials and Methods: Materials; Synthesis of the Iron Sources')
CARB=E('Main PDF p. 8, printed p. 159, Synthesis of FeCO3-Iron(II) Source; SI p. 2, Figure S1')
OLEATE=E('Main PDF p. 9, printed p. 160, Synthesis of Fe(II) Oleate; SI pp. 3-4, eq 3 and Figure S3')
THERM=E('Main PDF p. 9, printed p. 160, Nanocrystal Synthesis; SI p. 5, Figure S5 apparatus')
COND=E('SI p. 11, section 8; p. 12, Figure S14, no-ODE row / 40-60 min column; p. 14, Figure S16, 60 nm lower-right panel')
PHASE=E('Main PDF p. 4, printed p. 155, Figure 3c; p. 5, printed p. 156, Enhanced Size- and Shape-Controlled Synthesis')
OXID=E('Main PDF p. 7, printed p. 158, EELS phase interpretation; SI pp. 9-10, section 6 and Figure S12')
def Q(v=None,u='',e=None,**kw):return qty(v,u,e or GENERAL,**kw)
def F(v=None,e=None,**kw):return fact(v,e or GENERAL,**kw)
src=source(SID,'10.1021/acsnano.8b05032','Chemistry of Shape-Controlled Iron Oxide Nanocrystal Formation','Artur Feld; Agnes Weimer; Andreas Kornowski; Naomi Winckelmans; Jan-Philip Merkl; Hauke Kloust; Robert Zierold; Christian Schmidtke; Theo Schotten; Maria Riedner; Sara Bals; Horst Weller',2019,'Matching 19-page SI verified by title/authors and main Associated Content; relevant preparation, condition-map and phase pages visually reviewed.')
src['main_status']='11-page original main text reviewed; preparation pages 159-160 and phase Figure 3 visually reviewed. Journal year 2019; published online December 12, 2018.'
r=record(ID,'Phase-unresolved iron oxide: undiluted cubic condition with Fe(II)-derived oleate preparation','Fe–O','Iron oxides','Thermal decomposition of carbonate-derived iron oleate; no-ODE, 40-60 min post-nucleation condition',src,'Main pp. 159-160 and SI Figures S14/S16',kind='protocol_variant')
r['collection']='reviewed_literature'
r['material'].update(elements=['Fe','O'],components=['Fe–O'],architecture='unresolved')
r['lineage']['recipe_family']='feld2019-iron-carbonate-oleate-thermolysis'
r['intended_target']['composition']=F('Fe–O',COND,note='Elemental material system only. No exact product stoichiometry is asserted.')
r['intended_target']['phase']=F(e=COND,note='No uniquely specified target phase for the selected condition; isolated and air-exposed phase is unresolved.')
r['intended_target']['morphology']=F('cubic nanocrystals',COND,note='The selected published condition targets the late cubic morphology. This is a literature condition, not an invented batch.')
r['intended_target']['size']=Q(u='nm',e=COND,qualifier='The 60 nm panel label is an observed contextual result, not a prespecified size target.')

r['materials']=[
 material('ferrous-sulfate','iron(II) sulfate heptahydrate','FeSO4·7H2O','metal_source','precursor_preparation',GENERAL,notes=['99.0%, Sigma-Aldrich; degassed and stored under nitrogen.']),
 material('sodium-carbonate','sodium carbonate','Na2CO3','precipitating_reagent','precursor_preparation',GENERAL,notes=['Dry basis 99.95-100.05%, Sigma-Aldrich; degassed and stored under nitrogen.']),
 material('water','Milli-Q water','H2O','solvent','precursor_preparation',GENERAL,notes=['Paper reports 18.2 MOhm/cm; saturated for 24 h with nitrogen. Used for dissolution and four washes.']),
 material('nitrogen','nitrogen','N2','protective_gas','precursor_preparation',GENERAL,notes=['Protective gas and solvent saturation; flow rate and purity not specified for this protocol.']),
 material('ferrous-carbonate','prepared iron(II) carbonate','FeCO3','precursor_intermediate','precursor_preparation',CARB,notes=['Fresh filtered/washed precipitate used without further purification or drying; stock-preparation mass/mmol retained as reported, with conflict flag.']),
 material('oleic-acid','oleic acid','C18H34O2','ligand_and_reaction_medium','precursor_preparation',GENERAL,notes=['Materials lists technical grade 90% Sigma-Aldrich and pure 99.0% TCI. Exact grade of the selected Figure S16 condition is not identified. Pure acid is specifically discussed for a MALDI control; do not transfer that purity to this condition.']),
 material('iron-oleate','carbonate-derived iron oleate mixture',None,'metal_precursor','synthesis',OLEATE,notes=['Prepared in excess oleic acid. Source observes multiple complexes and redox chemistry; no single molecular formula, molar mass, isolated purity or stock molarity is imposed.'])
]
r['stocks']=[
 {'id':'ferrous-sulfate-stock','name':'Iron(II) sulfate aqueous solution','components':[{'material_id':'ferrous-sulfate','quantities':{'mass':Q(14.30,'g',CARB),'amount':Q(51.44,'mmol',CARB)}},{'material_id':'water','quantities':{'volume':Q(180,'mL',CARB)}}],'concentrations':{},'preparation_operation_ids':['dissolve-ferrous-sulfate'],'scope':'Reported precursor-preparation batch; not the nanocrystal reactor charge.','evidence':CARB},
 {'id':'carbonate-stock','name':'Sodium carbonate aqueous solution','components':[{'material_id':'sodium-carbonate','quantities':{'mass':Q(16.40,'g',CARB),'amount':Q(157.7,'mmol',CARB,qualifier='As printed; inconsistent with reported mass for anhydrous Na2CO3.')}},{'material_id':'water','quantities':{'volume':Q(180,'mL',CARB)}}],'concentrations':{},'preparation_operation_ids':['dissolve-sodium-carbonate'],'scope':'Reported precursor-preparation batch; mass and amount discrepancy preserved.','evidence':CARB},
 {'id':'iron-oleate-stock','name':'Fe(II)-carbonate-derived iron oleate in excess oleic acid','components':[{'material_id':'ferrous-carbonate','quantities':{'mass':Q(5.69,'g',OLEATE),'amount':Q(51.4,'mmol',OLEATE,qualifier='As printed; mass and amount do not agree for nominal FeCO3.')}},{'material_id':'oleic-acid','quantities':{'mass':Q(102.4,'g',OLEATE),'amount':Q(362.4,'mmol',OLEATE)}}],'concentrations':{},'preparation_operation_ids':['mix-carbonate-oleic-acid','form-oleate-60c','cool-oleate','age-oleate','dry-oleate-60c','dry-oleate-120c'],'scope':'Quantified upstream precursor preparation. Fraction or volume charged to the selected nanocrystal condition is not reported.','evidence':OLEATE}
]
states=[
 ('nitrogen-saturated-water','Nitrogen-saturated water',['water','nitrogen'],'mixture'),
 ('conditioned-ferrous-sulfate','Separately degassed iron(II) sulfate under nitrogen',['ferrous-sulfate','nitrogen'],'mixture'),
 ('conditioned-sodium-carbonate','Separately degassed sodium carbonate under nitrogen',['sodium-carbonate','nitrogen'],'mixture'),
 ('degassed-oleic-acid','Degassed oleic acid',['oleic-acid'],'mixture'),
 ('nitrogen-saturated-oleic-acid','Nitrogen-saturated oleic acid',['degassed-oleic-acid','nitrogen'],'mixture'),
 ('carbonate-slurry','Precipitated FeCO3 in mother liquor',['ferrous-sulfate-stock','carbonate-stock'],'mixture'),
 ('filtered-carbonate','Filtered wet FeCO3',['carbonate-slurry'],'fraction'),
 ('carbonate-mother-liquor','Discarded carbonate mother liquor',['carbonate-slurry'],'waste'),
 ('washed-carbonate','Washed wet FeCO3 precursor',['filtered-carbonate','nitrogen-saturated-water'],'fraction'),
 ('carbonate-wash-liquor','Carbonate wash waste',['filtered-carbonate','nitrogen-saturated-water'],'waste'),
 ('oleate-charge','FeCO3 with excess oleic acid',['washed-carbonate','nitrogen-saturated-oleic-acid'],'mixture'),
 ('warm-oleate','Oleate mixture after 60 C formation',['oleate-charge'],'mixture'),
 ('cooled-oleate','Room-temperature oleate emulsion',['warm-oleate'],'mixture'),
 ('aged-oleate','Aged milky gray oleate emulsion',['cooled-oleate'],'mixture'),
 ('partly-dried-oleate','Oleate mixture after vacuum at 60 C',['aged-oleate'],'mixture'),
 ('nanocrystal-charge','Unspecified aliquot of undiluted iron-oleate stock',['iron-oleate-stock'],'reaction_batch'),
 ('heated-reaction','Heated iron-oleate reaction',['nanocrystal-charge'],'reaction_batch'),
 ('cubic-condition-mixture','Reaction state in selected late cubic window',['heated-reaction'],'reaction_batch')
]
r['material_states']=[state(i,n,p,k) for i,n,p,k in states]
ops=[]
def OP(i,a,label,e,ins,outs,params=None,desc='',stage='precursor_preparation',env='nitrogen / Schlenk conditions',endpoint=None,retained=None):
    dep=[ops[-1]['id']] if ops else []
    ops.append(operation(i,a,label,e,ins,outs,depends=dep,parameters=params or {},stage=stage,description=desc,environment=F(env,e),endpoint=endpoint or F(e=e),retained_fraction=retained))

OP('condition-apparatus','evacuate_refill','Condition apparatus with nitrogen',GENERAL,['nitrogen'],[],{'cycles':Q(4,'count',GENERAL),'pressure':Q(u='mbar',e=GENERAL)},'Four evacuation/refill cycles; absolute pressure and vessel volume not stated.')
OP('condition-water','gas_saturate','Saturate water with nitrogen',GENERAL,['water','nitrogen'],['nitrogen-saturated-water'],{'duration':Q(24,'h',GENERAL),'gas_flow':Q(u='mL/min',e=GENERAL)},'Water-conditioning temperature is not specified.')
OP('condition-salts','degas_store','Condition precursor salts separately under nitrogen',GENERAL,['ferrous-sulfate','sodium-carbonate','nitrogen'],['conditioned-ferrous-sulfate','conditioned-sodium-carbonate'],{'duration':Q(u='h',e=GENERAL),'temperature':Q(u='degC',e=GENERAL)},'Separate reagent conditioning, not a mixed-salt reaction.')
OP('degas-oleic-acid','degas','Degas oleic acid',GENERAL,['oleic-acid'],['degassed-oleic-acid'],{'temperature':Q(25,'degC',GENERAL),'duration':Q(1,'h',GENERAL),'pressure':Q(0.5,'mbar',GENERAL)},env='vacuum')
OP('saturate-oleic-acid','gas_saturate','Saturate oleic acid with nitrogen',GENERAL,['degassed-oleic-acid','nitrogen'],['nitrogen-saturated-oleic-acid'],{'duration':Q(u='h',e=GENERAL)})
OP('dissolve-ferrous-sulfate','dissolve','Prepare ferrous sulfate solution',CARB,['conditioned-ferrous-sulfate','nitrogen-saturated-water'],['ferrous-sulfate-stock'],desc='14.30 g (51.44 mmol) in 180 mL water; amounts belong to this upstream stock.')
OP('dissolve-sodium-carbonate','dissolve','Prepare sodium carbonate solution',CARB,['conditioned-sodium-carbonate','nitrogen-saturated-water'],['carbonate-stock'],desc='16.40 g (157.7 mmol as printed) in 180 mL water; retain the mass/amount conflict.')
OP('precipitate-carbonate','add_stir','Precipitate FeCO3',CARB,['ferrous-sulfate-stock','carbonate-stock'],['carbonate-slurry'],{'stirring_speed':Q(800,'rpm',CARB),'duration':Q(30,'min',CARB),'temperature':Q(u='degC',e=CARB,qualifier='Room temperature; numeric value not reported.'),'addition_rate':Q(u='mL/min',e=CARB,qualifier='Slow addition; numeric rate not reported.')},'Slowly add ferrous sulfate solution into sodium carbonate solution and stir at room temperature.')
OP('filter-carbonate','filter','Filter carbonate precipitate',CARB,['carbonate-slurry'],['filtered-carbonate','carbonate-mother-liquor'],desc='Schlenk frit; retain precipitate.',retained='filtered-carbonate')
OP('wash-carbonate','wash','Wash carbonate four times',CARB,['filtered-carbonate','nitrogen-saturated-water'],['washed-carbonate','carbonate-wash-liquor'],{'wash_count':Q(4,'count',CARB),'wash_volume_each':Q(120,'mL',CARB)},'Use wet precipitate directly; no drying. Recovered wet mass and yield of this preparation are not provided.',retained='washed-carbonate')
OP('mix-carbonate-oleic-acid','mix','Charge the reported Fe(II) oleate preparation',OLEATE,['washed-carbonate','nitrogen-saturated-oleic-acid'],['oleate-charge'],{'temperature':Q(u='degC',e=OLEATE,qualifier='Room temperature.'),'oleic_acid_to_fe_molar_ratio':Q(7,'mol/mol',OLEATE,basis='moles OA per mole Fe as stated')},'Charge 5.69 g (51.4 mmol as printed) FeCO3 and 102.4 g (362.4 mmol) OA. No inference that the whole preceding wet-precipitate batch equals this charge.')
OP('form-oleate-60c','heat_stir','Form oleate at 60 C',OLEATE,['oleate-charge'],['warm-oleate'],{'temperature':Q(60,'degC',OLEATE),'duration':Q(1,'h',OLEATE),'stirring_speed':Q(u='rpm',e=OLEATE)})
OP('cool-oleate','cool','Cool oleate mixture to room temperature',OLEATE,['warm-oleate'],['cooled-oleate'],{'temperature':Q(u='degC',e=OLEATE,qualifier='Room temperature.'),'cooling_rate':Q(u='degC/min',e=OLEATE)})
OP('age-oleate','stir','Stir oleate emulsion at room temperature',OLEATE,['cooled-oleate'],['aged-oleate'],{'duration':Q(24,'h',OLEATE),'temperature':Q(u='degC',e=OLEATE,qualifier='Room temperature.')},endpoint=F('milky gray emulsion',OLEATE))
OP('dry-oleate-60c','vacuum_heat','Remove water and CO2 at 60 C',OLEATE,['aged-oleate'],['partly-dried-oleate'],{'temperature':Q(60,'degC',OLEATE),'duration':Q(2,'h',OLEATE),'pressure':Q(u='mbar',e=OLEATE)},env='vacuum',endpoint=F('brownish-black mixture',OLEATE))
OP('dry-oleate-120c','vacuum_heat','Further dry oleate up to 120 C',OLEATE,['partly-dried-oleate'],['iron-oleate-stock'],{'temperature':Q(120,'degC',OLEATE,qualifier='heated up to'),'duration':Q(u='h',e=OLEATE,minimum=1,maximum=2),'pressure':Q(u='mbar',e=OLEATE)},env='vacuum')
OP('charge-undiluted-oleate','charge','Select undiluted oleate condition',COND+THERM,['iron-oleate-stock'],['nanocrystal-charge'],{'stock_mass':Q(u='g',e=THERM),'stock_volume':Q(u='mL',e=THERM),'ode_volume_fraction':Q(0,'vol%',COND,qualifier='Source says no ODE; zero is explicit, not missing.')},'No ODE for this condition. Three-neck round-bottom flask with Vigreux and distillation columns. The Fe(II) route is a documented precursor option; the S16 specimen branch is unspecified.',stage='synthesis')
OP('heat-to-nucleation','heat','Heat iron oleate',THERM,['nanocrystal-charge'],['heated-reaction'],{'heating_rate':Q(6,'degC/min',THERM),'temperature':Q(u='degC',e=THERM,qualifier='Exact selected-condition plateau not specified; generic method states 330-350 C depending on dilution.'),'pressure':Q(u='mbar',e=THERM)},'Generic methods report 330-350 C and full runs of 3-5 h; neither an exact plateau nor the 3-5 h hold is assigned to the selected early aliquot. Nucleation zero is a relative observation, not elapsed heating time.',stage='synthesis',endpoint=F('nucleation',COND))
OP('grow-cubic-condition','grow','Reach selected late cubic condition',COND,['heated-reaction'],['cubic-condition-mixture'],{'time_after_nucleation':Q(u='min',e=COND,minimum=40,maximum=60),'temperature':Q(u='degC',e=COND),'stirring_speed':Q(u='rpm',e=COND)},'The 40-60 min window is measured after nucleation. Do not add a separate 3-5 h hold to this selected condition.',stage='synthesis',endpoint=F('selected 40-60 min post-nucleation window',COND))
r['operations']=ops
p=product('figure-s16-60nm-context','Fe–O',COND,link='general_context',state=None,notes=['Curator evidence locator for the source figure condition; not an author-assigned physical batch ID.','Fe:OA 1:7, no ODE and 40-60 min after nucleation are explicit. Whether the pictured specimen used Fe(II) or Fe(III) carbonate is not given.','TEM sample phase cannot be inferred from an independently sealed pristine XRD aliquot.'])
p['source_sample_label']='Figure S16, 60 nm panel (lower right)'
p['composition']=F('Fe–O',COND,note='Iron-oxygen system only; exact atomic stoichiometry of this imaged sample is not established.')
p['phase']=F(e=COND+OXID,note='Unknown for this specimen. Routine handling may produce FeO plus Fe3O4 and/or gamma-Fe2O3; no pure magnetite or maghemite label assigned.')
p['morphology']=F('cubic nanocrystals',COND)
p['surface']=F(e=COND,note='Oleic acid is present in synthesis; exact bound-ligand identity, coverage and surface composition of this specimen are not measured.')
r['products']=[p]
r['measurements']=[measurement('s16-reported-characteristic-size',p['sample_id'],'characteristic_size',Q(60,'nm',COND,qualifier='Reported image/condition-map size label; definition and spread not supplied. Not normalized to diameter.'),'TEM',COND,conditions='SI Figure S16 lower-right panel linked by caption to Figure S14 no-ODE / 40-60 min condition; stock branch and post-synthetic oxidation history unresolved.')]
r['quality']['experimental_outcome']='reported_product'
r['quality']['review_scope']='One literature condition with a documented Fe(II)-derived precursor option. No physical experiment or independently reproduced batch is claimed. Main/SI preparation and condition panels inspected; figure-to-precursor-branch linkage remains unresolved.'
r['quality']['missing_fields']=[
 'Exact Fe(II) versus Fe(III) precursor branch used for the Figure S16 60 nm specimen.',
 'Iron-oleate amount/volume charged to the selected nanocrystal run; full upstream stock is not assumed to be used.',
 'Exact selected-condition growth plateau within the general 330-350 C method range; nucleation temperature and absolute elapsed time.',
 'Oleic-acid grade/lot for the selected condition; technical 90% and pure 99% are both listed for different paper activities.',
 'Selected-condition sampling/quench, purification solvents/amounts/cycles, centrifugation, yield and storage atmosphere/time.',
 'Numerical room temperature, slow-addition rate, oleate-stage stirring speeds and vacuum pressures.',
 'Exact isolated-product stoichiometry, phase fractions, oxidation state distribution and oxidation history.',
 'Definition/spread of the 60 nm size label and exact measured coordinates; no diameter or CIF label supplied.'
]
r['quality']['conflicts']=[
 'FeCO3 charge is printed as 5.69 g and 51.4 mmol; nominal FeCO3 molar mass does not reconcile them. Preserve both, without choosing a correction.',
 'Na2CO3 is printed as 16.40 g and 157.7 mmol; anhydrous formula does not reconcile them. Preserve both.',
 'Generic method reports 3-5 h total high-temperature holds, whereas selected SI morphology evidence is 40-60 min after nucleation. These describe different timing scopes and are not concatenated.',
 'FeO/wustite established under inert sealed XRD conditions does not establish phase purity of the separately handled TEM sample. FFT of oxidized material cannot distinguish magnetite from maghemite; EELS and magnetic discussion concern additional sample contexts.'
]
r['context_links']=[{'label':'Original article and associated supporting information','url':'https://doi.org/10.1021/acsnano.8b05032','relation':'primary_source'}]
target=OUT/'canonical'/f'{ID}.json'
target.write_text(json.dumps(r,indent=2,ensure_ascii=False),encoding='utf-8')

paths={n:BASE/'downloaded_papers'/f'10.1021_acsnano.8b05032{suffix}.pdf' for n,suffix in [('main',''),('si','_si_1')]}
audit={'record_id':ID,'audit_date':'2026-09-17','scope':'One partial protocol variant; source-local figure condition, not a new experimental batch. Fe(II) precursor branch retained as an option with unverified linkage to the selected figure specimen.','sources':{n:{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for n,p in paths.items()},'matching_si_verified':True,'visual_review':{'main_pdf_pages':[4,8,9],'si_pdf_pages':[9,10,12,14]},'selected_condition':{'Fe_to_OA_molar_ratio':'1:7','ODE':'none','time_after_nucleation_min':[40,60],'source':'SI Figure S14; Figure S16 lower-right panel','reported_size_nm':60,'size_definition':'not explicitly defined; recorded as characteristic_size, not diameter','shape':'cubic','source_sample_branch':'Fe(II) or Fe(III) unspecified'},'phase_boundaries':[{'context':'fresh inert sealed capillary samples, Fig3c','finding':'wustite FeO from either initial iron oxidation state','applies_to_selected_TEM_specimen':False},{'context':'routinely purified/air-exposed octapod, SI S12 FFT','finding':'FeO core and Fe3O4 and/or gamma-Fe2O3 outer region; FFT alone cannot distinguish these outer phases','applies_to_selected_TEM_specimen':False},{'context':'oxidized octapod, main Fig7 EELS tomography','finding':'Fe2+-rich interior and Fe3+-dominant outer region; authors infer wustite to maghemite through magnetite/mixed intermediates','applies_to_selected_TEM_specimen':False}], 'mass_amount_conflicts':r['quality']['conflicts'][:2],'missing_fields':r['quality']['missing_fields'],'training_policy':{'precursor_selection':True,'partial_protocol':True,'size_conditioned_recipe':False,'exact_structure_recipe':False},'out_of_scope':['No main/SI PDF copied into Site assets.','No pure Fe3O4 or gamma-Fe2O3 assignment.','No extrapolated workup, plateau temperature, batch amount or size distribution.','No additional recipe count created from characterization figures.']}
(OUT/f'{ID}-audit.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False),encoding='utf-8')
contribution={'material_system':'Fe–O','elements':['Fe','O'],'contains_materials':['Fe–O'],'architecture':'unresolved','family':'Iron oxides','primaryrecordid':ID,'source':{'source_id':SID,'doi':src['doi'],'url':src['url'],'locator':'Main pp. 159-160; SI Figures S14/S16'},'components':[{'role':'phase-unresolved iron oxide','material':'Fe–O'}],'parent_record_id':None,'scope':'One reviewed literature protocol variant; does not assert a measured physical batch or an exact figure-to-precursor-branch link.','phase_note':'Inert pristine wustite and air-oxidized core/shell observations are distinct sample contexts; selected isolated stoichiometry and phase are unresolved.','training_scope':['precursor_selection','partial_protocol'],'excluded_training':['size_conditioned_recipe','exact_structure_recipe'],'canonical_path':str(target)}
(OUT/f'{ID}-contribution.json').write_text(json.dumps(contribution,indent=2,ensure_ascii=False),encoding='utf-8')
print(target)
print('Materials',len(r['materials']),'stocks',len(r['stocks']),'operations',len(r['operations']),'figure observations',len(r['measurements']))
