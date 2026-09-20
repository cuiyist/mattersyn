from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=sorted((B/'canonical-drafts').glob('*.json'))
R={read(p)['record_id'].removeprefix('braun-2001-'):read(p) for p in paths};C=[]
def check(n,ok,detail=''):C.append({'check':n,'passed':bool(ok),'detail':detail})
def op(r,o):return next(x for x in R[r]['operations'] if x['id']==o)
def m(r,i):return next(x for x in R[r]['measurements'] if x['id']==i)
def qty(name,q,v=None,lo=None,hi=None,unit=None,approx=None):
 check(name+'/value-bounds',(q.get('value'),q.get('minimum'),q.get('maximum'))==(v,lo,hi))
 if unit is not None:check(name+'/unit',q['unit']==unit)
 if approx is not None:check(name+'/approximation',q['approximate']==approx)
def p(r,o,k,**kw):qty(r+'/'+o+'/'+k,op(r,o)['parameters'][k],**kw)
def z(r,i,**kw):qty(r+'/'+i,m(r,i)['value'],**kw)
check('nine records',len(R)==9)
check('three routes three procedures three observations',Counter(r['record_type'] for r in R.values())=={'literature_protocol':3,'procedure':3,'observation':3})
check('45 operations',sum(len(r['operations']) for r in R.values())==45)
check('75 measurement rows',sum(len(r['measurements']) for r in R.values())==75)
check('25 material slots',sum(len(r['materials']) for r in R.values())==25)
for row in read(B/'canonical-record-manifest.json')['records']:check(row['id']+'/manifest-hash',sha(B/'canonical-drafts'/(row['id']+'.json'))==row['sha256'])
def walk(x,path):
 if isinstance(x,dict):
  if 'evidence' in x:
   for e in x['evidence']:check(path+'/source',e.get('source_id')=='braun2001' and bool(e.get('locator')))
  for k,v in x.items():walk(v,path+'/'+str(k))
 elif isinstance(x,list):
  for i,v in enumerate(x):walk(v,path+'/'+str(i))
for name,r in R.items():
 walk(r,name); ids={a['sample_id'] for a in r['products']}; states={s['id'] for s in r['material_states']}; mats={a['id'] for a in r['materials']}; ops={o['id'] for o in r['operations']}
 check(name+'/unknown physical batch',r['lineage']['batch_id'] is None)
 check(name+'/source-group',r['lineage']['source_group']=='braun2001')
 check(name+'/unknown SI explicit','No SI supplied or independently matched' in r['sources'][0]['si_status'])
 check(name+'/no atomic coordinates',r['structure_assets']==[])
 for a in r['measurements']:check(name+'/'+a['id']+'/sample',a['sample_id'] in ids)
 for a in r['products']:
  check(name+'/'+a['sample_id']+'/unknown phase',a['phase']['status']=='not_reported')
  if a.get('source_state_id'):check(name+'/'+a['sample_id']+'/state',a['source_state_id'] in states)
 for a in r['operations']:
  check(name+'/'+a['id']+'/graph-inputs',all(i in states|mats for i in a['inputs']))
  check(name+'/'+a['id']+'/graph-outputs',all(i in states for i in a['outputs']))
  check(name+'/'+a['id']+'/operation-dependencies',all(i in ops for i in a['depends_on']))
for key,seq,cs,bs,absn,pl,cross,short,long in [('i','A–B–C',1,1,625,820,600,500,650),('ii','A–B–C–B–C',2,2,700,950,700,500,900),('iii','A–B–C–C–C–B–C',4,2,670,820,650,600,750)]:
 r='system-'+key;rec=R[r]
 for o,k,v,u in [('a-prepare','solution_volume',100,'mL'),('a-prepare','cd2_concentration',.0002,'M'),('a-prepare','flask_capacity',250,'mL'),('a-prepare','initial_pH',7.9,'pH'),('a-inject','h2s_gas_volume',.6,'mL'),('a-grow','final_pH',4.6,'pH'),('a-purge','duration',20,'min')]:p(r,o,k,v=v,unit=u)
 p(r,'a-grow','acidic_onset_time',v=30,unit='s',approx=True)
 check(r+'/acidification not total growth time','not full growth duration' in op(r,'a-grow')['parameters']['acidic_onset_time']['basis'])
 check(r+'/gas volume not moles','no mole conversion' in op(r,'a-inject')['parameters']['h2s_gas_volume']['basis'])
 for bi in range(1,bs+1):
  oid=f'b{bi}-exchange'
  for k,v,u in [('hg_stock_volume',12,'mL'),('hg2_stock_concentration',.001,'M'),('hg_solution_pH',7,'pH')]:p(r,oid,k,v=v,unit=u)
  check(r+'/'+oid+'/pH source scope','added aqueous Hg2+' in op(r,oid)['parameters']['hg_solution_pH']['basis'])
  check(r+'/'+oid+'/no extra Cd or sulfur',['hg2','water']==op(r,oid)['inputs'][-2:] and 'cd2' not in op(r,oid)['inputs'] and 'h2s' not in op(r,oid)['inputs'])
  check(r+'/'+oid+'/retained released Cd','remains dissolved' in op(r,oid)['description'])
 for ci in range(1,cs+1):
  oid=f'c{ci}-grow';p(r,oid,'dropwise_addition_duration',v=25,unit='min');p(r,oid,'pH',v=7,unit='pH');p(r,oid,'h2s_stock_volume',unit='mL');p(r,oid,'h2s_stock_concentration',unit='M')
  p(r,f'c{ci}-purge','duration_lower_bound',lo=20,unit='min')
  check(r+'/'+oid+'/aqueous feed separate','h2s-aqueous' in op(r,oid)['inputs'] and 'h2s' not in op(r,oid)['inputs'])
  check(r+'/'+oid+'/no unreported argon atmosphere',op(r,oid)['environment']['value'] is None)
 extra=[o['id'] for o in rec['operations'] if o['action']=='cadmium_precursor_addition']
 check(r+'/conditional topups',extra==(['c2-add-cd','c3-add-cd'] if key=='iii' else []))
 for oid in extra:
  for k,u in [('additional_cd2_amount','mol'),('additional_cd2_stock_volume','mL'),('additional_cd2_stock_concentration','M')]:p(r,oid,k,unit=u)
 check(r+'/exact sequence',m(r,'step-sequence')['value']['value']==seq)
 for i,v,u in [('a-core-preparation-size',3.5,'nm'),('a-core-absorption',470,'nm'),('system-core-size',3.2,'nm'),('well-count',2 if key=='iii' else 1,'count'),('well-layer-count',2 if key=='ii' else 1,'monolayer'),('well-thickness',.8 if key=='ii' else .4,'nm'),('cap-layer-count',1,'monolayer'),('cap-thickness',.4,'nm'),('absorption-transition',absn,'nm'),('pl-maximum',pl,'nm'),('relaxation-crossover',cross,'nm'),('inset-short-probe',short,'nm'),('inset-long-probe',long,'nm')]:z(r,i,v=v,unit=u)
 z(r,'short-lived-component',v=5,unit='ps',approx=True)
 z(r,'estimated-qy-bound',hi=1,unit='%',approx=True);check(r+'/strict estimated upper QY bound',m(r,'estimated-qy-bound')['value']['maximum_exclusive'] is True)
 check(r+'/core contradiction','3.5 nm' in str(rec['quality']['conflicts']) and '3.2 nm' in str(rec['quality']['conflicts']))
 check(r+'/inset bleach preserved','bleach' in m(r,'inset-long-probe')['conditions'] and 'stimulated emission' in m(r,'inset-long-probe')['conditions'])
 check(r+'/partial tasks only',rec['quality']['requested_tasks']==['precursor_selection','partial_protocol'])
 check(r+'/temperature not fabricated',all('temperature' not in o['parameters'] for o in rec['operations']))
 check(r+'/no inserted isolation',not any(any(w in o['action'] for w in ['centrifug','drying','washing']) for o in rec['operations']))
 expected_samples=['a-cds-core','b-hgs']+(['c-single-well','d-thick-cds','second-hgs'] if key=='iii' else ['c-single-well','second-hgs'] if key=='ii' else [])+['final']
 check(r+'/source stage products only',[a['sample_id'] for a in rec['products']]==expected_samples)
 if key=='iii':z(r,'barrier-layer-count',v=2,unit='monolayer');z(r,'barrier-thickness',v=.8,unit='nm')
for o,k,v,u in [('excite','excitation_wavelength',440,'nm'),('excite','pump_pulse_duration',5,'ns'),('excite','laser_repetition_rate',10,'Hz'),('excite','detection_angle',90,'degree')]:p('photoluminescence-acquisition',o,k,v=v,unit=u)
check('PL pulse width attributed to NdYAG pump','Q-switched Nd:YAG' in op('photoluminescence-acquisition','excite')['parameters']['pump_pulse_duration']['basis'])
check('PL water reference separate',op('photoluminescence-acquisition','water-reference')['inputs']==['water'] and op('photoluminescence-acquisition','water-reference')['depends_on']==[])
check('PL subtraction consumes data not liquids',op('photoluminescence-acquisition','subtract')['inputs']==['pl-raw','water-reference-data'])
for o,k,v,u in [('load','cell_thickness',2,'mm'),('probe','fundamental_wavelength',800,'nm'),('pump','excitation_wavelength',400,'nm'),('pump','pulse_duration_fwhm',100,'fs'),('pump','pulse_energy',100,'uJ'),('delay-scan','optical_delay_line_spatial_resolution',3,'um'),('delay-scan','reported_delay_time_resolution',21,'fs')]:p('transient-absorption-acquisition',o,k,v=v,unit=u)
p('transient-absorption-acquisition','probe','probe_spectral_range',lo=450,hi=1050,unit='nm')
check('No fs laser repetition inferred',not any('repetition' in k for o in R['transient-absorption-acquisition']['operations'] for k in o['parameters']))
check('No transient pathlength moved to steady absorption',all('cell' not in k and 'path' not in k for o in R['absorption-acquisition']['operations'] for k in o['parameters']))
for r,o in [('absorption-acquisition','record'),('photoluminescence-acquisition','excite'),('transient-absorption-acquisition','load')]:p(r,o,'temperature',unit='degC');check(r+'/RT retained qualitatively','Room temperature' in op(r,o)['parameters']['temperature']['qualifier'])
z('optical-comparison','oscillator-ratio',v=2,unit='ratio');z('optical-comparison','atom-count-ratio',v=2,unit='ratio',approx=True);z('chemical-interpretation','solubility-contrast',v=26,unit='orders_of_magnitude')
check('Source S-minus not normalized away','Source prints S−' in m('chemical-interpretation','nucleation-ph')['value']['value'])
check('No invented System III quantitative theory','unavailable' in m('chemical-interpretation','wavefunction-scope')['value']['value'])
check('Reference 13 remains submitted','submitted' in m('literature-context','cited-preparation')['value']['value'])
notes={
 'system-i':'A–B–C; 100 mL/0.2 mM Cd feed, 0.6 mL gas, pH changes, 20 min A purge, 12 mL/1 mM Hg feed, 25 min aqueous sulfur overgrowth and ≥20 min C purge. Unknown salts, stabilizer, sulfur stock, temperature and growth duration preserved. Three stages and own final optical values retained.',
 'system-ii':'A–B–C–B–C; second exchange replaces existing cap, creates contiguous double HgS well, then recaps. No new Cd charge after either B, no false isolated two-well architecture. Five spectral stages and own 700/950/700 nm transition/PL/crossover values.',
 'system-iii':'A–B–C–C–C–B–C; unquantified Cd top-ups only in two consecutive C steps. Three CdS layers before second exchange leave two as barrier. Six plotted stages; no invented spectrum after the first extra C. Own 670/820/650 nm values and two separated wells retained.',
 'absorption-acquisition':'All 3/5/6 source stage assignments compared. Numerical steady-state hardware and dilution are absent. Second-derivative minima are distinct from PL maxima and relaxation crossover.',
 'photoluminescence-acquisition':'440 nm OPO, third harmonic Nd:YAG pump, 5 ns pump pulses/10 Hz, 90-degree detection, filter/monochromator/CCD, separate water reference and Raman/background subtraction. No material Raman dataset asserted.',
 'transient-absorption-acquisition':'400 nm/100 fs FWHM/100 µJ pump; 800 nm sapphire continuum 450–1050 nm; delay line 3 µm (21 fs), rotating 2 mm cell. No pump repetition rate, fluence or exact kinetic model invented. Author bleach/stimulated-emission interpretation kept explicit.',
 'optical-comparison':'Relative oscillator ratio, author approximate atom-count argument and equal HgS content, energy ordering, interface-trap interpretation and interwell coupling preserve source scope; no elemental assay or direct trap location implied.',
 'chemical-interpretation':'Source simplified S− notation and 26-order Ksp claim retained as author rationale. Conditional precursor inventory, separated-well growth logic, cited tetrahedral morphology, schematic wavefunctions and future barrier study are not new atomistic measurements.',
 'literature-context':'Prior preparation/theory/TEM/ODMR remain cited context, including unidentifiable submitted ref13. Present paper has no TEM/XRD/SAED/CIF or independently matched SI. Economic/manufacturing motivation remains qualitative.'}
rows=[{'record_id':r['record_id'],'sha256':sha(B/'canonical-drafts'/(r['record_id']+'.json')),'manual_source_review':'passed','operations_reviewed':[x['id'] for x in r['operations']],'measurement_rows_reviewed':[x['id'] for x in r['measurements']],'findings':notes[k]} for k,r in R.items()]
fail=[c for c in C if not c['passed']]
report={'status':'passed' if not fail else 'failed','source_id':'braun2001','audited_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':'00ac817e60651f0e7f9faabe85ba18372ac37fea1f0f5d174779c982064b4184','source_inventory_sha256':sha(B/'source-audit.json'),'canonical_manifest_sha256':sha(B/'canonical-record-manifest.json'),'record_hashes':{r['record_id']:r['sha256'] for r in rows},'record_count':9,'operation_count':45,'measurement_count':75,'material_slots':25,'manual_review_scope':'All four source pages independently read and visually inspected, all nine records including 45 operations and 75 measurement rows source-compared. Automated hash/quantity/lineage checks supplement that review. Bibliography, funding and figure-axis metadata remain in the complete source inventory and reader rather than being promoted to synthesis outcome measurements.','records':rows,'check_count':len(C),'checks':C,'failures':fail,'failure_count':len(fail),'limitations':['Local matched source is main-only; no SI independently located.','3.5/3.2 nm core discrepancy and Figure4 bleach/stimulated-emission label distinction are not resolved experimentally.','Nominal layers and optical interpretation do not establish exact crystal phase, coordinates or unique physical batch.','Only precursor selection and partial-protocol tasks requested; review/promotion/export/browser checks remain parent-owned.'],'site_mutated':False,'browser_verified':False}
(B/'canonical-records-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'canonical-records-audit.md').write_text('# Braun 2001 canonical source audit\n\n'+report['status']+f': nine records, 45 operations, 75 measurement rows and 25 material slots. {len(C)} supporting checks; {len(fail)} failures.\n\n'+'\n\n'.join('**'+k+'**: '+v for k,v in notes.items())+'\n\nExact file hashes and remaining source limits are recorded in canonical-records-audit.json. No Site or lifecycle mutation.\n',encoding='utf8')
print(json.dumps({'status':report['status'],'check_count':len(C),'failures':fail},ensure_ascii=False))
