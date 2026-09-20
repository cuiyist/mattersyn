"""Freeze only this private helper proposal; no shared artifact mutation."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
D=Path(__file__).resolve().parent
assert not(D/'package-manifest.json').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
assert read(D/'author-validation.json')['status']=='passed'
for x in read(D/'inputs.json').values():assert sha(Path(x['path']))==x['sha256']
rows=[{'path':p.relative_to(D).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}for p in sorted(D.rglob('*'))if p.is_file()and p.name!='package-manifest.json']
out={'schema':'mattersyn-private-delivery-helper-proposal/1','status':'frozen_author_proposal_for_root_review','author':'/root/norberg2004_extract','at':datetime.now(timezone.utc).isoformat(),'source_id':'friedfeld2019','dataset_version':'0.32.0','endpoint_plan_sha256':sha(D/'release-endpoints.json'),'files':rows,'validation_sha256':sha(D/'author-validation.json'),'shared_mutations_executed':False,'network_executed':False,'publication_status_changed':False}
(D/'package-manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'status':out['status'],'manifest_sha256':sha(D/'package-manifest.json'),'files':len(rows),'endpoint_plan_sha256':out['endpoint_plan_sha256'],'validation_sha256':out['validation_sha256']}))
