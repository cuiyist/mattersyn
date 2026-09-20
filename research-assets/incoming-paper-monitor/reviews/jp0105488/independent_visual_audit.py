from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,xml.etree.ElementTree as ET
B=Path(__file__).resolve().parent;V=B/'visuals'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
module=V/'gerion2001-protocol.mjs';manifest=read(V/'scene-manifest.json');creator=read(V/'creator-scene-review.json')
R={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')};C=[]
def check(n,ok,detail=''):C.append({'check':n,'passed':bool(ok),'detail':detail})
check('manifest-module-current',manifest['module_sha256']==sha(module))
check('creator-module-current',creator['module_sha256']==sha(module))
expected={(rid,o['id']) for rid,r in R.items() for o in r['operations']};actual={(s['record_id'],s['operation_id']) for s in manifest['scenes']}
check('all82-canonical-operations',expected==actual and len(actual)==82)
reviewed=[]
for s in manifest['scenes']:
 rid=s['record_id'];oid=s['operation_id'];o=next(o for o in R[rid]['operations'] if o['id']==oid);key=rid+'/'+oid
 p=V/s['file'];raw=p.read_text(encoding='utf8');tree=ET.fromstring(raw);labels=' '.join(t.text or '' for t in tree.iter() if t.tag.rsplit('}',1)[-1]=='text')
 check(key+'/scene-hash',sha(p)==s['svg_sha256']);check(key+'/canonical-hash',sha(B/'canonical-drafts'/(rid+'.json'))==s['record_sha256'])
 check(key+'/selected-parameters',s['parameters']==o['parameters']);check(key+'/selected-environment',s['environment']==o['environment'])
 check(key+'/explanatory-not-measured','explanatory' in raw and 'No measured microscopic structure or signal is simulated' in raw)
 if rid=='gerion-2001-silica-silanization':
  if o['environment'].get('value')!='Nitrogen':check(key+'/no-inherited-nitrogen-label','N₂' not in labels and 'Under nitrogen' not in labels)
  elif oid in ['dilute','stir1','heat1','age']:check(key+'/reported-nitrogen-displayed','N₂' in labels)
 if oid=='clear' and rid in ['gerion-2001-silica-silanization','gerion-2001-mpa-exchange']:check(key+'/retained-supernatant','Retain supernatant' in labels)
 if rid=='gerion-2001-mpa-exchange' and oid=='collect':check(key+'/retained-pellet','Retain pellet' in labels)
 if rid=='gerion-2001-silica-silanization' and oid=='centrifugal-concentrate':check(key+'/retained-upper-concentrate','Retain upper concentrate' in labels)
 if rid=='gerion-2001-mpa-exchange' and oid=='dry':check(key+'/nitrogen-dry-solid','Dry precipitate' in labels and 'N₂' in labels)
 if rid=='gerion-2001-hplc-acquisition' and oid=='inspect-fractions':check(key+'/separate-fractions',all(x in labels for x in ['Void fraction','Fluorescent fraction','Late fraction','separately']))
 if rid=='gerion-2001-ellman-assay' and oid=='prepare':check(key+'/separate-blank','Matched blank' in labels and 'No DTNB' in labels)
 if rid in ['gerion-2001-tem-acquisition','gerion-2001-eels-acquisition'] and oid in ['image','measure']:check(key+'/electron-beam-not-optical-laser','Electron source' in labels)
 if rid=='gerion-2001-buffer-exchange':check(key+'/alternatives','OR dialysis' in labels and 'OR buffer addition' in labels)
 reviewed.append({'record_id':rid,'operation_id':oid,'scene_sha256':sha(p),'source_semantic_review':'passed','canonical_parameters_and_environment_identical':s['parameters']==o['parameters'] and s['environment']==o['environment']})
for c in creator['contact_sheets']:check(c['file']+'/creator-reviewed-current-sheet',c['visually_inspected'] is True and sha(V/c['file'])==c['sha256'])
semantics=['Independently read the complete apparatus-module logic and labels, compared every record/operation mapping with the audited main-source extraction, and parsed all82 generated SVGs. Selected quantities and environments match final canonical records, with no independent numeric parameter reconstruction.','The inherited nitrogen inlet was corrected: only selected operations explicitly reporting nitrogen display N₂; unreported-atmosphere stages no longer silently inherit an inlet. This preserves the source/canonical distinction even though the reaction has overall nitrogen context.','Wet antisolvent precipitation is distinct from MPS priming, methanolic TMAH clarification, secondary silane addition, separately prepared pentahydrate quench, heating/cooling, aging and solvent exchange. No specific oil bath, mantle, pressure, ramp or stirring rate is asserted when unreported.','Workup drawings distinguish dialysis retention, upper membrane concentrate, filtered dispersion, fluorescent column fraction and final retained supernatant. The optional water branch remains optional; the conflicting0.22mm source unit is explicit. MPA first retains a pellet, dries under nitrogen, redissolves and finally retains supernatant.','Optical comparator and Ellman blank remain separate specimens. CW and storage monitoring do not share fabricated spectra, excitation or sampling conditions. TEM/EELS show electron optics and dried supports, AFM mica/probe stages are illustrative, and missing SI micrographs/maps are not recreated.','HPLC load/elute/fraction inspection remain separate physical stages; the three collected fractions are individually inspected. Gel diagrams display separate lanes and no synthetic measured bands; salt incubation remains distinct from salt-free gel running. Upstream stock and optional APS are not upgraded to complete upstream syntheses.','The module is gated to the current DOI/prefix. Molecular/particle insets, fluid colors, vessel geometry and apparatus layouts are explanatory, not measured atomic structure or original experimental imagery. Actual conditions and citations are parent-rendered alongside.']
failed=[x for x in C if not x['passed']]
report={'source_id':'gerion2001','status':'passed' if not failed else 'failed','audited_utc':datetime.now(timezone.utc).isoformat(),'module_sha256':sha(module),'scene_manifest_sha256':sha(V/'scene-manifest.json'),'creator_scene_review_sha256':sha(V/'creator-scene-review.json'),'source_inventory_sha256':sha(B/'source-audit.json'),'record_hashes':{rid:sha(B/'canonical-drafts'/(rid+'.json')) for rid in R},'operation_count':82,'semantic_review':semantics,'resolved_findings':['Default nitrogen inlet replaced by selected-operation atmosphere display.'],'check_count':len(C),'failure_count':len(failed),'checks':C,'failures':failed,'scene_reviews':reviewed,'independent_visual_scope':'All original11 main pages previously visually inspected. Current scope independently reviews source semantics, module logic, labels and scene/canonical linkage. Creator reports actual viewing of all14 final contact sheets; parent has additional selected-sheet/browser QA. This report does not claim independent viewing of all apparatus contact sheets.','creator_visual_coverage':creator['contact_sheets'],'browser_verified':False,'site_mutated':False}
report['independent_selected_contact_sheet']={'path':str(V/'review/scenes-10.png'),'sha256':sha(V/'review/scenes-10.png'),'actually_viewed':True,'scope':'Six affected second-growth/heating/cooling/quench states; corrected absence of inherited nitrogen inlet and readable explanatory labels.'}
(B/'visual-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'visual-source-audit.md').write_text('# Gerion 2001 apparatus source audit\n\n'+report['status']+f': 82 source-linked operation scenes, {len(C)} independent checks, {len(failed)} failures.\n\n'+'\n\n'.join(semantics)+'\n\n'+report['independent_visual_scope']+'\n',encoding='utf8')
print(json.dumps({'status':report['status'],'module_sha256':sha(module),'checks':len(C),'failures':failed},indent=2))
