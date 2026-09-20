"""Root source/visual audit of the independently authored molecular/apparatus proposal."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent;V=B/'visuals';S=B.parents[3]/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(name,ok):checks.append({'check':name,'passed':bool(ok)})
h=read(V/'handoff.json');records={p.stem:read(p)for p in (B/'canonical-drafts').glob('*.json')}
for rid,digest in h['canonical_record_hashes'].items():check('Current draft '+rid,sha(B/'canonical-drafts'/(rid+'.json'))==digest)
sm=read(V/'scene-manifest.json');check('Module matches viewed scenes',sha(V/'peng1998-protocol.mjs')==sm['module_sha256'])
expected={(r['record_id'],o['id'])for r in records.values()for o in r['operations']}
check('All 28 operation scenes',len(expected)==28 and expected=={(x['record_id'],x['operation_id'])for x in sm['scenes']})
for scene in sm['scenes']:
 check('Viewed scene hash '+scene['record_id']+'/'+scene['operation_id'],sha(V/scene['file'])==scene['sha256'])
for n in range(1,6):check('Root visually inspected contact sheet '+str(n),(V/f'review/scenes-{n:02}.png').is_file())
check('Root visually inspected molecular contact sheet',(V/'review/molecular-contact.png').is_file())
for a in read(V/'asset-manifest.json')['files']:check('Molecular asset hash '+a['path'],sha(V/a['path'])==a['sha256'])
entries=read(V/'registry-additions.json')['entries'];registry={e['id']:e for e in read(S/'dist/assets/chemical-registry/registry.json')['entries']}
for entry in read(V/'reused-references.json')['entries']:check('Unchanged reused identity '+entry['id'],entry==registry[entry['id']])
registry.update({e['id']:e for e in entries})
bindings=read(V/'bindings-additions.json')['recordBindings']
for rid,r in records.items():
 check('Complete material bindings '+rid,set(bindings[rid])=={m['id']for m in r['materials']})
 for mid,eid in bindings[rid].items():check('Resolved identity '+rid+'/'+mid,eid in registry)
prod=read(V/'product-reference-proposal.json')['recordBindings']
check('No calibration/model product geometry',not any(k.endswith(('cdse-calibration','inas-calibration','growth-model','pl-size-analysis'))for k in prod))
check('TMS3As formula',registry['tms3as']['formula']=='C9H27AsSi3')
check('TMS3As connectivity only',not registry['tms3as'].get('model3dPath'))
check('InAs phase unknown',all(p['phase']['value'] is None for r in records.values()if r['material']['formula']=='InAs'for p in r['products']))
report={'status':'passed' if all(x['passed']for x in checks)else'failed','reviewer':'mattersyn-primary','at':datetime.now(timezone.utc).isoformat(),'scope':'Root independently compared source-read main/SI and all 28 diagram renders in five contact sheets; inspected molecular contact sheet and source-specific bindings. No browser interaction assertion. All manuscript quantities, thermal phases, refeed elapsed times and aliquot scopes retained. Generic vessel, optical geometry and identity cards labeled illustrative.','check_count':len(checks),'checks':checks,'module_sha256':sm['module_sha256'],'observed_contact_sheets':[f'visuals/review/scenes-{n:02}.png'for n in range(1,6)]+['visuals/review/molecular-contact.png'],'findings':[]}
(B/'visual-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'checks':len(checks),'failures':[x for x in checks if not x['passed']]}))
assert report['status']=='passed'
