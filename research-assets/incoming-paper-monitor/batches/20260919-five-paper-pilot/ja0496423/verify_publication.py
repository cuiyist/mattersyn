from pathlib import Path
from datetime import datetime, timezone
from urllib.request import Request, build_opener
import hashlib,json
G=Path(__file__).resolve().parent;S=Path('[local path redacted]')
p=G/'publication-checkpoint.json';v=json.loads(p.read_text(encoding='utf-8-sig'))
assert v['deployment']['status']=='succeeded'
origin=v['deployment']['url'].rstrip('/')
checks=[]
opener=build_opener() # No cookie jar, Authorization, or Sites bypass header.
for suffix,local in [('records/gu-2004-heterodimer','dist/records/gu-2004-heterodimer.html'),('data/records/gu-2004-heterodimer.json','dist/data/records/gu-2004-heterodimer.json'),('data/paper-reviews/gu2004.json','dist/data/paper-reviews/gu2004.json'),('data/inventory-summary.json','dist/data/inventory-summary.json'),('material?id=fept-cds-dbce8b','dist/material.html')]:
 url=origin+'/'+suffix
 with opener.open(Request(url,headers={'User-Agent':'MatterSyn public availability verification'}),timeout=40) as r:
  raw=r.read();final=r.url;status=r.status
 assert final.split('/')[2]==origin.split('/')[2],final
 assert status==200
 expected=(S/local).read_bytes()
 exact=raw==expected
 hosting_addition=None
 if not exact and local.endswith('.html'):
  # Public Cloudflare delivery appends its standard JS telemetry before </body>.
  # Verify every authored byte before that footer, preserving the closing tags.
  head,footer=expected.rsplit(b'</body>',1)
  assert raw.startswith(head) and raw.endswith(b'</body>'+footer),suffix
  addition=raw[len(head):-(len(b'</body>')+len(footer))]
  assert addition.startswith(b'<script>') and addition.endswith(b'</script>'),suffix
  assert b'/cdn-cgi/challenge-platform/scripts/jsd/main.js' in addition,suffix
  hosting_addition='Cloudflare delivery script appended before body close; authored HTML unchanged'
 else:
  assert exact,suffix
 checks.append({'url':url,'final_url':final,'http_status':status,'sha256':hashlib.sha256(raw).hexdigest(),'matches_validated_local_bytes':exact,'authored_content_matches':True,'hosting_addition':hosting_addition})
v['anonymous_verification']={'status':'passed','at':datetime.now(timezone.utc).isoformat(),'authenticated':False,'cookies_used':False,'sites_bypass_used':False,'checks':checks}
p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'status':'passed','anonymous_routes_verified':len(checks),'version':v['version']['version_number'],'url':origin,'material':origin+'/material?id=fept-cds-dbce8b'}))
