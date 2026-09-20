from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
R={read(p)['record_id'].removeprefix('besson-2002-'):read(p) for p in sorted((B/'canonical-drafts').glob('*.json'))}; C=[]
def ck(n,ok,d=''):C.append({'check':n,'passed':bool(ok),'detail':d})
def op(r,i):return next(o for o in R[r]['operations'] if o['id']==i)
def m(r,i):return next(x for x in R[r]['measurements'] if x['id']==i)
def q(n,x,v=None,lo=None,hi=None,u=None,approx=None):
 ck(n+'/value-bounds',(x.get('value'),x.get('minimum'),x.get('maximum'))==(v,lo,hi))
 if u is not None:ck(n+'/unit',x['unit']==u)
 if approx is not None:ck(n+'/approximation',x['approximate']==approx)
def p(r,o,k,**kw):q(r+'/'+o+'/'+k,op(r,o)['parameters'][k],**kw)
def z(r,i,**kw):q(r+'/'+i,m(r,i)['value'],**kw)
ck('12 records',len(R)==12);ck('36 operations',sum(len(r['operations']) for r in R.values())==36);ck('98 measurements',sum(len(r['measurements']) for r in R.values())==98)
ck('Record types',Counter(r['record_type'] for r in R.values())=={'literature_protocol':2,'protocol_variant':1,'procedure':7,'observation':2})
def walk(x,where):
 if isinstance(x,dict):
  if 'evidence' in x:
   for e in x['evidence']:ck(where+'/source',e.get('source_id')=='besson2002' and bool(e.get('locator')))
  for k,v in x.items():walk(v,where+'/'+str(k))
 elif isinstance(x,list):
  for i,v in enumerate(x):walk(v,where+'/'+str(i))
for name,r in R.items():
 walk(r,name); samples={x['sample_id'] for x in r['products']}; states={x['id'] for x in r['material_states']}; mats={x['id'] for x in r['materials']}; ops={x['id'] for x in r['operations']}
 ck(name+'/unknown physical batch',r['lineage']['batch_id'] is None);ck(name+'/source group',r['lineage']['source_group']=='besson2002');ck(name+'/no atomic coordinate claim',r['structure_assets']==[])
 ck(name+'/SI missingness explicit','No supporting information supplied or matched' in r['sources'][0]['si_status'])
 for a in r['measurements']:ck(name+'/'+a['id']+'/sample association',a['sample_id'] in samples)
 for a in r['products']:
  if a.get('source_state_id'):ck(name+'/'+a['sample_id']+'/state link',a['source_state_id'] in states)
 for a in r['operations']:
  ck(name+'/'+a['id']+'/inputs',all(i in states|mats for i in a['inputs']));ck(name+'/'+a['id']+'/outputs',all(i in states for i in a['outputs']));ck(name+'/'+a['id']+'/dependencies',all(i in ops for i in a['depends_on']))
for row in read(B/'canonical-record-manifest.json')['records']:ck(row['id']+'/manifest hash',sha(B/'canonical-drafts'/(row['id']+'.json'))==row['sha256'])
for o,k,v,u in [('mix','teos_ratio',1,'relative mol'),('mix','water_ratio',5,'relative mol'),('mix','ethanol_ratio',3.8,'relative mol'),('mix','water_pH',1.25,'pH'),('age','temperature',60,'°C'),('age','duration',1,'h'),('template','ctab_teos_molar_ratio',.1,'mol/mol'),('dilute','dilution_ratio',1,'ratio'),('spin-coat','rotation_speed',3000,'rpm'),('calcine','temperature',450,'°C')]:p('ctab-silica-host',o,k,v=v,u=u)
ck('1:1 dilution basis unresolved','not specified' in op('ctab-silica-host','dilute')['parameters']['dilution_ratio']['basis'])
ck('Water pH not mixed-sol pH','not a measured mixed-sol pH' in op('ctab-silica-host','mix')['parameters']['water_pH']['basis'])
ck('Air belongs to calcination only',op('ctab-silica-host','calcine')['environment']['value']=='Air' and op('ctab-silica-host','age')['environment']['value'] is None)
for o,k,u in [('spin-coat','duration','s'),('calcine','duration','h'),('calcine','heating_rate','°C/min')]:p('ctab-silica-host',o,k,u=u)
z('ctab-silica-host','film-thickness',v=300,u='nm',approx=True);z('ctab-silica-host','pore-diameter',v=3.5,u='nm');z('ctab-silica-host','initial-c',v=6.9,u='nm')
ck('Pore diameter is spherical model derived',m('ctab-silica-host','pore-diameter')['value']['status']=='author_derived')
for o,k,v,u in [('prepare','cadmium_nitrate_concentration',.1,'M'),('complex','ammonia_equivalents',1,'equiv'),('complex','sodium_citrate_equivalents',1,'equiv'),('complex','citrate_stock_concentration',1,'M'),('adjust-ph','target_pH',9.5,'pH')]:p('cadmium-stock',o,k,v=v,u=u)
p('cadmium-stock','complex','ammonia_stock_concentration',u='M');p('cadmium-stock','adjust-ph','additional_ammonia_volume',u='mL')
for host,size1,size2,cyc in [('ctab',2.2,3.6,9),('copolymer',3.3,5.8,6)]:
 r=host+'-cds-loading';p(r,'impregnate','solution_pH',v=9.5,u='pH');p(r,'repeat','total_cycles',v=cyc,u='cycles')
 for o,k,u in [('impregnate','immersion_duration','min'),('impregnate','solution_volume','mL'),('rinse','rinse_volume','mL'),('evacuate','vacuum_pressure','Pa'),('evacuate','duration','min'),('sulfide','h2s_pressure_endpoint','Pa'),('sulfide','gas_flow','mL/min'),('sulfide','exposure_duration','min')]:p(r,o,k,u=u)
 ck(r+'/symbolic pressure retained','atmospheric pressure' in op(r,'sulfide')['endpoint']['value'])
 ck(r+'/partial tasks only',R[r]['quality']['requested_tasks']==['precursor_selection','partial_protocol'])
 z(r,'first-cycle-diameter',v=size1,u='nm');z(r,'saturated-diameter',v=size2,u='nm');z(r,'saturation-cycles',v=cyc,u='cycles')
 for i in ('first-cycle-diameter','saturated-diameter'):ck(r+'/'+i+'/derived optical size',m(r,i)['value']['status']=='author_derived')
 ck(r+'/no final isolation invented',not any('centrifug' in o['action'] or 'dry' in o['action'] or 'anneal' in o['action'] for o in R[r]['operations']))
ck('Copolymer count is interpretation of plotted endpoint',op('copolymer-cds-loading','repeat')['parameters']['total_cycles']['status'] in ['figure_read','inferred'])
ck('Copolymer figure count not typed author saturation measurement','endpoint' in m('copolymer-cds-loading','saturation-cycles')['property'])
ck('Copolymer not assigned CTAB atomic phase',R['copolymer-cds-loading']['products'][-1]['phase']['value'] is None)
z('copolymer-cds-loading','weak-confinement-size',lo=5,u='nm');ck('Strict above-five interpretation',m('copolymer-cds-loading','weak-confinement-size')['value']['minimum_exclusive'] is True)
for s in ('ctab-series','copolymer-series'):
 z('uv-visible',s+'-spectral-range',lo=300,hi=600,u='nm');z('uv-visible',s+'-absorbance-range',lo=0,hi=.5,u='dimensionless')
for i,v in [('calcined',6.9),('cadmium-adsorbed',6.8),('saturated',7.2)]:z('xrd',i+'-meso-c',v=v,u='nm')
z('xrd','adsorbed-relative-intensity',v=.5,u='ratio',approx=True);z('xrd','figure-range',lo=2.2,hi=2.9,u='degree');z('xrd','calcined-scale',v=.5,u='ratio');z('xrd','first-cycle-scale',v=5,u='ratio')
for r in ('xrd','sims'):
 pr=next(x for x in R[r]['products'] if x['sample_id']=='cadmium-adsorbed');ck(r+'/pre-H2S composition is unresolved',pr['composition']['value'] is None)
 ck(r+'/pre-H2S material identified',any(x['id']=='cadmium-adsorbed-film' and x['formula'] is None for x in R[r]['materials']))
for k,v,u in [('acceleration_voltage',200,'kV'),('point_resolution',.18,'nm')]:p('hrtem','image',k,v=v,u=u)
for i,v in [('filled-scale-bar',30),('empty-scale-bar',30),('enlargement-scale-bar',20),('meso-a',6),('meso-c',6.8)]:z('hrtem',i,v=v,u='nm')
z('hrtem','meso-c-a',v=1.13,u='ratio');ck('HRTEM image power not SAED','not SAED' in m('hrtem','power-definition')['value']['value'])
ck('Correct hexagonal index signs','[11−20]' in m('hrtem','projection')['value']['value'] and '01−11' in m('hrtem','power-labels')['value']['value'])
ck('XRD/HRTEM mesoscopic c discrepancy retained',all('7.2' in str(R[r]['quality']['conflicts']) and '6.8' in str(R[r]['quality']['conflicts']) for r in ('hrtem','xrd')))
for i,v,a in [('first-surface-emission',640,True),('next-surface-emission',640,None),('bound-exciton',450,None)]:z('pl-silicon',i,v=v,u='nm',approx=a)
z('pl-silicon','figure-wavelength-range',lo=300,hi=700,u='nm')
ck('Silicon PL template unresolved','template' in str(R['pl-silicon']['quality']['missing_fields']))
ck('PL source caption/body conflict retained',len(R['pl-silicon']['quality']['conflicts'])>0 and 'upper' in str(R['pl-silicon']['quality']['conflicts']))
ck('PL new Cd state not completed growth cycle','not a completed second' in op('pl-silicon','reimpregnate')['description'])
for i,v,u in [('reference-size',3.5,'nm'),('cds-volume',13,'%'),('pore-volume',15,'%'),('pores-per-cell',2,'count'),('pore-filling',85,'%')]:z('loading-fraction',i,v=v,u=u)
ck('Rounded filling estimate retained',m('loading-fraction','pore-filling')['value']['approximate'] is True)
for i in ('cds-volume','pore-volume','pore-filling'):ck(i+'/author model',m('loading-fraction',i)['value']['status']=='author_derived')
z('chemical-intuition','ph-window',lo=9,hi=10,u='pH');z('chemical-intuition','adsorption-threshold',lo=9,u='pH');z('chemical-intuition','silica-solubility',lo=10,u='pH')
for i in ('adsorption-threshold','silica-solubility'):ck(i+'/strict bound',m('chemical-intuition',i)['value']['minimum_exclusive'] is True)
z('literature-context','historical-nano-scale',hi=10,u='nm');z('literature-context','historical-pore-range',lo=2,hi=30,u='nm')
notes={
'ctab-silica-host':'Input-water pH, 1:5:3.8 molar ratio, 60 °C/1 h aging, CTAB ratio 0.1, unresolved-basis ethanol dilution, 3000 rpm spin coating and 450 °C air calcination checked. About 300 nm thickness, mesoscopic texture, author-derived 3.5 nm spherical-pore estimate and initial 6.9 nm c remain scoped.',
'cadmium-stock':'0.1 M starting cadmium nitrate and separate 1 M citrate stock, one equivalent each ammonia/citrate and further ammonia to pH 9.5 retained. Unknown equivalence reference, hydration, total volume, ammonia concentration, final Cd concentration and solution coordination remain unresolved.',
'ctab-cds-loading':'Five-stage adsorption/rinse/vacuum/H2S/repetition sequence; film retained rather than isolated powder. Symbolic atmospheric H2S endpoint and missing times/flow/quantities preserved. Nine total cycles, 2.2 to 3.6 nm optical size, color sequence and narrow-distribution interpretation checked. Local blende fringes do not become a refined lattice.',
'copolymer-cds-loading':'Unidentified triblock host and missing matrix recipe remain explicit. Shared loading conditions are inherited. 3.3 to 5.8 nm optical endpoints, loss of excitonic features after second impregnation and cited >5 nm weak-confinement rationale checked. Six-cycle plotted endpoint must remain an inference when joined to prose saturation.',
'uv-visible':'Separate CTAB and copolymer series, original curve labels, zero-cycle plotting origins and non-digitized intermediate markers preserved. Plot axes are not instrument acquisition specifications; sizes rely on cited gap-size conversion.',
'xrd':'Cu Kα/X’Pert/Bragg–Brentano acquisition, mesoscopic texture/reflections, c=6.9/6.8/7.2 nm sequence, qualitative half-intensity, display factors 0.5 and 5, contrast evolution and unchanged width reviewed. Cd-adsorbed pre-H2S state no longer mislabelled CdS.',
'hrtem':'200 kV/0.18 nm Topcon microscopy, underfocus assumptions, separate empty/filled cross sections, all three scale bars, local CdS atomic fringes, projection signs and Fourier-power identity checked. Mesoscopic P6₃/mmc/a≈6/c≈6.8/c:a1.13 not promoted to atomic CdS structure; XRD discrepancy and residual empty pores retained.',
'sims':'Two states are explicitly separate: Cd adsorbed before H2S and CdS-saturated film. Homogeneous depth distribution is qualitative; no invented profile, numerical composition, EDS or acquisition settings.',
'pl-silicon':'Silicon substrate separately replaces Pyrex; host template unassigned. First H2S, next Cd impregnation and later cycles remain distinct. 640 and 450 nm bands are emissions, not chosen excitation wavelengths. Proposed vacancy/passivation/quenching mechanisms are interpretations. Body/caption curve-order conflict and room-temperature missingness preserved.',
'loading-fraction':'Separate 3.5 nm CdS comparator, 13% derived CdS volume, 15% derived pore volume, two mesopores/cell and approximate 85% filling reviewed. Cited reverse-micelle recipe is not invented; 3.5 versus 3.6 nm and total-fill versus residual-pore/model distinctions retained.',
'chemical-intuition':'pH window and strict limits, adsorption/complexation/rinsing/H2S transport/silanol regeneration/contrast interpretations and hypothetical sulfide/selenide outlook scoped. No unmeasured surface complexes, rates, additional materials or atomic coordinates inferred.',
'literature-context':'Cited host, unpublished copolymer, gap-size conversion, earlier single-cycle powders, comparator preparation, blende and PL references remain context. Historical <10 nm and 2–30 nm values are not present-sample measurements. Bibliography and figure-only metadata remain fully available in source inventory/reader.'}
rows=[{'record_id':r['record_id'],'sha256':sha(B/'canonical-drafts'/(r['record_id']+'.json')),'manual_source_review':'passed','operations_reviewed':[x['id'] for x in r['operations']],'measurement_rows_reviewed':[x['id'] for x in r['measurements']],'findings':notes[k]} for k,r in R.items()]
fail=[x for x in C if not x['passed']]
out={'status':'passed' if not fail else 'failed','source_id':'besson2002','audited_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':'9f1b5b781e7a36f1ec109eb14ee724bb6c99a8156b4bc6899cfffe8ab613c357','source_inventory_sha256':sha(B/'source-audit.json'),'canonical_manifest_sha256':sha(B/'canonical-record-manifest.json'),'record_hashes':{x['record_id']:x['sha256'] for x in rows},'record_count':len(R),'operation_count':36,'measurement_count':98,'material_slots':sum(len(r['materials']) for r in R.values()),'manual_review_scope':'Independently read and visually inspected all six supplied pages; compared every record, all 36 operation conditions/states and all 98 measurement rows to the source. Programmatic checks below supplement that substantive review. Bibliography, figure-only metadata and historical details remain in the 173-unit source inventory and reader, not automatic training outcomes.','records':rows,'check_count':len(C),'checks':C,'failures':fail,'failure_count':len(fail),'limits':['No matched SI or cited full text reviewed.','No raw-spectrum digitization, new sample identity, unique physical batch or atomic geometry inferred.','Six-cycle copolymer endpoint, optical sizes, filling fraction and mesoscopic structures retain their distinct interpretation scopes.'],'site_mutated':False,'browser_verified':False}
(B/'canonical-records-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'canonical-records-audit.md').write_text('# Besson 2002 canonical source audit\n\n'+out['status']+f": 12 records, 36 operations, 98 measurements; {len(C)} supporting checks and {len(fail)} failures.\n\n"+'\n\n'.join('**'+k+'**: '+v for k,v in notes.items())+'\n\nExact current record hashes are recorded in the JSON report. No Site mutation or browser verification claimed.\n',encoding='utf8')
print(json.dumps({'status':out['status'],'check_count':len(C),'failures':fail},ensure_ascii=False))
