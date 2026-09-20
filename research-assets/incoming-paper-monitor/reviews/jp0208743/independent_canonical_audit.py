from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
R={read(p)['record_id'].removeprefix('dantas-2002-'):read(p) for p in sorted((B/'canonical-drafts').glob('*.json'))};C=[]
def ck(n,v,d=''):C.append({'check':n,'passed':bool(v),'detail':d})
def op(r,i):return next(o for o in R[r]['operations'] if o['id']==i)
def m(r,i):return next(x for x in R[r]['measurements'] if x['id']==i)
def q(n,x,v=None,lo=None,hi=None,u=None,approx=None):
 ck(n+'/value-bounds',(x.get('value'),x.get('minimum'),x.get('maximum'))==(v,lo,hi))
 if u is not None:ck(n+'/unit',x['unit']==u)
 if approx is not None:ck(n+'/approximation',x['approximate']==approx)
def p(r,o,k,**kw):q(r+'/'+o+'/'+k,op(r,o)['parameters'][k],**kw)
def z(r,i,**kw):q(r+'/'+i,m(r,i)['value'],**kw)
ck('16 records',len(R)==16);ck('48 operations',sum(len(r['operations']) for r in R.values())==48);ck('110 measurements',sum(len(r['measurements']) for r in R.values())==110)
ck('Record types',Counter(r['record_type'] for r in R.values())=={'literature_protocol':6,'procedure':8,'observation':2})
def walk(x,where):
 if isinstance(x,dict):
  if 'evidence' in x:
   for e in x['evidence']:ck(where+'/source',e.get('source_id')=='dantas2002' and bool(e.get('locator')))
  for k,v in x.items():walk(v,where+'/'+str(k))
 elif isinstance(x,list):
  for i,v in enumerate(x):walk(v,where+'/'+str(i))
for name,r in R.items():
 walk(r,name); samples={x['sample_id'] for x in r['products']};states={x['id'] for x in r['material_states']};mats={x['id'] for x in r['materials']};ops={x['id'] for x in r['operations']}
 ck(name+'/unknown physical batch',r['lineage']['batch_id'] is None);ck(name+'/source group',r['lineage']['source_group']=='dantas2002');ck(name+'/no atomic coordinates',r['structure_assets']==[])
 ck(name+'/SI missingness','No matching SI supplied' in r['sources'][0]['si_status'])
 for a in r['measurements']:ck(name+'/'+a['id']+'/sample association',a['sample_id'] in samples)
 for a in r['products']:
  if a.get('material_state_id'):ck(name+'/'+a['sample_id']+'/state link',a['material_state_id'] in states)
  ck(name+'/'+a['sample_id']+'/phase unknown',a['phase']['value'] is None)
 for a in r['operations']:
  ck(name+'/'+a['id']+'/inputs',all(i in states|mats for i in a['inputs']));ck(name+'/'+a['id']+'/outputs',all(i in states for i in a['outputs']));ck(name+'/'+a['id']+'/dependencies',all(i in ops for i in a['depends_on']))
for row in read(B/'canonical-record-manifest.json')['records']:ck(row['id']+'/manifest hash',sha(B/'canonical-drafts'/(row['id']+'.json'))==row['sha256'])
routes={'sg1':1,'sg2':3,'sg3':6,'sg4':12,'afm1':5,'afm2':30}
for r in ['glass-host']+list(routes):
 ck(r+'/PbO2 literal',next(x for x in R[r]['materials'] if x['id']=='lead-dioxide')['formula']=='PbO2')
 ck(r+'/sulfur source unknown',next(x for x in R[r]['materials'] if x['id']=='sulfur-source')['formula'] is None)
 ck(r+'/vessel not reagent',next(x for x in R[r]['materials'] if x['id']=='aluminum-crucible')['role']=='vessel')
 ck(r+'/six listed powders',op(r,'mix')['inputs']==['silica','sodium-carbonate','zinc-oxide','alumina','lead-dioxide','boron-oxide'])
 for o,k,v,u in [('melt','temperature',1400,'°C'),('melt','duration',2,'h'),('stress-relief','temperature',350,'°C'),('stress-relief','duration',3,'h')]:
  p(r,o,k,v=v,u=u);ck(r+'/'+o+'/'+k+'/scope',op(r,o)['parameters'][k]['status']==('reported' if r=='glass-host' else 'inherited'))
 for o in R[r]['operations']:ck(r+'/'+o['id']+'/atmosphere unreported',o['environment']['value'] is None)
 p(r,'mix','batch_mass',u='g');p(r,'quench','cooling_rate',u='°C/min');ck(r+'/symbolic room temperature',op(r,'quench')['endpoint']['value']=='Room temperature; numeric value not supplied')
 ck(r+'/aluminum caveat','aluminum crucible' in op(r,'melt')['description'] and 'unresolved' in op(r,'melt')['description'])
 ck(r+'/no phantom sulfur addition','sulfur-source' not in op(r,'mix')['inputs'])
 ck(r+'/vessel not material ancestor',next(s for s in R[r]['material_states'] if s['id']=='fused-matrix')['parent_ids']==['powder-mixture'])
ck('Pregrowth glass no PbS assigned',R['glass-host']['products'][0]['composition']['value'] is None)
for r,h in routes.items():
 p(r,'anneal','temperature',v=600,u='°C');p(r,'anneal','duration',v=h,u='h');p(r,'anneal','heating_rate',u='°C/min');z(r,'growth-duration',v=h,u='h')
 ck(r+'/explicit six-way identity',R[r]['products'][0]['source_sample_label'].startswith(r.upper()))
 ck(r+'/partial tasks',R[r]['quality']['requested_tasks']==['precursor_selection','partial_protocol'])
 ck(r+'/upstream inherited not independent melt',all('not evidence of six independently counted fusion batches' in op(r,o)['description'] for o in ['mix','melt','quench','stress-relief']))
 ck(r+'/no isolated powder',R[r]['products'][0]['composition']['value']=='PbS/glass')
for r,values in [('sg1',[1.391,2.486,2.691,2.894]),('sg2',[1.420,2.200,2.490,2.863])]:
 for i,v in zip(['s','1','2','3'],values):z(r,'absorption-'+i,v=v,u='eV')
for r,v in [('sg1',24),('sg2',27),('sg3',40)]:
 z(r,'optical-size',v=v,u='Å');ck(r+'/optical size is author derived',m(r,'optical-size')['value']['status']=='author_derived');ck(r+'/size metric unresolved','neither diameter nor radius' in m(r,'optical-size')['conditions'])
ck('SG4 no invented size',not any('size' in a['property'] for a in R['sg4']['measurements']))
z('sg1','main-aspl',v=2.978,u='eV',approx=True);z('sg1','near-excitation-line',v=2.476,u='eV',approx=True);z('sg1','power-exponent',v=.86,u='dimensionless',approx=True)
for r,rounded,exact,depth in [('afm1',40,40.19,1.57),('afm2',291,291.24,0)]:
 for i,v,a in [('afm-size',rounded,True),('afm-grain-height',exact,False),('afm-substrate-depth',depth,False)]:z(r,i,v=v,u='Å',approx=a)
 ck(r+'/no SG optical data assigned',not any('absorption' in x['property'] or 'aspl' in x['property'] for x in R[r]['measurements']))
 ck(r+'/height not diameter','not a measured particle diameter' in m(r,'afm-size')['conditions'])
ck('Only SG cut/polished',op('optical-preparation','cut')['inputs']==['sg1-specimen','sg2-specimen','sg3-specimen','sg4-specimen'])
ck('Polished cohorts stay separate',all(s['kind']=='sample_set' for s in R['optical-preparation']['material_states']))
z('optical-absorption','prose-spectral-range',lo=.5,hi=3,u='eV')
ck('Figure1 main/inset and peak ordering','Main panel SG2' in m('optical-absorption','figure1-scope')['value']['value'] and 'SG1(SG2)' in m('optical-absorption','figure1-scope')['value']['value'])
ck('Figure1 inset discrepancy retained','3.5' in m('optical-absorption','figure1-ticks')['value']['value'] and bool(R['optical-absorption']['quality']['conflicts']))
ck('Bulk curve not new sample','not a separately synthesized' in m('optical-absorption','bulk-comparator')['value']['value'])
p('photoluminescence','excite','excitation_wavelength',v=514.5,u='nm');ck('Argon laser not atmosphere','not the synthesis atmosphere' in op('photoluminescence','excite')['description'])
z('photoluminescence','source-aspl-range',lo=2.409,hi=2.978,u='eV');z('photoluminescence','figure7-axis',lo=2.3,hi=2.9,u='eV')
ck('Broad ASPL narrative not reconstructed spectrum','not a tabulated continuous emission bandwidth' in m('photoluminescence','source-aspl-range')['conditions'])
ck('Raman tentative','more likely' in m('photoluminescence','near-line-mechanism')['value']['value'])
for k in ['afm1_scan_width','afm1_scan_height']:p('afm-analysis','scan',k,v=5,u='µm')
for i,hi in [('afm1-hist-range',90),('afm2-hist-range',670)]:z('afm-analysis',i,lo=0,hi=hi,u='Å')
ck('AFM1 and SG3 not same sample','distinct samples and size metrics' in m('afm-analysis','cross-cohort-comparison')['value']['value'])
for k in ['electron_effective_mass_ratio','hole_effective_mass_ratio']:p('parabolic-model','solve',k,v=.25,u='m0')
z('parabolic-model','radius-axis',lo=10,hi=90,u='Å');p('four-band-model','solve','hamiltonian_dimension',v=4,u='matrix dimension');z('four-band-model','radius-axis',lo=10,hi=50,u='Å')
z('four-band-model','strong-regime',hi=80,u='Å');z('four-band-model','weak-size',lo=100,u='Å');ck('Weak threshold strict',m('four-band-model','weak-size')['value']['minimum_exclusive'] is True)
z('four-band-model','comparison-size',v=24,u='Å');z('four-band-model','comparison-energy',v=2.44,u='eV');z('four-band-model','rounded-experimental-energy',v=2.48,u='eV')
ck('2.44 calculation status',m('four-band-model','comparison-energy')['value']['status']=='author_derived')
ck('SpaceI literal',m('four-band-model','space-i')['value']['value']=='Space I: j = l + 1/2, π = (−1)^(l+1).')
ck('SpaceII literal',m('four-band-model','space-ii')['value']['value']=='Space II: j = (l + 1) − 1/2, π = (−1)^l.')
for r in ['parabolic-model','four-band-model']:ck(r+'/calculation is data not physical batch',all(s['kind']=='analysis_data' for s in R[r]['material_states']))
p('power-response','sweep','excitation_wavelength',v=514.5,u='nm');z('power-response','exponent',v=.86,u='dimensionless',approx=True)
ck('Power density kW/cm²','kW/cm²' in m('power-response','power-axis')['value']['value'])
ck('Power SG1 only',[x['id'] for x in R['power-response']['materials']]==['sg1-specimen'])
ck('No unique proof','not unique mechanistic proof' in m('power-response','sublinear-inference')['value']['value'])
for i in ['growth','phonon-model','auger-model','two-step-first','two-step-second','localization','photon-source','saturation','model-support','raman']:ck('Mechanism/'+i+'/author interpretation',m('mechanisms',i)['value']['status']=='author_derived')
for i,v,u in [('bohr-radius',200,'Å'),('bulk-gap',.41,'eV'),('small-dot-gap',5.2,'eV')]:z('literature-context',i,v=v,u=u)
z('literature-context','telecom-wavelength',lo=1,hi=2,u='µm');z('literature-context','telecom-energy',lo=.6,hi=1.3,u='eV')
notes={
'glass-host':'All six listed powder identities and source-assigned functions checked; PbO2 retained literally. Unknown ratios, charges, purity grades, sulfur source/loading/addition stage remain unresolved. 1400 °C/2 h literal aluminum crucible, fast cooling to symbolic room temperature and 350 °C/3 h stress relief are exact. Pregrowth matrix is not assigned measured PbS.',
**{r:f'{r.upper()} is the distinct {h} h, 600 °C growth endpoint. Four common upstream operations are inherited without asserting independent melt batches. No atmosphere, ramp, isolation, complete weighed precursor set or atomic phase is invented. '+('Optical cohort only; paired peaks and model-size annotations retain sample identity and ambiguous metric.' if r.startswith('sg') else 'AFM cohort only; rounded prose sizes and precise grain-height/depth annotations are separate, not diameters or optical measurements.') for r,h in routes.items()},
'optical-preparation':'Cutting and polishing apply only to SG1–SG4; comparison states are sample sets, not mixtures. Thickness, abrasives, cleaning and AFM preparation remain absent.',
'optical-absorption':'All paired SG1(SG2) feature energies, Figure1 main/inset reversal, 0.5–3.0 prose versus 3.5 inset tick, feature assignments, annealing trends and Figure2 bulk E^(1/2) reference reviewed. Broad-band illumination is not invented from the PL laser.',
'photoluminescence':'SPEX-750M and literal Joban-Yvon CCD wording, 514.5 nm Ar-ion excitation, room temperature, four SG spectra, narrative 2.409–2.978 eV versus narrow Figure5 window, dual Figure7 axes and tentative resonant-Raman assignment retained. AFM specimens receive no invented PL.',
'afm-analysis':'Figure4a 5×5 µm² overview, selected enlargement, independent AFM2 view, correlation/depth histograms and 0–90/0–670 Å displayed axes checked. AFM1 5 h and SG3 6 h are only compared, not joined as one sample or one metric.',
'parabolic-model':'Infinite-well single-particle Schrödinger/parabolic-band assumptions and both 0.25 m0 masses are model parameters, not measured values or a DFT input. Figure3a radius axis and labels retained without digitizing curves.',
'four-band-model':'4×4 k·p/envelope formalism, nearly isotropic approximation, original SpaceI/II definitions, angular momentum/parity labels, ≤80 and strict >100 Å statements, 24 Å/2.44 eV calculation and rounded 2.48 versus original 2.486 comparison checked. No complete Hamiltonian or radius/diameter conversion supplied.',
'power-response':'SG1-only 514.5 nm log–log intensity experiment, arbitrary integrated intensity, kW/cm² power density and approximate derived 0.86 exponent verified. No fitted uncertainty, raw power table or per-sample exponent invented.',
'mechanisms':'Diffusion, surface trapping, phonon bottleneck, Auger exclusion argument, sequential two-photon pathway, localization, recycling and state-population explanation remain attributed author interpretations. No defect species, rates, Raman mode or laser proof invented.',
'literature-context':'200 Å Bohr radius, 0.41 and about 5.2 eV gaps, 1–2 µm/0.6–1.3 eV telecom context and cited systems remain prior literature context. Current 21-reference bibliography and all figure-only labels remain fully retained in source inventory/reader, not synthetic outcomes.'}
rows=[{'record_id':r['record_id'],'sha256':sha(B/'canonical-drafts'/(r['record_id']+'.json')),'manual_source_review':'passed','operations_reviewed':[x['id'] for x in r['operations']],'measurement_rows_reviewed':[x['id'] for x in r['measurements']],'findings':notes[k]} for k,r in R.items()]
fail=[x for x in C if not x['passed']]
out={'status':'passed' if not fail else 'failed','source_id':'dantas2002','audited_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':'c8fd35a429bf636fcccc5dfeb3211cea44299e911fbfc80e1a308c75b7b04917','source_inventory_sha256':sha(B/'source-audit.json'),'canonical_manifest_sha256':sha(B/'canonical-record-manifest.json'),'record_hashes':{x['record_id']:x['sha256'] for x in rows},'record_count':16,'operation_count':48,'measurement_count':110,'material_slots':sum(len(r['materials']) for r in R.values()),'manual_review_scope':'All five main pages independently read and visually inspected, with high-resolution original figure labels checked. Every record, all operation conditions/states and all 110 measurement rows independently compared with source. Supporting checks supplement the manual scientific review.','records':rows,'check_count':len(C),'checks':C,'failures':fail,'failure_count':len(fail),'limits':['No matched SI or cited external full texts read.','Shared upstream preparation is not six independently documented melts; physical batch IDs remain unknown.','Optical size, theoretical radius and AFM grain height remain distinct; no refined phase or coordinates.'],'site_mutated':False,'browser_verified':False}
(B/'canonical-records-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'canonical-records-audit.md').write_text('# Dantas 2002 canonical source audit\n\n'+out['status']+f': 16 records, 48 operations, 110 measurements; {len(C)} supporting checks; {len(fail)} failures.\n\n'+'\n\n'.join('**'+k+'**: '+v for k,v in notes.items())+'\n\nExact current hashes are bound in the JSON report. No Site edits or browser verification.\n',encoding='utf8')
print(json.dumps({'status':out['status'],'checks':len(C),'failures':fail},ensure_ascii=False))
