from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import urllib.request,json,hashlib
W=Path(__file__).resolve().parent;PUBLIC=W.parents[2]/'mattersyn-github-public-clean/mattersyn-site'
BASE='https://cuiyist.github.io/mattersyn-site/'
EXPECTED='8b1d50201a0ba3d801fa3bdd1b6b9f4403415d93'
paths=['material.html','cdse.html','dataset.html','reader-app.mjs','reader-structures.mjs','reader-particle.mjs','reader.css','protocol-references.mjs','data/reader-release.json','data/structure-recipe-coverage.json','data/reader-presentation.json','assets/crystal-references/wmd-FAPbI3.cif','assets/crystal-references/provenance/wmd-LICENSE.md','assets/chemical-thumbnails/sasongko2025-oa-reference.svg','records/sasongko-2025-hot-injection.html','README.md']
headers={'User-Agent':'MatterSyn-public-release-verification','Cache-Control':'no-cache'}
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=45) as response:return response.read(),response.status,response.geturl()
def check(path):
    raw,status,url=get(BASE+path+'?release='+EXPECTED[:7]);expected=(PUBLIC/path).read_bytes()
    return {'path':path,'http_status':status,'same_bytes_as_published_checkout':raw==expected,'sha256':hashlib.sha256(raw).hexdigest(),'login_redirect':('login' in url),'bytes':len(raw)}
with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(check,paths))
run=json.loads(get('https://api.github.com/repos/cuiyist/mattersyn-site/actions/runs/35777260522')[0])
report={'verified_at':datetime.now(timezone.utc).isoformat(),'site_commit':EXPECTED,'anonymous_http':True,'pages_deployment':{k:run[k] for k in ['status','conclusion','head_sha','html_url']},'artifacts':results,'status':'passed' if all(x['http_status']==200 and x['same_bytes_as_published_checkout'] and not x['login_redirect'] for x in results) and run['conclusion']=='success' and run['head_sha']==EXPECTED else 'failed'}
(W/'live-delivery.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps({'status':report['status'],'site_commit':EXPECTED,'anonymous_artifacts_verified':len(results),'deployment':run['conclusion']},indent=2));raise SystemExit(report['status']!='passed')
