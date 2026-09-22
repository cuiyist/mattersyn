"""Verify the exact progress-only GitHub Pages release without authentication."""
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import hashlib, json, subprocess, urllib.request

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
SITE=ROOT.parent/'mattersyn-github-public-clean/mattersyn-site'
GIT=r'C:\Program Files\Git\cmd\git.exe'
commit=subprocess.check_output([GIT,'-c','safe.directory='+SITE.as_posix(),'-C',str(SITE),'rev-parse','HEAD']).decode().strip()
def fetch(url):
    request=urllib.request.Request(url,headers={'User-Agent':'MatterSyn-release-verification','Cache-Control':'no-cache'})
    with urllib.request.urlopen(request,timeout=30) as response:
        return response.read(),response.geturl(),response.status
api='https://api.github.com/repos/cuiyist/mattersyn-site/actions/runs?head_sha='+commit
runs=json.loads(fetch(api)[0])['workflow_runs']
successful=[r for r in runs if r['head_sha']==commit and r['conclusion']=='success' and 'pages' in r['name'].lower()]
def check(rel):
    raw,url,status=fetch('https://cuiyist.github.io/mattersyn-site/'+rel+'?release='+commit[:12])
    return {'path':rel,'status':status,'matches_published_checkout':raw==(SITE/rel).read_bytes(),
            'sha256':hashlib.sha256(raw).hexdigest(),'same_origin':url.startswith('https://cuiyist.github.io/mattersyn-site/')}
with ThreadPoolExecutor(max_workers=4) as pool:
    rows=list(pool.map(check,['index.html','progress.html','progress.mjs','data/review-progress.json']))
report={'verified_at':datetime.now(timezone.utc).isoformat(),'site_commit':commit,
        'release_scope':'Screening progress only; zero scientific records added.',
        'pages_runs':[{'id':r['id'],'status':r['status'],'conclusion':r['conclusion'],'name':r['name']} for r in runs],
        'authenticated':False,'cookies_used':False,'checks':rows,
        'passed':bool(successful) and all(r['status']==200 and r['matches_published_checkout'] and r['same_origin'] for r in rows)}
(OUT/('live-progress-delivery-'+commit[:12]+'.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
if report['passed']:
    (OUT/'live-progress-delivery.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report,indent=2))
raise SystemExit(not report['passed'])
