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
paths=['index.html','progress.html','progress.mjs','data/review-progress.json','README.md','REFERENCES.md','dataset.html','data/dataset-manifest.json','data/paper-reviews/norberg2004.json','assets/figures/norberg2004/figure-3.png','records/nagasaki-2004-biotin-cds.html','records/ribeiro-2004-hydrolysis.html','records/norberg-2004-hydrolysis.html',
 'material.html','records/heo-2003-in66-route.html','data/records/heo-2003-in66-route.json','data/paper-reviews/heo2003.json','heo2003-protocol.mjs','heo2003-average-viewer.mjs','heo2003-reflection-viewer.mjs','assets/crystal-references/heo2003-average-view.json','assets/crystal-references/heo2003-average-position-occupancy.cif','assets/heo2003/heo2003-reflections.json','assets/heo2003/heo2003-reflections.tsv']
def check(rel):
 status,raw,final=anonymous(BASE+rel+'?verify='+site_head)
 return {'path':rel,'url':BASE+rel,'http_status':status,'sha256':sha(raw),'matches_checked_local_bytes':status==200 and raw==(D/rel).read_bytes(),'redirect_stays_on_site':final.startswith(BASE)}
paths += ['records/evans-2010-pbse-qd.html','records/evans-2010-cdse-qd.html','records/evans-2010-molecular9-structure.html','data/records/evans-2010-topse-distillation.json','data/paper-reviews/evans2010.json','data/measurement-display.json','evans2010-protocol.mjs','evans2010-products.mjs','stock-scope.mjs','assets/chemical-registry/models/evans2010-species9-reference-3d.json','assets/figures/evans2010/figure-S15.png','assets/figures/evans2010/figure-S16.png']
if (D/'data/paper-reviews/morrison2017.json').exists():
 paths += ['records/morrison-2017-monolayer-shell.html','records/morrison-2017-excess-precursor-hot.html','records/morrison-2017-precursor-preparation.html','data/records/morrison-2017-monolayer-shell.json','data/paper-reviews/morrison2017.json','morrison2017-protocol.mjs','assets/chemical-registry/product-contexts.json','assets/chemical-registry/solution-components.json','assets/chemical-registry/models/morrison2017-thf-reference-3d.json','assets/figures/morrison2017/figure-7.png','assets/figures/morrison2017/figure-8.png']
if (D/'data/paper-reviews/lian2021.json').exists():
 paths += ['records/lian-2021-bulk-a-route.html','records/lian-2021-bulk-b-route.html','records/lian-2021-nc-a-route.html','records/lian-2021-bulk-characterization.html','data/records/lian-2021-nc-a-route.json','data/paper-reviews/lian2021.json','lian2021-protocol.mjs','lian2021-bulk-viewer.mjs','lian2021-bulk-viewer.css','crystal-viewer.mjs','assets/crystal-references/lian2021-bulk-a-non-h.json','assets/crystal-references/lian2021-bulk-b-non-h.json','assets/crystal-references/lian2021-bulk-a-non-h-partial.cif','assets/crystal-references/lian2021-bulk-b-non-h-partial.cif','assets/figures/lian2021/figure-4.png','assets/figures/lian2021/figure-s11.png']
if (D/'data/paper-reviews/ghosh2012.json').exists():
 paths += ['records/ghosh-2012-core-standard-route.html','records/ghosh-2012-optimized-shell-route.html','records/ghosh-2012-constant-s-variant.html','records/ghosh-2012-photophysical-results.html','data/records/ghosh-2012-core-standard-route.json','data/paper-reviews/ghosh2012.json','ghosh2012-protocol.mjs','protocol-visuals.mjs','assets/chemical-registry/registry.json','assets/chemical-registry/bindings.json','assets/chemical-registry/models/ghosh2012-liquid-nitrogen-reference-2d.json','assets/figures/ghosh2012/figure-1.png','assets/figures/ghosh2012/figure-s4.png','assets/figures/ghosh2012/table-s1.png']
if (D/'data/paper-reviews/sommer2020.json').exists():
 paths += ['records/sommer-2020-mw-route.html','records/sommer-2020-scf-route.html','records/sommer-2020-acs-route.html','records/sommer-2020-insitu-nitrate.html','records/sommer-2020-phase-size-results.html','records/sommer-2020-optical-results.html','data/records/sommer-2020-mw-route.json','data/paper-reviews/sommer2020.json','sommer2020-protocol.mjs','assets/chemical-registry/models/sommer2020-water-3d.json','assets/chemical-registry/svg/sommer2020-spinel-observed-phase-symbol.svg','assets/chemical-registry/svg/sommer2020-zno-observed-phase-symbol.svg','assets/chemical-registry/svg/sommer2020-alooh-observed-phase-symbol.svg','assets/figures/sommer2020/figure-12.png','assets/figures/sommer2020/figure-13.png','assets/figures/sommer2020/table-1.png','assets/figures/sommer2020/heating-profiles.png']
assert len(paths)==len(set(paths))
with ThreadPoolExecutor(max_workers=5) as pool:checks=list(pool.map(check,paths))
excluded_status,_,_=anonymous(BASE+'assets/figures/norberg2004/pages/main-01.png?verify='+site_head)
withheld=['assets/figures/heo2003/pages/main-01.png','assets/figures/heo2003/pages/si-01.png','assets/figures/evans2010/pages/main-01.png','assets/figures/evans2010/pages/si-01.png']
withheld += ['assets/figures/morrison2017/pages/main-01.png','assets/figures/morrison2017/pages/si-01.png']
withheld += ['assets/figures/lian2021/pages/main-01.png','assets/figures/lian2021/pages/si-01.png']
if (D/'data/paper-reviews/ghosh2012.json').exists():withheld += ['assets/figures/ghosh2012/pages/main-01.png','assets/figures/ghosh2012/pages/si-01.png']
if (D/'data/paper-reviews/sommer2020.json').exists():withheld += ['assets/figures/sommer2020/pages/main-01.png','assets/figures/sommer2020/pages/si-01.png']
withheld_checks=[{'path':p,'http_status':anonymous(BASE+p+'?verify='+site_head)[0]} for p in withheld]
readmes=[]
for name,dest,commit in [('mattersyn',P,project_head),('mattersyn-site',D,site_head)]:
 status,raw,_=anonymous('https://raw.githubusercontent.com/cuiyist/'+name+'/'+commit+'/README.md')
 readmes.append({'repository':name,'http_status':status,'bytes_match':raw==(dest/'README.md').read_bytes(),'doi_links':raw.count(b'https://doi.org/')})
result={'schema':'mattersyn-public-delivery-verification/2','verified_at':datetime.now(timezone.utc).isoformat(),'repositories':repositories,'pages':{k:pages.get(k) for k in ('status','html_url','source','https_enforced')},'build':{k:build.get(k) for k in ('status','commit','created_at','updated_at','error')},'anonymous':{'authenticated':False,'cookies_used':False,'checks':checks,'excluded_complete_page_http_status':excluded_status,'readmes':readmes},'site_commit':site_head,'project_commit':project_head}
ok=all(r['public'] and r['anonymous_status']==200 and r['commit_matches'] for r in repositories) and build.get('status')=='built' and build.get('commit')==site_head and all(c['matches_checked_local_bytes'] and c['redirect_stays_on_site'] for c in checks) and excluded_status==404 and all(x['http_status']==200 and x['bytes_match'] and x['doi_links']==expected_citation_count for x in readmes)
result['expected_citation_count']=expected_citation_count
result['anonymous']['additional_withheld_paths']=withheld_checks
ok=ok and all(x['http_status']==404 for x in withheld_checks)
result['status']='passed' if ok else 'pending_or_mismatch_requires_review'
out=R/'research-assets/github-public-delivery-verification.json';out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':result['status'],'repositories':repositories,'build':result['build'],'anonymous_checks_passed':sum(x['matches_checked_local_bytes'] for x in checks),'anonymous_checks_total':len(checks),'excluded_page_status':excluded_status,'readmes':readmes},indent=2))
