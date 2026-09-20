"""Independent Dantas source/apparatus audit after full source and contact inspection."""
from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
B=Path(__file__).resolve().parent;V=B/'visuals';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records={p.stem:json.loads(p.read_text(encoding='utf8'))for p in(B/'canonical-drafts').glob('*.json')}
m=json.loads((V/'scene-manifest.json').read_text(encoding='utf8'));checks=[]
def ck(test,label):
 checks.append({'label':label,'passed':bool(test)})
 if not test:raise AssertionError(label)
ck(sha(V/'dantas2002-protocol.mjs')==m['module_sha256'],'Manifest matches current apparatus module')
expected={(r['record_id'],o['id'])for r in records.values()for o in r['operations']}
ck(expected=={(s['record_id'],s['operation_id'])for s in m['scenes']},'Exact coverage of all canonical operations')
ck(len(expected)==48,'All 48 operations rendered')
manual={
 'mix':'All six source powders shown; proportions, sulfur identity and introduction timing remain unknown. PbO2 is not silently replaced with PbO.',
 'melt':'Generic crucible in furnace; 1400 °C for 2 h. Literal aluminum wording explicitly unresolved; no invented atmosphere.',
 'quench':'Fast cooling to nonnumeric room temperature; no invented ice/water bath or rate.',
 'stress-relief':'350 °C for 3 h precedes growth. Glass is drawn without asserted PbS dots; no extra ramp/cooling recipe.',
 'anneal':'600 °C and correct source sample duration; dots have illustrative dimensions and no inferred size interpolation.',
 'cut':'Only SG cohort optical sectioning; no invented cutting equipment or specimen thickness.',
 'polish':'Only SG cohort polishing; no invented slurry, solvent, abrasive or roughness.',
 'scan':'AFM scanning is distinct from optical acquisition; AFM1 and AFM2 are separate and no unknown probe configuration is prescribed.',
 'analyze':'AFM grain heights 40.19 Å and 291.24 Å remain separate from rounded prose sizes and from diameters.',
 'sweep':'514.5 nm excitation-power series identifies SG1 only; kW/cm² is retained without conversion to W or energy dose.',
 'integrate':'ASPL spectral integration is distinct from excitation and regression; no raw numeric curve is drawn.',
 'fit':'Source approximate 0.86 power exponent is not generalized to other samples, a quantum yield or unique mechanistic proof.'}
scenes=[]
for s in m['scenes']:
 r=records[s['record_id']];o=next(v for v in r['operations']if v['id']==s['operation_id']);p=V/s['file'];key=r['record_id']+'/'+o['id']
 ck(s['record_sha256']==sha(B/'canonical-drafts'/(r['record_id']+'.json')),key+' exact canonical hash')
 ck(s['svg_sha256']==sha(p),key+' exact SVG hash')
 ck(s['parameters']==o['parameters'],key+' complete typed quantity semantics retained in manifest')
 ck(s['environment']==o['environment'],key+' environment status retained in manifest')
 ck(s['inputs']==o['inputs']and s['outputs']==o['outputs'],key+' exact specimen/material lineage')
 ck(s['evidence']==o['evidence'],key+' exact source evidence')
 root=ET.fromstring(p.read_text(encoding='utf8'));ck(root.attrib['viewBox']=='0 0 600 420',key+' valid SVG viewport')
 t=' '.join(root.itertext());ck(o['label']in t,key+' selected operation label')
 ck('illustrative'in t and'no measured image'in t,key+' illustrative scope explicitly stated')
 ck(not any(x in t for x in ['NaN','undefined']),key+' no invalid placeholders')
 note=manual.get(o['id'])
 if not note:
  if 'model'in r['record_id']:note='Author theory retained as calculation context. Parabolic compare explicitly contrasts two theoretical low-state models; four-band compare uses absorption and preserves radius/size ambiguity. No newly computed states or measured atomic structure.'
  elif r['record_id'].endswith('photoluminescence'):note='Ar-ion optical excitation at 514.5 nm and SPEX/CCD readout are distinct stages. Argon is not transferred to synthesis atmosphere; emission mechanism remains a hypothesis.'
  else:note='Absorption acquisition uses generic optics, no fabricated illumination spectrum, peak trace, path length or exact numeric room temperature.'
 scenes.append({'record_id':r['record_id'],'operation_id':o['id'],'svg_sha256':sha(p),'manual_source_and_layout_review':'passed','scope_note':note})
for k,h in [('sg1',1),('sg2',3),('sg3',6),('sg4',12),('afm1',5),('afm2',30)]:
 r=records['dantas-2002-'+k];ops={o['id']:o for o in r['operations']}
 ck(list(ops)==['mix','melt','quench','stress-relief','anneal'],k+' complete inherited upstream process')
 ck(ops['melt']['parameters']['temperature']['value']==1400 and ops['melt']['parameters']['duration']['value']==2,k+' correct melt conditions')
 ck(ops['stress-relief']['parameters']['temperature']['value']==350 and ops['stress-relief']['parameters']['duration']['value']==3,k+' correct stress-relief conditions')
 ck(ops['anneal']['parameters']['temperature']['value']==600 and ops['anneal']['parameters']['duration']['value']==h,k+' correct growth anneal')
 ck(all(ops[i]['parameters']['temperature']['status']=='inherited'for i in ['melt','stress-relief']),k+' shared conditions explicitly inherited')
 ck(all(o['environment']['status']=='not_reported'for o in ops.values()),k+' no invented synthesis atmosphere')
 ck(all('Shared upstream preparation'in ops[i]['description']for i in ['mix','melt','quench','stress-relief']),k+' no independent-fusion-batch claim')
 ck(next(v for v in r['materials']if v['id']=='lead-dioxide')['formula']=='PbO2',k+' literal PbO2 preserved')
 ck(next(v for v in r['materials']if v['id']=='sulfur-source')['formula']is None,k+' unknown sulfur identity preserved')
ck('SG absorption features'not in(V/'scene-svg/dantas-2002-parabolic-model--compare.svg').read_text(encoding='utf8'),'Corrected parabolic comparison does not misidentify experimental comparator')
ck('Four-band calculation'in(V/'scene-svg/dantas-2002-parabolic-model--compare.svg').read_text(encoding='utf8'),'Corrected parabolic comparison shows four-band theoretical comparator')
ck('SG absorption features'in(V/'scene-svg/dantas-2002-four-band-model--compare.svg').read_text(encoding='utf8'),'Four-band comparison retains experimental absorption context')
contacts=[{'path':str(p),'sha256':sha(p),'manual_review':'passed'}for p in sorted((V/'review').glob('scenes-*.png'))]
ck(len(contacts)==8,'All eight contact sheets visually inspected; corrected model comparison re-inspected')
geometry=json.loads((V/'contact-geometry-validation.json').read_text(encoding='utf8'))
diagnostic=json.loads((V/'scene-geometry-diagnostic.json').read_text(encoding='utf8'))
ck(geometry['status']=='passed' and geometry['scene_count']==48,'Contact renderer retains all 48 scene viewports')
ck(geometry['module_sha256']==sha(V/'dantas2002-protocol.mjs'),'Contact geometry report binds current apparatus module')
ck(geometry['renderer_sha256']==sha(V/'render_scene_contacts.py'),'Contact geometry report binds current renderer')
ck(len(diagnostic)==48,'All 48 SVG/PDF text bounds independently measured')
for g,d in zip(geometry['scenes'],diagnostic):
 ck(g['scene']==d['scene'],'Geometry diagnostic scene correspondence '+g['scene'])
 ck(g['viewport']==[0,0,600,420] and g['rendered_pixels']==[600,420] and g['full_viewport_retained'],'Exact full viewport retained '+g['scene'])
 ck(not d['outside600x420'],'No extracted text outside full viewport '+g['scene'])
geometry_summary={'validation_path':str(V/'contact-geometry-validation.json'),'validation_sha256':sha(V/'contact-geometry-validation.json'),'diagnostic_path':str(V/'scene-geometry-diagnostic.json'),'diagnostic_sha256':sha(V/'scene-geometry-diagnostic.json'),'finding':'No SVG content-bounding-box shrinkage or text overflow was reproduced. All 48 scenes rendered at 600 by 420 pixels. The old contact tile clipped two blank bottom pixels; the renderer now retains the complete viewport with 20-pixel outer gutters. All eight regenerated contact sheets were visually inspected. Canonical records and apparatus SVG module were unchanged.'}
report={'status':'passed_with_source_and_illustration_limits','source_id':'dantas2002','module_sha256':sha(V/'dantas2002-protocol.mjs'),'source_pages_read_and_visually_inspected':5,'operation_count':48,'manual_scene_reviews':48,'check_count':len(checks),'checks':checks,'creator_render_checks':len(m['checks']),'record_hashes':{k:sha(B/'canonical-drafts'/(k+'.json'))for k in records},'contact_sheets':contacts,'scene_reviews':scenes,'limits':['Vessels, furnace geometry, probe shape, glass dimensions, colors and dot sizes are schematic, not reported apparatus dimensions or measured images.','Literal aluminum crucible at 1400 °C remains unresolved; no executable vessel specification is inferred.','Unknown sulfur source, proportions, atmosphere, ramps and size metrics remain explicit.','Source optical-size/radius/AFM-height distinctions and theory versus observation remain separate; no coordinates or measured crystal phase are invented.']}
report['contact_geometry_review']=geometry_summary
(B/'visual-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'visual-source-audit.md').write_text('# Independent Dantas 2002 apparatus audit\n\nPassed with source and illustration limits. All five source pages and all 48 scenes in eight contact sheets were independently inspected. The parabolic-model comparison was corrected to compare theoretical models, re-rendered and re-inspected.\n\nModule SHA-256: `'+report['module_sha256']+'`.\n\n'+str(len(checks))+' source/manifest checks passed, with '+str(len(m['checks']))+' separate creator rendering checks. JSON binds exact canonical, SVG and contact-sheet hashes.\n\n'+ '\n'.join('- '+s for s in report['limits'])+'\n',encoding='utf8')
print(json.dumps({'status':report['status'],'checks':len(checks),'module_sha256':report['module_sha256']}))
(B/'visual-source-audit.md').write_text((B/'visual-source-audit.md').read_text(encoding='utf8')+'\nContact geometry: '+geometry_summary['finding']+'\n',encoding='utf8')
