"""Source-led complete-paper package. Writes only this external review directory."""
import json, sys, hashlib
from copy import deepcopy
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path('[local path redacted]')
OUT = ROOT / 'research-assets/deep-review-20260917/ir2005'
sys.path.insert(0, str(ROOT / 'recipe-atlas/scripts'))
from record_helpers import ev, fact, qty, source, record, material, state, operation, product, measurement

SID='stowell2005'; DOI='10.1021/nl050648f'; URL='https://doi.org/'+DOI
TITLE='Iridium Nanocrystal Synthesis and Surface Coating-Dependent Catalytic Activity'
AUTHORS='Cynthia A. Stowell and Brian A. Korgel'
SYNTH_IDS={'oa':'stowell-2005-ir-oa-oleylamine-290c','top':'stowell-2005-ir-top-290c','toab':'stowell-2005-ir-toab-270c','topb':'stowell-2005-ir-topb-270c'}
SIZE_ID='stowell-2005-ir-oa-size-selection'
CHAR_ID='stowell-2005-ir-characterization-methods'
ASSAY_ID='stowell-2005-ir-hydrogenation-assay'
CYCLE_IDS={x:'stowell-2005-ir-'+x+'-recycling-assay' for x in ['toab','topb']}
SRC=source(SID,DOI,TITLE,AUTHORS,2005,si='Matching 4-page SI verified by exact title, authors, affiliations and corresponding recipe/measurement content; all four pages read and visually inspected')
SRC['main_status']='All 5 main-article pages, Figures 1–5, both equations and bibliography read; every page and figure visually inspected'

def E(loc):return ev(SID,loc)
def Q(v=None,u='',loc='',**kw):return qty(v,u,evidence=E(loc),**kw)
CHEM='SI p. 1, Chemicals'
OA='SI pp. 1–2, Oleic Acid and Oleylamine Capped Iridium'
TOP='SI p. 2, Trioctylphosphine Capped Iridium'
SALTS='SI p. 3, Tetraoctylammonium Bromide or Tetraoctylphosphonium Bromide Capped Iridium'
CAT='SI p. 3, Catalysis; main p. 1204, batch hydrogenation conditions'
TEM='SI pp. 3–4, Transmission Electron Microscopy'
XRD='SI p. 4, Powder X-Ray Diffraction; main p. 1204, Figure 1B and discussion'
SAXS='SI p. 4, Small Angle X-Ray Scattering; main p. 1204, Figure 1C and Eq. 1'
GC='SI p. 4, Gas Chromatography/Mass Spectroscopy; main p. 1204'
F1='Main p. 1204, Figure 1 and associated text'
F2='Main pp. 1204–1205, Figure 2 and associated text'
F3='Main p. 1205, Figure 3 and associated text'
F4='Main p. 1206, Figure 4 and associated text'
F5='Main pp. 1206–1207, Figure 5 and associated text'

CONFLICTS=[
 {'id':'printed-ligand-volumes','source_locators':[OA], 'issue':'SI prints 0.08 µL oleic acid and 0.085 µL oleylamine. These unusually small amounts are legible in the source.', 'handling':'Preserved exactly with an unresolved-unit warning; not changed to mL or converted into a supposedly corrected recipe.'},
 {'id':'oa-formula-printing','source_locators':[CHEM], 'issue':'The Chemicals section prints oleic acid as C18H34O2H.', 'handling':'Named identity retained; canonical formula left null rather than silently correcting the printed formula. Conventional identity is not used to repair the source unannounced.'},
 {'id':'saxs-radius-wording','source_locators':[F1], 'issue':'Eq. 1 and the fit define R_av as mean radius and sigma as radius-distribution standard deviation, but one prose sentence calls the reported R_av values diameters.', 'handling':'Store 1.09 and 1.92 nm as author-derived radii using the explicit definition; retain the contradictory wording. Do not silently store them as diameters.'},
 {'id':'saxs-solvent','source_locators':['Main p. 1204, SAXS discussion','SI p. 4, SAXS method'], 'issue':'Main text describes Figure 1C particles dispersed in hexane; the SI SAXS method specifies cyclohexane.', 'handling':'Both reported solvent assignments retained with unresolved sample/method mapping.'},
 {'id':'toab-first-tof','source_locators':['Main p. 1205 body text','Main p. 1204 Figure 2 caption','Main p. 1206 body text and Figure 4 caption'], 'issue':'First-use TOAB TOF is 4 s^-1 in body text, 5 s^-1 in Figure 2/Figure 4 captions.', 'handling':'Separate source statements; never averaged or treated as independent trials.'},
 {'id':'toab-second-tof','source_locators':['Main p. 1206 body text and Figure 4 caption'], 'issue':'Cycle-2 TOAB TOF is 13 s^-1 in body text versus 14 s^-1 in Figure 4 caption.', 'handling':'Both source values retained.'},
 {'id':'pressure-basis','source_locators':[CAT], 'issue':'Main text gives 3 psig and 1.22 × 10^5 Pa together, without labeling the latter absolute. They are not the same pressure basis.', 'handling':'Store 3 psig explicitly as gauge and retain the printed Pa value with its unspecified basis; it is consistent with an approximate absolute counterpart at atmospheric ambient, not a replacement gauge value.'},
 {'id':'topb-distinct-catalytic-series','source_locators':[F2,F5], 'issue':'Figure 2 TOPB is initially active (TOF 270 s^-1), whereas the Figure 5 series is initially inactive (0 s^-1). Main p. 1207 explicitly distinguishes these samples.', 'handling':'Separate contextual series; do not overwrite, average, or infer identical surface coverage/batch.'},
 {'id':'supplier-wording','source_locators':[CHEM], 'issue':'The specific reagent list assigns dioctyl ether and TOP to Fluka, while a later general sentence says all solvents were analytical grade from Aldrich.', 'handling':'Specific named supplier is retained for named reagents; the broad solvent statement is retained for unspecified workup solvents.'},
 {'id':'topb-name-abbreviation','source_locators':['Main p. 1205 ligand discussion',CHEM], 'issue':'One discussion sentence abbreviates the name as tetraphosphonium bromide; abstract and SI identify tetraoctylphosphonium bromide (TOPB).', 'handling':'Use the explicit full SI chemical identity; preserve the wording inconsistency in the audit.'}
]

def base(rid,title,method,loc,kind='protocol_variant'):
 r=record(rid,title,'Ir','Noble-metal nanocrystals',method,deepcopy(SRC),loc,kind=kind)
 r['collection']='reviewed_literature';r['material'].update(elements=['Ir'],components=['Ir'],architecture='single_material')
 r['lineage']['recipe_family']='stowell2005-ir'
 r['quality']['review_scope']='Complete-paper review: all 5 main and 4 SI pages inspected. This record covers its named variant/procedure, not an independently reproduced or fully batch-paired experiment. Sample IDs identify evidence contexts; different IDs do not prove different physical specimens.'
 r['quality']['experimental_outcome']='reported_product'
 r['quality']['requested_tasks']=['precursor_selection','partial_protocol'] if kind!='procedure' else []
 r['intended_target']['phase']['note']='No independent prospective phase target supplied; observed assignments remain sample-specific.'
 r['intended_target']['size']['basis']='No prospective numerical size target supplied for this record.'
 if kind=='procedure':
  for key in ['composition','phase','morphology']:r['intended_target'][key]=fact(status='not_applicable',evidence=E(loc),note='Shared characterization/assay/fractionation procedure; not a new nanocrystal synthesis target.')
  r['intended_target']['size']=qty(unit='nm',status='not_applicable',evidence=E(loc),basis='No new nanocrystal synthesis target.')
 r['context_links']=[{'label':TITLE,'url':URL,'relation':'primary_source'}]
 return r

CHEMICALS={
 'ir-precursor':('(Methylcyclopentadienyl)(1,5-cyclooctadiene)iridium','C14H19Ir','metal_precursor',99,'Strem'),
 'diol':('1,2-Hexadecanediol','C16H34O2','reducing_agent',90,'Aldrich'),
 'dioctyl-ether':('Dioctyl ether','C16H34O','solvent',97,'Fluka'),
 'oa':('Oleic acid',None,'ligand',65,'Fluka'),
 'oam':('Oleylamine','C18H37N','ligand',70,'Fluka'),
 'top':('Trioctylphosphine (TOP)','C24H51P','ligand_and_solvent',90,'Fluka'),
 'toab':('Tetraoctylammonium bromide (TOAB)','C32H68BrN','ligand',98,'Aldrich'),
 'topb':('Tetraoctylphosphonium bromide (TOPB)','C32H68BrP','ligand',97,'Aldrich'),
 'decene':('1-Decene','C10H20','assay_substrate',94,'Aldrich'),
 'decane':('Decane','C10H22','assay_product_and_listed_chemical',99,'Aldrich'),
 'nitrogen':('Nitrogen','N2','process_gas',None,None),
 'hydrogen':('Hydrogen','H2','assay_reagent',None,None),
 'hexanol':('Hexanol','C6H14O','antisolvent',None,'Aldrich'),
 'chloroform':('Chloroform','CHCl3','solvent',None,'Aldrich'),
 'ethanol':('Ethanol','C2H6O','antisolvent',None,'Aldrich'),
 'cyclohexane':('Cyclohexane','C6H12','solvent',None,'Aldrich'),
 'hexane':('Hexane','C6H14','solvent',None,'Aldrich'),
 'toluene':('Toluene','C7H8','solvent',None,'Aldrich')
}
def mat(k,loc,qs=None,stage='synthesis',role=None,notes=None):
 name,formula,default_role,purity,supplier=CHEMICALS[k];qs=deepcopy(qs or {});notes=list(notes or [])
 if purity is not None:qs['purity']=Q(purity,'%',CHEM,basis='Reported supplier purity, not independently assayed')
 if supplier:notes.append('Supplier: '+supplier+'.')
 if k in ['ir-precursor','diol','dioctyl-ether','oa','oam','top','toab','topb','decene','decane']:notes.append('Authors state reagents were used without further purification.')
 if k=='oa':notes.append('SI prints formula C18H34O2H; formula is unresolved rather than silently normalized.')
 if k=='ir-precursor':notes.append('Source condensed formula (C6H7)(C8H12)Ir; purchased precursor, not synthesized in this work.')
 if purity is None and supplier:notes.append('General SI solvent statement: analytical grade; no numerical purity or lot provided.')
 return material(k,name,formula,role or default_role,stage,E(loc)+E(CHEM),qs,notes)

def add_product(r,sid,label,loc,surface=None,phase=None,stateid=None,link='general_context',notes=None,parent=None):
 p=product(sid,'Ir',E(loc),link=link,state=stateid,phase=phase,surface=surface,notes=notes)
 p['source_sample_label']=label;p['parent_sample_id']=parent;r['products'].append(p);return p
def add_measure(r,mid,sid,prop,v=None,u='',loc='',technique='',conditions='',**kw):
 m=measurement(mid,sid,prop,Q(v,u,loc,**kw),technique,E(loc),conditions=conditions);r['measurements'].append(m);return m
def op(r,oid,action,label,loc,ins,outs,**kw):
 r['operations'].append(operation(oid,action,label,E(loc),ins,outs,**kw))
def st(r,sid,name,parents=None,kind='mixture'):r['material_states'].append(state(sid,name,parents,kind))
def stock(r,sid,name,components,preps,loc,scope):
 r['stocks'].append({'id':sid,'name':name,'components':components,'concentrations':{},'preparation_operation_ids':preps,'scope':scope,'evidence':E(loc)})
def common_gaps():return ['Physical synthesis batch IDs and exact mapping of recipe/workup variants to figure specimens are not supplied.',
 'Reagent lots/storage, stirring rate, heating ramp, gas purity/flow rate and pressure are not fully specified.',
 'Centrifugation speed/time and workup solvent volumes are not supplied.',
 'Final dispersion concentration, isolated mass/yield and product storage are not supplied.',
 'No measured sample atomic coordinates or CIF are provided.']

RECORDS=[]
for ligand in ['oa','top']:
 loc=OA if ligand=='oa' else TOP;rid=SYNTH_IDS[ligand]
 name='Oleic-acid/oleylamine' if ligand=='oa' else 'TOP'
 r=base(rid,f'Stowell and Korgel (2005) · {name}-capped Ir at 290 °C','Hot injection with hexadecanediol reduction',loc)
 precursor_mass=.19 if ligand=='oa' else .38;diol_mass=.195 if ligand=='oa' else .39
 solvent='dioctyl-ether' if ligand=='oa' else 'top';reactor_v=7.5 if ligand=='oa' else 10;feed_v=1 if ligand=='oa' else 2
 r['materials']=[mat('ir-precursor',loc,{'mass':Q(precursor_mass,'g',loc,basis='Precursor injection flask')}),mat('diol',loc,{'mass':Q(diol_mass,'g',loc,basis='Hot reaction flask')}),
 mat(solvent,loc,{'reactor_volume':Q(reactor_v,'mL',loc),'feed_volume':Q(feed_v,'mL',loc)}),mat('nitrogen',loc),
 mat('hexanol',loc,{'volume_per_wash':Q(None,'mL',loc)},stage='workup'),mat('chloroform',loc,{'redispersion_volume':Q(None,'mL',loc)},stage='workup')]
 if ligand=='oa':
  for k,v in [('oa',.08),('oam',.085)]:r['materials'].append(mat(k,loc,{'volume':Q(v,'µL',loc,qualifier='Printed unit/amount retained; correctness unresolved',raw_text=str(v)+' µl')}))
  for k in ['ethanol','cyclohexane','toluene']:r['materials'].append(mat(k,loc,stage='fractionation' if k=='ethanol' else 'workup',notes=['Optional size-selection antisolvent.' if k=='ethanol' else 'Reported redispersion alternative, not a simultaneous addition.']))
 r['quality']['missing_fields']=common_gaps()+['Injection rate/duration and post-injection temperature trajectory are not supplied.']
 if ligand=='oa':r['quality']['conflicts']=[CONFLICTS[0]['issue']+' '+CONFLICTS[0]['handling'],CONFLICTS[1]['issue']]
 r['quality']['experimental_outcome']='reported_product'
 components=[{'material_id':'ir-precursor','quantities':{'mass':Q(precursor_mass,'g',loc)}},{'material_id':solvent,'quantities':{'volume':Q(feed_v,'mL',loc)}}]
 stock(r,'precursor-feed-stock','Ir precursor solution for injection',components,['prepare-feed','deoxygenate-feed'],loc,'Source reports precursor mass and solvent volume; final measured solution volume and concentration are not supplied.')
 reactor_inputs=['diol',solvent]+(['oa','oam'] if ligand=='oa' else [])
 st(r,'reactor-charge','Reductant/ligand/solvent charge',reactor_inputs);st(r,'reactor-deoxygenated','Deoxygenated reaction charge',['reactor-charge']);st(r,'hot-reactor','Hot reaction medium',['reactor-deoxygenated'])
 st(r,'feed-mixture','Ir precursor in feed solvent',['ir-precursor',solvent]);st(r,'feed-ready','Deoxygenated precursor feed',['feed-mixture'],'stock');st(r,'reaction-product','Product reaction dispersion',['hot-reactor','feed-ready'],'reaction_batch')
 op(r,'prepare-reactor','load','Prepare the reaction flask',loc,reactor_inputs,['reactor-charge'],parameters={'flask_capacity':Q(25,'mL',loc),'necks':Q(3,'count',loc),'solvent_volume':Q(reactor_v,'mL',loc),'diol_mass':Q(diol_mass,'g',loc)},description='Three-neck round-bottom flask. OA route specifies two septa and a condenser/stopcock on the third neck, connected to a Schlenk line; TOP route inherits flask preparation explicitly.')
 inherited='reported' if ligand=='oa' else 'inherited'
 op(r,'deoxygenate-reactor','freeze_pump_thaw','Deoxygenate the reaction charge',loc,['reactor-charge'],['reactor-deoxygenated'],depends=['prepare-reactor'],stage='precursor_preparation',parameters={'cycles':Q(3,'count',OA if ligand=='top' else loc,status=inherited,basis='TOP: flasks prepared as in preceding OA method' if ligand=='top' else 'Directly stated'), 'vacuum_pressure':Q(None,'Pa',loc)})
 op(r,'heat-reactor','heat','Heat the reaction medium under nitrogen',loc,['reactor-deoxygenated','nitrogen'],['hot-reactor'],depends=['deoxygenate-reactor'],parameters={'temperature':Q(290,'°C',loc),'heating_rate':Q(None,'°C/min',loc)},environment=fact('Nitrogen flow' if ligand=='oa' else 'Nitrogen',E(loc if ligand=='oa' else 'Main p. 1205, TOP synthesis')))
 op(r,'prepare-feed','dissolve','Prepare the separate precursor injection solution',loc,['ir-precursor',solvent],['feed-mixture'],stage='precursor_preparation',branch='precursor-feed',parameters={'flask_capacity':Q(25,'mL',loc),'necks':Q(3,'count',loc),'ir_precursor_mass':Q(precursor_mass,'g',loc),'solvent_volume':Q(feed_v,'mL',loc)})
 op(r,'deoxygenate-feed','freeze_pump_thaw','Deoxygenate the separate precursor feed',loc,['feed-mixture'],['feed-ready'],depends=['prepare-feed'],stage='precursor_preparation',branch='precursor-feed',parameters={'cycles':Q(3,'count',OA,status='inherited',basis='Same deoxygenation/flask preparation as preceding described method'), 'temperature':Q(None,'°C',loc,qualifier='Room temperature for OA; inherited previous flask preparation for TOP')},description='OA feed remains at room temperature; no numeric room temperature is supplied.')
 op(r,'inject-and-react','inject_then_heat','Inject precursor and allow reduction/growth',loc,['hot-reactor','feed-ready'],['reaction-product'],depends=['heat-reactor','deoxygenate-feed'],parameters={'injection_reactor_temperature':Q(290,'°C',loc),'reaction_duration':Q(2 if ligand=='oa' else 1.5,'h',loc),'injection_duration':Q(None,'s',loc)},endpoint=fact('Dark brown liquid' if ligand=='oa' else 'Brown product',E(loc)))
 if ligand=='top':
  st(r,'cooled-product','Cooled TOP reaction product',['reaction-product']);op(r,'cool-product','cool','Cool after heating',loc,['reaction-product'],['cooled-product'],depends=['inject-and-react'],parameters={'end_temperature':Q(None,'°C',loc),'cooling_duration':Q(None,'min',loc)})
  st(r,'washed-product','TOP-capped Ir after hexanol/chloroform centrifugation',['cooled-product','hexanol','chloroform'],'product')
  op(r,'wash-product','centrifuge_and_wash','Clean using alternating hexanol/chloroform solutions',loc,['cooled-product','hexanol','chloroform'],['washed-product'],depends=['cool-product'],stage='workup',parameters={'wash_count':Q(None,'count',loc),'centrifugation_force':Q(None,'g',loc),'centrifugation_duration':Q(None,'min',loc)},description='Number of washes and exact fraction transfers are not independently specified for TOP; do not import the OA count.')
 else:
  for sid,state_name,parents,kind in [('initial-precipitate','Initial hexanol precipitate',['reaction-product','hexanol'],'fraction'),('discarded-supernatant','Discarded initial supernatant',['reaction-product','hexanol'],'waste'),('washed-product','OA/oleylamine-capped Ir after repeat washing',['initial-precipitate','chloroform','hexanol'],'product'),('redispersed-product','Optional redispersed product',['washed-product'],'product')]:st(r,sid,state_name,parents,kind)
  op(r,'initial-isolation','precipitate_and_centrifuge','Precipitate with hexanol and retain nanocrystals','Main p. 1203, OA/oleylamine purification',['reaction-product','hexanol'],['initial-precipitate','discarded-supernatant'],depends=['inject-and-react'],stage='workup',retained_fraction='initial-precipitate',parameters={'centrifugation_duration':Q(None,'min','Main p. 1203',qualifier='Brief'),'centrifugation_force':Q(None,'g','Main p. 1203')},description='Supernatant is explicitly discarded; cooling conditions are not supplied.')
  op(r,'repeat-wash','redisperse_precipitate_centrifuge','Repeat chloroform/hexanol washing','Main p. 1203, OA/oleylamine purification',['initial-precipitate','chloroform','hexanol'],['washed-product'],depends=['initial-isolation'],stage='workup',retained_fraction='washed-product',parameters={'post_initial_wash_cycles':Q(2,'count','Main p. 1203',status='calculated',qualifier='Narrative count: one described wash, repeated again',basis='Excludes initial precipitation',derivation='One described wash plus one repeat gives two post-initial wash cycles.'),'chloroform_volume':Q(None,'mL',loc),'hexanol_volume':Q(None,'mL',loc)},description='After the initial isolation, redispersion/reprecipitation/centrifugation is described once and repeated again; source does not specify solvent volumes or centrifugation settings.')
  op(r,'optional-redispersion','redisperse','Optional redispersion in a nonpolar solvent',loc,['washed-product'],['redispersed-product'],depends=['repeat-wash'],stage='workup',branch='optional-redispersion',optional=True,parameters={'solvent_volume':Q(None,'mL',loc)},description='Chloroform, cyclohexane and toluene are alternatives, not simultaneous inputs.')
  r['operations'][-1]['optional_inputs']=['chloroform','cyclohexane','toluene']
  r['condition_options']=[{'id':'redispersion-'+k,'label':'Optional '+CHEMICALS[k][0]+' redispersion','parameters':{'volume':Q(None,'mL',loc)},'evidence':E(loc)} for k in ['chloroform','cyclohexane','toluene']]
 add_product(r,ligand+'-method-product',('OA/oleylamine' if ligand=='oa' else name)+'-capped Ir method product',loc,surface=name+'-capped',stateid='washed-product',link='explicit',notes=['Composition and ligand formulation are linked to this method; numerical figure outcomes remain separately scoped.'])
 if ligand=='oa':
  add_product(r,'oa-purified-family','OA/oleylamine-coated particles after purification','Main p. 1203',surface='Oleic-acid/oleylamine-coated')
  add_measure(r,'oa-family-size-range','oa-purified-family','diameter',u='nm',loc='Main p. 1203',minimum=1.5,maximum=5,qualifier='Purified formulation-wide range; not one mean',technique='TEM-associated reported size range')
  for sample,label,v,tech,phase in [('oa-fig1a','Figure 1A',4,'TEM',None),('oa-fig1d','Figure 1D',5,'HRTEM','face-centered cubic'),('oa-xrd','Figure 1B',5.3,'Scherrer analysis of XRD','face-centered cubic'),('oa-tem-average','Mean TEM diameter mentioned in XRD discussion',5,'TEM',None)]:
   add_product(r,sample,label,F1,surface='Oleic-acid/oleylamine-coated',phase=phase,notes=['Do not identify separate Figure 1 panels solely by similar diameter.'])
   add_measure(r,sample+'-size',sample,'diameter',v,'nm',F1,tech,approximate=sample=='oa-fig1a',status='author_derived' if sample=='oa-xrd' else 'reported',qualifier='Crystallite-size estimate by Scherrer broadening' if sample=='oa-xrd' else 'Single imaged particle' if sample=='oa-fig1d' else '')
 else:
  p=add_product(r,'top-fig3c','Figure 3C',F3,surface='TOP-coated');p['morphology']=fact('Irregular, strongly polydisperse particles',E(F3))
  add_measure(r,'top-size-range',p['sample_id'],'diameter',u='nm',loc=F3,minimum=10,maximum=100,qualifier='Reported range, not a mean',technique='TEM')
 RECORDS.append(r)

for ligand in ['toab','topb']:
 # The four source variants are independently parameterized; equal masses do not imply equal molar ligand concentrations.
 r=base(SYNTH_IDS[ligand],f'Stowell and Korgel (2005) · {ligand.upper()}-capped Ir at 270 °C','Single-flask thermal reduction with 1,2-hexadecanediol',SALTS)
 if ligand=='toab':r['revision']=2
 r['materials']=[mat('ir-precursor',SALTS,{'mass':Q(.2,'g',SALTS)}),mat('diol',SALTS,{'mass':Q(.2,'g',SALTS)}),mat('dioctyl-ether',SALTS,{'volume':Q(7,'mL',SALTS)}),mat(ligand,SALTS,{'mass':Q(.76,'g',SALTS)}),mat('nitrogen','Main p. 1205'),mat('ethanol',SALTS,{'rinse_volume':Q(None,'mL',SALTS)},stage='workup')]
 st(r,'charge','Single-flask reaction charge',['ir-precursor','diol','dioctyl-ether',ligand]);st(r,'deoxygenated','Deoxygenated charge',['charge']);st(r,'reaction','Black reaction dispersion',['deoxygenated'],'reaction_batch');st(r,'isolated','Particles after one ethanol rinse',['reaction','ethanol'],'product')
 op(r,'load','load','Charge one three-neck round-bottom flask',SALTS,['ir-precursor','diol','dioctyl-ether',ligand],['charge'],parameters={'capacity':Q(25,'mL',SALTS),'necks':Q(3,'count',SALTS)})
 op(r,'deoxygenate','freeze_pump_thaw','Perform three freeze–pump–thaw cycles',SALTS,['charge'],['deoxygenated'],depends=['load'],stage='precursor_preparation',parameters={'cycles':Q(3,'count',SALTS),'pressure':Q(None,'Pa',SALTS),'cycle_duration':Q(None,'min',SALTS)})
 op(r,'heat','heat','Heat the single-flask formulation',SALTS,['deoxygenated','nitrogen'],['reaction'],depends=['deoxygenate'],parameters={'temperature':Q(270,'°C',SALTS),'duration':Q(30,'min',SALTS,qualifier='Reported heating duration; ramp/hold split unspecified')},environment=fact('Nitrogen',E('Main p. 1205')),endpoint=fact('Black liquid',E(SALTS)))
 op(r,'ethanol-isolation','rinse_and_isolate','Isolate using one ethanol rinse',SALTS,['reaction','ethanol'],['isolated'],depends=['heat'],stage='workup',retained_fraction='isolated',parameters={'rinse_count':Q(1,'count',SALTS),'ethanol_volume':Q(None,'mL',SALTS)},description='Separation mechanics and cooling conditions are unspecified. More extensive antisolvent treatment can remove ligands; it is not silently added to this procedure.')
 add_product(r,ligand+'-method-product',ligand.upper()+' method product',SALTS,surface=ligand.upper()+'-capped',stateid='isolated',link='explicit')
 panel='A' if ligand=='toab' else 'B';s=add_product(r,ligand+'-fig3','Figure 3'+panel,F3,surface=ligand.upper()+'-capped',notes=['Described as crystalline, but Figure 1 FCC assignment belongs to the OA/oleylamine formulation.', 'Exact synthesis batch and preparation-to-Figure-3 linkage are not supplied.'])
 s['phase']=fact(evidence=E(F3),note='Crystalline is reported; this formulation-specific phase is not assigned explicitly.')
 add_measure(r,ligand+'-size-range',s['sample_id'],'diameter',u='nm',loc=F3,minimum=1.5 if ligand=='toab' else 2,maximum=3 if ligand=='toab' else 5,technique='TEM',qualifier='Reported figure size range, not mean ± spread')
 if ligand=='topb':add_measure(r,'topb-tem-mean',s['sample_id'],'diameter',4,'nm',F3,'TEM',basis='Mean diameter in body text; not the distinct approximately 5 nm Figure 2 catalyst')
 r['quality']['missing_fields']=common_gaps()+['Ethanol isolation mechanics and cooling endpoint are not reported.']
 r['products'][0]['notes'].append('Five-to-ten antisolvent precipitations are a separate qualitative over-washing observation, not this one-rinse recipe. See coverage.json.')
 if ligand=='toab':r['quality']['review_scope']+=' Revision 2 supersedes the selected-only record; contextual catalytic measurements now reside in the shared assay/recycling records, not as additional synthesis batches.'
 RECORDS.append(r)

# Optional fractionation is a distinct shared procedure, not a fifth Ir synthesis.
r=base(SIZE_ID,'Stowell and Korgel (2005) · Optional OA/oleylamine Ir size selection','Size-selective precipitation','Main pp. 1203–1204; SI p. 2',kind='procedure')
r['lineage']['parent_record_id']=SYNTH_IDS['oa']
r['materials']=[material('oa-ir-input','Purified OA/oleylamine-coated Ir nanocrystals','Ir','product_input','fractionation',E('Main p. 1203'),{'amount':Q(None,'g','Main p. 1203')},['Physical parent batch unknown.']),mat('chloroform','Main p. 1203',stage='fractionation'),mat('ethanol','Main p. 1203',stage='fractionation')]
st(r,'starting-dispersion','Starting Ir dispersion',['oa-ir-input','chloroform']);st(r,'fraction-small','First described SAXS size fraction',['starting-dispersion','ethanol'],'fraction');st(r,'fraction-large','Second described SAXS size fraction',['starting-dispersion','ethanol'],'fraction')
op(r,'disperse','disperse','Disperse product in chloroform','Main p. 1203',['oa-ir-input','chloroform'],['starting-dispersion'],stage='fractionation',parameters={'volume':Q(None,'mL','Main p. 1203')})
op(r,'size-select','size_selective_precipitation','Obtain size-selected fractions using ethanol','Main pp. 1203–1204; Figure 1C',['starting-dispersion','ethanol'],['fraction-small','fraction-large'],depends=['disperse'],stage='fractionation',parameters={'ethanol_volume':Q(None,'mL','Main p. 1203'),'fractionation_rounds':Q(None,'count','Main p. 1203')},description='The two Figure 1C fractions are explicitly from one reaction. Exact collection order, solvent ratios and retained pellet/supernatant mapping are not reported.')
parent=add_product(r,'oa-selection-parent','Common synthesis reaction underlying both Figure 1C fractions',F1,surface='Oleic-acid/oleylamine-coated')
for name,radius,sigma,stateid,symbol in [('small',1.09,.283,'fraction-small','open square'),('large',1.92,.635,'fraction-large','open circle')]:
 p=add_product(r,'oa-saxs-'+name,'Figure 1C '+symbol+' series',F1,surface='Oleic-acid/oleylamine-coated',stateid=stateid,parent=parent['sample_id'],notes=['Shared parent reaction is explicit; link to an exact quantified synthesis run and fractionation procedure is incomplete.', 'Main text says hexane; SI method says cyclohexane.'])
 add_measure(r,'saxs-'+name+'-radius',p['sample_id'],'radius',radius,'nm',F1,'Gaussian-distribution spherical SAXS fit',status='author_derived',qualifier='R_av is radius by model definition; one source sentence inconsistently calls it diameter')
 add_measure(r,'saxs-'+name+'-radius-sigma',p['sample_id'],'radius_standard_deviation',sigma,'nm',F1,'Gaussian-distribution spherical SAXS fit',status='author_derived',basis='Sigma of fitted radius distribution; not diameter spread or SEM')
r['quality']['missing_fields']=['Fractionation volumes, increments, cycle count, endpoints and fraction-retention choices are unreported.','Exact parent batch and aliquot identities are unreported.','SAXS solvent and radius/diameter prose discrepancy remain unresolved.']
r['quality']['conflicts']=[CONFLICTS[2]['issue'],CONFLICTS[3]['issue']]
RECORDS.append(r)

# Shared characterization procedures preserve alternatives; none establishes cross-figure specimen identity.
r=base(CHAR_ID,'Stowell and Korgel (2005) · Structural characterization procedures','TEM/HRTEM, XRD and SAXS specimen preparation and measurement','SI pp. 3–4',kind='procedure')
r['materials']=[material('ir-specimen','Ir nanocrystal specimen, ligand/batch selected separately','Ir','sample','characterization',E('SI pp. 3–4'),notes=['A procedure input class, not a new physical sample.']),
mat('chloroform',TEM,stage='characterization'),mat('cyclohexane',SAXS,stage='characterization'),mat('hexane','Main p. 1204 SAXS discussion',stage='characterization'),
material('carbon-copper-grid','Carbon-coated copper TEM grid',None,'support','characterization',E(TEM),{'mesh':Q(200,'mesh',TEM)}),
material('quartz-substrate','Quartz XRD substrate',None,'support','characterization',E(XRD)),
material('silver-behenate','Silver behenate',None,'calibration_standard','characterization',E(SAXS),notes=['Scattering-angle calibration standard; SI condensed formula retained in coverage inventory.']),
material('kapton-window','Kapton sample-holder windows',None,'sample_container_window','characterization',E(SAXS))]
for sid,label,parents in [('tem-grid','Drop-cast TEM specimen',['ir-specimen','chloroform','carbon-copper-grid']),('xrd-substrate','Drop-cast XRD specimen',['ir-specimen','chloroform','quartz-substrate']),('saxs-cell','SAXS dispersion in windowed holder',['ir-specimen','kapton-window'])]:st(r,sid,label,parents,'aliquot')
op(r,'prepare-tem','drop_cast','Prepare TEM specimens',TEM,['ir-specimen','chloroform','carbon-copper-grid'],['tem-grid'],stage='characterization',branch='tem',parameters={'grid_mesh':Q(200,'mesh',TEM),'dispersion_concentration':Q(None,'mg/mL',TEM,qualifier='Dilute')})
op(r,'acquire-tem','measure','Acquire TEM or HRTEM',TEM,['tem-grid'],[],depends=['prepare-tem'],stage='characterization',branch='tem',description='Alternative instrument modes, not sequential voltage steps: JEOL 2010F HRTEM at 200 kV or Phillips EM208 low-resolution TEM at 120 kV. Which mode applies to every image is not specified.')
r['condition_options']=[{'id':'hrtem','label':'JEOL 2010F HRTEM','parameters':{'accelerating_voltage':Q(200,'kV',TEM)},'evidence':E(TEM)},{'id':'lrtem','label':'Phillips EM208 LRTEM','parameters':{'accelerating_voltage':Q(120,'kV',TEM)},'evidence':E(TEM)}]
op(r,'prepare-xrd','drop_cast','Prepare powder XRD specimen',XRD,['ir-specimen','chloroform','quartz-substrate'],['xrd-substrate'],stage='characterization',branch='xrd')
op(r,'acquire-xrd','measure','Acquire powder XRD',XRD,['xrd-substrate'],[],depends=['prepare-xrd'],stage='characterization',branch='xrd',parameters={'radiation_wavelength':Q(1.54,'Å',XRD)},description='Bruker-Nonius powder diffractometer (SI spelling Burker-Nonius), Cu Kα radiation. Scan step, acquisition time and line-broadening corrections are not supplied.')
op(r,'prepare-saxs','prepare_dispersion','Prepare SAXS dispersion',SAXS,['ir-specimen','kapton-window'],['saxs-cell'],stage='characterization',branch='saxs',description='SI specifies cyclohexane; main Figure 1C text specifies hexane. Solvent assignment remains unresolved; alternatives are not mixed.')
r['operations'][-1]['optional_inputs']=['cyclohexane','hexane']
op(r,'acquire-saxs','calibrate_and_measure','Calibrate and acquire SAXS',SAXS,['saxs-cell','silver-behenate'],[],depends=['prepare-saxs'],stage='characterization',branch='saxs',parameters={'generator_power':Q(3,'kW',SAXS),'xray_wavelength':Q(.154,'nm','Main p. 1204, SAXS discussion')},description='Rotating copper-anode generator, Bruker Nonius/Molecular Metrology; silver-behenate angle calibration, Kapton windows, corrections for background and sample absorption. Fit Eq. 1 using isolated spherical particles and a Gaussian radius distribution.')
r['quality']['experimental_outcome']='not_established'
r['quality']['missing_fields']=['Per-figure physical specimen IDs, sample concentrations, cast volumes and drying details are missing.','XRD acquisition/line-broadening settings and complete SAXS acquisition/fit settings are missing.','Main/SI SAXS solvent assignment is unresolved.','No raw scattering data, measured CIF or direct atomic-coordinate model is supplied.']
r['quality']['conflicts']=[CONFLICTS[3]['issue']]
RECORDS.append(r)

def assay_base(rid,title):
 r=base(rid,title,'1-Decene hydrogenation assay and GC/MS',CAT,kind='procedure')
 r['materials']=[material('ir-catalyst','Ligand-capped Ir catalyst, selected sample','Ir','catalyst','characterization',E(CAT),{'mass':Q(None,'g',CAT)},['Ligand formulation and sample selection are scoped separately; exact physical synthesis batch unknown.']),mat('decene',CAT,{'decene_to_ir_mass_ratio':Q(1000,'g/g',CAT,basis='1-decene mass divided by reported Ir nanocrystal/iridium mass; ligand correction unspecified')},stage='characterization'),mat('hydrogen',CAT,stage='characterization'),mat('decane',GC,stage='characterization',notes=['Purchased decane is listed; precise calibration-standard preparation is not reported.'])]
 stock(r,'catalyst-feed','Ir catalyst dispersed in 1-decene',[{'material_id':'ir-catalyst','quantities':{'mass':Q(None,'g',CAT)}},{'material_id':'decene','quantities':{'volume':Q(None,'mL',CAT)}}],['prepare-catalyst-feed'],CAT,'Feed concentration and volume not supplied; do not infer them from the final mass ratio and total assay volume.')
 st(r,'substrate-reactor','1-Decene under hydrogen',['decene','hydrogen']);st(r,'catalyst-feed-state','Ir in 1-decene',['catalyst-feed'],'stock');st(r,'assay-mixture','Hydrogenation mixture after catalyst injection',['substrate-reactor','catalyst-feed-state'],'reaction_batch');st(r,'gc-aliquots','Time-series GC/MS aliquots',['assay-mixture'],'aliquot');st(r,'recovered-catalyst','Ir particles recovered after vacuum evaporation',['assay-mixture'],'product')
 op(r,'prepare-reactor','heat_and_bubble_gas','Prepare hydrogenation substrate reactor',CAT,['decene','hydrogen'],['substrate-reactor'],stage='characterization',parameters={'reactor_capacity':Q(100,'mL',CAT),'temperature':Q(75,'°C',CAT),'hydrogen_pressure_gauge':Q(3,'psig',CAT),'pressure_pa_as_printed':Q(122000,'Pa','Main p. 1204',qualifier='Source leaves pressure basis unlabeled; approximately absolute counterpart of 3 psig at atmospheric ambient')},environment=fact('Hydrogen bubbled through 1-decene',E(CAT)))
 op(r,'prepare-catalyst-feed','disperse','Prepare catalyst dispersion in 1-decene',CAT,['ir-catalyst','decene'],['catalyst-feed-state'],stage='characterization',branch='catalyst-feed',parameters={'feed_volume':Q(None,'mL',CAT)})
 op(r,'inject-catalyst','inject','Start catalytic reaction by injecting Ir dispersion',CAT,['substrate-reactor','catalyst-feed-state'],['assay-mixture'],depends=['prepare-reactor','prepare-catalyst-feed'],stage='characterization',parameters={'total_liquid_volume':Q(15,'mL','Main p. 1204'),'decene_to_ir_mass_ratio':Q(1000,'g/g',CAT),'transient_temperature':Q(70,'°C','SI p. 3, Catalysis'),'recovered_temperature':Q(75,'°C','SI p. 3, Catalysis'),'temperature_recovery_time':Q(1,'min','SI p. 3, Catalysis')})
 op(r,'sample-time-series','withdraw_aliquots','Collect assay aliquots at the stated schedule',CAT,['assay-mixture'],['gc-aliquots'],depends=['inject-catalyst'],stage='characterization',parameters={'early_interval':Q(1,'min',CAT),'early_window_end':Q(20,'min',CAT),'middle_interval':Q(5,'min',CAT),'middle_window_end':Q(60,'min',CAT),'late_interval':Q(10,'min',CAT),'aliquot_volume':Q(None,'mL',CAT)},description='Aliquots enter screw-cap GC vials. Exact zero-time convention, individual sample sizes and assay endpoint vary or remain unspecified; sampling times are not independent synthesis experiments.')
 op(r,'gc-ms','measure','Quantify 1-decene/decane by calibrated GC/MS',GC,['gc-aliquots'],[],depends=['sample-time-series'],stage='characterization',description='SI specifies Hewlett-Packard 5890 Series II; main also allows Finnigan MAT GCQ. Calibration assesses relative decene/decane amounts. Purchased decane is inventoried but its use as a prepared calibration standard is not explicit. Column, oven program, standards concentrations, response factors and detection limit are unreported.')
 op(r,'recover-catalyst','vacuum_evaporate','Recover catalyst by evaporating liquid',CAT,['assay-mixture'],['recovered-catalyst'],depends=['inject-catalyst'],stage='characterization',branch='recovery',parameters={'vacuum_pressure':Q(None,'Pa',CAT),'temperature':Q(None,'°C',CAT),'duration':Q(None,'min',CAT)},description='The text states later recovery by vacuum evaporation; exact handling of sampled versus bulk catalyst and inter-cycle mass recovery are not reported.')
 r['quality']['experimental_outcome']='reported_partial'
 r['quality']['missing_fields']=['Exact physical catalyst batches, feed volume/concentration, catalyst mass, ligand-corrected mass basis and active-site population are not reported.','GC/MS calibration details and detection limits are not reported.','Raw time-series values and per-cycle mass recovery are not supplied; curves are not digitized in this package.','Recovery vacuum/temperature/time and details of inter-cycle replenishment are not supplied.']
 r['quality']['conflicts']=[CONFLICTS[6]['issue']]
 return r

r=assay_base(ASSAY_ID,'Stowell and Korgel (2005) · Comparative first-use Ir hydrogenation assay')
conditions='75 °C, 3 psig hydrogen, 1000:1 decene/Ir mass ratio; context-specific selected catalyst, not a synthesis condition.'
for key,label,size in [('oa2','OA/oleylamine, Figure 2 diamond',2),('oa4','OA/oleylamine, Figure 2 cross',4),('oa15','OA/oleylamine, text-only 1.5 nm test',1.5),('oa5','OA/oleylamine, text-only 5 nm test',5),('top','TOP, Figure 2 plus',None),('toab','TOAB, Figure 2 open circle',1.5),('topb','TOPB, Figure 2 open square',5)]:
 p=add_product(r,'assay-'+key,label,F2,surface='Oleic-acid/oleylamine-coated' if key.startswith('oa') else key.upper()+'-coated',notes=['Exact source synthesis batch and relation to TEM/XRD samples are unknown.'])
 if size is not None:add_measure(r,key+'-catalyst-diameter',p['sample_id'],'diameter',size,'nm',F2,'TEM-associated catalyst size',approximate=key in ['toab','topb'],conditions=conditions)
 if key.startswith('oa') or key=='top':
  p['notes'].append('No measurable catalytic conversion is reported; this is not a verified numerical zero and not failed Ir synthesis.')
  add_measure(r,key+'-conversion-limit',p['sample_id'],'1_decene_conversion',u='%',loc=F2,technique='GC/MS',qualifier='No measurable conversion reported; numerical detection limit unspecified',conditions=conditions)
  if key in ['oa15','oa5']:add_measure(r,key+'-observation-time',p['sample_id'],'assay_observation_duration',5,'h',F2,'Reported assay duration',conditions='No measurable conversion after this duration.')
 if key in ['toab','topb']:
  add_measure(r,key+'-conversion',p['sample_id'],'1_decene_conversion',42 if key=='toab' else 100,'%',F2,'GC/MS',conditions=conditions+(' After 230 min.' if key=='toab' else ' After 60 min.'))
  add_measure(r,key+'-endpoint',p['sample_id'],'conversion_observation_time',230 if key=='toab' else 60,'min',F2,'Reported assay duration',conditions='Time attached to the separately reported conversion, not a required synthesis hold.')
  add_measure(r,key+'-tof-body',p['sample_id'],'turnover_frequency',4 if key=='toab' else 270,'s^-1','Main p. 1205 body text, Eq. 2','Author calculation from GC/MS and TEM',status='author_derived',basis='Assumes every surface Ir atom is catalytically active; active population not directly measured',conditions=conditions,qualifier='Conflicts with 5 s^-1 Figure 2 caption' if key=='toab' else '')
  if key=='toab':add_measure(r,'toab-tof-caption',p['sample_id'],'turnover_frequency',5,'s^-1','Main p. 1204, Figure 2 caption','Author calculation',status='author_derived',qualifier='Caption conflicts with 4 s^-1 body text',conditions=conditions)
r['quality']['conflicts'] += [CONFLICTS[4]['issue'],CONFLICTS[7]['issue']]
RECORDS.append(r)

for ligand in ['toab','topb']:
 r=assay_base(CYCLE_IDS[ligand],f'Stowell and Korgel (2005) · {ligand.upper()} catalyst recycling series')
 r['lineage']['parent_record_id']=ASSAY_ID
 def inherited_assay_context(value):
  if isinstance(value,dict):
   if value.get('status')=='reported':
    value['status']='inherited'
    if 'basis' in value:value['basis']=(value['basis']+'; ' if value['basis'] else '')+'Shared study assay method, not independently repeated per-cycle specification'
    elif 'note' in value:value['note']=(value['note']+'; ' if value['note'] else '')+'Inherited shared assay context'
   for child in value.values():inherited_assay_context(child)
  elif isinstance(value,list):
   for child in value:inherited_assay_context(child)
 for section in ['materials','stocks','operations']:inherited_assay_context(r[section])
 loc=F4 if ligand=='toab' else F5
 r['quality']['review_scope']+=' Successive cycles share a catalyst lineage and must not be counted as independent nanocrystal syntheses. Common assay conditions are study context; batch identity relative to Figure 2 is not inferred.'
 st(r,'recycled-series-final','Catalyst after the reported recycling series',['recovered-catalyst'],'product')
 op(r,'repeat-assay-cycles','repeat_assay_with_recovered_catalyst','Repeat hydrogenation using recovered catalyst',loc,['recovered-catalyst'],['recycled-series-final'],depends=['recover-catalyst'],stage='characterization',branch='recycling',parameters={'total_reported_cycles':Q(5 if ligand=='toab' else 6,'count',loc,basis='Highest reported catalytic cycle, including first use'),'per_cycle_mass_recovery':Q(None,'%',loc),'replenishment_volume':Q(None,'mL',loc)},description='Repeat the shared assay with the same catalyst lineage. Per-cycle endpoints and observed rates are stored separately. The source does not supply quantitative recovery losses or complete inter-cycle handling; no fixed endpoint is imposed across all cycles.')
 initial=add_product(r,ligand+'-before-cycling',ligand.upper()+' catalyst before recycling',loc,surface=ligand.upper()+'-coated',notes=['For TOPB, main p. 1207 explicitly distinguishes this initially inactive sample from Figure 2.'] if ligand=='topb' else ['Figure 4B is the before-catalysis TEM view; exact identity relative to Figure 2 is not established.'])
 if ligand=='toab':add_measure(r,'toab-initial-size',initial['sample_id'],'diameter',1.5,'nm',F4,'TEM-associated catalyst diameter')
 caption_tofs=[5,14,50,124,38] if ligand=='toab' else [0,24,36,None,119,75]
 body_tofs=[4,13,50,124,38] if ligand=='toab' else [0,None,None,None,119,75]
 prev=initial['sample_id']
 for i,(ct,bt) in enumerate(zip(caption_tofs,body_tofs),1):
  sid=ligand+'-cycle-'+str(i);p=add_product(r,sid,ligand.upper()+' recycling cycle '+str(i),loc,surface=ligand.upper()+'-coated (coverage may change during cycling)',parent=prev,notes=['Catalytic-cycle identifier, not an author-assigned synthesis batch.'])
  if ligand=='topb' and i==4:p['notes'].append('A fourth cycle is implied by the sequence but omitted from Figure 5 legend/data reporting; no outcome is invented.')
  if ct is not None:add_measure(r,sid+'-tof-caption',sid,'turnover_frequency',ct,'s^-1',('Main p. 1206, Figure 4 caption' if ligand=='toab' else 'Main p. 1206, Figure 5 caption'),'Author calculation from GC/MS and TEM',status='author_derived',basis='All-surface-atoms-active normalization; not a measured active-site count',qualifier='Conflicts with body text' if ligand=='toab' and i<3 else '',conditions='Successive cycle '+str(i)+'; recovered catalyst lineage, not a fresh synthesis.')
  if bt is not None and bt!=ct:add_measure(r,sid+'-tof-body',sid,'turnover_frequency',bt,'s^-1',loc+' body text','Author calculation',status='author_derived',qualifier='Body text value; conflicts with caption')
  if ligand=='toab':
   add_measure(r,sid+'-conversion',sid,'1_decene_conversion',42 if i==1 else 100,'%',F4,'GC/MS',conditions='Endpoint stated in body text.')
   if i in [1,2,5]:add_measure(r,sid+'-conversion-time',sid,'conversion_observation_time',230 if i in [1,2] else 150,'min',F4,'Reported assay duration',basis='Time to the source-stated conversion; cycle-specific endpoint')
   else:add_measure(r,sid+'-conversion-time',sid,'conversion_observation_time',u='min',loc=F4,technique='Reported qualitative timing',qualifier='Complete conversion in a shorter time than 230 min; no exact time transcribed from graph')
   if i==4:p['notes'].append('Figure 4C shows TEM after four hydrogenation reactions; aggregation is observed. Do not relabel this as after cycle 5.')
   if i==5:
    add_measure(r,'toab-cycle5-size',sid,'diameter',3,'nm',F4,'TEM',basis='Average particle size after fifth cycle stated in body text')
    add_measure(r,'toab-cycle5-effective-aggregate-size',sid,'model_effective_aggregate_diameter',10,'nm',F4,'Author comparison model',status='author_derived',qualifier='Assumed aggregate diameter for surface-area normalization; not independently measured particle size')
    add_measure(r,'toab-cycle5-aggregate-tof',sid,'model_aggregate_normalized_turnover_frequency',127,'s^-1',F4,'Author comparison calculation',status='author_derived',basis='Uses the hypothetical 10 nm aggregate surface-to-volume model, unlike the 38 s^-1 particle-based normalization')
  prev=sid
 if ligand=='toab':r['quality']['conflicts'] += [CONFLICTS[4]['issue'],CONFLICTS[5]['issue']]
 else:r['quality']['conflicts'] += [CONFLICTS[7]['issue']];r['quality']['missing_fields'].append('Cycle 4 TOF/curve is absent from the Figure 5 reporting; exact per-cycle conversion endpoints are not tabulated.')
 # The descriptive assay sequence is a shared procedure. No unreported fixed number of synthesis or wash cycles is introduced.
 RECORDS.append(r)

for r in RECORDS:
 (OUT/'canonical'/(r['record_id']+'.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# Whole-paper coverage manifest, separate from schema-bound records.
docs=json.loads((OUT/'document-review-manifest.json').read_text(encoding='utf-8'))
sections={
 'main':{1:['Bibliographic identity, abstract and introduction','Four ligand formulations','OA/oleylamine synthesis and purification','Optional size selection'],2:['Figure 1 TEM/HRTEM, XRD and SAXS','Gaussian spherical SAXS model and Eq. 1','Common hydrogenation/GC-MS procedure','Figure 2 and inactive OA/oleylamine samples'],3:['Figure 3 ligand-dependent TEM','TOP/TOAB/TOPB synthesis context','First-use catalytic endpoints','TOF normalization and Eq. 2'],4:['Figure 4 TOAB recycling and TEM','Excessive antisolvent precipitation observation','Aggregation normalization example','Figure 5 TOPB recycling'],5:['TOPB recycling continuation','Ligand-coverage interpretation and conclusions','Acknowledgments and SI availability statement','References 1–35']},
 'si':{1:['Title/authors and SI identity','Complete chemicals/purity/supplier list','OA/oleylamine synthesis start'],2:['OA/oleylamine synthesis continuation and workup','TOP synthesis and workup'],3:['TOAB and TOPB synthesis/workup','Hydrogenation assay and catalyst recovery','TEM/HRTEM instrument details start'],4:['TEM preparation continuation','Powder XRD','SAXS and calibration','GC/MS calibration/analysis']}}
for d in docs:
 for p in d['pages']:
  p.update(text_read=True,visual_review=True,sections=sections[d['role']][p['page']],unresolved=[])
  if d['role']=='si' and p['page']==1:p['unresolved']=['Printed OA/OAm µL amounts and OA formula anomaly remain unresolved; all values are legible.']
  if d['role']=='main' and p['page']==2:p['unresolved']=['SAXS radius wording/solvent and pressure basis differences are preserved.']
  if d['role']=='main' and p['page'] in [3,4]:p['unresolved']=['TOAB TOF body/caption discrepancies remain unresolved.']
  if d['role']=='main' and p['page']==5:p['unresolved']=['Referenced original methods/interpretive sources were not independently read in this package.']
(OUT/'document-review-manifest.json').write_text(json.dumps(docs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
crops=json.loads((OUT/'figure-crop-manifest.json').read_text(encoding='utf-8'))
for c in crops:c['visually_reviewed']=True;c['visual_review']='Compared against complete source page; all original panels, axes, labels and scale bars are retained. Caption is paraphrased separately. Poppler reported fallback-font warnings; plotted labels/scale bars were readable in the inspected crops.'
(OUT/'figure-crop-manifest.json').write_text(json.dumps(crops,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

figures=[
 {'id':'figure-1','figure':1,'page':2,'printed_page':1204,'caption_paraphrase':'OA/oleylamine-coated Ir: size-selected TEM, FCC XRD, SAXS fractions and a single-particle HRTEM image.',
  'panels':{'A':'Approximately 4 nm size-selected TEM, 10 nm scale bar','B':'XRD indexed FCC Ir, JCPDS 46-1044; labels (111), (200), (220), (311), (222)','C':'Two size fractions from the same synthesis reaction; open squares and open circles; Eq. 1 fit curves are models, symbols measurements','D':'5 nm particle HRTEM inset, 5 nm scale bar'},
  'sample_links':[{'record_id':SYNTH_IDS['oa'],'sample_ids':['oa-fig1a','oa-fig1d','oa-xrd','oa-tem-average'],'status':'formulation context; panel-to-panel identity unresolved'},{'record_id':SIZE_ID,'sample_ids':['oa-saxs-small','oa-saxs-large'],'status':'common parent reaction explicit; exact fractionation recipe incomplete'}],
  'quantitative_facts':{'tem_a_diameter_nm_approx':4,'tem_d_single_particle_nm':5,'xrd_scherrer_size_nm':5.3,'tem_mean_comparison_nm':5,'saxs_Rav_nm':[1.09,1.92],'saxs_sigma_radius_nm':[.283,.635],'xrd_2theta_axis_degrees':[30,90],'saxs_q_axis_nm_inverse':[.4,3.6],'scale_bars_nm':{'A':10,'D':5}},
  'limitations':['R_av/radius wording conflict; no automatic diameter conversion.','SAXS specimen solvent conflict.','XRD peak positions/line widths and SAXS raw points are not digitized.']},
 {'id':'figure-2','figure':2,'page':2,'printed_page':1204,'caption_paraphrase':'Remaining 1-decene during hydrogenation with differently capped Ir particles.',
  'sample_links':[{'record_id':ASSAY_ID,'sample_ids':['assay-oa2','assay-oa4','assay-top','assay-toab','assay-topb'],'status':'assay-series context; exact synthesis batch mapping unresolved'}],
  'quantitative_facts':{'temperature_C':75,'hydrogen_pressure_psig':3,'catalyst_diameters_nm':{'OA_OAm_diamond':2,'OA_OAm_cross':4,'TOAB_circle':1.5,'TOPB_square':5},'TOAB_conversion_percent_at_230min':42,'TOPB_conversion_percent_at_60min':100,'TOAB_TOF_body_s_inverse':4,'TOAB_TOF_caption_s_inverse':5,'TOPB_TOF_s_inverse':270,'time_axis_min':[0,250],'y_axis':'Decene Concentration (%); remaining substrate, not conversion'},
  'limitations':['OA/OAm and TOP inactivity is not a calibrated numeric zero.','Curve points not digitized.','No author batch ID; sizes alone do not join specimens across figures.']},
 {'id':'figure-3','figure':3,'page':3,'printed_page':1205,'caption_paraphrase':'TEM contrasts TOAB-, TOPB- and TOP-coated Ir morphologies and sizes.',
  'panels':{'A':'TOAB','B':'TOPB (two magnifications)','C':'TOP with inset'},
  'sample_links':[{'record_id':SYNTH_IDS[x],'sample_ids':[x+'-fig3' if x!='top' else 'top-fig3c'],'status':'ligand-formulation context; exact batch mapping unresolved'} for x in ['toab','topb','top']],
  'quantitative_facts':{'diameter_ranges_nm':{'TOAB':[1.5,3],'TOPB':[2,5],'TOP':[10,100]},'TOPB_body_mean_nm':4,'scale_bars_nm':{'A':5,'B_main':10,'B_inset':5,'C_main':100,'C_inset':20}},
  'limitations':['TOPB 4 nm mean is distinct from the approximately 5 nm catalytic sample label.','Crystalline does not establish that Figure 1 FCC evidence applies to every ligand formulation.']},
 {'id':'figure-4','figure':4,'page':4,'printed_page':1206,'caption_paraphrase':'TOAB recycling changes hydrogenation response; TEM compares the initial catalyst and material after four assay cycles.',
  'panels':{'A':'Five catalytic cycles','B':'Before catalysis, 10 nm scale','C':'After four hydrogenations, 5 nm scale'},
  'sample_links':[{'record_id':CYCLE_IDS['toab'],'sample_ids':['toab-before-cycling']+['toab-cycle-'+str(i) for i in range(1,6)],'status':'successive catalyst lineage; physical link to Figure 2 not established'}],
  'quantitative_facts':{'initial_diameter_nm':1.5,'temperature_C':75,'first_and_second_assay_endpoint_min':230,'body_TOFs_s_inverse':[4,13,50,124,38],'caption_TOFs_s_inverse':[5,14,50,124,38],'body_conversion_percent':[42,100,100,100,100],'fifth_cycle_complete_conversion_time_min':150,'fifth_cycle_mean_particle_nm':3,'comparison_assumed_aggregate_nm':10,'comparison_aggregate_TOF_s_inverse':127,'scale_bars_nm':{'B':10,'C':5},'time_axis_min':[0,250],'y_axis':'remaining decene concentration'},
  'limitations':['Body/caption disagreements in cycles 1 and 2.','3 nm value concerns fifth-cycle particles; panel C is after four cycles.','The 10 nm aggregate is a comparison-model input.','Exact cycle-3/4 completion times are not tabulated or digitized.']},
 {'id':'figure-5','figure':5,'page':4,'printed_page':1206,'caption_paraphrase':'Initially inactive TOPB-coated Ir becomes active during recycling, then slows on the sixth cycle.',
  'sample_links':[{'record_id':CYCLE_IDS['topb'],'sample_ids':['topb-cycle-'+str(i) for i in [1,2,3,5,6]],'status':'separate initially inactive TOPB series, explicitly distinguished from Figure 2'}],
  'quantitative_facts':{'caption_cycle_TOFs_s_inverse':{'1':0,'2':24,'3':36,'5':119,'6':75},'cycle_4_TOF':None,'time_axis_min':[0,140],'y_axis':'remaining decene concentration'},
  'limitations':['Fourth-cycle curve/TOF not supplied in reporting.','No exact catalyst size or batch identifier for this series.','Do not merge 0 s^-1 initial activity with the Figure 2 270 s^-1 specimen.','Endpoint times and full curve data are not digitized.']}
]
for f,c in zip(figures,crops):f.update(reviewed=True,review_status='complete_figure_and_caption_visually_reviewed',original_crop_asset=c)

inventory=[]
for r in RECORDS:
 inventory.append({'id':r['record_id'],'label':r['title'],'record_ids':[r['record_id']],'status':'source_reviewed_partial_protocol' if r['record_type']!='procedure' else 'source_reviewed_shared_procedure_or_assay','source_locators':list(dict.fromkeys(e['locator'] for o in r['operations'] for e in o['evidence'])),'gaps':r['quality']['missing_fields']})
inventory += [
 {'id':'commercial-upstream-reagents','label':'Commercial precursors; no local upstream synthesis described','record_ids':list(SYNTH_IDS.values()),'status':'source_reviewed_purchase_inventory','source_locators':[CHEM],'gaps':['Supplier synthesis routes, lot IDs and storage are not provided.']},
 {'id':'overwashing-observation','label':'Excessive antisolvent precipitation of TOAB/TOPB particles','record_ids':[SYNTH_IDS['toab'],SYNTH_IDS['topb']],'status':'qualitative_observation_not_independent_complete_recipe','source_locators':['Main p. 1206, ligand-desorption discussion'],'quantitative_facts':{'precipitation_count_range':[5,10]},'gaps':['Antisolvent, volumes, exact cycle count by ligand, measured coverage and identified batch are not specified.']}
]
characterization=[
 {'technique':'TEM/HRTEM','source_locators':[TEM,F1,F3,F4],'figures':[1,3,4],'procedure_record':CHAR_ID,'conditions':{'JEOL_2010F_HRTEM_kV':200,'Phillips_EM208_LRTEM_kV':120,'grid_mesh':200,'grid':'carbon-coated copper','carrier':'chloroform, dilute, drop cast'},'quantitative_label_scope':'All text/caption sizes captured in records and figure inventory; no pixel-derived size histograms invented.','gaps':['Particle-count statistics and full distribution measurement protocol not supplied.']},
 {'technique':'XRD','source_locators':[XRD,F1],'figures':[1],'procedure_record':CHAR_ID,'conditions':{'instrument':'Bruker-Nonius powder diffractometer (source spelling varies)','radiation':'Cu Kα','wavelength_angstrom':1.54,'carrier':'chloroform','substrate':'quartz'},'reported_facts':{'phase':'FCC for OA/oleylamine specimen','reference':'JCPDS 46-1044','Scherrer_diameter_nm':5.3},'gaps':['Exact peak positions, instrumental correction, scan settings and measured CIF absent.']},
 {'technique':'SAXS','source_locators':[SAXS,F1],'figures':[1],'procedure_record':CHAR_ID,'conditions':{'generator':'Rotating copper anode, Bruker Nonius/Molecular Metrology','power_kW':3,'wavelength_nm':.154,'SI_carrier':'cyclohexane','main_Fig1C_carrier':'hexane','windows':'Kapton','angle_standard':'silver behenate','standard_formula_as_printed':'CH3(CH2)20COOAg','corrections':['background scattering','sample absorption']},'model':'Eq. 1: isolated spherical-particle form factor with Gaussian radius distribution and R^6 weighting. Fit values are author-derived.', 'general_method_claim':'>10^10 particles can be probed; not a measured per-sample particle count.', 'gaps':['Raw intensities, parameter uncertainties and full fitting settings absent; radius/diameter wording conflict.']},
 {'technique':'GC/MS','source_locators':[GC,CAT,F2,F4,F5],'figures':[2,4,5],'procedure_record':ASSAY_ID,'conditions':{'main_instrument_alternatives':['Hewlett-Packard 5890 Series II','Finnigan MAT GCQ'],'SI_instrument':'Hewlett-Packard 5890 Series II','calibration':'relative 1-decene and decane amounts'},'model':'Eq. 2 TOF=(1/N_act)(dn/dt), with all surface atoms treated as active; reported N_act uses estimated particle surface area/unit-cell surface normalization.', 'gaps':['GC column/program, calibration concentrations, response factors, detection limits and raw chromatograms absent.']},
 {'technique':'Surface-ligand behavior','source_locators':['Main pp. 1206–1207'], 'figures':[4,5], 'observations':['TOAB/TOPB can lose redispersibility after 5–10 antisolvent precipitations.','OA/oleylamine material remains redispersible after repeated precipitation; no numeric count.','Activity/aggregation changes during recycling are observed.'], 'interpretations':['Authors attribute activation to ligand desorption and larger exposed Ir surface; precise surface coverage is not directly measured.','Authors attribute particle enlargement to Ostwald ripening and compare Ir–N/Ir–P bonding through cited work.'], 'gaps':['No direct ligand-coverage assay or binding-energy measurement is reported in this paper.']}
]
referenced=[
 {'reference':24,'bibliography_as_printed':'Sun, S.; Murray, C. B.; Weller, D.; Folks, L.; Moser, A. Science 2000, 287, 1989–1992.','role':'FePt synthesis framework cited as analogous to the OA/oleylamine Ir method.','status':'Bibliography inspected; original full method not independently resolved in this package. Ir SI amounts remain the authority for this record.'},
 {'reference':23,'bibliography_as_printed':'Hoke, J. B.; Stern, E. W.; Murray, H. H. J. Mater. Chem. 1991, 1, 551–554.','role':'Background for the organometallic CVD precursor; current study purchases precursor from Strem.','status':'Original paper not inspected; no upstream precursor synthesis imported.'},
 {'references':[25,26,27,28],'role':'SAXS theory/model sources','status':'Current paper equation and its stated assumptions reviewed; cited originals not independently read.'},
 {'reference':33,'role':'TOF total-surface-site normalization precedent','status':'Current paper assumption reviewed; original not independently read.'},
 {'references':[29,30,31,32,34,35],'role':'Ligand binding, ripening and surface/catalysis interpretation','status':'Current article interpretations retained as authors’ explanations; underlying primary references not independently verified here.'}
]
equation_crops=json.loads((OUT/'equation-crop-manifest.json').read_text(encoding='utf-8'))
for c in equation_crops:
 c['visually_reviewed']=True
 c['visual_review']='Original equation, nearby definitions and assumptions inspected. PDFium retains the proportionality glyph that the Poppler first attempt omitted. No content was manually redrawn.'
(OUT/'equation-crop-manifest.json').write_text(json.dumps(equation_crops,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
equations=[
 {'id':1,'label':'Equation 1 — SAXS model','source_locator':'Main p. 1204, Equation 1 and surrounding definitions','scope':'SAXS sphere/Gaussian-radius model; not direct atom coordinates','formula_text':'I(q) ∝ ∫ N(R) P(qR) R^6 dR','formula_latex':r'I(q)\propto\int N(R)P(qR)R^6\,dR','supporting_definitions':[{'symbol':'q','formula':'q = 4π sin(θ)/λ','meaning':'Scattering-vector magnitude; scattering angle is 2θ and λ = 0.154 nm.'},{'symbol':'P(qR)','formula':'[3(sin(qR) − qR cos(qR))/(qR)^3]^2','meaning':'Sphere form factor.'},{'symbol':'N(R)','formula':'exp[−(R − R_av)^2/(2σ^2)]/(σ√(2π))','meaning':'Gaussian radius distribution; R_av mean radius and σ standard deviation.'}],'assumptions':['Dilute, nonaggregating, isolated spherical particles.','Gaussian radius distribution with R^6 intensity weighting.','The equation is proportional; no absolute intensity normalization or integration bounds are stated.'],'outputs':'Author-fitted mean radii and distribution widths for the two size fractions in Figure 1C.','limits':['The source later calls these radius parameters diameters in one sentence; both wording and radius-based definition are retained.','No fit covariance, numerical intensity arrays or measured atom coordinates supplied.'],'reviewed':True,'original_crop_asset':equation_crops[0]},
 {'id':2,'label':'Equation 2 — turnover frequency','source_locator':'Main p. 1205, Equation 2 and following paragraph','scope':'TOF normalization; active-site count assumed from surface atoms','formula_text':'TOF = (1/N_act)(dn/dt)','formula_latex':r'\mathrm{TOF}=\frac{1}{N_{\mathrm{act}}}\frac{dn}{dt}','supporting_definitions':[{'symbol':'n in Eq. 2','meaning':'Number of reacted molecules; t is time.'},{'symbol':'N_act','formula_as_printed':'N_act = A_P/(A_UC n)','meaning':'Printed surface-site normalization; A_P is the average-particle surface area, A_UC the surface area of an Ir unit-cell face, and this later n denotes Ir atoms in a unit-cell face.'}],'assumptions':['All surface Ir atoms are used as active sites for normalization, although ligand-covered atoms may be unavailable.','Average nanocrystal diameter used for the calculation is measured by TEM.'],'outputs':'Author-derived turnover frequencies in s^-1, not an independently measured active-site population.','limits':['N_act expression is transcribed as printed rather than silently algebraically corrected; the symbol n is reused for two meanings in the source.','Particle/site normalization and actual ligand coverage cannot be independently reconstructed from the supplied data.','Body/caption TOF disagreements remain separate source facts; no recomputation resolves them.'],'reviewed':True,'original_crop_asset':equation_crops[1]}
]
coverage={
 'paper':{'doi':DOI,'title':TITLE,'authors':AUTHORS,'journal':'Nano Letters','year':2005,'volume':5,'issue':7,'pages':'1203–1207','published_online':'2005-06-02','url':URL},
 'documents':docs,
 'document_identity_verification':{'main_doi_visible':True,'si_title_authors_affiliation_match':True,'si_content_correspondence_verified':True,'note':'SI does not print a DOI on the inspected first page; match rests on title/authors and exact corresponding methods, not filename alone.'},
 'recipe_inventory':inventory,'figures':figures,'tables':[],'schemes':[],
 'table_scheme_scope':'All 9 supplied pages inspected: no numbered tables or schemes occur. Five numbered main figures and two numbered main equations occur; SI has no figures/tables.',
 'equations':equations,
 'characterization_inventory':characterization,'evidence_conflicts':CONFLICTS,'referenced_methods_not_locally_resolved':referenced,
 'coverage_status':{'document_reading':'complete_for_supplied_main_and_matched_si','pages_read':9,'pages_visually_reviewed':9,'numbered_figures_reviewed':5,'canonical_synthesis_variants':4,'canonical_shared_procedures_and_assays':5,'canonical_record_count':len(RECORDS),'source_conflicts_resolved':False,'exact_recipe_outcome_pairing_complete':False,'raw_curve_digitization_complete':False,'scope':'Whole-paper section/figure/recipe coverage completed; experimental reconstruction remains partial. This is not a claim of fully curated raw numerical datasets or complete laboratory SOPs.'},
 'remaining_gaps':['Printed ligand-volume/formula ambiguities and listed measurement/reporting conflicts cannot be resolved from these documents.','Most exact physical batch and cross-figure mappings are not supplied.','Original graph points, diffraction curves, image-derived distributions and raw chromatograms are not provided as machine-readable data and have not been digitized.','Referenced originals listed above have not been independently read; no values are borrowed from them.','No full ligand-coverage measurement, active-site count or measured atomic-coordinate/CIF pair is available.','The general antisolvent-overwashing observation is inventoried but cannot support a fully parameterized independent protocol.'],
 'training_note':'Four synthesis variants may support partial-protocol/precursor supervision with uncertainties intact. Shared assays, fitted/assumed models, unassigned figures and recycling cycles are not independent synthesis labels. All requested tasks are disabled on shared assay/characterization records.',
 'independent_audit':'Independent audit by synthesis_prior_art on 2026-09-17: all 5 main and 4 SI pages and five figures checked; corrected OA/oleylamine product surface label; original equation crops, formulas and assumptions verified. No further scientific quantity or sample-linkage corrections identified. See audit.md.'
}
(OUT/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
contributions=[{'material_system':'Ir','elements':['Ir'],'contains_materials':['Ir'],'architecture':'single_material','primaryrecordid':rid,'source':{'source_id':SID,'doi':DOI,'url':URL},'scope':'Source-reviewed ligand-specific protocol; ligand is a surface cap, not an inorganic shell.'} for rid in SYNTH_IDS.values()]
(OUT/'material-contributions.json').write_text(json.dumps(contributions,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Wrote',len(RECORDS),'records:',', '.join(r['record_id'] for r in RECORDS))
