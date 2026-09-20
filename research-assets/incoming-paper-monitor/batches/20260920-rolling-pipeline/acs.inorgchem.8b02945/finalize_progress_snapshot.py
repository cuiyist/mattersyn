"""Record the next author freeze without claiming an independent audit."""
from pathlib import Path
from datetime import datetime,timezone
import json,sys,hashlib,subprocess
F=Path(__file__).resolve().parent;MON=F.parents[2];M=F.parents[4];J=F.parent/'acs.jpcc.5c05144'
sys.path.insert(0,str(MON));import monitor
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
assert sha(J/'package-freeze.json')=='c4e1c1cdd065b46e16f1b2fec288a998dec8c5c0fc0867c8e6e902c6242eda08'
monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id='legacy::10.1021_acs.jpcc.5c05144',
 data={'author_source_freeze':str(J/'package-freeze.json'),'author_source_freeze_sha256':sha(J/'package-freeze.json'),'source_audit_passed':False,'source_status':'author extraction frozen; independent audit pending','publication_status':'not published'},
 note='Sasongko main9+SI11 author reading/extraction frozen; independent scientific audit pending.',
 milestones={'read':{'status':'complete','evidence':[str(J/'package-freeze.json')],'note':'Author read all20pages; independent reading/audit pending.'},'extract':{'status':'complete','evidence':[str(J/'package-freeze.json')],'note':'Author extraction complete; not independently approved.'}})
p=MON/'public-progress-editorial.json';ed=read(p);j=ed['current_work'][1]
j['stage']='Complete source extraction; independent audit pending'
j['summary']='The extractor has read all nine main-paper pages and eleven SI pages. The frozen proposal preserves 48 facts, 21 source operations, 121 table cells and 17 selected source crops. Independent reading and scientific audit are still required.'
j['stages'][1]={'label':'Author reading and recipe extraction','status':'complete','detail':'All 20 supplied pages read; source conflicts and gaps retained in an immutable author proposal. This does not imply independent approval.'}
p.write_text(json.dumps(ed,indent=2,ensure_ascii=False)+'\n','utf8')
for s in ['build_queue_report.py','build_public_progress.py']:subprocess.run([sys.executable,str(MON/s)],check=True)
now=datetime.now(timezone.utc).isoformat();p=M/'MEMORY.md'
note=f'''## 2026-09-20 — Parallel source and presentation checkpoints

Saved {now}. Sasongko2025 main9+SI11 author extraction is now frozen at acs.jpcc.5c05144/package-freeze.json SHA c4e1c1cdd065b46e16f1b2fec288a998dec8c5c0fc0867c8e6e902c6242eda08 (76files;48facts,21operations,121tablecells,17crops); independent audit pending. Friedfeld canonical/reader v2 freeze ff8767ef6a51f4184825de335dfe9906fab80e53b97e641fa534f6344f25a112 (125files) is ready for root independent review. Norberg is preparing its apparatus; Peng is preparing symbolic product contexts while Backlog audits root molecular proposal. No further paper claim admitted in this checkpoint.

First molecular finding: original cached N2 used an unsuitable1.460Å bond. Preserve root molecularfreeze7c1a864d...; a pending bounded correction must use the already-qualified Gu/NIST1.09768Å geometry, retaining gas-versus-coolant captions. Generic broad bond-length checks are insufficient. No molecule or InP publication approval claimed. Canonical and source uncertainties remain as recorded. Public queue files now include both current paper statuses; deployment verification still pending. Full sources remain local and paid API pilot deferred.

'''
p.write_text(note+p.read_text('utf8'),'utf8')
print(json.dumps({'source_author_freeze':'Sasongko ready; independent audit pending','Friedfeld_canonical':'v2 ready; independent audit pending','website_progress':'local ready'}))
