from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import json,hashlib,runpy
B=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
R={read(p)['record_id'].removeprefix('yi-2002-'):read(p) for p in sorted((B/'canonical-drafts').glob('*.json'))};C=[]
def ck(n,v,d=''):C.append({'check':n,'passed':bool(v),'detail':d})
def op(r,i):return next(o for o in R[r]['operations'] if o['id']==i)
def m(r,i):return next(x for x in R[r]['measurements'] if x['id']==i)
def mat(r,i):return next(x for x in R[r]['materials'] if x['id']==i)
def q(n,x,v=None,lo=None,hi=None,u=None,status=None):
 ck(n+'/value-bounds',(x.get('value'),x.get('minimum'),x.get('maximum'))==(v,lo,hi))
 if u is not None:ck(n+'/unit',x['unit']==u)
 if status is not None:ck(n+'/status',x['status']==status)
def p(r,o,k,**kw):q(r+'/'+o+'/'+k,op(r,o)['parameters'][k],**kw)
def z(r,i,**kw):q(r+'/'+i,m(r,i)['value'],**kw)
generated=runpy.run_path(str(B/'build_records.py'))['records']
for r in generated:ck(r['record_id']+'/actual equals independently read authoring',r==R[r['record_id'].removeprefix('yi-2002-')])
ck('18 records',len(R)==18);ck('105 operations',sum(len(r['operations'])for r in R.values())==105);ck('91 measurements',sum(len(r['measurements'])for r in R.values())==91)
ck('types',Counter(r['record_type']for r in R.values())=={'literature_protocol':6,'procedure':11,'observation':1})
def walk(x,where):
 if isinstance(x,dict):
  for e in x.get('evidence',[]):ck(where+'/source',e.get('source_id')=='yi2002' and bool(e.get('locator')))
  for k,v in x.items():walk(v,where+'/'+str(k))
 elif isinstance(x,list):
  for i,v in enumerate(x):walk(v,where+'/'+str(i))
for name,r in R.items():
 walk(r,name);samples={x['sample_id']for x in r['products']};states={x['id']for x in r['material_states']};mats={x['id']for x in r['materials']};ops={x['id']for x in r['operations']}
 ck(name+'/unknown batch',r['lineage']['batch_id'] is None);ck(name+'/no atomic coordinates',r['structure_assets']==[]);ck(name+'/SI unknown','No matching SI supplied' in r['sources'][0]['si_status'])
 ck(name+'/nominal target',r['intended_target']['composition']['value']=='La2(MoO4)3:Yb,Er')
 for a in r['measurements']:ck(name+'/'+a['id']+'/sample',a['sample_id']in samples)
 for a in r['products']:
  if a.get('material_state_id'):ck(name+'/'+a['sample_id']+'/state',a['material_state_id']in states)
 for a in r['operations']:
  ck(name+'/'+a['id']+'/inputs',all(i in states|mats for i in a['inputs']));ck(name+'/'+a['id']+'/outputs',all(i in states for i in a['outputs']));ck(name+'/'+a['id']+'/dependencies',all(i in ops for i in a['depends_on']))
for row in read(B/'canonical-record-manifest.json')['records']:ck(row['id']+'/manifest',sha(B/'canonical-drafts'/(row['id']+'.json'))==row['sha256'])
charges={'lanthanum-oxide':(1.176,3.607),'ytterbium-oxide':(.3692,.937),'erbium-oxide':(.05370,.140),'ammonium-molybdate':(1.961,9.37)}
for r in ['stock-a','stock-b','anneal-600','anneal-700','anneal-800','anneal-900','anneal-1000']:
 for i,(mass,amount)in charges.items():
  if not any(x['id']==i for x in R[r]['materials']):continue
  explicit=r in ['stock-a','stock-b','anneal-800']
  q(r+'/'+i+'/mass',mat(r,i)['quantities']['mass'],v=mass if explicit else None,u='g')
  q(r+'/'+i+'/amount',mat(r,i)['quantities']['amount'],v=amount if explicit else None,u='mmol')
  if i!='ammonium-molybdate':q(r+'/'+i+'/purity',mat(r,i)['quantities']['purity'],v=99.99,u='%')
  if r.startswith('anneal'):ck(r+'/'+i+'/precursor role',mat(r,i)['role']=='metal_precursor' and mat(r,i)['stage']=='synthesis' and 'introduced through' in ' '.join(mat(r,i)['notes']))
 if r!='stock-b':
  p(r,'redissolve-a','water_volume',v=30,u='mL');p(r,'stir-a','duration',v=1,u='h');p(r,'dry-a','temperature',u='°C');p(r,'dry-a','duration',u='min')
  ck(r+'/unknown final molarity',R[r]['stocks'][0]['concentrations']['rare_earth_concentration']['value'] is None)
 if r!='stock-a':p(r,'dissolve-b','water_volume',v=30,u='mL');p(r,'stir-b','duration',v=1,u='h');ck(r+'/literal molybdate',mat(r,'ammonium-molybdate')['formula']=='(NH4)2MoO4')
for t in [600,700,800,900,1000]:
 r='anneal-'+str(t);inherited='reported'if t==800 else'inherited'
 for o,k,v,u in [('stir-suspension','duration',20,'min'),('transfer','vessel_capacity',100,'mL'),('hydrothermal','temperature',180,'°C'),('hydrothermal','duration',1,'h'),('centrifuge','rotation_rate',6000,'rpm'),('centrifuge','duration',10,'min'),('wash','wash_count',2,'cycles')]:p(r,o,k,v=v,u=u,status=inherited)
 p(r,'combine','addition_rate',lo=20,hi=30,u='drops/min',status=inherited);p(r,'hydrothermal','pressure',u='bar');p(r,'wash','wash_volume',u='mL');p(r,'dry','temperature',u='°C');p(r,'dry','duration',u='h')
 p(r,'ramp','target_temperature',v=t,u='°C');p(r,'ramp','heating_rate',v=20 if t==800 else None,u='°C/min');p(r,'anneal','temperature',v=t,u='°C');p(r,'anneal','duration',v=5,u='h')
 ck(r+'/dry air only',op(r,'dry')['environment']['value']=='Air' and op(r,'anneal')['environment']['value'] is None and op(r,'ramp')['environment']['value'] is None)
 ck(r+'/B into A',op(r,'combine')['inputs']==['solution-a','solution-b'] and 'B-to-A' in op(r,'combine')['description'])
 ck(r+'/stock stages physical',all(op(r,o)['stage']=='precursor_preparation' for o in ['dissolve-a','dry-a','redissolve-a','stir-a','dissolve-b','stir-b']))
 ck(r+'/both feed conflicts',len(R[r]['quality']['conflicts'])==1 and 'stoichiometry' in R[r]['quality']['conflicts'][0])
 ck(r+'/retained precipitate',op(r,'centrifuge')['retained_fraction']=='precipitate')
 if t!=800:ck(r+'/common not separate measured batch',all('Inherited common' in op(r,o)['description'] for o in ['dissolve-a','hydrothermal','wash','cool']))
 ck(r+'/no interpolated per-variant diameter',not any('size' in x['property']for x in R[r]['measurements'])if t!=800 else True)
z('anneal-800','crystallite-size',v=52.5,u='nm',status='author_derived')
ck('800 minor phase', 'second phase' in next(x for x in R['anneal-800']['products']if x['sample_id']=='final')['phase']['value'])
ck('bulk inputs distinct MoO3',op('bulk','mix')['inputs']==['lanthanum-oxide','molybdenum-trioxide','ytterbium-oxide','erbium-oxide'])
for k,v in [('la_ratio',77),('yb_ratio',20),('er_ratio',3)]:p('bulk','mix',k,v=v,u='molar parts')
p('bulk','fire','temperature',v=1200,u='°C');p('bulk','fire','duration',v=5,u='h');p('bulk','press','pressure',u='bar');ck('Bulk air',op('bulk','fire')['environment']['value']=='Air')
ck('Grinding comparison analytical not mixture',next(x for x in R['bulk-grinding']['material_states']if x['id']=='grinding-comparison')['kind']=='analysis_data')
ck('Grinding no size invented','final size' in op('bulk-grinding','grind')['description'] and len(R['bulk-grinding']['measurements'])==2)
for k,v in [('peak_two_theta',28.053),('measured_fwhm_b1',.186),('instrument_broadening_b0',.104)]:p('xrd','scherrer',k,v=v,u='°')
z('xrd','scherrer-size',v=52.5,u='nm',status='author_derived');ck('XRD minor phase','second phase' in R['xrd']['products'][0]['phase']['value']);ck('XRD not SAED','SAED' in m('xrd','single-crystal-inference')['value']['value'])
z('tem','scale-before',v=300,u='nm');z('tem','scale-after',v=100,u='nm');z('tem','diameter-range',lo=40,hi=60,u='nm')
z('particle-size','majority-range',lo=45,hi=65,u='nm');z('particle-size','average',v=53,u='nm');z('particle-size','rounded-summary',v=50,u='nm');ck('No assumed DLS/hydrodynamic type','does not specify' in op('particle-size','acquire')['description'])
for r in ['particle-size','downconversion','near-ir','power-response']:ck(r+'/generic specimen',R[r]['materials'][0]['id']=='nanocrystal-specimen' and all(x['recipe_link']=='general_context'for x in R[r]['products']))
p('downconversion','excite','excitation_wavelength',v=374,u='nm');z('downconversion','emission-h',v=525,u='nm');z('downconversion','emission-s',v=549,u='nm')
p('upconversion','excite','excitation_wavelength',v=980,u='nm');p('upconversion','excite','laser_power_specification',v=50,u='mW')
ck('Separate physical comparison specimens',R['upconversion']['material_states'][0]['kind']=='sample_set')
for w in [519,541,653]:z('upconversion','peak-'+str(w),v=w,u='nm')
ck('Selected800 not brightness maximum','not the claimed maximum' in m('upconversion','selected-condition')['value']['value'])
p('near-ir','acquire','wavenumber_range',lo=9000,hi=11000,u='cm^-1');z('near-ir','center-wavenumber',v=10238,u='cm^-1');z('near-ir','center-wavelength',v=976,u='nm');z('near-ir','band-wavenumber',lo=9875,hi=10625,u='cm^-1');z('near-ir','band-wavelength',lo=941,hi=1013,u='nm')
ck('NearIR inverted original ordinate','0 at the top and 1 at the bottom' in m('near-ir','plot-axis')['value']['value'])
for er in [1,2,3,4,5,7]:z('erbium-series','fraction-'+str(er),v=er,u='mol%')
ck('Er6 not fabricated',not any(x['id']=='fraction-6'for x in R['erbium-series']['measurements']));ck('Er doses unreported','not six fully weighed' in m('erbium-series','recipe-limit')['value']['value']);ck('Fig7 prose/curve conflict',len(R['erbium-series']['quality']['conflicts'])==2)
for w,roundv,v in [(519,2.20,2.2024),(541,1.89,1.8853),(653,2.09,2.0907)]:
 z('power-response','slope-prose-'+str(w),v=roundv,u='dimensionless',status='author_derived');z('power-response','slope-figure-'+str(w),v=v,u='dimensionless',status='author_derived')
z('power-response','caption-wavelength',v=520,u='nm');z('power-response','photon-count',v=2,u='photons',status='author_derived');p('power-response','sweep','irradiance',u='W/cm^2')
for i in ['sensitizer','two-steps','bulk-decay','surface-sites','lifetime','emission-location','size-explanation']:ck('Mechanism/'+i+'/attribution',m('mechanisms',i)['value']['status']=='author_derived')
ck('Figure9 I9/2 literal','4I9/2' in m('mechanisms','energy-diagram')['value']['value']);ck('No current bioassay','no current bioconjugation' in m('mechanisms','applications')['value']['value'])
notes={
'stock-a':'All three oxide masses, mmol, 99.99% grades and Aldrich source; diluted acid dissolution, warming dry, 30 mL added water and one-hour room-temperature stirring verified. Actual nitrate identity, acid amount, final stock volume and molarity remain unknown.',
'stock-b':'Literal (NH4)2MoO4, 1.961 g and 9.37 mmol retained with unresolved formula/mass discrepancy. 30 mL added water and one-hour room-temperature stirring are not a measured final molarity.',
**{'anneal-'+str(t):f'{t} °C / 5 h endpoint retains the complete stock and hydrothermal framework. B enters A at 20–30 drops/min; 20 min stirring, 100 mL vessel, 180 °C/1 h, 6000 rpm/10 min, two washes and air drying verified. '+('800 °C carries the explicitly weighed recipe, 20 °C/min ramp and measured XRD phase/52.5 nm coherent size.'if t==800 else 'Common upstream parameters and natural cooling are explicitly inherited; per-endpoint charges and ramp unknown. No independent physical batch or interpolated size is asserted.')+' Annealing atmosphere, hydrothermal pressure and stock chemistry unresolved; both precursor conflicts retained.'for t in [600,700,800,900,1000]},
'bulk':'La/Yb/Er oxide plus MoO3 mixing, cation ratio 77:20:3, pellet pressing and 1200 °C/5 h air firing independently verified. No hydrothermal charges, unknown Mo ratio, ramp, pellet pressure or direct bulk refinement copied.',
'bulk-grinding':'Current-paper control is retained as incomplete grinding procedure and optical comparison. No final size, spectrum, quantified loss or independently measured defect concentration is invented.',
'xrd':'800 °C/5 h specimen only; tetragonal phase with unidentified minor phase and ICDD 45-0407, 28.053° peak, 0.186°/0.104° widths and author-derived 52.5 nm retained. No fabricated wavelength, Scherrer constants, phase purity, coordinates or SAED.',
'tem':'Before/after800 °C panels have separate 300/100 nm bars; 40–60 nm majority range is the joint source discussion, not a panel-specific histogram. Nearly spherical appearance and unchanged-size claim retained without measured lattice.',
'particle-size':'BI-90Plus distribution, 45–65 nm majority, approximately53 nm mean and rounded50 nm summary remain distinct from Scherrer size and TEM. No assumed exact batch, DLS weighting, hydrodynamic metric, or histogram digitization.',
'downconversion':'374 nm excitation and 525/549 nm peaks/assignments preserved. Solid emission versus dotted excitation remain distinct; excitation-scan monitoring wavelength unknown.',
'upconversion':'980 nm external laser50 mW specification, LS-50B/front-surface/fiber setup, 519/541/653 nm assignments, five anneal endpoints and independent1200 °C bulk comparison verified. Separate sample-set state, arbitrary scales and no absolute quantum yield. 800 °C is size/intensity compromise, not brightest curve.',
'near-ir':'PE SYSTEM2000/quartz optics,9000–11000 cm−1 scan,~10238/976 center and9875–10625 cm−1/941–1013 nm source companion interval retained. Original reversed absorbance ordinate preserved; proposed excitation window is not a measured efficiency map.',
'erbium-series':'Only six visible points1,2,3,4,5,7%; no6% recipe. Printed1–7% trend versus near-maximum4% point is explicit. Nominal Er percentage denominator, compensation doses and exact channel are unknown; no six weighed syntheses.',
'power-response':'All three exact legend slopes and rounded prose values retained as author regression results;519 versus caption520 conflict remains. Log axes have no physical power unit/calibration;50 mW does not specify each point. Approximately two-photon interpretation is not a uniquely proven mechanism.',
'mechanisms':'Every energy-level label, sensitizer/emitter role, proposed surface/interior emission and lifetime rationale reviewed. These are author models or prior references, not measured rates, site occupancy, absolute efficiency, bioconjugation or laser demonstration. All27 bibliography entries remain in full reader/source inventory.'}
rows=[{'record_id':r['record_id'],'sha256':sha(B/'canonical-drafts'/(r['record_id']+'.json')),'manual_source_review':'passed','operations_reviewed':[x['id']for x in r['operations']],'measurement_rows_reviewed':[x['id']for x in r['measurements']],'findings':notes[k]}for k,r in R.items()]
fail=[x for x in C if not x['passed']]
out={'status':'passed'if not fail else'failed','source_id':'yi2002','audited_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':'6438ee53b3fffb86f5e36508f265041d9235b8ee9f3e20dd99d46aae91c68a57','source_inventory_sha256':sha(B/'source-audit.json'),'canonical_manifest_sha256':sha(B/'canonical-record-manifest.json'),'record_hashes':{x['record_id']:x['sha256']for x in rows},'record_count':18,'operation_count':105,'measurement_count':91,'material_slots':57,'manual_review_scope':'All five main pages independently read and visually inspected, with high-resolution Figure2/8/9 labels. Complete authoring and actual byte-bound records independently compared with source: all105 operations,91 measurement rows,stocks,materials,products,unknowns and contexts. Supporting assertions do not replace scientific review.','records':rows,'check_count':len(C),'checks':C,'failure_count':len(fail),'failures':fail,'limits':['No matched SI or cited external full texts read.','Nominal host/dopant formula is not a composition assay or refined atomic structure.','Temperature comparisons share an inherited preparation framework; unknown individual masses and ramp rates are not invented.','No absolute optical quantum efficiency, lifetime or exact figure-to-batch linkage is supplied.'],'site_mutated':False,'browser_verified':False}
(B/'canonical-records-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'canonical-records-audit.md').write_text('# Yi 2002 canonical source audit\n\n'+out['status']+f':18 records,105 operations,91 measurements; {len(C)} supporting checks; {len(fail)} failures.\n\n'+'\n\n'.join('**'+k+'**: '+v for k,v in notes.items())+'\n\nExact current hashes are bound in the JSON report. No Site edits or browser verification.\n',encoding='utf8')
print(json.dumps({'status':out['status'],'checks':len(C),'failures':fail},ensure_ascii=False))
