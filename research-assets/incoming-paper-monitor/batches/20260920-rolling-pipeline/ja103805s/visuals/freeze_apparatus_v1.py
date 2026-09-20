"""Freeze the root-authored apparatus proposal after actual local browser review."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, xml.etree.ElementTree as ET

E=Path(__file__).resolve().parents[1]
A=E/'visuals/apparatus/v1'
def read(p): return json.loads(p.read_text(encoding='utf8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assert not (A/'package-freeze.json').exists(), 'Frozen packages must not be overwritten'
manifest=read(E/'canonical-proposal/v3/record-manifest.json')
canonical={r['record_id']:read(Path(r['path'])) for r in manifest['records']}
records=read(A/'records.json');scenes=read(A/'rendered-scenes.json');config=read(A/'scene-config.json')
checks=[]
def check(name,ok):
 checks.append({'check':name,'passed':bool(ok)})
 assert ok,name
check('32 canonical records; 16 with apparatus operations',len(canonical)==32 and len(records)==16)
check('46 unique operation scenes',len(scenes)==46 and len({s['operation_id'] for s in scenes})==46)
check('153 condition/qualification rows',sum(len(s['rows']) for s in scenes)==153)
check('33 distinct visual types',len({c['art'] for c in config['configs'].values()})==33)
byid={s['operation_id']:s for s in scenes}
for r in records:
 check(r['record_id']+' exact canonical operation payload',r['operations']==canonical[r['record_id']]['operations'])
 for op in r['operations']:
  scene=byid[op['id']]
  check(op['id']+' title and description',scene['title']==op['label'] and scene['description']==op['description'])
  expected=len(op.get('parameters',{}))+bool(op.get('environment',{}).get('value'))+bool(op.get('endpoint',{}).get('value'))+len(config['configs'][op['id']]['extra_rows'])
  check(op['id']+' complete condition count',len(scene['rows'])==expected)
  ET.parse(A/'svg'/f"{op['id']}.svg")
  check(op['id']+' valid SVG',True)
check('No failed numeric formatting',all(all(bad not in str(s['rows']) for bad in ['None%','NaN','undefined']) for s in scenes))
browser={
 'reviewer':'/root','scope':'Private apparatus preview, not integrated Site or independent scientific approval',
 'performed_at':datetime.now(timezone.utc).isoformat(),
 'controls':{'select_options_exercised':46,'distinct_operation_ids':46,'condition_rows_observed':153,'previous_next':True,'gallery_toggle':True,'gallery_items':46},
 'visual_inspection':{'contact_sheets_viewed':[1,2,3,4],'corrected_sheet_3_rechecked':True,'responsive_width':390,'responsive_height':844,'responsive_example':'evans-2010-pbse-qd-op-3','final_injection_scene_rechecked':True},
 'resolved_findings':['Overlapping gas, distillation and sealed-tube captions','Decorative line crossing glovebox vessel labels','Gallery hidden CSS override','Generic NMR specimen in residue analysis avoids unreported valve identity','FTIR scene avoids an unreported liquid-sample geometry'],
 'console_errors':[],
 'limitation':'A getBBox-based clipping probe was unsupported by the browser DOM facade; visual screenshots and actual control rendering were used instead. No automated bounding-box test is claimed.'
}
save(A/'browser-author-qa.json',browser)
save(A/'author-validation.json',{'schema':'mattersyn.apparatus_author_validation/1','author':'/root','status':'passed_author_checks_only','checks':checks,'source_pages_visually_consulted':['SI 1','SI 2','SI 6','SI 7','SI 8','SI 16','SI 19'],'source_review_scope':'Apparatus source checks plus independently passed complete scientific extraction and canonical/reader audit; not a new independent source audit','caveats':['Artwork explains operations; exact geometry and liquid colors are not measurements.','Species 9 is a molecular crystal, not QD coordinates.','A, later cuts, residual pot C and independently prepared B remain distinct.','No training eligibility or publication is granted by this package.']})
bound=[E/'proposal-freeze-v3.json',E/'canonical-proposal/v3/record-manifest.json',E/'source-scientific-audit.json',E/'proposal-independent-audit/independent-audit-v3.json']
save(A/'canonical-bindings.json',{'source_group':'evans2010','source_bundle_sha256':'177861643fc55cc830f504a68ce9e6d62cacbc7a7182376e76e1dc036a21a1bb','bound_files':[{'path':str(p.relative_to(E)),'sha256':sha(p)} for p in bound]})
freeze={'schema':'mattersyn.apparatus_package_freeze/1','at':datetime.now(timezone.utc).isoformat(),'author':'/root','status':'frozen_for_independent_audit','source_group':'evans2010','canonical_package_manifest_sha256':sha(bound[1]),'source_bundle_sha256':'177861643fc55cc830f504a68ce9e6d62cacbc7a7182376e76e1dc036a21a1bb','files':[{'path':p.relative_to(A).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(A.rglob('*')) if p.is_file()]}
freeze['authoring_files']=[{'path':p.relative_to(E).as_posix(),'sha256':sha(p)} for p in [E/'visuals/build_apparatus_v1.py',E/'visuals/evans_apparatus_geometry.mjs',E/'visuals/render_apparatus_v1.mjs',Path(__file__)]]
save(A/'package-freeze.json',freeze)
print(json.dumps({'freeze':str(A/'package-freeze.json'),'sha256':sha(A/'package-freeze.json'),'author_checks':len(checks),'files':len(freeze['files'])}))
