"""Exact-file checks accompanying the independent source and 47-scene review."""
from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
B=Path(__file__).resolve().parent;V=B/'visuals';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records={p.stem:json.loads(p.read_text(encoding='utf8'))for p in(B/'canonical-drafts').glob('*.json')};m=json.loads((V/'scene-manifest.json').read_text(encoding='utf8'));checks=[];texts={};reviews=[]
def ck(test,label):
 checks.append({'label':label,'passed':bool(test)})
 if not test:raise AssertionError(label)
ck(sha(V/'sashchiuk2004-protocol.mjs')==m['module_sha256'],'Exact current module hash')
expected={(r['record_id'],o['id'])for r in records.values()for o in r['operations']}
ck(expected=={(s['record_id'],s['operation_id'])for s in m['scenes']},'All and only canonical operations rendered')
ck(len(expected)==47,'All 47 expected operations')
for s in m['scenes']:
 r=records[s['record_id']];o=next(v for v in r['operations']if v['id']==s['operation_id']);p=V/s['file'];key=r['record_id']+'/'+o['id']
 ck(s['record_sha256']==sha(B/'canonical-drafts'/(r['record_id']+'.json')),key+' exact canonical hash')
 ck(s['svg_sha256']==sha(p),key+' exact SVG hash')
 for f in ['parameters','environment','inputs','outputs','evidence']:ck(s[f]==o[f],key+' canonical field '+f)
 rt=ET.fromstring(p.read_text(encoding='utf8'));t=' '.join(rt.itertext());texts[key]=t
 ck(rt.attrib.get('viewBox')=='0 0 600 450',key+' complete viewport')
 ck(o['label']in t,key+' canonical operation label')
 ck('Apparatus geometry is explanatory'in t,key+' illustration identity')
 ck(not any(x in t for x in ['NaN','undefined']),key+' finite placeholders')
 reviews.append({'record_id':r['record_id'],'operation_id':o['id'],'svg_sha256':sha(p),'source_semantics':'passed','layout':'passed'})
def ops(k):return {o['id']:o for o in records['sashchiuk-2004-'+k]['operations']}
def scene(k,o):return texts['sashchiuk-2004-'+k+'/'+o]
def xml(k,o):return ET.fromstring((V/f'scene-svg/sashchiuk-2004-{k}--{o}.svg').read_text(encoding='utf8'))
for k,ratio in [('individual-low',[.25,.6,50]),('sphere-intermediate',[.5,1.2,50]),('wire-intermediate',[.5,1.2,50]),('wire-high',[1,2.5,50])]:
 o=ops(k)
 for key,v in zip(['selenium_mass_part','lead_precursor_mass_part','tbp_mass_part'],ratio):ck(o['prepare-stock']['parameters'][key]['value']==v,k+' correct '+key)
 ck(o['prepare-stock']['parameters']['temperature']['status']=='not_reported',k+' numerical glovebox stock temperature unknown')
 ck(o['heat-topo']['parameters']['temperature']['value']==150 and o['heat-topo']['parameters']['topo_mass']['value']==6,k+' source mother solution quantities')
 ck(o['heat-topo']['environment']['value']=='Argon flow',k+' argon explicit at mother heating')
 ck(o['injection']['parameters']['post_injection_temperature']['value']==118,k+' injection thermal drop')
 ck(o['injection']['parameters']['stock_injection_volume']['status']=='not_reported',k+' injected amount unresolved')
 ck(not any(e.tag.endswith('rect')and e.attrib.get('fill')=='#cfaa6c'for e in xml(k,'heat-topo').iter()),k+' no PbSe nanocrystals in pre-injection TOPO')
 for oid in ['injection','grow']:
  ck(o[oid]['environment']['status']=='not_reported',k+'/'+oid+' atmosphere not invented')
  ck('Ar flow'not in scene(k,oid),k+'/'+oid+' no implied continuous argon label')
 ck('Mass ratio'in scene(k,'prepare-stock'),k+' mass proportions labeled')
ck(ops('individual-low')['grow']['parameters']['duration']['value']==15,'Low route duration is15min')
ck(ops('individual-low')['cool']['parameters']['target_temperature']['value']==70,'Low route cooling endpoint70C')
ck('separate approximately 5 min aliquot'in scene('individual-low','grow'),'Figure1A distinct from15min endpoint')
ck(ops('sphere-intermediate')['grow']['parameters']['duration']['minimum']==10 and ops('sphere-intermediate')['grow']['parameters']['duration']['maximum']==60,'Sphere regime retained as10–60min interval')
ck(ops('wire-intermediate')['grow']['parameters']['duration']['value']==90,'Intermediate-wire90min source route')
ck(ops('wire-high')['grow']['parameters']['duration']['value']==40 and 'not shown'in scene('wire-high','grow'),'High-wire40min remains unshown source route')
ck((V/'scene-svg/sashchiuk-2004-sphere-intermediate--grow.svg').read_bytes()!=(V/'scene-svg/sashchiuk-2004-wire-high--grow.svg').read_bytes(),'Assembly morphologies have distinct illustrative scenes')
ck(ops('aliquot-workup')['quench']['parameters']['methanol_volume']['value']==1,'Methanol1mL applies to removed aliquot')
ck('full-batch isolation protocol'in scene('aliquot-workup','withdraw'),'Aliquot workup not claimed as whole-batch workup')
ck(ops('aliquot-workup')['centrifuge']['retained_fraction']=='isolated-product','Centrifuge retains source product')
ck(ops('aliquot-workup')['repeat']['parameters']['cycle_count']['value']is None,'Several cycles not converted to a fabricated number')
ck('butanol isomer'in scene('aliquot-workup','redisperse').lower(),'Butanol isomer unresolved')
for oid,v in [('tem',200),('hrtem',300),('saed',200),('edax',200)]:ck(ops('microscopy')[oid]['parameters']['accelerating_voltage']['value']==v,'Source '+oid+' beam voltage')
ck('4 kV in Methods'in scene('microscopy','sem')and '10.0 kV label'in scene('microscopy','sem'),'SEM method/image voltage discrepancy preserved')
ck('wire assembly'in scene('microscopy','microdiffraction')and 'not shown'in scene('microscopy','microdiffraction'),'Unshown microdiffraction has correct wire scope')
ck('Figure 1E / Figure 2C'in scene('microscopy','saed'),'Original two source SAED patterns identified')
ck('0.5:1:50 conflicts with body 0.5:1.2:50'in scene('absorption','prepare'),'Optical caption/body ratio conflict explicit')
ck(ops('device-fabrication')['anneal']['parameters']['temperature']['value']is None,'Device annealing temperature unknown')
ck('chlorotrimethylsilane'in scene('device-fabrication','hydrophobize'),'Source trimethylsilane identity not silently replaced')
ck('ρ = 0.15'in scene('electrical','normalize')and 'σ ≈ 7'in scene('electrical','normalize'),'Reported resistivity and approximate conductivity distinguished')
ck('future work'in scene('electrical','measure'),'Gate/temperature studies not claimed as existing data')
g=json.loads((V/'contact-geometry-validation.json').read_text(encoding='utf8'));d=json.loads((V/'scene-geometry-diagnostic.json').read_text(encoding='utf8'))
ck(g['module_sha256']==m['module_sha256'],'Geometry bound to current module')
ck(g['scene_count']==47 and len(d)==47,'All47 geometry checks present')
for a,b in zip(g['scenes'],d):
 ck(a['scene']==b['scene'],'Geometry scene alignment '+a['scene'])
 ck(a['viewport']==[0,0,600,450]and a['rendered_pixels']==[600,450]and a['full_viewport_retained'],'Full viewport '+a['scene'])
 ck(not b['outside600x450'],'No clipped text '+a['scene'])
contacts=[{'path':str(p),'sha256':sha(p),'manual_review':'passed'}for p in sorted((V/'review').glob('scenes-*.png'))]
ck(len(contacts)==8,'All eight contact sheets independently visually inspected')
props=json.loads((B/'structural-property-additions.json').read_text(encoding='utf8'));ck(set(props)<={q['property']for r in records.values()for q in r['measurements']},'All28 structural property keys exist')
aud=json.loads((B/'canonical-records-audit.json').read_text(encoding='utf8'));hashes={k:sha(B/'canonical-drafts'/(k+'.json'))for k in records};ck(aud['record_hashes']==hashes,'Canonical hashes match independent source audit')
report={'status':'passed_with_source_and_illustration_limits','source_id':'sashchiuk2004','module_sha256':m['module_sha256'],'source_pages_read_and_visually_inspected':{'main':7,'si':0},'operation_count':47,'manual_scene_reviews':47,'check_count':len(checks),'checks':checks,'creator_render_checks':len(m['checks']),'record_hashes':hashes,'contact_sheets':contacts,'scene_reviews':reviews,'geometry_validation_sha256':sha(V/'contact-geometry-validation.json'),'geometry_diagnostic_sha256':sha(V/'scene-geometry-diagnostic.json'),'corrections_applied':['Removed nanocrystal markers from TOPO before precursor injection.','Distinguished individual crystals, spherical clusters and ordered-wire motifs during growth.','SEM now uses a generic support, without transferring TEM grid preparation.','Unshown microdiffraction refers to the wire assembly, not individually measured constituent particles.','Resistivity displayed as reported0.15; conductivity retains approximation.'],'limits':['All apparatus, particle positions/counts, cluster outlines and device layer dimensions are explanatory, not measured geometry.','Source caption/body precursor ratios remain unresolved. Images are not automatically assigned to the four Methods/body route endpoints.','The low-temperature branch endpoint15min differs from Figure1A~5min. Wires at high stock40min are explicitly not shown.','Removed aliquot workup uses1mL methanol; full mother-batch workup is unestablished.','Unknown stock amount, Pb-cHxBu molecular identity, later atmosphere, heating rates, butanol isomer and device-processing settings remain missing.','Original SAED and micrographs remain separate from cartoons and structure models. This apparatus audit does not certify a measured CIF.','Transport/polarization formulas and energy estimates are source model content, not direct measurements or validated success labels.','Private source/scene inspection and geometry checks do not replace final browser and publication verification.']}
(B/'visual-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'visual-source-audit.md').write_text('# Independent Sashchiuk 2004 apparatus review\n\nAll seven original main pages, the full apparatus module and all47 scenes across eight contact sheets were independently inspected. The final corrected scenes were rechecked.\n\nModule SHA-256: `'+m['module_sha256']+'`.\n\n'+str(len(checks))+' supporting checks passed, in addition to188 creator rendering checks. Canonical, SVG and contact-sheet hashes are bound in the JSON report.\n\n'+'\n'.join('- '+x for x in report['limits'])+'\n',encoding='utf8')
print(json.dumps({'status':report['status'],'checks':len(checks),'module_sha256':m['module_sha256']}))
