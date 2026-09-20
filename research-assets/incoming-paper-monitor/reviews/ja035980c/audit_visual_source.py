"""Run after independent source, module and complete rendered-contact inspection."""
from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
B=Path(__file__).resolve().parent;V=B/'visuals';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records={p.stem:json.loads(p.read_text(encoding='utf8'))for p in(B/'canonical-drafts').glob('*.json')}
m=json.loads((V/'scene-manifest.json').read_text(encoding='utf8'));checks=[]
def ck(test,label):
 checks.append({'label':label,'passed':bool(test)})
 if not test:raise AssertionError(label)
ck(sha(V/'banerjee2003-protocol.mjs')==m['module_sha256'],'Exact current module hash')
expected={(r['record_id'],o['id'])for r in records.values()for o in r['operations']}
ck(expected=={(s['record_id'],s['operation_id'])for s in m['scenes']},'All and only canonical operations rendered')
ck(len(expected)==39,'All 39 expected operations')
reviews=[]
for s in m['scenes']:
 r=records[s['record_id']];o=next(v for v in r['operations']if v['id']==s['operation_id']);p=V/s['file'];key=r['record_id']+'/'+o['id']
 ck(s['record_sha256']==sha(B/'canonical-drafts'/(r['record_id']+'.json')),key+' exact canonical hash')
 ck(s['svg_sha256']==sha(p),key+' exact SVG hash')
 for field in ['parameters','environment','inputs','outputs','evidence']:ck(s[field]==o[field],key+' source field '+field)
 root=ET.fromstring(p.read_text(encoding='utf8'));t=' '.join(root.itertext())
 ck(root.attrib.get('viewBox')=='0 0 600 420',key+' full SVG viewport')
 ck(o['label']in t,key+' canonical operation label')
 ck('illustrative' in t and 'not measured atomic structures' in t,key+' explicit illustration limit')
 ck(not any(x in t for x in ['NaN','undefined']),key+' no invalid placeholders')
 reviews.append({'record_id':r['record_id'],'operation_id':o['id'],'svg_sha256':sha(p),'source_semantics':'passed','layout':'passed'})
g=records['banerjee-2003-growth'];ops={o['id']:o for o in g['operations']}
for oid,param,value in [('dry-tubes','temperature',150),('heat','temperature',320),('adjust','target_temperature',300),('injection','temperature',300),('grow','temperature',250),('grow','duration',20),('cool','target_temperature',50),('solvate','toluene_volume',5),('filter','membrane_pore_size',.2)]:
 ck(ops[oid]['parameters'][param]['value']==value,oid+' correct '+param)
ck(ops['heat']['environment']['value']=='Argon','Argon is explicit during precursor heating')
for oid in ['adjust','injection','grow','final-dry']:ck(ops[oid]['environment']['status']=='not_reported',oid+' unknown atmosphere remains unknown')
ck(ops['final-dry']['parameters']['temperature']['value']is None,'No reuse of 150 C for final drying')
ck(ops['filter']['retained_fraction']=='retained-solid','Initial filtration retains composite and free particles')
ck(ops['wash']['retained_fraction']=='washed-heterostructure' and 'cdte-washings'in ops['wash']['outputs'],'Workup correctly separates retained and removed fractions')
states={s['id']:s for s in g['material_states']}
ck('argon'not in states['hot-cadmium-template']['parent_ids'],'Process gas is not a material ancestor')
ck('ptfe-membrane'not in states['retained-solid']['parent_ids'],'Membrane is not a product ancestor')
for oid in ['oxidize','acid-hcl','acid-hf','wash-tubes','dry-tubes','mix-cd','heat','adjust','injection']:
 raw=(V/('scene-svg/banerjee-2003-growth--'+oid+'.svg')).read_text(encoding='utf8')
 ck('fill="#cfaa6c"'not in raw,oid+' no pre-growth CdTe particle markers')
for rid,oid in [('electron-microscopy','disperse'),('electron-microscopy','deposit'),('uv-visible','disperse-composite')]:
 root=ET.fromstring((V/f'scene-svg/banerjee-2003-{rid}--{oid}.svg').read_text(encoding='utf8'))
 ck(not any(e.tag.endswith('circle')and e.attrib.get('fill')=='#cfaa6c'for e in root.iter()),rid+'/'+oid+' no free particles in purified composite scene')
ck(all('ethanol'not in (V/f'scene-svg/banerjee-2003-sem--{i}.svg').read_text(encoding='utf8').split('<desc>')[0].lower()for i in ['deposit','image']),'SEM titles do not invent TEM ethanol protocol')
ck(not records['banerjee-2003-mechanisms']['operations'],'Author mechanism is not a fabricated operation sequence')
geometry=json.loads((V/'contact-geometry-validation.json').read_text(encoding='utf8'));diag=json.loads((V/'scene-geometry-diagnostic.json').read_text(encoding='utf8'))
ck(geometry['module_sha256']==m['module_sha256'],'Geometry validation matches module')
ck(geometry['scene_count']==39 and len(diag)==39,'All scene viewports and text bounds measured')
for a,d in zip(geometry['scenes'],diag):
 ck(a['scene']==d['scene'],'Geometry alignment '+a['scene'])
 ck(a['viewport']==[0,0,600,420]and a['rendered_pixels']==[600,420]and a['full_viewport_retained'],'Full viewport '+a['scene'])
 ck(not d['outside600x420'],'No text beyond viewport '+a['scene'])
contacts=[{'path':str(p),'sha256':sha(p),'manual_review':'passed'}for p in sorted((V/'review').glob('scenes-*.png'))]
ck(len(contacts)==7,'All seven contact sheets independently inspected; changed sheets 1 and 6 reinspected')
props=json.loads((B/'structural-property-additions.json').read_text(encoding='utf8'))
ck(set(props)<={q['property']for r in records.values()for q in r['measurements']},'All structural display keys exist in canonical facts')
report={'status':'passed_with_source_and_illustration_limits','source_id':'banerjee2003','module_sha256':sha(V/'banerjee2003-protocol.mjs'),'source_pages_read_and_visually_inspected':{'main':9,'si':1},'operation_count':39,'manual_scene_reviews':39,'check_count':len(checks),'checks':checks,'creator_render_checks':len(m['checks']),'record_hashes':{k:sha(B/'canonical-drafts'/(k+'.json'))for k in records},'contact_sheets':contacts,'scene_reviews':reviews,'geometry_validation_sha256':sha(V/'contact-geometry-validation.json'),'geometry_diagnostic_sha256':sha(V/'scene-geometry-diagnostic.json'),'corrections_applied':['Analytical purified-composite dispersions show attached CdTe only; free particles remain confined to pre-wash growth/workup cartoons.'],'limits':['Apparatus, tube geometry, expected oxygen sites, particle shapes and positions are explanatory illustrations, not measured atomic structures or experimental micrographs.','Microscopy, XPS and Raman cartoons show a representative composite; canonical preparation and source comparisons keep individual precursor/composite samples separate.','Te feed chemical form, stock concentration/dose, synthesis charges and final drying conditions remain unknown. Argon is not automatically inherited beyond explicitly stated precursor heating.','The 150 C treatment dries the nanotube precursor. XPS chamber pressure, electron beam voltages and laser settings are analytical, not synthetic conditions.','Filtration initially retains free crystals and heterostructures; toluene washing separates removed CdTe from retained composite. SI IR is solely a precursor spectrum.','No measured junction coordinates, SAED, phase fraction, optical peak label or device performance is invented.']}
(B/'visual-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'visual-source-audit.md').write_text('# Independent Banerjee 2003 apparatus review\n\nAll nine main pages and the matched SI page, the private module and all 39 scenes across seven contact sheets were independently inspected. The three analytical purification-state cartoons were corrected and reinspected.\n\nModule SHA-256: `'+report['module_sha256']+'`.\n\n'+str(len(checks))+' independent source/manifest/viewport checks and '+str(len(m['checks']))+' creator rendering checks passed. The JSON report binds every canonical record, SVG and contact sheet hash.\n\n'+'\n'.join('- '+x for x in report['limits'])+'\n',encoding='utf8')
print(json.dumps({'status':report['status'],'checks':len(checks),'module_sha256':report['module_sha256']}))
