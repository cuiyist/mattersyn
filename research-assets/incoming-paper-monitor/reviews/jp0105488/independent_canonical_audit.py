from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import json, hashlib
B=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
paths=sorted((B/'canonical-drafts').glob('*.json'))
R={read(p)['record_id'].replace('gerion-2001-',''):read(p) for p in paths}
C=[]
def check(n,ok,detail=''):C.append({'check':n,'passed':bool(ok),'detail':detail})
def op(r,o):return next(x for x in R[r]['operations'] if x['id']==o)
def m(r,i):return next(x for x in R[r]['measurements'] if x['id']==i)
def qty(name,q,v=None,lo=None,hi=None,unit=None,approx=None):
 check(name+'/value-and-bounds',(q.get('value'),q.get('minimum'),q.get('maximum'))==(v,lo,hi))
 if unit is not None:check(name+'/unit',q['unit']==unit)
 if approx is not None:check(name+'/approximation',q['approximate']==approx)
def p(r,o,k,**kw):qty(r+'/'+o+'/'+k,op(r,o)['parameters'][k],**kw)
def z(r,i,**kw):qty(r+'/'+i,m(r,i)['value'],**kw)
check('28-records',len(R)==28)
check('record-types',Counter(r['record_type'] for r in R.values())=={'literature_protocol':2,'procedure':16,'observation':10})
check('82-operations',sum(len(r['operations']) for r in R.values())==82)
check('186-measurements',sum(len(r['measurements']) for r in R.values())==186)
check('128-material-slots',sum(len(r['materials']) for r in R.values())==128)
manifest=read(B/'canonical-record-manifest.json')
for row in manifest['records']:check(row['id']+'/manifest-hash',sha(B/'canonical-drafts'/(row['id']+'.json'))==row['sha256'])
def walk(x,path=''):
 if isinstance(x,dict):
  if 'evidence' in x:
   for e in x['evidence']:check(path+'/source-locator',e.get('source_id')=='gerion2001' and bool(e.get('locator')))
  for k,v in x.items():yield from walk(v,path+'/'+str(k))
 elif isinstance(x,list):
  for i,v in enumerate(x):yield from walk(v,path+'/'+str(i))
 yield None
for name,r in R.items():
 list(walk(r,name));ids={a['sample_id'] for a in r['products']}
 for a in r['measurements']:check(name+'/'+a['id']+'/sample-exists',a['sample_id'] in ids)
 check(name+'/missing-SI-explicit','not located' in json.dumps(r['quality']['missing_fields']) and 'No SI located/matched' in json.dumps(r['sources']))
 check(name+'/no-measured-coordinates',r['structure_assets']==[])
 for a in r['products']:
  check(name+'/'+a['sample_id']+'/phase-unreported',a['phase']['status']=='not_reported')

# Quantitative anchors checked against the independently read main article,
# not copied from creator validation output.
for r in ['silica-silanization','mpa-exchange']:
 p(r,'precipitate','stock_volume',v=1,unit='mL');p(r,'precipitate','stock_optical_density',v=2,approx=True)
s='silica-silanization'
for o,k,v,u in [('mps','mps_volume',50,'uL'),('basify','base_solution_volume',5,'uL'),('dilute','methanol_volume',120,'mL'),('dilute','base_solution_volume',750,'uL'),('dilute','flask_capacity',500,'mL'),('stir1','duration',1,'h'),('heat1','duration',30,'min'),('feed2','methanol_volume',90,'mL'),('feed2','water_volume',10,'mL'),('feed2','phosphonate_stock_volume',600,'uL'),('feed2','mps_volume',20,'uL'),('prepare-quench','methanol_volume',20,'mL'),('prepare-quench','tmscl_volume',2,'mL'),('rest24','duration',24,'h'),('dialyze-methanol','membrane_mwco',10000,'Da'),('dialyze-methanol','duration',1,'day'),('filter045','pore_size',.45,'um'),('centrifugal-concentrate','membrane_mwco',100000,'Da'),('column','buffer_concentration',10,'mM'),('filter022','pore_size',.22,'um'),('optional-filter','pore_size_as_printed',.22,'mm'),('optional-vacufuge','temperature',60,'degC'),('clear','relative_centrifugal_force',20000,'g'),('clear','duration',30,'min')]:p(s,o,k,v=v,unit=u)
for o,k,v,u in [('dilute','pH',10,'pH'),('heat1','temperature',60,'degC'),('heat2','temperature',60,'degC'),('heat3','temperature',60,'degC'),('stir2','duration',2,'h'),('stir3','duration',2,'h'),('heat3','duration',30,'min'),('cool2','temperature',30,'degC'),('prepare-quench','base_mass',3,'g'),('centrifugal-concentrate','final_volume',2,'mL'),('column','buffer_pH',7,'pH'),('column','eluted_volume',3,'mL')]:p(s,o,k,v=v,unit=u,approx=True)
p(s,'heat2','duration_upper_bound',hi=5,unit='min');check('strict-less-than-5min',op(s,'heat2')['parameters']['duration_upper_bound']['maximum_exclusive'] is True)
p(s,'age','duration',lo=2,hi=4,unit='day');p(s,'rotovap','volume_reduction_factor',lo=2,hi=5,unit='fold');p(s,'rest12','duration_lower_bound',lo=12,unit='h');p(s,'optional-dialysis','duration',lo=1,hi=4,unit='day')
check('optional-water-branch-explicit',all(op(s,x)['optional'] for x in ['optional-dialysis','optional-filter','optional-vacufuge']))
check('final-supernatant-retained',op(s,'clear')['retained_fraction']=='final-supernatant' and op(s,'clear')['optional_inputs']==['optional-concentrated'])
z(s,'applicability-size',lo=2,hi=8,unit='nm',approx=True)
check('scope-size-not-final-target',R[s]['intended_target']['size']['status']=='not_reported')
r='mpa-exchange'
for o,k,v,u in [('resuspend','dmf_volume',1,'mL'),('resuspend','mpa_volume',.1,'mL'),('prepare-dmap','dmap_mass_per_unit_stock',20,'mg'),('prepare-dmap','dmf_volume_per_unit_stock',1,'mL'),('collect','relative_centrifugal_force',3000,'g'),('collect','duration',1,'h'),('clear','relative_centrifugal_force',20000,'g'),('clear','duration',30,'min')]:p(r,o,k,v=v,unit=u)
p(r,'sonicate','duration',lo=10,hi=30,unit='min',approx=True);p(r,'age','duration',lo=1,hi=4,unit='day');p(r,'add-dmap','dmap_stock_volume',lo=3,hi=7,unit='mL',approx=True);p(r,'dissolve','water_volume',lo=.1,hi=1,unit='mL')
check('MPA-first-pellet-final-supernatant',op(r,'collect')['retained_fraction']=='mpa-precipitate' and op(r,'clear')['retained_fraction']=='mpa-supernatant')
for r,o,k,v,u in [('optical-acquisition','absorbance','optical_path_length',2,'mm'),('optical-acquisition','qy','matched_optical_density',.15,'dimensionless'),('optical-acquisition','qy','excitation_wavelength',480,'nm'),('optical-acquisition','qy','reference_quantum_yield',95,'%'),('storage-photostability','prepare','sample_volume',1,'mL'),('storage-photostability','prepare','optical_density_at_exciton',.01,'dimensionless'),('storage-photostability','measure','excitation_wavelength',340,'nm'),('storage-photostability','measure','subsequent_measurements_per_time',4,'measurements'),('cw-photostability','prepare','sample_volume',1,'uL'),('cw-photostability','prepare','optical_density',.065,'dimensionless'),('cw-photostability','irradiate','laser_power',.5,'mW'),('cw-photostability','irradiate','spot_size',700,'um'),('cw-photostability','irradiate','observation_duration',4,'h'),('cw-photostability','record','sampling_interval',5,'s'),('eels-acquisition','measure','silicon_edge_energy',110,'eV'),('eels-acquisition','measure','selenium_edge_energy',67,'eV'),('ellman-assay','read','read_wavelength',412,'nm'),('ellman-assay','read','reagent_extinction_coefficient',13600,'M^-1 cm^-1'),('afm-acquisition','rinse','rinse_amount',3,'drops'),('hplc-acquisition','elute','flow_rate',.5,'mL/min'),('hplc-acquisition','elute','detection_wavelength',210,'nm')]:p(r,o,k,v=v,unit=u)
z('cw-photostability','nc-stability',lo=4,unit='h',approx=True);z('cw-photostability','plotted-end',v=4000,unit='s')
check('CW-comparison-not-mixture',R['cw-photostability']['material_states'][0]['kind']=='sample_set')
check('HPLC-fraction-not-chromatogram-input',op('hplc-acquisition','inspect-fractions')['inputs']==['hplc-eluent'])
check('HPLC-context-not-specific-blue-specimen',all(m('hplc-acquisition',i)['sample_id']=='discussion-context' for i in ['small-size-fraction','pore-limit-context','size-limit']))
check('HPLC-gel-context-paired',m('hplc-acquisition','gel-comparison')['sample_id']=='paired-gel')
for color,vals in {'blue':(504,None,None,None),'green':(544,522,18,81),'yellow':(576,560,12,66),'orange':(595,576,9,60),'red':(644,620,5,71)}.items():
 for key,val in zip(['emission','absorption','qy','retention'],vals):
  mid=color+'-'+key
  if color=='blue' and key=='retention':mid='blue-relative-qy'
  z('optical-properties',mid,v=val,unit='nm' if key in ['emission','absorption'] else '%')
  if val is None:check(mid+'/not-determined',m('optical-properties',mid)['value']['status']=='not_reported')
for color,vals in {'green':(2.7,4.2,.5,6,5,1,2),'yellow':(3.1,4.4,.4,9,5,2,4),'red':(4.1,5.6,.4,14,9,4,8),'dark-red':(4.8,6.4,.4,17,12,5,10)}.items():
 for key,val in zip(['core-diameter','core-shell-diameter','core-shell-spread','silica-height','mpa-height','shell-estimate','source-height-increase'],vals):z('size-'+color,key,v=val,unit='nm')
 check(color+'/shell-author-derived',m('size-'+color,'shell-estimate')['value']['status']=='author_derived')
 check(color+'/paired-coating-branches',next(x for x in R['size-'+color]['products'] if x['sample_id']=='silica')['parent_sample_id']=='core-shell' and next(x for x in R['size-'+color]['products'] if x['sample_id']=='mpa')['parent_sample_id']=='core-shell')
check('no-hard-AFM-cutoff','not a verified' in m('afm-acquisition','histogram-filter')['value']['value'])
check('qualitative-long-heating-not-one-hour-threshold',m('synthesis-controls','overheat-duration')['property']=='reference_duration_in_much_longer_than_statement' and m('synthesis-controls','overheat-duration')['value']['minimum'] is None)
check('phosphonate-removal-no-omission-recipe','no fully specified removal procedure or omission-control recipe' in m('synthesis-controls','no-phosphonate-outcome')['value']['value'])
notes={
'core-shell-stock':'Cited upstream preparation remains unavailable. Butanol/TOPO storage, core-mass concentration basis and aging retain their own scope.',
'silica-silanization':'All 30 states/operations compared with Experimental B and Discussion A: reagent doses, separate quench stock, short second heat, workup fractions, optional branch, rest chronology and filter-unit conflicts retained.',
'mpa-exchange':'All 11 operations checked; DMAP stock amount is not a whole-batch fixed dose. First pellet and final supernatant are separately retained. No upstream core/shell recipe invented.',
'aps-functionalization':'Optional APS follows MPS priming and accompanies phosphonate; missing dose and incomplete variant retained.',
'buffer-exchange':'Three alternative exchange methods are not mandatory serial operations. Buffer formulations remain incompletely specified.',
'optical-acquisition':'Absorption/PL/QY apparatus, 2 mm cell, matched 480 nm OD, separate aqueous dye and source-assumed QY retained.',
'storage-photostability':'340 nm dilute-storage assay and four-measurement means remain distinct from CW laser sampling.',
'cw-photostability':'Independent test/dye samples; 1 µL, 488 nm, 0.5 mW, 700 µm spot and ROI/sampling checked. Approximate minimum 4 h claim versus 4000 s displayed extent preserved.',
'tem-acquisition':'Alternative source instruments/voltages/solvents retained; no actual source micrograph invented from the unavailable SI.',
'eels-acquisition':'Qualitative Se-rich center/Si-rich surround is unshown preliminary data; energies not product band gaps.',
'afm-acquisition':'Deposition/rinse/counting protocol and source selection inconsistency preserved; heights not tip-convolved widths.',
'hplc-acquisition':'Two preparation traces, three original fractions, detector areas, shared gel comparison and broader discussion inference remain distinct.',
'hplc-purification':'Partial additional dialysis/NAP cleanup lacks durations, bath composition and repetition count; no invented complete variant.',
'ellman-assay':'Paired DTNB-free control; coefficient and pH/concentration/time retained. Several-hundred surface estimate remains upper/confounded estimate.',
'gel-electrophoresis':'General buffer/gel/voltage/time options retained separately from figure-specific conditions.',
'gel-ph-stability':'Separate silica/MPA lanes and acidic/neutral conditions retain correct sample and buffer scope.',
'gel-salt-stability':'Incubation and salt-free running buffer separated; visible 2 mM lane conflict and distinct long-term high-salt batches preserved.',
'gel-band-narrowing':'Selection/re-run separate aliquots; source pH8.5/8.6 conflict and <=30% selection yield are not reaction-yield labels.',
'optical-properties':'All Table1 cells including unavailable blue values, prose peak conflicts and study-wide spectral summaries compared independently.',
'synthesis-controls':'Incomplete failures/alternatives retained as context. Qualitative much-longer-than-1h statement is not a calibrated threshold.',
'silanization-mechanism':'Author ligand-exchange/hydrolysis/condensation and timing guidance are not measured unique surface structures.',
'surface-interpretation':'Surface estimates, gel limitations, HPLC/AFM ambiguities, aggregation and incomplete shell interpretation remain qualified.',
'upstream-controls':'No-CdSe ZnS and poor-solvent controls preserve unknown precursor identities/amounts and scattering-proxy limits.',
'literature-context':'Cited mechanisms, biological motivation and future work remain contextual rather than primary new recipe data.'}
for x in ['green','yellow','red','dark-red']:notes['size-'+x]='Table2 row and source prose independently checked. Core to core/shell then two coating branches preserved; no physical-batch join to same-named optical Table1 cohort. Shell estimates marked author-derived.'
records=[{'record_id':r['record_id'],'sha256':sha(B/'canonical-drafts'/(r['record_id']+'.json')),'manual_source_review':'passed','operations_reviewed':[x['id'] for x in r['operations']],'measurement_rows_reviewed':[x['id'] for x in r['measurements']],'findings':notes[k]} for k,r in R.items()]
failed=[c for c in C if not c['passed']]
report={'source_id':'gerion2001','status':'passed' if not failed else 'failed','audited_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':read(B/'source-identity.json')['source_sha256'],'source_inventory_sha256':sha(B/'source-audit.json'),'canonical_manifest_sha256':sha(B/'canonical-record-manifest.json'),'record_hashes':{r['record_id']:r['sha256'] for r in records},'record_count':28,'operation_count':82,'measurement_count':186,'material_slots':128,'manual_review_scope':'All supplied 11 main pages previously independently read as text and visually inspected; all 28 canonical records and 82 operations/186 measurement rows substantively source-compared. Changed rows independently rechecked after author correction. Automated checks supplement, not replace, that review.','records':records,'check_count':len(C),'failure_count':len(failed),'checks':C,'failures':failed,'resolved_findings':['CW approximate lower bound preserved separately from acquisition duration','Analytical data and separate comparator sets no longer typed as mixtures','HPLC physical eluent separated from chromatogram data; study-wide and paired-gel scope fixed','AFM claimed cutoff qualified against visible contradictory features','Identity evidence points to actual assay sections','Phosphonate removal not silently expanded into omission control','Source-rounded height increases, blue unavailable relative QY, applicability range and hardware/supplier details added'],'limitations':['Announced HRTEM/AFM SI not located or inspected; completeness applies only to supplied main article.','Source inconsistencies retained, not experimentally resolved.','No measured atomic coordinates, phase refinement, single-core guarantee or new upstream synthesis recipe.','Quality/review promotion, schema integration, training-export selection and browser rendering are parent-owned subsequent steps.'],'site_mutated':False,'browser_verified':False}
(B/'canonical-records-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'canonical-records-audit.md').write_text('# Gerion 2001 canonical source audit\n\n'+report['status']+f': 28 records, 82 operations, 186 measurement rows and 128 material slots. {len(C)} supporting checks; {len(failed)} failures.\n\nComplete supplied-main reading and independent visual coverage are recorded in source-audit.json. Declared SI is still not located or verified.\n\n'+'\n\n'.join('**'+k+'**: '+v for k,v in notes.items())+'\n\nAll reviewed file hashes, resolved corrections and remaining limits are in canonical-records-audit.json. No Site changes or browser verification were performed.\n',encoding='utf8')
print(json.dumps({'status':report['status'],'checks':len(C),'failures':failed},indent=2))
