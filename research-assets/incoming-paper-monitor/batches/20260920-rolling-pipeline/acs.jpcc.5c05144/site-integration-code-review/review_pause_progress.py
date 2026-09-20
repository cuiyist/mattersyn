from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,json,re,subprocess
O=Path(__file__).resolve().parent;J=O.parent;M=J.parents[4];MON=J.parents[2];S=M/'recipe-atlas';BASE=M.parent/'mattersyn-github-project'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text('utf8'))
checks=[];bound={};deltas=[]
def ck(n,b):checks.append({'check':n,'passed':bool(b)});assert b,n
pairs=[(MON/'build_public_progress.py',BASE/'research-assets/incoming-paper-monitor/build_public_progress.py'),(S/'dist/progress.mjs',BASE/'recipe-atlas/dist/progress.mjs'),(J/'build_verified_progress.py',BASE/J.relative_to(M)/'build_verified_progress.py')]
for current,old in pairs:
 ck('prior snapshot exists '+old.name,old.is_file());bound[str(current)]=sha(current);bound[str(old)]=sha(old)
 snap=O/'pause-baseline'/old.name;snap.parent.mkdir(parents=True,exist_ok=True);snap.write_bytes(old.read_bytes())
 if current.suffix=='.py':ast.parse(current.read_text('utf8'));ck(current.name+' parses',True)
 deltas.append({'file':str(current),'baseline':str(old),'before_sha256':sha(old),'after_sha256':sha(current)})

old=pairs[0][1].read_text('utf8');now=pairs[0][0].read_text('utf8')
ck('public JSON projection unchanged',old.split("for name in (")[0]==now.split("for name in (")[0])
ck('all existing HTML targets retained plus progress page',"('index.html','library.html','dataset.html','inventory.html','progress.html')" in now)
state_node=next(n for n in ast.walk(ast.parse(now)) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='state' for t in n.targets))
for name,estimate,work,expected in [('paused',{'status':'paused_for_joint_review'},[],'Work is paused for joint review'),('empty',{'status':'being_recalibrated'},[],'No paper is currently under review.'),('active',{'status':'working'},[{'short_label':'Fixture'}],'Fixture remains in preparation.')]:
 result=eval(compile(ast.Expression(state_node.value),'<isolated safe state>','eval'),{'editorial':{'estimate':estimate},'current':work});ck('Python widget '+name,expected in result)
ck('Python empty list guard precedes index',isinstance(state_node.value,ast.IfExp) and 'if current else' in ast.unparse(state_node.value))
ck('progress script cache version updated',"src=\"progress.mjs?v=0.33.0-pause\"" in now)

oldjs=pairs[1][1].read_text('utf8');js=pairs[1][0].read_text('utf8')
ck('unchanged refresh cadence, network and errors',oldjs[oldjs.index("let last=''"):]==js[js.index("let last=''"):])
ck('unchanged metrics/source scopes after pause insertion',oldjs[oldjs.index(' const c=data.corpus;'):]==js[js.index(' const c=data.corpus;'):])
ck('removed next-batch fallback',"??'Next batch'" not in js and 'selection in preparation' not in js)
ck('paused no-active view added',"if(paused&&!data.current_work.length)" in js)

oldverified=pairs[2][1].read_text('utf8');newverified=pairs[2][0].read_text('utf8')
normal="normalize=lambda x:re.sub(r'src=\"progress\\.mjs[local path redacted]
ck('normalization scope is exact progress module URL',normal in newverified)
assertion="assert len(old)==len(new)==1 and re.sub(pattern,'',before,flags=re.S)==re.sub(pattern,'',after,flags=re.S)"
replacement=normal+"\nassert len(old)==len(new)==1 and normalize(re.sub(pattern,'',before,flags=re.S))==normalize(re.sub(pattern,'',after,flags=re.S))"
expected=oldverified.replace(assertion,replacement).replace("homepage.write_text(before.replace(old[0],new[0]),'utf8')","homepage.write_text(normalize(before.replace(old[0],new[0])),'utf8')")
ck('verified progress only exact normalization/assert/write delta',expected==newverified)
normalize=lambda x:re.sub(r'src="progress\.mjs\?v=[^"]+"','src="progress.mjs?v=0.33.0-pause"',x)
pattern=r'<!--review-progress-start-->.*?<!--review-progress-end-->'
home=S/'dist/index.html';oldhome=BASE/'recipe-atlas/dist/index.html';before=oldhome.read_text('utf8');after=home.read_text('utf8')
ow=re.findall(pattern,before,re.S);nw=re.findall(pattern,after,re.S)
ck('actual exactly one homepage widget',len(ow)==len(nw)==1)
ck('actual homepage outside-widget data/placement preserved',normalize(re.sub(pattern,'',before,flags=re.S))==normalize(re.sub(pattern,'',after,flags=re.S)))
ck('actual homepage matches old placement with new text/cache',normalize(before.replace(ow[0],nw[0]))==after)
for target in ['index.html','progress.html']:ck('actual pause cache URL '+target,'src="progress.mjs?v=0.33.0-pause"' in (S/'dist'/target).read_text('utf8'))
fixture='<script src="other.mjs?v=1"></script><link href="progress.css?v=1"><script src="progress.mjs?v=old"></script>'
ck('normalization leaves other script/style untouched',normalize(fixture)==fixture.replace('progress.mjs?v=old','progress.mjs?v=0.33.0-pause'))

data=read(S/'dist/data/review-progress.json');editorial=read(MON/'public-progress-editorial.json');control=read(MON/'review-control.json');release=read(MON/'latest-publication.json')
ck('actual current work empty',data['current_work']==editorial['current_work']==[])
ck('actual zero active claims',data['corpus']['active_review_claims']==0)
ck('actual paused estimate',data['estimate']['status']==editorial['estimate']['status']==control['status']=='paused_for_joint_review')
ck('no admission and resume needs instruction',control['new_paper_admission_allowed'] is False and control['resume_requires_user_instruction'] is True)
ck('public scientific counts copied unchanged from verified release',all(data['published'][k]==release[k] for k in data['published']))
ck('existing progress builder output passed',read(J/'site-integration-proposal/verified-progress-build.json')['status']=='passed')
node='[local path redacted]'
p=subprocess.run([node,str(O/'pause_progress_consumer_test.mjs')],capture_output=True,text=True);ck('actual current consumer test executes',p.returncode==0)
consumer=read(O/'pause-progress-consumer-checks.json');ck('all consumer function assertions pass',all(x['passed'] for x in consumer['checks']))
for p in [home,oldhome,S/'dist/progress.html',S/'dist/data/review-progress.json',MON/'public-progress-editorial.json',MON/'review-control.json',MON/'latest-publication.json',J/'site-integration-proposal/verified-progress-build.json',O/'pause-progress-consumer-checks.json',O/'pause_progress_consumer_test.mjs']:bound[str(p)]=sha(p)
r={'status':'passed','scope':'Bounded read-only pause rendering delta review. Prior project snapshots compared; isolated Python state expressions and actual current JS consumer tested with minimal DOM. No full builder execution, Site/scientific content mutation or network.','check_count':len(checks)+consumer['check_count'],'mechanical_checks':checks,'actual_consumer_checks':consumer['check_count'],'open_findings':[],'deltas':deltas,'actual_state':{'active_claims':0,'current_work':[],'estimate':'paused_for_joint_review'},'homepage_placement_preserved':True,'scientific_projection_unchanged':True,'browser_review':'Root separate actual browser check','bound_files':bound,'created_utc':datetime.now(timezone.utc).isoformat()}
(O/'pause-progress-review.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
(O/'pause-progress-review.md').write_text('Passed the bounded pause rendering review. Both server-rendered and browser-rendered summaries handle paused, active and empty states. Empty paused work displays the request-to-resume message and never suggests another batch. Public scientific projection and refreshing logic are unchanged. Homepage normalization touches only the progress.mjs cache URL; actual widget placement and all other homepage content are preserved. Current data reports zero claims, empty work and paused status. No builder, network or shared mutation was executed by this reviewer; actual browser review remains root’s separate check.\n','utf8')
print(json.dumps({'status':r['status'],'checks':r['check_count'],'sha256':sha(O/'pause-progress-review.json')},indent=2))
