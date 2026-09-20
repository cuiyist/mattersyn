from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
A=Path(__file__).resolve().parent;P=A.parents[1];C=P/'canonical-proposal/v1'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,v):(A/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not(A/'package-freeze.json').exists()
bindings=read(A/'canonical-bindings.json');scenes=read(A/'rendered-scenes.json');pv=read(A/'preview-manifest.json');va=read(A/'author-validation.json');now=datetime.now(timezone.utc).isoformat();checks=[]
def ck(n,ok):checks.append({'check':n,'passed':bool(ok)});assert ok,n
ck('Canonical exact',sha(C/'package-manifest.json')==bindings['canonical_package_sha256']and sha(C/'record-manifest.json')==bindings['record_manifest_sha256'])
ck('Source exact',sha(P/'package-freeze.json')==bindings['source_freeze_sha256'])
for p,h in read(C/'package-manifest.json')['bound_files'].items():ck('Frozen canonical input '+p,sha(p)==h)
for b in bindings['bindings']:
 ck('Record hash '+b['scene_id'],sha(b['record_path'])==b['record_sha256']);r=read(b['record_path']);op=r['operations'][int(b['operation_pointer'].split('/')[2])]
 for k in['inputs','outputs','retained_fraction']:ck(b['scene_id']+' '+k,b[k]==op[k])
 ck(b['scene_id']+' source locator',b['source_evidence']==op['evidence']and bool(b['supplemental_source_evidence']))
 s=next(s for s in scenes if s['kind']==b['scene_id']);ck(b['scene_id']+' allconditions',len([x for x in s['rows']if x['kind']=='operation_parameter'])==len(op['parameters']))
for s in pv['scenes']:
 ck(s['scene_id']+' SVG',sha(A/s['svg_path'])==s['svg_sha256']);ck(s['scene_id']+' PNG',sha(A/s['png_path'])==s['png_sha256'])
for c in pv['contacts']:ck(c['path'],sha(A/c['path'])==c['sha256'])
ck('35distinctscenes/19sourceops',len(scenes)==35 and len({s['kind']for s in scenes})==35 and len({s['operation_id']for s in scenes})==19)
ck('All43parameters/167rows',va['canonical_parameters']==43 and va['total_display_rows']==167)
ck('Authorfactorycheckspass',va['checks']==911 and va['status']=='passed_author_checks_not_independent_approval')
save('author-visual-review.json',{'author':'/root/backlog_eta','recorded_at':now,'status':'passed_author_visual_review_not_independent_approval','actual_scope':'All nine contact sheets were opened and all35 scenes visually inspected. After moving the burette tip directly over the Erlenmeyer opening and removing liquid shading from the dry BET specimen, all three final drip previews and the final BET preview were reopened individually. Source-provenance additions changed no visible text or pixels.','scene_count':35,'contact_count':9,'checks':['Readable labels and conditions without visible clipping.','Burette and Erlenmeyer geometry align with the stated direction of addition.','Three alcohol alternatives remain visibly separate.','Filtration keeps solid and filtrate branches separate; NH4OH is only a10mLfiltrate diagnostic.','Drying24h precedes acetone wash; no extra drying step.','Calcination atmosphere unknown; TGA in air only.','XPS exposure and fitting conflict notes remain analytical contexts.','No original pattern, spectrum, lattice or atomic model is fabricated.'],'bound_previews':{str(A/s['png_path']):s['png_sha256']for s in pv['scenes']},'mounted_browser_test':False,'independent_approval':False})
save('final-author-checks.json',{'author':'/root/backlog_eta','created_at':now,'status':'passed_author_checks','check_count':len(checks),'checks':checks,'factory_checks':va['checks'],'independent_approval':False})
allow=['pati2009-protocol.mjs','quantity-value.mjs']+[s['svg_path']for s in pv['scenes']]
save('public-asset-proposal.json',{'status':'private_candidates_pending_distinct_audit','assets':{n:{'path':str(A/n),'sha256':sha(A/n)}for n in allow},'not_in_site_allowlist':['records.json','private manifests','full source or raw source payloads','author PNG/contact previews'],'publication_approved':False})
bound={str(p):sha(p)for p in sorted(A.rglob('*'))if p.is_file()and'__pycache__'not in p.parts}
for n in['package-freeze.json','source-facts.json','source-inventory.json','source-independent-audit/independent-audit.json','root-preview-reading.md']:
 p=P/n
 if p.exists():bound[str(p)]=sha(p)
for n in['package-manifest.json','record-manifest.json']:
 p=C/n;bound[str(p)]=sha(p)
for b in bindings['bindings']:bound[b['record_path']]=b['record_sha256']
save('package-freeze.json',{'schema':'mattersyn-private-apparatus-package/1','author':'/root/backlog_eta','created_at':now,'source_id':'pati2009','doi':'10.1021/la8031286','status':'frozen_author_proposal_pending_distinct_apparatus_audit','counts':{'record_scopes':14,'operation_instances':35,'distinct_source_operations':19,'art_types':len({x['art']for x in read(A/'scene-config.json')['configs'].values()}),'canonical_parameters':43,'display_rows':167,'svg_previews':35,'png_previews':35,'contact_sheets':9,'bound_files':len(bound)},'source_freeze_sha256':sha(P/'package-freeze.json'),'canonical_package_sha256':sha(C/'package-manifest.json'),'module_sha256':sha(A/'pati2009-protocol.mjs'),'bound_files':bound,'independent_approval':False,'mounted_browser_approval':False,'site_written':False,'published':False})
print(json.dumps({'freeze':str(A/'package-freeze.json'),'sha256':sha(A/'package-freeze.json'),'bound_files':len(bound),'final_checks':len(checks),'module':sha(A/'pati2009-protocol.mjs')}))
