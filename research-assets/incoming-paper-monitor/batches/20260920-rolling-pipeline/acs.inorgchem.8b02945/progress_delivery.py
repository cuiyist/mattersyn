"""Bounded progress-only staging and anonymous delivery verification."""
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import urlopen,Request
import sys,json,hashlib,subprocess,re
F=Path(__file__).resolve().parent;M=F.parents[4];O=F/'progress-publication'
sys.path.insert(0,str(M/'research-assets'))
import public_projection_policy as policy
from sync_github_public import io_path
G='C:/Program Files/Git/cmd/git.exe'
P=M.parent/'mattersyn-github-project';S=M.parent/'mattersyn-github-public-clean/mattersyn-site'
def git(p,*args):return subprocess.check_output([G,'-c','safe.directory='+p.as_posix(),'-c','core.longpaths=true','-C',str(p),*args]).decode().strip()
sha=lambda x:hashlib.sha256(x).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n','utf8')
mode=sys.argv[1]
if mode=='stage':
 old=subprocess.check_output([G,'-c','safe.directory='+S.as_posix(),'-C',str(S),'show','HEAD:index.html']);new=(S/'index.html').read_bytes()
 if old!=new:
  pattern=rb'<!--review-progress-start-->.*?<!--review-progress-end-->'
  assert re.findall(pattern,old,re.S)==re.findall(pattern,new,re.S)
  assert re.sub(pattern,b'',old,flags=re.S)==re.sub(pattern,b'',new,flags=re.S)
  # The progress generator merely moved the unchanged teaser around inventory.
  # Preserve the existing homepage layout; only the queue data needs release.
  (S/'index.html').write_bytes(old);(M/'recipe-atlas/dist/index.html').write_bytes(old)
 rows=[]
 for d,prefix in [(S,'recipe-atlas/dist/'),(P,'')]:
  git(d,'add','-A');paths=[p for p in git(d,'diff','--cached','--name-only','--diff-filter=ACMR','-z').split('\0') if p]
  if d==S:assert set(paths)=={'data/review-progress.json'},paths
  for rel in paths:
   assert not policy.exclude_path(prefix+rel),rel
   assert Path(rel).suffix.lower() not in {'.pdf','.doc','.docx','.zip','.tar','.gz','.pyc'},rel
   p=io_path(d/rel);assert not p.is_symlink() and p.stat().st_size<100*1024*1024,rel
   policy.reject_credentials(prefix+rel,p.read_bytes())
  rows.append({'repository':d.name,'changed_files':len(paths),'forbidden_paths':0,'oversize_files':0,'symlinks':0})
 save(O/'staged-projection-check.json',{'status':'passed','rows':rows,'source_documents_local_only':True})
 print(json.dumps(rows))
elif mode=='verify':
 import github_public_delivery as gh
 gh.TOKEN=gh.credential();_,u=gh.api('/user');assert u.get('login')=='cuiyist' and u.get('id')==147659097
 heads={'mattersyn':git(P,'rev-parse','HEAD'),'mattersyn-site':git(S,'rev-parse','HEAD')};repos=[]
 for name,h in heads.items():
  _,r=gh.api('/repos/cuiyist/'+name);_,c=gh.api('/repos/cuiyist/'+name+'/commits/main')
  assert r.get('private') is False and c.get('sha')==h
  repos.append({'repository':name,'public':True,'commit':h})
 _,build=gh.api('/repos/cuiyist/mattersyn-site/pages/builds/latest')
 if build.get('status')!='built' or build.get('commit')!=heads['mattersyn-site']:
  print(json.dumps({'status':'build_pending','latest_status':build.get('status'),'expected_commit':heads['mattersyn-site']}));sys.exit(2)
 results=[]
 for rel in ['progress.html','data/review-progress.json','data/dataset-manifest.json','README.md','REFERENCES.md']:
  url='https://cuiyist.github.io/mattersyn-site/'+rel+'?checkpoint='+heads['mattersyn-site']
  with urlopen(Request(url,headers={'User-Agent':'MatterSyn progress verification','Cache-Control':'no-cache'}),timeout=45) as r:raw=r.read();status=r.status
  expected=(S/rel).read_bytes();assert status==200 and sha(raw)==sha(expected),rel
  results.append({'path':rel,'status':status,'sha256':sha(raw),'anonymous_exact_match':True})
 report={'status':'passed','verified_at':datetime.now(timezone.utc).isoformat(),'scope':'Changed progress data plus unchanged progress page, science manifest and references; prior full science verification remains separate.','repositories':repos,'pages_build':{'commit':build['commit'],'status':build['status'],'updated_at':build.get('updated_at')},'endpoints':results,'new_science_records_published':False,'prior_full_science_verification':str(M/'research-assets/github-public-delivery-verification.json')}
 save(O/'anonymous-progress-verification.json',report)
 print(json.dumps({'status':'passed','site_commit':heads['mattersyn-site'],'project_commit':heads['mattersyn'],'anonymous_endpoints':len(results),'new_science_records_published':False}))
else:raise ValueError('Expected stage or verify')
