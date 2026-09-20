"""Refresh cutoff partition and public progress only after verified science release."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,sys,re
F=Path(__file__).resolve().parent;MON=F.parents[2];M=F.parents[4];S=M/'recipe-atlas';D=MON/'deadline-20260920'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
release=read(MON/'latest-publication.json');assert release['dataset_version']=='0.33.0'and release['status']=='published_verified'
active=read(D/'active-cutoff.json');out=D/'sasongko-published-scope-20260920.json'
if not out.exists():
 subprocess.run([sys.executable,str(D/'partition_deadline_scope.py'),'--cutoff-manifest',active['cutoff_manifest']['path'],'--ledger',str(MON/'ledger.json'),'--output',str(out)],check=True)
part=read(out);assert part['counts']['included_terminal_scopes']==32
active['counts']=part['counts'];active['latest_scope_partition']={'path':str(out),'sha256':sha(out)};active['recorded_at']=datetime.now(timezone.utc).isoformat();save(D/'active-cutoff.json',active)
ed=read(MON/'public-progress-editorial.json')
assert not ed['current_work']
assert read(MON/'review-control.json')['status']=='paused_for_joint_review'
save(MON/'public-progress-editorial.json',ed)
homepage=S/'dist/index.html';before=homepage.read_text('utf8')
for name in ['build_queue_report.py','build_public_progress.py']:subprocess.run([sys.executable,str(MON/name)],check=True)
after=homepage.read_text('utf8');pattern=r'<!--review-progress-start-->.*?<!--review-progress-end-->'
old=re.findall(pattern,before,re.S);new=re.findall(pattern,after,re.S)
assert len(old)==len(new)==1 and re.sub(pattern,'',before,flags=re.S)==re.sub(pattern,'',after,flags=re.S)
# Update the text while preserving the established homepage placement.
homepage.write_text(before.replace(old[0],new[0]),'utf8')
save(F/'site-integration-proposal/verified-progress-build.json',{'status':'passed','scientific_commit':release['scientific_dataset_commit'],'cutoff_counts':part['counts'],'progress_sha256':sha(S/'dist/data/review-progress.json'),'homepage_placement_preserved':True})
print('Updated verified release progress and fixed-cutoff counts; no new scientific data.')
