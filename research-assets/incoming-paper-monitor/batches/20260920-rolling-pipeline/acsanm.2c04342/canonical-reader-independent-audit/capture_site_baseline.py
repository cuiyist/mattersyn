from pathlib import Path
import sys,json,hashlib,datetime
P=Path('[local path redacted]');A=P/'site-integration-independent-audit';A.mkdir(exist_ok=True);S=Path('[local path redacted]');sys.path.insert(0,str(S/'scripts'));from dataset_lib import eligibility
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records={p.stem:{'sha256':sha(p),'eligibility':eligibility(json.loads(p.read_text('utf-8')))} for p in sorted((S/'data/records').glob('*.json'))};assert len(records)==586 and not any(k.startswith('matuhina-2023') for k in records)
files=['dist/assets/chemical-registry/registry.json','dist/assets/chemical-registry/bindings.json','dist/assets/chemical-registry/solution-components.json','dist/assets/chemical-registry/product-contexts.json','data/measurement-display.json','data/inventory-summary.json','dist/protocol-visuals.mjs','scripts/build_dataset.py','scripts/dataset_lib.py','scripts/build_paper_reviews.py','scripts/build_reader_views.py','scripts/build_atlas.py','dist/material-hub.mjs']
for f in files:
 dst=A/'independent-baseline'/f;dst.parent.mkdir(parents=True,exist_ok=True);assert not dst.exists();dst.write_bytes((S/f).read_bytes())
p=A/'independent-baseline.json';assert not p.exists();x={'schema':'mattersyn-independent-site-baseline/1','source_id':'matuhina2023','reviewer':'/root/norberg2004_extract','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'site_path':str(S),'expected_version':'0.29.0','record_count':len(records),'records':records,'files':{f:sha(S/f) for f in files},'site_modified':False};p.write_text(json.dumps(x,indent=2)+'\n','utf-8');print('baseline',sha(p),'records',len(records),'snapshotfiles',len(files))
