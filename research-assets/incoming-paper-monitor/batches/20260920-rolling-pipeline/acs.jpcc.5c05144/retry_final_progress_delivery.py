from pathlib import Path
from datetime import datetime,timezone
import sys,urllib.request,json,hashlib
from release_support import load_config,read,validate_delivery
J=Path(__file__).resolve().parent;M=J.parents[4];D=M.parent/'mattersyn-github-public-clean/mattersyn-site';O=J/'site-integration-proposal';p=M/'research-assets/github-public-delivery-verification.json';v=read(p)
failed=[x for x in v['anonymous']['checks'] if not x['matches_checked_local_bytes']]
expected={'index.html','progress.html','progress.mjs','data/inventory-summary.json','data/review-progress.json','data/paper-reviews/sasongko2025.json'}
assert {x['path']for x in failed}==expected and v['build']['status']=='building'
prior=O/'progress-delivery-propagation-pending.json';assert not prior.exists();prior.write_bytes(p.read_bytes())
sys.path.insert(0,str(M/'research-assets'));import github_public_delivery as gh
gh.TOKEN=gh.credential();_,build=gh.api('/repos/cuiyist/mattersyn-site/pages/builds/latest');assert build['status']=='built' and build['commit']==v['site_commit']
_,pages=gh.api('/repos/cuiyist/mattersyn-site/pages')
v['build']={k:build.get(k) for k in ('status','commit','created_at','updated_at','error')};v['pages']={k:pages.get(k)for k in ('status','html_url','source','https_enforced')}
for x in failed:
 req=urllib.request.Request(x['url']+'?verify='+v['site_commit']+'&afterbuild=1',headers={'User-Agent':'MatterSyn-publication-verification','Cache-Control':'no-cache'})
 with urllib.request.urlopen(req,timeout=45)as r:status=r.status;raw=r.read();url=r.url
 assert status==200 and raw==(D/x['path']).read_bytes() and url.startswith('https://cuiyist.github.io/mattersyn-site/'),x['path']
 x.update(http_status=status,sha256=hashlib.sha256(raw).hexdigest(),matches_checked_local_bytes=True,redirect_stays_on_site=True)
v['retry_evidence']={'at':datetime.now(timezone.utc).isoformat(),'prior_receipt_sha256':hashlib.sha256(prior.read_bytes()).hexdigest(),'retried_paths':sorted(expected),'reason':'Initial requests preceded completion of the exact Pages build. All six changed resources refetched after built status.','cookies_used':False,'authenticated':False};v['status']='passed'
validate_delivery(J,v,read(O/'release-endpoints.json'),load_config(J));p.write_text(json.dumps(v,indent=2)+'\n','utf8');print('Exact finalbuild verified; all672anonymous bytes pass including allsixchanged paths refetched afterbuild.')
