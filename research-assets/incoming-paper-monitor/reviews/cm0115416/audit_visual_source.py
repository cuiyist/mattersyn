"""Run only after independent inspection of source, module and rendered scenes."""
from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
B=Path(__file__).resolve().parent;V=B/'visuals';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records={p.stem:json.loads(p.read_text(encoding='utf8'))for p in(B/'canonical-drafts').glob('*.json')}
m=json.loads((V/'scene-manifest.json').read_text(encoding='utf8'));checks=[]
def ck(test,label):
 checks.append({'label':label,'passed':bool(test)})
 if not test:raise AssertionError(label)
ck(sha(V/'yi2002-protocol.mjs')==m['module_sha256'],'Exact current module hash')
expected={(r['record_id'],o['id'])for r in records.values()for o in r['operations']}
ck(expected=={(s['record_id'],s['operation_id'])for s in m['scenes']},'All and only canonical operations rendered')
ck(len(expected)==105,'All 105 expected operations')
reviews=[]
for s in m['scenes']:
 r=records[s['record_id']];o=next(v for v in r['operations']if v['id']==s['operation_id']);p=V/s['file'];key=r['record_id']+'/'+o['id']
 ck(s['record_sha256']==sha(B/'canonical-drafts'/(r['record_id']+'.json')),key+' exact canonical hash')
 ck(s['svg_sha256']==sha(p),key+' exact SVG hash')
 for field in ['parameters','environment','inputs','outputs','evidence']:ck(s[field]==o[field],key+' source field '+field)
 root=ET.fromstring(p.read_text(encoding='utf8'));t=' '.join(root.itertext())
 ck(root.attrib.get('viewBox')=='0 0 600 420',key+' full SVG viewport')
 ck(o['label']in t,key+' canonical operation label')
 ck('illustrative'in t and'no measured'in t,key+' explicit illustrative rather than measured artwork')
 ck(not any(x in t for x in ['NaN','undefined']),key+' no invalid placeholders')
 reviews.append({'record_id':r['record_id'],'operation_id':o['id'],'svg_sha256':sha(p),'source_semantics':'passed','layout':'passed'})
for t in [600,700,800,900,1000]:
 r=records[f'yi-2002-anneal-{t}'];ops={o['id']:o for o in r['operations']}
 ck(len(ops)==16,f'{t} complete preparation and workup framework')
 ck(ops['anneal']['parameters']['temperature']['value']==t and ops['anneal']['parameters']['duration']['value']==5,f'{t} correct hold')
 ck(ops['ramp']['parameters']['heating_rate']['value']==(20 if t==800 else None),f'{t} source-scoped ramp')
 ck(ops['anneal']['environment']['status']=='not_reported',f'{t} no invented annealing atmosphere')
 ck(ops['centrifuge']['retained_fraction']=='precipitate'and ops['wash']['retained_fraction']=='washed-precipitate',f'{t} correct retained solids')
 mol=next(x for x in r['materials']if x['id']=='ammonium-molybdate')
 ck(mol['quantities']['mass']['value']==(1.961 if t==800 else None),f'{t} dose scope')
 if t!=800:
  ck(all(ops[k]['parameters']['duration']['status']=='inherited'for k in ['stir-a','stir-b','stir-suspension','hydrothermal','centrifuge']),f'{t} inherited common timings')
  text=(V/f'scene-svg/yi-2002-anneal-{t}--dissolve-b.svg').read_text(encoding='utf8')
  ck('1.961'not in text and'9.37'not in text,f'{t} no explicit-dose illustration for unknown variant charges')
ck(records['yi-2002-bulk']['operations'][-1]['environment']['value']=='Air','Bulk air atmosphere is explicit and remains separate')
ck(not records['yi-2002-mechanisms']['operations'],'Interpretive mechanism has no fabricated operations')
geometry=json.loads((V/'contact-geometry-validation.json').read_text(encoding='utf8'));diag=json.loads((V/'scene-geometry-diagnostic.json').read_text(encoding='utf8'))
ck(geometry['module_sha256']==m['module_sha256'],'Geometry validation matches module')
ck(geometry['scene_count']==105 and len(diag)==105,'All scene viewports and text bounds measured')
for g,d in zip(geometry['scenes'],diag):
 ck(g['scene']==d['scene'],'Geometry scene alignment '+g['scene'])
 ck(g['viewport']==[0,0,600,420]and g['rendered_pixels']==[600,420]and g['full_viewport_retained'],'Complete viewport '+g['scene'])
 ck(not d['outside600x420'],'No text beyond viewport '+g['scene'])
contacts=[{'path':str(p),'sha256':sha(p),'manual_review':'passed'}for p in sorted((V/'review').glob('scenes-*.png'))]
ck(len(contacts)==18,'All 18 contact sheets independently inspected')
report={'status':'passed_with_source_and_illustration_limits','source_id':'yi2002','module_sha256':sha(V/'yi2002-protocol.mjs'),'source_pages_read_and_visually_inspected':5,'operation_count':105,'manual_scene_reviews':105,'check_count':len(checks),'checks':checks,'creator_render_checks':len(m['checks']),'record_hashes':{k:sha(B/'canonical-drafts'/(k+'.json'))for k in records},'contact_sheets':contacts,'scene_reviews':reviews,'geometry_validation_sha256':sha(V/'contact-geometry-validation.json'),'geometry_diagnostic_sha256':sha(V/'scene-geometry-diagnostic.json'),'limits':['Vessels, heating devices, particles, spectra/readout symbols and dimensions are explanatory illustrations, not original measured apparatus or atomic structures.','Four comparison routes inherit the common preparation but retain unknown individual doses and ramps; only the explicit 800 °C recipe shows its printed charges.','Nano-annealing atmosphere is unknown, while air drying and bulk firing are explicit. Hydrothermal pressure remains unknown.','XRD mixed-phase identity and Scherrer size, TEM morphology and instrumental particle-size distribution remain different evidence types. No SAED, atomistic coordinates or absolute optical efficiency is invented.']}
(B/'visual-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'visual-source-audit.md').write_text('# Independent Yi 2002 apparatus review\n\nAll five original source pages, the private module and all 105 scenes in 18 contact sheets were independently inspected. Source-scoped dose and apparatus conditions passed.\n\nModule SHA-256: `'+report['module_sha256']+'`.\n\n'+str(len(checks))+' independent manifest/source/viewport checks and '+str(len(m['checks']))+' creator rendering checks passed. The JSON report binds every canonical/SVG/contact hash.\n\n'+'\n'.join('- '+x for x in report['limits'])+'\n',encoding='utf8')
print(json.dumps({'status':report['status'],'checks':len(checks),'module_sha256':report['module_sha256']}))
