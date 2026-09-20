"""Source-reviewed Nakonechnyi2017 variants. No Site writes or inferred run IDs."""
import sys,json,copy
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent;SITE=R.parents[2]/'recipe-atlas'
sys.path.insert(0,str(R/'runtime'))
import jsonschema
sys.path.insert(0,str(SITE/'scripts'))
from record_helpers import *
from dataset_lib import validate_record,eligibility
SID='nakonechnyi2017';PREFIX='nakonechnyi-2017-';DOI='10.1021/acs.chemmater.7b00354'
SRC=source(SID,DOI,'Mechanistic Insights in Seeded Growth Synthesis of Colloidal Core/Shell Quantum Dots','Igor Nakonechnyi, Michael Sluydts, Yolanda Justo, Jacek Jasieniak, Zeger Hens',2017,si='All 7 pages of identity-matched SI fully read and visually reviewed, 17 September 2026')
SRC['main_status']='All 9 main-article pages fully read and visually reviewed, 17 September 2026'
REC=[]
def E(loc):return ev(SID,loc)
def Q(v=None,u='',loc='Main PDF p.2, printed 4720, Experimental Section',**kw):return qty(v,u,evidence=E(loc),**kw)
def F(v=None,loc='Main PDF p.2, printed 4720, Experimental Section',**kw):return fact(v,E(loc),**kw)
def M(id,name,formula,role,loc,qs=None,stage='synthesis',notes=None):return material(id,name,formula,role,stage,E(loc),qs,notes)
def base(slug,title,formula,loc,parent=None,kind='literature_protocol'):
 r=record(PREFIX+slug,title,formula,'II-VI colloidal nanocrystals','Hot injection / seeded growth',copy.deepcopy(SRC),loc,kind)
 r['collection']='reviewed_literature';r['lineage'].update(recipe_family='nakonechnyi2017-cdse',parent_record_id=PREFIX+parent if parent else None)
 comps=formula.split('/');r['material'].update(components=comps,architecture='core_shell' if len(comps)>1 else 'single_material',elements=list(dict.fromkeys(__import__('re').findall('[A-Z][a-z]?',formula))))
 r['quality']['review_scope']='Complete main and SI document review; this record is one method/variant, not a count of independent physical batches. Contextual measurements retain unresolved batch links. Other paper routes have separate records and coverage inventory.'
 r['quality']['missing_fields']=['Author batch IDs, reagent suppliers/purities/lots, stirring and flask capacity.','Ramp rates, injection duration, gas flow and pressure, actual post-injection temperature trajectory.','Exact specimen linkage across method paragraph, TEM, SAED and Table 1.','Numerical spectra and yield-curve source data are not tabulated; original plots retained without guessed values.','Final storage and isolated bulk yield; no measured sample atomic coordinates.']
 r['quality']['requested_tasks']=['precursor_selection','partial_protocol'];r['context_links']=[{'label':'Original article and matching SI','url':'https://doi.org/'+DOI,'relation':'primary_source'}]
 return r
def add_measure(r,id,sample,prop,v,u,loc,tech='As reported',**kw):
 conditions=kw.pop('conditions','Contextual source sample; exact recipe batch not identified.')
 r['measurements'].append(measurement(id,sample,prop,Q(v,u,loc,**kw),tech,E(loc),conditions))
def augment_acquisition(r):
 for m in r['measurements']:
  if 'absorp' in m['property'] and 'UV-vis: PerkinElmer' not in m['conditions']:m['conditions']+=' UV-vis: PerkinElmer Lambda 950 or Varian Cary 500; specific instrument, path length and dilution not assigned per spectrum.'
  if m['property']=='photoluminescence_quantum_yield' and 'Absolute PLQY: 152 mm' not in m['conditions']:m['conditions']+=' Absolute PLQY: 152 mm Spectralon-coated integrating sphere, Princeton Instruments ProEM 16002 CCD and Acton SP2358 spectrograph; excitation wavelength and exact optical specimen not stated.'
  if m['technique']=='TEM' and 'Carbon-coated copper grid by dropcasting;' not in m['conditions']:m['conditions']+=' Carbon-coated copper grid by dropcasting; Cs-corrected JEOL 2200 FS; voltage and particle count not stated.'
def independent_audit_refinements(r):
 # 17 September 2026 cross-audit: retain source quantities while disambiguating
 # inherited legacy units and removing unsupported sequence/sample assertions.
 for o in r['operations']:
  for key,q in o['parameters'].items():
   if 'centrifugation' in key and q.get('unit')=='g':q['unit']='g_relative'
 if r['record_id']==PREFIX+'zb-cdse-cds-low-oa-control':
  loc='Main PDF p.4, printed 4722, OA/Cd 3:1 comparison; Figures 1d-f and 3a'
  r['quality']['missing_fields']=[x for x in r['quality']['missing_fields'] if 'Figure 1b' not in x and 'statistical meaning of' not in x]
  r['quality']['missing_fields']+=['Exact physical batch identity for the low-OA Figure 1d-f series, its TEM specimen, and any diffraction specimen; no low-OA size or shell-thickness statistic is reported.']
  r['quality']['conflicts']=['The parent high-OA method lists 5.6 mmol OA/0.25 mmol CdO (22.4 charged ratio), whereas its results use 20:1. The low-OA branch is labeled 3:1, but the free-versus-total acid basis and absolute low-OA charge are unresolved. No high-OA charge or 8.6 nm size is assigned to this branch.']
  for o in r['operations']:
   if o['id']=='select-tem-sample':o['description']='Figure 1e is the low-OA TEM context; the Figure 1 caption applies the 2 min convention to panels d-f. Physical pairing to this inherited generic workup remains unreported.'
 if r['record_id'].startswith(PREFIX+'core-stability-'):
  loc='SI PDF p.2, printed S2, section S1 and Figure S1';e=E(loc)
  mids=[m['id'] for m in r['materials'] if m['id']!='toluene']
  params=copy.deepcopy(r['operations'][0]['parameters']);params['seed_amount']=Q(50,'nmol',loc)
  params['injection_temperature']=params.pop('temperature')
  r['material_states']=[state('control-batch','Stated omission-control reaction after seed addition',mids,'reaction_batch'),state('aliquot-300s','Unpurified 300s aliquot',['control-batch','toluene'],'aliquot')]
  sample=r['operations'][-1];sample['depends_on']=['run-control']
  r['operations']=[operation('run-control','control_reaction','Run the stated precursor-omission control',e,mids,['control-batch'],parameters=params,description='Partial shared-condition description: 50 nmol CdSe cores and the named remaining compounds were used under the main-method conditions. The SI does not separately resolve precursor addition order or feed-versus-reactor placement. In particular, TOP-S is not asserted to be heated in the reactor before the seed addition. The main synthesis prepares a core/TOP-S feed, while SI describes core injection into a reaction mixture containing the selected compounds.'),sample]
  r['quality']['missing_fields']+=['Control-specific addition order and feed-versus-reactor allocation of remaining compounds; the operation graph intentionally does not resolve that order.']

def save(r):
 independent_audit_refinements(r)
 r['quality']['missing_fields']=list(dict.fromkeys(r['quality']['missing_fields']))
 augment_acquisition(r);errors=validate_record(r)
 if errors:raise ValueError('\n'.join(errors))
 REC.append(r);return r

# Re-reviewed existing scoped records: preserve identifiers and increment revisions.
for slug in ['zb-cdse-core','zb-cdse-cds-seeded-growth']:
 prior=R/'canonical'/(PREFIX+slug+'.json')
 r=json.loads((prior if prior.exists() else SITE/'data/records'/(PREFIX+slug+'.json')).read_text(encoding='utf-8'))
 if not prior.exists():r['revision']+=1
 r['sources']=[copy.deepcopy(SRC)]
 r['quality']['review_scope']='All 9 main and 7 SI pages read and visually reviewed. This record preserves its selected route; other routes, controls, all figures and simulation-only values are covered separately in coverage.json. Physical batch identities remain unresolved.'
 if slug=='zb-cdse-core':
  r['operations']=[o for o in r['operations'] if o['id']!='quantify-cores']
  r['operations'][5]['stage']='surface_exchange'
  r['quality']['missing_fields']+=['Original Flamee et al. 2013 cited method not reviewed in this bounded paper/SI audit; the reproduced brief protocol is retained.']
  for m in r['materials']:
   if m['id']=='selenium_dispersion':m['quantities']={'selenium':m['quantities']['selenium']}
  for s in r['stocks']:
   if s['id']=='se-ode-stock':s['components'][0]['quantities']={'selenium':s['components'][0]['quantities']['selenium']}
  r['operations'].append(operation('quantify-cores','measure_absorption','Determine core concentration',E('Main PDF p.2, Zinc Blende CdSe Core QDs'),['purified_oleate_capped_zb_cdse'],[],depends=['s7'],stage='characterization',description='Use the average absorbance of a diluted sample at 300, 320 and 340 nm and the cited volume-fraction relation. The resulting concentration and dilution factor are not reported.',parameters={f'absorption_wavelength_{n}':Q(n,'nm') for n in [300,320,340]}))
 else:
  r['measurements']=[m for m in r['measurements'] if m['id']!='table1-core-diameter']
  add_measure(r,'table1-core-diameter','table1-zb-cdse-cds-context','core_diameter',3.1,'nm','Main PDF p.4, Table 1, zb-CdSe/CdS row',tech='Table 1; measurement basis not stated for this column')
  r['quality']['missing_fields']+=['Original Cirillo et al. 2014 flash method is cited but not independently reviewed in this bounded audit.']
 save(r)

# Wurtzite CdSe core preparation, including TOP pre-injection and thermal workup.
loc='Main PDF p.2, printed 4720, Wurtzite CdSe Core QDs';e=E(loc)
r=base('wz-cdse-core','Nakonechnyi et al. (2017) · Wurtzite CdSe core preparation','CdSe',loc)
r['method']='Hot injection of TOP-Se after TOP pre-injection'
for id,name,formula,role,v,u in [('cdo','Cadmium oxide','CdO','metal_precursor',1.5,'mmol'),('tdpa','TDPA (source abbreviation)',None,'ligand',6,'mmol'),('oleyl-alcohol','Oleyl alcohol','C18H36O','additive',24,'mmol'),('topo','Trioctylphosphine oxide','C24H51OP','solvent',10,'g'),('top','Trioctylphosphine','C24H51P','solvent',2,'mL')]:r['materials'].append(M(id,name,formula,role,loc,{'amount':Q(v,u,loc)}))
r['materials'] += [M('top-se','TOP-Se precursor',None,'chalcogen_precursor',loc,notes=['2 M supplied stock. The stock preparation, solvent composition, storage and purity are not specified.']),M('nitrogen','Nitrogen','N2','process_gas',loc),M('methanol','Methanol','CH4O','antisolvent',loc,{'volume':Q(15,'mL',loc)},stage='workup'),M('hexane','Hexane','C6H14','solvent',loc,{'volume_per_cycle':Q(1,'mL',loc)},stage='workup'),M('ethanol','Ethanol','C2H6O','antisolvent',loc,{'volume_per_cycle':Q(1,'mL',loc)},stage='workup')]
r['stocks']=[{'id':'top-se-stock','name':'2 M TOP-Se stock','components':[{'material_id':'top-se','quantities':{'aliquot_volume':Q(1.5,'mL',loc)}}],'concentrations':{'reported_concentration':Q(2,'mol/L',loc)},'preparation_operation_ids':[],'scope':'Supplied stock; preparation missing. No molecule-level solution speciation asserted.','evidence':e}]
st=[('charge','CdO/TDPA/oleyl-alcohol/TOPO charge',['cdo','tdpa','oleyl-alcohol','topo'],'mixture'),('conditioned','Charge after 120 C nitrogen flow',['charge','nitrogen'],'mixture'),('colorless','Colorless high-temperature solution',['conditioned'],'mixture'),('top-treated','Solution after TOP and temperature recovery',['colorless','top'],'mixture'),('batch','CdSe core reaction',['top-treated','top-se-stock'],'reaction_batch'),('cooled','Water-bath cooled dispersion',['batch'],'mixture'),('destabilized','Methanol-destabilized dispersion',['cooled','methanol'],'mixture'),('separated','Separated core fraction',['destabilized'],'fraction'),('purified','Thrice-purified wz-CdSe cores',['separated','hexane','ethanol'],'product')]
r['material_states']=[state(a,b,c,d) for a,b,c,d in st]
r['operations']=[operation('charge','mix','Combine core precursors',e,['cdo','tdpa','oleyl-alcohol','topo'],['charge']),operation('pretreat','heat','Condition under nitrogen',e,['charge','nitrogen'],['conditioned'],depends=['charge'],parameters={'temperature':Q(120,'degC',loc),'duration':Q(1,'h',loc)},environment=F('nitrogen flow',loc)),operation('dissolve','heat','Heat until colorless',e,['conditioned'],['colorless'],depends=['pretreat'],parameters={'temperature':Q(350,'degC',loc),'duration':Q(None,'min',loc)},endpoint=F('solution becomes colorless',loc)),operation('top-preinject','inject','Inject TOP and recover temperature',e,['colorless','top'],['top-treated'],depends=['dissolve'],parameters={'top_volume':Q(2,'mL',loc),'recovery_duration':Q(None,'s',loc)},endpoint=F('temperature recovered',loc)),operation('se-inject','inject','Inject 2 M TOP-Se',e,['top-treated','top-se-stock'],['batch'],depends=['top-preinject'],parameters={'stock_volume':Q(1.5,'mL',loc),'stock_concentration':Q(2,'mol/L',loc),'injection_temperature':Q(350,'degC',loc,status='inherited',basis='Recovery after preceding 350 C step; actual trajectory not recorded.')},description='Rapid core nucleation/growth follows TOP-Se injection; numerical injection duration unreported.'),operation('quench','cool','Quench after approximately five seconds',e,['batch'],['cooled'],depends=['se-inject'],parameters={'time_after_injection':Q(5,'s',loc,approximate=True,raw_text='After ±5 s',qualifier='Author uses ± as an approximate duration, not a measured uncertainty.'),'water_bath_temperature':Q(None,'degC',loc)},description='Quickly cool using a preheated water bath. Bath temperature and cooling rate not stated.'),operation('destabilize','precipitate','Add methanol near 80 C',e,['cooled','methanol'],['destabilized'],depends=['quench'],parameters={'mixture_temperature':Q(80,'degC',loc,approximate=True),'methanol_volume':Q(15,'mL',loc)}),operation('separate','centrifuge','Centrifuge destabilized dispersion',e,['destabilized'],['separated'],depends=['destabilize'],parameters={'duration':Q(1,'min',loc),'relative_force':Q(3000,'g_relative',loc,status='inherited',basis='Global here-and-afterward statement in zb-core paragraph.')},description='Source states centrifugation, but does not explicitly identify the retained fraction for this route.'),operation('wash','purify','Purify three times',e,['separated','hexane','ethanol'],['purified'],depends=['separate'],stage='workup',parameters={'cycles':Q(3,'count',loc),'hexane_per_cycle':Q(1,'mL',loc),'ethanol_per_cycle':Q(1,'mL',loc),'relative_force':Q(3000,'g_relative',loc,status='inherited',basis='Global centrifugation statement.'),'cycle_duration':Q(None,'min',loc)})]
for o in r['operations']:
 if o['id'] in ['destabilize','separate']:o['stage']='workup'
r['products']=[product('wz-core-method-product','CdSe',e,'explicit','purified','wurtzite',notes=['No quantitative core size or absorption peak is linked to this core-method paragraph. Table 1 gives distinct 3.4 and 3.6 nm seed contexts in shell systems; neither is assigned here.'])]
r['quality']['experimental_outcome']='reported_product';r['quality']['missing_fields']+=['TDPA is not expanded in these source documents; identity not filled from a guessed abbreviation.','2 M TOP-Se preparation and solvent composition; temperature recovery and exact time basis of ±5 s.','Preheated bath temperature, retained centrifuged fraction, later wash durations and final dispersion.','Drijvers et al. 2016 upstream method and phosphonate-surface study are cited but not independently reviewed here.']
save(r)

def shell(slug,phase,shellmat,seeds,blank=False):
 heading=f'{phase}-CdSe/{shellmat} by Seeded Growth';loc='Main PDF p.2, printed 4720, '+heading;e=E(loc)
 control_loc='Main PDF p.4, Figure 3'+('a' if shellmat=='CdS' else 'b') if phase=='zb' else 'Main PDF p.5, Figure 4'+('c' if shellmat=='CdS' else 'f')
 label=(f'{phase}-route {shellmat} no-seed control' if blank else f'{phase}-CdSe/{shellmat}'+(f' · {seeds} nmol seeds' if phase=='zb' and shellmat=='ZnSe' else ''))
 r=base(slug,'Nakonechnyi et al. (2017) · '+label,shellmat if blank else 'CdSe/'+shellmat,loc,parent=None if blank else phase+'-cdse-core',kind='protocol_variant' if blank or phase=='zb' else 'literature_protocol')
 metal='Cd' if shellmat=='CdS' else 'Zn';ch='S' if shellmat=='CdS' else 'Se';isw=phase=='wz'
 metalamt=.6 if isw and metal=='Cd' else .25 if metal=='Cd' else .65
 oaamt=2.5 if isw and metal=='Cd' else 5.6 if metal=='Cd' else 5.3;oaunit='g' if isw and metal=='Cd' else 'mmol'
 prepT=340 if isw else 260 if metal=='Cd' else 310;injectT=340 if isw else 260
 r['materials']=[M('metal-oxide',metal+' oxide',metal+'O','metal_precursor',loc,{'amount':Q(metalamt,'mmol',loc)}),M('oa','Oleic acid','C18H34O2','ligand',loc,{'reactor_amount':Q(oaamt,oaunit,loc)}),M('nitrogen','Nitrogen','N2','process_gas',loc),M('metal-oleate','In situ '+metal+' oleate',None,'intermediate',loc,stage='precursor_preparation',notes=['Not an isolated weighed material; solution speciation and conversion yield unreported.'])]
 if isw and metal=='Cd':r['materials'].append(M('topo','Trioctylphosphine oxide','C24H51OP','solvent',loc,{'reactor_mass':Q(2.5,'g',loc)}));solv='topo'
 else:r['materials'].append(M('ode','1-Octadecene','C18H36','solvent',loc,{'reactor_volume':Q(3.8,'mL',loc)}));solv='ode'
 if not blank:r['materials'].append(M('seeds',phase+'-CdSe core nanocrystals','CdSe','seed',loc,{'nanocrystal_amount':Q(seeds,'nmol',loc,basis='Nanocrystals, not formula-unit amount.'),'dispersion_volume':Q(None,'mL',loc)},notes=['Dried cores explicitly stated only for wz-CdSe/CdS.','Preparation dependency, not verified physical batch identity.']))
 if isw:
  r['materials'] += [M('chalcogen',ch+' elemental precursor',ch,'chalcogen_precursor',loc,{'amount':Q(.5 if ch=='S' else .96,'mmol',loc)},notes=['Dissolved/added with cores in TOP. Do not assign a single molecular solution species.']),M('top','Trioctylphosphine','C24H51P','solvent',loc,{'feed_volume':Q(1,'mL',loc),'preinjection_volume':Q(1,'mL',loc)})]
  comps=[{'material_id':'chalcogen','quantities':{'amount':Q(.5 if ch=='S' else .96,'mmol',loc)}},{'material_id':'top','quantities':{'volume':Q(1,'mL',loc)}}];stock_id='chalcogen-feed';stock_conc={}
 else:
  stockV=.38 if ch=='S' else .215;feedV=1.12 if ch=='S' else 1.285
  r['materials'].append(M('top-chalcogen','TOP-'+ch+' precursor',None,'chalcogen_precursor',loc,notes=['Supplied 2 M stock; preparation, solvent composition and storage unreported.']))
  next(m for m in r['materials'] if m['id']=='ode')['quantities']['feed_volume']=Q(feedV,'mL',loc)
  comps=[{'material_id':'top-chalcogen','quantities':{'stock_aliquot':Q(stockV,'mL',loc),'stock_concentration':Q(2,'mol/L',loc)}},{'material_id':'ode','quantities':{'feed_volume':Q(feedV,'mL',loc)}}];stock_id='chalcogen-feed';stock_conc={}
  r['stocks'].append({'id':'supplied-top-stock','name':'Supplied 2 M TOP-'+ch,'components':[{'material_id':'top-chalcogen','quantities':{}}],'concentrations':{'reported_concentration':Q(2,'mol/L',loc)},'preparation_operation_ids':[],'scope':'Unresolved upstream preparation; stock carrier not quantitatively specified.','evidence':e})
 if not blank:comps.append({'material_id':'seeds','quantities':{'nanocrystal_amount':Q(seeds,'nmol',loc)}})
 r['stocks'].append({'id':stock_id,'name':('Chalcogen-only' if blank else 'Core/chalcogen')+' injection feed','components':comps,'concentrations':stock_conc,'preparation_operation_ids':['prepare-feed'],'scope':'Entire described feed rapidly injected. Components do not establish solution speciation; total measured volume unreported.','evidence':e})
 r['materials'] += [M('toluene','Toluene','C7H8','dilution_solvent',loc,{'volume_per_aliquot':Q(1,'mL',loc)},stage='characterization'),M('ethanol','Ethanol','C2H6O','antisolvent',loc,{'initial_volume':Q(None,'mL',loc),'wash_volume':Q(1,'mL',loc)},stage='workup'),M('hexane','Hexane','C6H14','solvent',loc,{'wash_volume':Q(1,'mL',loc)},stage='workup')]
 r['material_states']=[state('charge','Three-neck flask charge',['metal-oxide','oa',solv]),state('conditioned','Pretreated charge',['charge','nitrogen']),state('metal-medium','In situ metal-oleate medium',['conditioned']),state('feed-state','Prepared injection feed',[stock_id],'stock'),state('batch','Reaction dispersion',['metal-medium','feed-state'],'reaction_batch'),state('tem-aliquot','TEM-selected aliquot',['batch'],'aliquot'),state('tem-ppt','Ethanol precipitate',['tem-aliquot','ethanol'],'fraction'),state('tem-purified','Thrice-purified TEM sample',['tem-ppt','hexane','ethanol'],'product')]
 r['operations']=[operation('load','load','Charge three-neck flask',e,['metal-oxide','oa',solv],['charge'],parameters={'flask_capacity':Q(None,'mL',loc)}),operation('pretreat','heat','Nitrogen-flow pretreatment',e,['charge','nitrogen'],['conditioned'],depends=['load'],parameters={'temperature':Q(120,'degC',loc),'duration':Q(1,'h',loc)},environment=F('nitrogen flow',loc)),operation('form-oleate','heat','Form metal oleate in situ',e,['conditioned'],['metal-medium'],depends=['pretreat'],stage='precursor_preparation',parameters={'temperature':Q(prepT,'degC',loc),'duration':Q(None,'min',loc)},endpoint=F('Complete dissolution of metal oxide / formation of metal oleate',loc)),operation('prepare-feed','mix','Prepare injection feed',e,[c['material_id'] for c in comps],['feed-state'],stage='precursor_preparation',description='Separate preparation; source does not prescribe its precise timing relative to the reactor conditioning.')]
 deps=['form-oleate','prepare-feed']
 if isw:
  r['material_states'].append(state('top-treated','Metal medium after TOP pre-injection',['metal-medium','top']))
  r['operations'].append(operation('top-preinject','inject','Inject TOP then recover temperature',e,['metal-medium','top'],['top-treated'],depends=['form-oleate'],parameters={'volume':Q(1,'mL',loc),'recovery_duration':Q(None,'s',loc)},endpoint=F('temperature recovered',loc)))
  hot='top-treated';deps=['top-preinject','prepare-feed']
 else:hot='metal-medium'
 r['operations'].append(operation('inject','inject','Rapidly inject prepared feed',e,[hot,stock_id],['batch'],depends=deps,parameters={'temperature':Q(injectT,'degC',loc,status='inherited' if isw else 'reported',basis='Recovered reactor temperature' if isw else 'Injection temperature explicitly stated.'),'duration':Q(None,'s',loc)},description='For zb-CdSe/ZnSe the source separately gives 310 C for precursor formation and 260 C for injection; cooling transition details are missing.' if not isw and ch=='Se' else 'Numerical injection duration and immediate temperature transient unreported.'))
 times=([5,30,60,120,180,240,300,360] if ch=='S' else [5,60,150,300,600,1200,1800,3600]) if isw else ([10,30,60,90,120,180,240,300,360] if ch=='S' else [30,60,240,480,720,1080,1620,2400])
 for t in times:
  sid='aliquot-'+str(t)+'s';r['material_states'].append(state(sid,'Unpurified '+str(t)+' s yield aliquot',['batch','toluene'],'aliquot'))
  r['operations'].append(operation('take-'+sid,'sample','Withdraw '+str(t)+' s aliquot',e,['batch','toluene'],[sid],depends=['inject'],stage='characterization',branch='yield-time-series',parameters={'time_after_injection':Q(t,'s',loc),'toluene_volume':Q(1,'mL',loc),'aliquot_mass':Q(None,'g',loc),'aliquot_volume':Q(None,'mL',loc)},description='Sampling time is not an independent batch endpoint. Unpurified absorption used for yield.'))
 if not blank:
  r['operations'] += [operation('select-tem','sample','Select TEM sample',e,['batch'],['tem-aliquot'],depends=['inject'],stage='characterization',branch='tem-preparation',parameters={'sampling_time':Q(None,'s',loc)},description='Generic methods paragraph does not assign a TEM sampling time; figure-specific times remain separate.'),operation('tem-precipitate','precipitate','Precipitate TEM sample with ethanol',e,['tem-aliquot','ethanol'],['tem-ppt'],depends=['select-tem'],stage='workup',branch='tem-preparation',parameters={'ethanol_volume':Q(None,'mL',loc)}),operation('tem-wash','purify','Purify TEM sample three times',e,['tem-ppt','hexane','ethanol'],['tem-purified'],depends=['tem-precipitate'],stage='workup',branch='tem-preparation',parameters={'cycles':Q(3,'count',loc),'hexane_per_cycle':Q(1,'mL',loc),'ethanol_per_cycle':Q(1,'mL',loc),'relative_force':Q(3000,'g_relative',loc,status='inherited',basis='Global centrifugation condition on main p.2.'),'cycle_duration':Q(None,'min',loc)})]
 r['products']=[product('method-product',shellmat if blank else 'CdSe/'+shellmat,e,'explicit','batch',notes=['Method-level product, physical batch ID and exact final collection time not reported.'])]
 r['quality']['experimental_outcome']='reported_product'
 if blank:
  r['quality']['requested_tasks']=['partial_protocol'];r['lineage']['parent_record_id']=None
  r['quality']['review_scope']+=' No-seed control condition identified by '+control_loc+'. All shared amounts/steps are inherited, not independently restated for this control.'
  r['operations']=[o for o in r['operations'] if o['branch']!='tem-preparation']
  r['material_states']=[s for s in r['material_states'] if not s['id'].startswith('tem-')]
  r['materials']=[m for m in r['materials'] if m['id'] not in ['ethanol','hexane']]
  def inherit(x):
   if isinstance(x,dict):
    if x.get('status')=='reported' and 'value' in x:x['status']='inherited';x['evidence']+=E(control_loc)
    for v in x.values():inherit(v)
   elif isinstance(x,list):
    for v in x:inherit(v)
  inherit({'materials':r['materials'],'stocks':r['stocks'],'operations':r['operations']})
  r['operations'][0]['parameters']['seed_amount']=Q(0,'nmol',control_loc,basis='Control explicitly has no coinjected CdSe seeds; not a missing value.')
  r['products'][0]['link_evidence']=E(control_loc);r['products'][0]['phase']=F(None,control_loc,note='No-seed control crystal phase not established by core/shell SAED.')
 else:
  # One contextual material-system object holds Table 1 values, never exact loading labels.
  sid='table1-'+phase+'-'+shellmat.lower();tl='Main PDF p.4, Table 1, '+phase+'-CdSe/'+shellmat+' row'
  r['products'].append(product(sid,'CdSe/'+shellmat,E(tl),'general_context',notes=['The table gives a material-system row, not a specimen/batch ID. No allocation to a particular seed loading is made.','d_shell heading/footnote says shell thickness, but body text discusses overall diameters. Keep ambiguity.']))
  add_measure(r,'table1-core-diameter',sid,'core_diameter',3.1 if not isw else 3.4 if ch=='S' else 3.6,'nm',tl)
  add_measure(r,'table1-plqy',sid,'photoluminescence_quantum_yield',55 if not isw else 60 if ch=='S' else 80,'%',tl,tech='Absolute integrating-sphere PLQY')
  if isw:
   add_measure(r,'table1-ambiguous-d-shell',sid,'source_d_shell_dimension_unresolved',11.2,'nm',tl,qualifier='Table labels thickness; body implies overall particle diameter. Excluded from diameter-target training.')
   add_measure(r,'table1-ambiguous-spread',sid,'source_d_shell_spread_unresolved',2.3 if ch=='S' else 1.4,'nm',tl,qualifier='Reported ±; type of spread not specified.')
  phase_loc='SI PDF p.3, printed S3, Figure S2'+('a' if isw and ch=='S' else 'c' if isw else 'd')
  r['products'].append(product('saed-context','CdSe/'+shellmat,E(phase_loc),'general_context',phase='wurtzite' if isw else 'zinc blende',notes=['SAED identifies overall core/shell phase for the TEM material system. Exact batch and seed loading not stated.']))
  fign='4a' if isw and ch=='S' else '4d' if isw else '2c';fl='Main PDF p.'+('5' if isw else '4')+', Figure '+fign
  p=product('tem-context','CdSe/'+shellmat,E(fl),'general_context',notes=['Separate figure context, not assigned as an exact run outcome.']);p['source_sample_label']='Figure '+fign;p['morphology']=F('quasi-spherical' if isw else 'irregular',fl);r['products'].append(p)
 if ch=='Se' and not isw:r['quality']['conflicts'].append('Method uses 5.3 mmol OA and 0.65 mmol ZnO (charged ratio 8.1538); Fig.2 caption says OA/Zn20:1. No resolution or exact loading-to-figure association supplied.')
 if isw:r['quality']['conflicts'].append('Table1 d_shell is defined as shell thickness, while body describes overall-particle size increase. Table number remains semantically unresolved; no numeric shell thickness label inferred.')
 r['quality']['missing_fields']+=['Supplied stock synthesis/speciation and exact physical seed batch/dispersion carrier.','Generic final quench/hold endpoint; isolated bulk workup is not specified by TEM aliquot preparation.','Named prior flash method not independently reviewed here.']
 return r

for seeds in [25,50,100]:save(shell('zb-cdse-znse-'+str(seeds)+'nmol','zb','ZnSe',seeds))
save(shell('wz-cdse-cds-seeded-growth','wz','CdS',100))
save(shell('wz-cdse-znse-seeded-growth','wz','ZnSe',100))
for phase in ['zb','wz']:
 for sm in ['CdS','ZnSe']:save(shell(phase+'-route-'+sm.lower()+'-no-seed-control',phase,sm,0,True))

# Low-acid comparison: full common framework with the changed OA charge left unknown.
r=copy.deepcopy(next(r for r in REC if r['record_id']==PREFIX+'zb-cdse-cds-seeded-growth'))
r.update(record_id=PREFIX+'zb-cdse-cds-low-oa-control',revision=1,record_type='protocol_variant',title='Nakonechnyi et al. (2017) · Low-OA CdSe/CdS mixed-nucleation comparison')
r['lineage']['parent_record_id']=PREFIX+'zb-cdse-cds-seeded-growth';lowloc='Main PDF p.4, printed 4722, OA/Cd 3:1 comparison; Figures 1d-f and 3a'
def inherit_low(x):
 if isinstance(x,dict):
  if x.get('status')=='reported' and 'value' in x:x['status']='inherited';x['evidence']+=E(lowloc)
  for v in x.values():inherit_low(v)
 elif isinstance(x,list):
  for v in x:inherit_low(v)
inherit_low({'materials':r['materials'],'stocks':r['stocks'],'operations':r['operations']})
next(m for m in r['materials'] if m['id']=='oleic-acid')['quantities']['amount']=Q(None,'mmol',lowloc,basis='Low-OA charge not restated; the meaning of ratio is unresolved, so no charge is derived.')
for o in r['operations']:
 if 'oa_amount' in o['parameters']:o['parameters']['oa_amount']=Q(None,'mmol',lowloc,basis='Amount not restated for 3:1 branch.')
r['condition_options']=[{'id':'reported-low-oa','label':'OA/Cd3:1; other reaction parameters stated unchanged','parameters':{'oa_cd_ratio':Q(3,'mol/mol',lowloc)},'evidence':E(lowloc)}]
r['products']=[product('low-oa-context','CdSe/CdS + separately nucleated CdS',E(lowloc),'general_context',notes=['Broad population of smaller particles than high-OA case; simultaneous shelling and secondary CdS nucleation, not a pure shell-only success.','Exact physical batch and OA charge unresolved.'])]
r['material']['architecture']='composite';r['measurements']=[];add_measure(r,'low-oa-exciton','low-oa-context','first_exciton_absorption',570,'nm',lowloc,tech='UV-vis',basis='CdSe-derived transition in low-OA comparison; not the separate CdS absorption peak.')
r['quality']['experimental_outcome']='reported_partial';r['quality']['requested_tasks']=['partial_protocol'];r['quality']['missing_fields']+=['Low-acid absolute OA charge and definition of free-versus-total acid ratio.']
r['quality']['review_scope']='Low-OA3:1 comparison explicitly described as holding all other parameters constant. Common method values marked inherited. Exact OA quantity and sample linkage unresolved. Full main/SI reviewed.'
save(r)

# SI controls: omission of one or both reactive precursors. These are stability observations.
for key,label,cad,sul,ratio in [('neither','Neither Cd nor S precursor',False,False,None),('top-s-only','TOP-S only',False,True,None),('cd-oa-1to3','Cadmium oleate with Cd:OA1:3',True,False,3),('cd-oa-1to20','Cadmium oleate with Cd:OA1:20',True,False,20)]:
 loc='SI PDF p.2, printed S2, section S1 and Figure S1';e=E(loc)
 r=base('core-stability-'+key,'Nakonechnyi et al. (2017) · CdSe stability control · '+label,'CdSe',loc,parent='zb-cdse-core',kind='protocol_variant');r['method']='Blank seeded-growth stability control'
 r['materials']=[M('cores','CdSe core nanocrystals','CdSe','seed',loc,{'amount':Q(50,'nmol',loc,basis='Nanocrystal amount.')}),M('ode','1-Octadecene','C18H36','solvent',loc,{'reactor_volume':Q(3.8,'mL',loc,status='inherited',basis='SI says remaining compounds same amounts/conditions as main methods.'),'feed_volume':Q(1.12,'mL',loc,status='inherited',basis='Same-amount statement; no solvent replacement for omitted stocks specified.')}),M('oa','Oleic acid','C18H34O2','ligand',loc,{'amount':Q(None,'mmol',loc,basis='Control-specific charge not explicitly tabulated; do not reconcile acid-ratio conflict.')}),M('nitrogen','Nitrogen','N2','process_gas',loc),M('toluene','Toluene','C7H8','dilution_solvent',loc,{'aliquot_diluent':Q(1,'mL',loc,status='inherited',basis='Same conditions as method; exact control sample dilution not restated.')},stage='characterization')]
 if cad:r['materials'].append(M('cadmium-oleate','Cadmium oleate precursor',None,'metal_precursor',loc,{'cadmium_amount':Q(.25,'mmol',loc,status='inherited',basis='Main CdS method with SI same-compounds statement; isolated oleate concentration unreported.')}))
 if sul:
  r['materials'].append(M('top-s','TOP-S precursor solution',None,'chalcogen_precursor',loc,{'volume':Q(.38,'mL',loc,status='inherited'),'concentration':Q(2,'mol/L',loc,status='inherited')}))
  r['stocks']=[{'id':'top-s-stock','name':'Inherited TOP-S stock','components':[{'material_id':'top-s','quantities':{}}],'concentrations':{'concentration':Q(2,'mol/L',loc,status='inherited')},'preparation_operation_ids':[],'scope':'Preparation unreported; inherited from main protocol.','evidence':e}]
 mids=[m['id'] for m in r['materials'] if m['id'] not in ['cores','toluene','nitrogen']]
 r['material_states']=[state('control-medium','Control reaction medium',mids),state('control-batch','Control after CdSe injection',['control-medium','cores'],'reaction_batch'),state('aliquot-300s','Unpurified 300s aliquot',['control-batch','toluene'],'aliquot')]
 params={'temperature':Q(260,'degC',loc,status='inherited',basis='SI explicitly inherits main method conditions.'),'pretreatment_temperature':Q(120,'degC',loc,status='inherited'),'pretreatment_duration':Q(1,'h',loc,status='inherited')}
 if ratio:params['oa_cd_ratio']=Q(ratio,'mol/mol',loc,basis='Figure legend Cd:OA1:'+str(ratio))
 r['operations']=[operation('prepare-control','prepare_control','Prepare stated omission-control medium',e,mids+['nitrogen'],['control-medium'],stage='precursor_preparation',parameters=params,description='SI states all remaining compounds and conditions match methods. Complete control-specific solvent balance and preparation detail are not independently given. Do not add the omitted precursor. No assumption of a CdO dissolution endpoint when Cd is absent.'),operation('inject-cores','inject','Inject 50 nmol CdSe seeds',e,['control-medium','cores'],['control-batch'],depends=['prepare-control'],parameters={'seed_amount':Q(50,'nmol',loc),'temperature':Q(260,'degC',loc,status='inherited')}),operation('sample','sample','Analyze unpurified 300s aliquot',e,['control-batch','toluene'],['aliquot-300s'],depends=['inject-cores'],stage='characterization',parameters={'time_after_seed_injection':Q(300,'s',loc),'aliquot_mass':Q(None,'g',loc)},description='Absorption normalized at first-exciton peak. With aliquot mass the authors assess core size/concentration; no significant change found, no numerical detection limit given.')]
 r['products']=[product('stability-aliquot','CdSe',e,'explicit','aliquot-300s',notes=['First-exciton absorption unchanged and no significant core concentration change; these are qualitative null-change observations, not zero-valued quantitative labels.'])]
 r['quality']['experimental_outcome']='reported_product';r['quality']['requested_tasks']=['partial_protocol'];r['quality']['missing_fields']+=['Exact control-specific solvent balance, stock replacement volumes, acid charge and measurement detection limits.'];r['quality']['conflicts']=['SI1:20 nominal acid ratio is not silently reconciled with main5.6mmol OA/0.25mmol CdO.']
 save(r)

OUT=R/'canonical';OUT.mkdir(exist_ok=True)
for r in REC:(OUT/(r['record_id']+'.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
report={'schema_version':'1.0.0','record_count':len(REC),'record_ids':[r['record_id'] for r in REC],'validation':'passed','errors':[],'counts_are':'Literature method/variant/control records, not independent experimentally identified batches.','eligibility':{r['record_id']:eligibility(r) for r in REC}}
(R/'canonical-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='eligibility'},indent=2))
