"""Anonymous verification of the published website against the checked deployment files."""
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import urllib.request,urllib.error,json,hashlib
ROOT=Path('[local path redacted]')
PUBLIC=ROOT.parent/'mattersyn-github-public/mattersyn-site'
BASE='https://cuiyist.github.io/mattersyn-site/'
paths=['index.html','cdse.html','material.html','dataset.html','data/dataset-manifest.json',
    'records/nagasaki-2004-biotin-cds.html','records/ribeiro-2004-hydrolysis.html','records/norberg-2004-hydrolysis.html',
    'data/records/norberg-2004-hydrolysis.json','data/paper-reviews/ribeiro2004.json',
    'assets/figures/ribeiro2004/figure-4.png','norberg2004-protocol.mjs']
def check(rel):
    request=urllib.request.Request(BASE+rel,headers={'User-Agent':'MatterSyn-publication-check'})
    with urllib.request.urlopen(request,timeout=60) as response:
        data=response.read();local=(PUBLIC/rel).read_bytes()
        return {'url':BASE+rel,'final_url':response.url,'http_status':response.status,
            'sha256':hashlib.sha256(data).hexdigest(),'matches_checked_local_bytes':data==local}
with ThreadPoolExecutor(max_workers=6) as pool:checks=list(pool.map(check,paths))
private_api_status=None
try:
    with urllib.request.urlopen('https://api.github.com/repos/cuiyist/mattersyn',timeout=30) as r:private_api_status=r.status
except urllib.error.HTTPError as error:private_api_status=error.code
report={'status':'passed' if all(c['matches_checked_local_bytes'] for c in checks) and private_api_status==404 else 'failed',
    'verified_at':datetime.now(timezone.utc).isoformat(),'website':BASE,'authenticated':False,'cookies_used':False,
    'private_repository_anonymous_api_status':private_api_status,'public_commit':'6e9c97b961fa0d5db2463cc017f483e406908389',
    'checks':checks}
(ROOT/'research-assets/github-publication-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':report['status'],'checked_urls':len(checks),'website':BASE,
    'all_bytes_match':all(c['matches_checked_local_bytes'] for c in checks),'private_repository_anonymous_api_status':private_api_status},indent=2))
raise SystemExit(report['status']!='passed')
