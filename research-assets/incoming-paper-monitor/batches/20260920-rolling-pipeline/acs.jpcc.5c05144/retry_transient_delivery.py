from pathlib import Path
from datetime import datetime,timezone
import urllib.request,json,hashlib
from release_support import load_config,read,validate_proof_fields
J=Path(__file__).resolve().parent;M=J.parents[4];D=M.parent/'mattersyn-github-public-clean/mattersyn-site';p=M/'research-assets/github-public-delivery-verification.json';v=read(p);O=J/'site-integration-proposal'
failed=[x for x in v['anonymous']['checks'] if not x['matches_checked_local_bytes']]
assert len(failed)==1 and failed[0]['http_status']==503
prior=O/'science-delivery-transient-503.json';assert not prior.exists();prior.write_bytes(p.read_bytes())
x=failed[0];req=urllib.request.Request(x['url']+'?verify='+v['site_commit']+'&retry=1',headers={'User-Agent':'MatterSyn-publication-verification','Cache-Control':'no-cache'})
with urllib.request.urlopen(req,timeout=45) as r:status=r.status;raw=r.read();url=r.url
assert status==200 and raw==(D/x['path']).read_bytes() and url.startswith('https://cuiyist.github.io/mattersyn-site/')
x.update(http_status=status,sha256=hashlib.sha256(raw).hexdigest(),matches_checked_local_bytes=True,redirect_stays_on_site=True)
v['retry_evidence']={'at':datetime.now(timezone.utc).isoformat(),'prior_receipt_sha256':hashlib.sha256(prior.read_bytes()).hexdigest(),'retried_path':x['path'],'http_status':200,'cookies_used':False,'authenticated':False};v['status']='passed'
validate_proof_fields(v,read(O/'release-endpoints.json'),load_config(J))
p.write_text(json.dumps(v,indent=2)+'\n','utf8');print('Passed672endpoints; isolated503retry confirmed exact bytes; original failed receipt preserved.')
