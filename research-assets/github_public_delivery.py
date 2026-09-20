"""Scoped, authorized public MatterSyn delivery. Tokens never enter files or logs."""
from pathlib import Path
import argparse,json,os,subprocess,urllib.request,urllib.error
OWNER='cuiyist';GIT=r'C:\Program Files\Git\cmd\git.exe'
ROOT=Path(__file__).resolve().parent.parent
NAMES={'mattersyn','mattersyn-site'}
def credential():
 env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
 p=subprocess.run([GIT,'credential','fill'],input='protocol=https\nhost=github.com\nusername=cuiyist\n\n',text=True,capture_output=True,env=env)
 if p.returncode:raise SystemExit('GitHub credential lookup failed; no credential details logged.')
 fields=dict(x.split('=',1) for x in p.stdout.splitlines() if '=' in x)
 if not fields.get('password'):raise SystemExit('GitHub credential unavailable.')
 return fields['password']
def api(path,method='GET',payload=None):
 req=urllib.request.Request('https://api.github.com'+path,method=method,headers={'Accept':'application/vnd.github+json','Authorization':'Bearer '+TOKEN,'User-Agent':'MatterSyn-public-delivery','X-GitHub-Api-Version':'2026-03-10'},data=json.dumps(payload).encode() if payload is not None else None)
 try:
  with urllib.request.urlopen(req,timeout=60) as r:return r.status,json.loads(r.read()or b'{}')
 except urllib.error.HTTPError as e:
  if e.code==404:return 404,{}
  raise SystemExit(f'GitHub {method} {path}: HTTP {e.code}; no credential or response-body details logged.')
def compact(repo):return {k:repo.get(k) for k in ('id','name','private','html_url','default_branch','archived')}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['status','preserve-and-create','enable-pages']);parser.add_argument('--repo',choices=sorted(NAMES));parser.add_argument('--expected-old-id',type=int);args=parser.parse_args()
 TOKEN=credential();_,user=api('/user')
 if user.get('login','').lower()!=OWNER or user.get('id')!=147659097:raise SystemExit('Unexpected GitHub account; stopped.')
 result={'account':OWNER,'action':args.action}
 if args.action=='status':
  result['repositories']=[]
  for name in sorted(NAMES):
   status,r=api('/repos/'+OWNER+'/'+name);result['repositories'].append({'exists':status!=404,**compact(r)})
  status,p=api('/repos/'+OWNER+'/mattersyn-site/pages');result['pages']={'exists':status!=404,**{k:p.get(k) for k in ('status','html_url','source','https_enforced')}}
  status,b=api('/repos/'+OWNER+'/mattersyn-site/pages/builds/latest');result['build']={k:b.get(k) for k in ('status','commit','created_at','updated_at','error')}
 elif args.action=='preserve-and-create':
  if not args.repo or not args.expected_old_id:raise SystemExit('Exact repository and old ID required.')
  name=args.repo;archive=name+'-source-archive-20260920'
  status,old=api('/repos/'+OWNER+'/'+name)
  if status==404 or old.get('id')!=args.expected_old_id:raise SystemExit('Current repository differs from reviewed original ID; inspect state before any retry.')
  astatus,a=api('/repos/'+OWNER+'/'+archive)
  if astatus!=404:raise SystemExit('Preservation name already exists; inspect before retry.')
  # Preserve the original object store privately. A newly created public repository
  # only receives reachable, filtered objects from a separate clean local Git store.
  _,saved=api('/repos/'+OWNER+'/'+name,'PATCH',{'name':archive,'private':True})
  if saved.get('id')!=args.expected_old_id or saved.get('private') is not True or saved.get('name')!=archive:raise SystemExit('Private preservation state not verified; stopped.')
  _,new=api('/user/repos','POST',{'name':name,'private':False,'auto_init':False,'description':'MatterSyn source-linked materials synthesis atlas'+(' — public project, memory, skills and audit history' if name=='mattersyn' else ' — public website'),'homepage':'https://cuiyist.github.io/mattersyn-site/'})
  if new.get('private') is not False or new.get('name')!=name:raise SystemExit('Fresh public repository not verified; stopped.')
  result.update(preserved_private=compact(saved),created_public=compact(new))
 elif args.action=='enable-pages':
  _,r=api('/repos/'+OWNER+'/mattersyn-site')
  if r.get('private') is not False:raise SystemExit('Website repository must be public.')
  status,p=api('/repos/'+OWNER+'/mattersyn-site/pages')
  if status==404:_,p=api('/repos/'+OWNER+'/mattersyn-site/pages','POST',{'source':{'branch':'main','path':'/'},'build_type':'legacy'})
  result['pages']={k:p.get(k) for k in ('status','html_url','source','https_enforced')}
 print(json.dumps(result,indent=2))
