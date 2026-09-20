"""Read-only package verification plus the root's actual bounded visual/source review."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,subprocess,sys
J=Path(__file__).resolve().parent; A=J/'visuals/apparatus'; O=J/'apparatus-independent-audit'
sys.path.insert(0,str(J.parents[4]/'research-assets'))
from sync_github_public import io_path
read=lambda p:json.loads(io_path(p).read_text('utf8'))
sha=lambda p:hashlib.sha256(io_path(p).read_bytes()).hexdigest()
O.mkdir(exist_ok=True)
assert not (O/'independent-audit.json').exists()
checks=[]
def ck(label,yes):
 checks.append({'check':label,'passed':bool(yes)})
 assert yes,label
f=read(A/'package-freeze.json')
ck('Apparatus author is distinct',f['author']!='/root')
for name,h in f['bound_files'].items():ck('Frozen '+name,sha(A/name)==h)
for name,h in f['external_inputs'].items():ck('External '+name,sha(Path(name))==h)
records={p.stem:read(p) for p in (J/'canonical-proposal/v1/records').glob('*.json')}
def ptr(v,p):
 for k in p.lstrip('/').split('/'):
  k=k.replace('~1','/').replace('~0','~');v=v[int(k)] if isinstance(v,list) else v[k]
 return v
scenes=read(A/'rendered-scenes.json');typed=read(A/'typed-field-map.json')
expected={(r['record_id'],o['id']) for r in records.values() for o in r['operations']}
ck('All 21 operations uniquely mapped',{(s['record_id'],s['operation_id']) for s in scenes}==expected and len(scenes)==21)
for t in typed:
 rid=t['scene_id'].split('--')[0]
 ck('Quantity '+t['scene_id']+t['pointer'],ptr(records[rid],t['pointer'])==t['quantity'])
ck('170 typed quantities',len(typed)==170)
ck('Quantity helper equals current Site',sha(A/'quantity-value.mjs')==sha(J.parents[4]/'recipe-atlas/dist/quantity-value.mjs'))
# Execute the actual frozen module without running any author regeneration or changing its files.
js="""import fs from 'node:fs';import {pathToFileURL} from 'node:url';
const a=process.argv[2],out=process.argv[3];
const m=await import(pathToFileURL(a+'/sasongko2025-protocol.mjs'));
const rs=JSON.parse(fs.readFileSync(a+'/records.json','utf8'));
let count=0;const checks=[];
class E{constructor(t){this.tagName=t;this.style={};this.dataset={};this.children=[];this.innerHTML='';this.textContent='';}append(...x){this.children.push(...x);}querySelector(){return{style:{}};}}
globalThis.document={createElement:t=>new E(t)};
for(const r of rs)for(const o of r.operations){const s=m.buildSasongko2025Scene(o,r),art=m.createSasongko2025Art(o,r),grid=m.createSasongko2025ConditionGrid(o,r);if(!s||art.dataset.scene!==r.record_id+'--'+o.id||grid.children.length!==s.rows.length)throw Error('Selection '+o.id);if(m.buildSasongko2025Scene(o,{...r,lineage:{source_group:'foreign'}})!==null||m.buildSasongko2025Scene({...o,id:'unknown'},r)!==null)throw Error('Scope');if(!s.rows.every(x=>typeof x.value==='string'&&!/undefined|NaN/.test(x.value)))throw Error('Value');checks.push({record:r.record_id,operation:o.id,rows:s.rows.length,passed:true});count++;}
if(count!==21)throw Error('Count');fs.writeFileSync(out,JSON.stringify({status:'passed',scenes:count,checks},null,2));"""
(O/'check-module.mjs').write_text(js,'utf8')
node=Path(r'[local path redacted]')
subprocess.run([str(node),str(O/'check-module.mjs'),str(A),str(O/'executed-module-checks.json')],check=True)
ck('Independent actual module checks',read(O/'executed-module-checks.json')['scenes']==21)
viewed=['source-render/'+x+'.png' for x in ['main-02','main-03','main-04','si-03','si-04','si-05','si-06','si-09']]
viewed+=['visuals/apparatus/contacts/'+x+'.png' for x in [*[f'art-contact-{i}' for i in range(1,5)],*[f'contact-{i}' for i in range(1,7)]]]
review=[
 'Actually read the eight listed original main/SI pages; full-source approval is the separate Backlog audit, not claimed here.',
 'Actually inspected all 21 apparatus illustrations and adjacent condition-layout contact panels. Dense paired rows additionally checked against exact canonical quantity objects.',
 'SI S3: whole FA preparation 0.1042 g salt/0.8 mL OA/3.2 mL ODE, 60 C/30 min/vacuum then135 C/2 h/N2 is distinct from 0.51 mL injection.',
 'SI S3: lead0.075 mmol/ODE2.5 mL; 60 C30 min then135 C30 min; OA alternatives precede0.2 mL OAm; selected25/50/100 C30 min hold precedes injection and prompt cooling.',
 'Main Figures1-3: nine paired contexts retain fixed companion conditions; no Cartesian product, interpolated outcome, replicate count or cross-technique aliquot identity inferred.',
 'First12000 rpm5 min retains precipitate; hexane redispersion then6000 rpm5 min retains supernatant. Absolute washing/hexane volumes, RCF and storage remain unknown.',
 'Optical/XRD/TEM acquisition kept separate from synthesis. 4 ns is instrument response, not laser pulse width. 140/250 K interpretations are not imposed reaction settings.',
 'SI S5/S6 Raman80-190 K displayed and80-200 K prose retained;633 nm and50-300 cm^-1 match source.350 K aging0-210 min30 min increments and separate300 K reference matchS9.',
 'Vessels/heaters/tubes/optical layouts/particle symbols are explicitly explanatory. No invented bath, atomic structure, micrograph, spectrum or pure whole-sample assignment.'
]
audit={'schema':'mattersyn.independent_apparatus_audit/1','at':datetime.now(timezone.utc).isoformat(),'reviewer':'/root','author':f['author'],'status':'passed','open_findings':[], 'inputs':{'apparatus_freeze':{'path':str(A/'package-freeze.json'),'sha256':sha(A/'package-freeze.json')}},'source_audit_sha256':sha(J/'source-independent-audit/independent-audit-v2.json'),'canonical_audit_sha256':sha(J/'canonical-independent-audit/independent-audit-v1.json'),'checks':checks,'check_count':len(checks),'manual_review':review,'actually_viewed':[{'path':p,'sha256':sha(J/p)} for p in viewed],'executed_module_checks_sha256':sha(O/'executed-module-checks.json'),'browser_approval':False,'training_approval':False,'publication_approval':False}
(O/'independent-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'status':'passed','checks':len(checks),'audit_sha256':sha(O/'independent-audit.json')}))
