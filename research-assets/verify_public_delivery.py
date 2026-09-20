"""Verify the exact public repositories and deployed website anonymously."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib,json,subprocess,urllib.request,urllib.error
import github_public_delivery as gh
R=Path(__file__).resolve().parent.parent;D=R.parent/'mattersyn-github-public-clean/mattersyn-site';P=R.parent/'mattersyn-github-project'
GIT=r'C:\Program Files\Git\cmd\git.exe';BASE='https://cuiyist.github.io/mattersyn-site/'
def head(p):return subprocess.check_output([GIT,'-c','safe.directory='+p.as_posix(),'-C',str(p),'rev-parse','HEAD'],text=True).strip()
def sha(b):return hashlib.sha256(b).hexdigest()
def anonymous(url):
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'MatterSyn-publication-verification','Cache-Control':'no-cache'}),timeout=45) as r:return r.status,r.read(),r.url
 except urllib.error.HTTPError as e:return e.code,b'',url
citations=json.loads((R/'research-assets/reference-readme-generation.json').read_text(encoding='utf-8-sig'))
assert citations['source_manifest_sha256']==sha((D/'data/dataset-manifest.json').read_bytes())
expected_citation_count=citations['primary_sources']
site_head=head(D);project_head=head(P);gh.TOKEN=gh.credential();_,user=gh.api('/user')
assert user.get('login')=='cuiyist' and user.get('id')==147659097
repositories=[]
for name,expected in [('mattersyn',project_head),('mattersyn-site',site_head)]:
 _,r=gh.api('/repos/cuiyist/'+name);_,c=gh.api('/repos/cuiyist/'+name+'/commits/main')
 status,raw,_=anonymous('https://api.github.com/repos/cuiyist/'+name)
 repositories.append({'name':name,'id':r['id'],'public':r.get('private') is False,'anonymous_status':status,'expected_commit':expected,'remote_commit':c.get('sha'),'commit_matches':c.get('sha')==expected})
_,pages=gh.api('/repos/cuiyist/mattersyn-site/pages');_,build=gh.api('/repos/cuiyist/mattersyn-site/pages/builds/latest')
paths=['index.html','progress.html','progress.mjs','data/review-progress.json','README.md','REFERENCES.md','dataset.html','data/dataset-manifest.json','data/paper-reviews/norberg2004.json','assets/figures/norberg2004/figure-3.png','records/nagasaki-2004-biotin-cds.html','records/ribeiro-2004-hydrolysis.html','records/norberg-2004-hydrolysis.html']
def check(rel):
 status,raw,final=anonymous(BASE+rel+'?verify='+site_head)
 return {'path':rel,'url':BASE+rel,'http_status':status,'sha256':sha(raw),'matches_checked_local_bytes':status==200 and raw==(D/rel).read_bytes(),'redirect_stays_on_site':final.startswith(BASE)}
with ThreadPoolExecutor(max_workers=5) as pool:checks=list(pool.map(check,paths))
excluded_status,_,_=anonymous(BASE+'assets/figures/norberg2004/pages/main-01.png?verify='+site_head)
readmes=[]
for name,dest,commit in [('mattersyn',P,project_head),('mattersyn-site',D,site_head)]:
 status,raw,_=anonymous('https://raw.githubusercontent.com/cuiyist/'+name+'/'+commit+'/README.md')
 readmes.append({'repository':name,'http_status':status,'bytes_match':raw==(dest/'README.md').read_bytes(),'doi_links':raw.count(b'https://doi.org/')})
result={'schema':'mattersyn-public-delivery-verification/2','verified_at':datetime.now(timezone.utc).isoformat(),'repositories':repositories,'pages':{k:pages.get(k) for k in ('status','html_url','source','https_enforced')},'build':{k:build.get(k) for k in ('status','commit','created_at','updated_at','error')},'anonymous':{'authenticated':False,'cookies_used':False,'checks':checks,'excluded_complete_page_http_status':excluded_status,'readmes':readmes},'site_commit':site_head,'project_commit':project_head}
ok=all(r['public'] and r['anonymous_status']==200 and r['commit_matches'] for r in repositories) and build.get('status')=='built' and build.get('commit')==site_head and all(c['matches_checked_local_bytes'] and c['redirect_stays_on_site'] for c in checks) and excluded_status==404 and all(x['http_status']==200 and x['bytes_match'] and x['doi_links']==expected_citation_count for x in readmes)
result['expected_citation_count']=expected_citation_count
result['status']='passed' if ok else 'pending_or_mismatch_requires_review'
out=R/'research-assets/github-public-delivery-verification.json';out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':result['status'],'repositories':repositories,'build':result['build'],'anonymous_checks_passed':sum(x['matches_checked_local_bytes'] for x in checks),'anonymous_checks_total':len(checks),'excluded_page_status':excluded_status,'readmes':readmes},indent=2))
