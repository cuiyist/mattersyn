"""Exact-file checks supporting completed independent source and visual review."""
from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
B=Path(__file__).resolve().parent;V=B/'visuals';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records={p.stem:json.loads(p.read_text(encoding='utf8'))for p in(B/'canonical-drafts').glob('*.json')}
m=json.loads((V/'scene-manifest.json').read_text(encoding='utf8'));checks=[]
def ck(test,label):
 checks.append({'label':label,'passed':bool(test)})
 if not test:raise AssertionError(label)
ck(sha(V/'schwartz2003-protocol.mjs')==m['module_sha256'],'Exact current module hash')
expected={(r['record_id'],o['id'])for r in records.values()for o in r['operations']}
ck(expected=={(s['record_id'],s['operation_id'])for s in m['scenes']},'All and only canonical operations rendered')
ck(len(expected)==95,'All 95 expected operations')
reviews=[];texts={}
for s in m['scenes']:
 r=records[s['record_id']];o=next(v for v in r['operations']if v['id']==s['operation_id']);p=V/s['file'];key=r['record_id']+'/'+o['id']
 ck(s['record_sha256']==sha(B/'canonical-drafts'/(r['record_id']+'.json')),key+' exact canonical hash')
 ck(s['svg_sha256']==sha(p),key+' exact SVG hash')
 for field in ['parameters','environment','inputs','outputs','evidence']:ck(s[field]==o[field],key+' canonical field '+field)
 root=ET.fromstring(p.read_text(encoding='utf8'));t=' '.join(root.itertext());texts[key]=t
 ck(root.attrib.get('viewBox')=='0 0 600 420',key+' full SVG viewport')
 ck(o['label']in t,key+' canonical operation label')
 ck('Apparatus and particles are illustrative'in t,key+' explicit illustration limit')
 ck(not any(x in t for x in ['NaN','undefined']),key+' no invalid placeholders')
 reviews.append({'record_id':r['record_id'],'operation_id':o['id'],'svg_sha256':sha(p),'source_semantics':'passed','layout':'passed'})
def ops(k):return {o['id']:o for o in records['schwartz-2003-'+k]['operations']}
def scene(k,o):return texts['schwartz-2003-'+k+'/'+o]
for k in ['zno-route','co-route','ni-route']:
 o=ops(k)
 for oid,param,value in [('prepare-metal','solution_volume',90),('prepare-metal','total_metal_concentration',.101),('prepare-base','solution_volume',30),('prepare-base','base_concentration',.552),('add-base','addition_rate',2),('add-base','base_equivalents',1.8)]:ck(o[oid]['parameters'][param]['value']==value,k+'/'+oid+' '+param)
 ck(o['add-base']['parameters']['temperature']['value']is None,k+' room temperature not converted to an invented number')
 ck('OR'in scene(k,'precipitate')and 'OR'in scene(k,'redisperse'),k+' alternative solvent rendering')
 ck(not any(x in scene(k,'add-base').lower()for x in ['argon','nitrogen','vacuum','heater']),k+' no unreported synthetic apparatus/atmosphere')
 for i in ['prepare-metal','prepare-base']:
  rt=ET.fromstring((V/f'scene-svg/schwartz-2003-{k}--{i}.svg').read_text(encoding='utf8'))
  ck(not any(e.tag.endswith('circle')for e in rt.iter()),k+'/'+i+' no nanocrystals before base reaction')
for k in ['topo-zno','topo-co','topo-ni']:
 o=ops(k)
 ck(o['heat-topo']['parameters']['temperature']['value']==180,k+' source TOPO temperature')
 ck(o['heat-topo']['parameters']['duration']['minimum']==30 and not o['heat-topo']['parameters']['duration'].get('minimum_exclusive',False),k+' at least 30 min')
 ck(o['cool']['parameters']['target_temperature']['maximum']==80 and o['cool']['parameters']['target_temperature']['maximum_exclusive'],k+' below 80 C strict bound')
 ck(o['repeat-cycle']['parameters']['total_cycles']['value']==2,k+' two total purification cycles')
 ck(o['redisperse']['parameters']['additional_topo_mass']['value']==1,k+' separate additional 1 mg TOPO')
 ck(o['heat-topo']['environment']['status']=='not_reported'and 'Atmosphere unreported'in scene(k,'heat-topo'),k+' unknown atmosphere not replaced')
 ck('Agent not separately named'in scene(k,'precipitate'),k+' final precipitation agent remains unresolved')
 ck('loss of size uniformity'in scene(k,'remove-excess'),k+' amine precaution scientific direction')
ck('pure ZnO'in scene('topo-zno','heat-topo')and 'related doped examples'in scene('topo-zno','heat-topo'),'Pure ZnO surface treatment does not claim dopant removal')
ck('0.66 equivalents'in scene('dopant-series','add-base')and '30 µL'not in scene('dopant-series','add-base'),'Series uses its own 0.66 equivalents without borrowing kinetic aliquot')
ck('0.6 / 0.66 equiv conflict'in scene('pure-kinetics','add-base'),'Printed kinetic discrepancy explicitly preserved')
ck('200 kV'in scene('microscopy','image')and 'SEM voltage unreported'in scene('microscopy','image'),'TEM beam voltage not assigned to aggregate SEM')
ck('Figures 2c, 5c and S3'in scene('microscopy','diffraction'),'Actual separate source diffraction panels identified')
ck('3.8 ± 0.6 nm pure ZnO'in scene('microscopy','histogram')and '2.9 ± 0.3 nm Co:ZnO'in scene('microscopy','histogram'),'Distinct TEM populations preserved')
ck('Zero-field reference'in scene('zeeman','extract')and 'separate mean-field analysis'in scene('zeeman','extract'),'Measured Zeeman shift distinct from model fit')
ck('Room temperature'in scene('aggregation','evaporate')and 'No post-aggregation anneal'in scene('aggregation','evaporate'),'Ambient aggregation not represented as thermal synthesis')
ck('quantum yield'in scene('luminescence','measure'),'PL quenching is not an absolute QY label')
ck('different definitions'in scene('mcd','normalize'),'C0/D0 and B0/D0 remain distinct normalization quantities')
geometry=json.loads((V/'contact-geometry-validation.json').read_text(encoding='utf8'));diag=json.loads((V/'scene-geometry-diagnostic.json').read_text(encoding='utf8'))
ck(geometry['module_sha256']==m['module_sha256'],'Geometry validation matches module')
ck(geometry['scene_count']==95 and len(diag)==95,'All scene viewports and text bounds measured')
for a,d in zip(geometry['scenes'],diag):
 ck(a['scene']==d['scene'],'Geometry alignment '+a['scene'])
 ck(a['viewport']==[0,0,600,420]and a['rendered_pixels']==[600,420]and a['full_viewport_retained'],'Full viewport '+a['scene'])
 ck(not d['outside600x420'],'No text beyond viewport '+a['scene'])
contacts=[{'path':str(p),'sha256':sha(p),'manual_review':'passed'}for p in sorted((V/'review').glob('scenes-*.png'))]
ck(len(contacts)==16,'All 16 contact sheets independently inspected; corrected scenes and representative dot-geometry changes reinspected')
props=json.loads((B/'structural-property-additions.json').read_text(encoding='utf8'))
ck(set(props)<={q['property']for r in records.values()for q in r['measurements']},'All structural display keys exist in canonical facts')
aud=json.loads((B/'canonical-records-audit.json').read_text(encoding='utf8'))
ck(aud['record_hashes']=={k:sha(B/'canonical-drafts'/(k+'.json'))for k in records},'All final canonical hashes match independent source audit')
report={'status':'passed_with_source_and_illustration_limits','source_id':'schwartz2003','module_sha256':sha(V/'schwartz2003-protocol.mjs'),'source_pages_read_and_visually_inspected':{'main':14,'si':4},'operation_count':95,'manual_scene_reviews':95,'check_count':len(checks),'checks':checks,'creator_render_checks':len(m['checks']),'record_hashes':{k:sha(B/'canonical-drafts'/(k+'.json'))for k in records},'contact_sheets':contacts,'scene_reviews':reviews,'geometry_validation_sha256':sha(V/'contact-geometry-validation.json'),'geometry_diagnostic_sha256':sha(V/'scene-geometry-diagnostic.json'),'corrections_applied':['Dopant-series base addition displays its own 0.66-equivalent condition without borrowing a 30 microliter kinetic dose.','TEM and aggregate SEM apparatus and voltage scope distinguished.','Zeeman measured relative shift distinguished from mean-field analysis.','TOPO precursor-removal precaution says loss of size uniformity; pure ZnO scene scopes dopant removal only to related doped examples.','Electron-diffraction placeholder contrast improved; original source patterns remain separately linked.','Human-readable numerical spacing improved and all dispersed cartoon particles positioned within liquid.'],'limits':['Vessel geometry, particle size, position and color are explanatory; no measured atomic coordinates or refined dopant occupancies are created.','Co/Ni doped-system reference structures use an undoped ZnO host only. Apparatus review does not validate a new crystal-coordinate artifact.','Typical preparative quantities and small-volume kinetic/titration values remain separate; numerical room temperature, several workup quantities and atmospheres are unknown.','TOPO is a technical reagent with unquantified phosphonic-acid impurities. The pure TOPO component is a named structural reference, not a pure-stock claim.','Each TEM/SAED, optical, SI control and magnetic aggregate population retains its own specimen scope. Measurement fields and cryogenic temperatures are not synthesis conditions.','Author-derived exchange constants, domain counts, carrier mechanisms and ferromagnetism interpretation are not exact structural or validated success labels.','This is a private source/scene/geometry audit; final browser behavior and publication are separate parent checks.']}
(B/'visual-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'visual-source-audit.md').write_text('# Independent Schwartz 2003 apparatus review\n\nAll 14 main pages and four matched SI pages, the complete private module and all 95 scenes across 16 contact sheets were inspected. The source-specific corrections and representative final liquid geometry were reinspected.\n\nModule SHA-256: `'+report['module_sha256']+'`.\n\n'+str(len(checks))+' independent source/manifest/viewport checks and '+str(len(m['checks']))+' creator rendering checks passed. Exact canonical, SVG and contact-sheet hashes are bound in the JSON report.\n\n'+'\n'.join('- '+x for x in report['limits'])+'\n',encoding='utf8')
print(json.dumps({'status':report['status'],'checks':len(checks),'module_sha256':report['module_sha256']}))
