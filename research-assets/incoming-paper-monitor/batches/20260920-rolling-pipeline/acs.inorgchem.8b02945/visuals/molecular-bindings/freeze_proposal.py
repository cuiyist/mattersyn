from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
O=Path(__file__).resolve().parent;F=O.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not (O/'package-freeze.json').exists()
checks=json.loads((O/'consumer-checks.json').read_text('utf8'));assert checks['status']=='passed'
proof={'schema':'mattersyn-molecular-bindings-proposal/1','author':'/root','created_at':datetime.now(timezone.utc).isoformat(),'status':'immutable_author_proposal_pending_independent_audit','counts':{'material_slots':77,'stock_instances':8,'component_slots':16,'identities':39,'consumer_checks':2168},'canonical_freeze':{'path':str(F/'canonical-proposal/draft-v2/package-freeze.json'),'sha256':sha(F/'canonical-proposal/draft-v2/package-freeze.json')},'molecular_audit':{'path':str(F/'molecular-independent-audit/independent-audit.json'),'sha256':sha(F/'molecular-independent-audit/independent-audit.json')},'author_visual_review':'Root rendered and viewed new varied-MSC stock at full1100px; quantity/amount unknown, inherited1mLvolumelabeled,representative20mg/0.00121mmolexcluded. Componentgraphs unchanged.','browser_testing':False,'training_approval':False,'bound_files':{str(p.relative_to(O)):sha(p) for p in sorted(O.rglob('*')) if p.is_file()}}
(O/'package-freeze.json').write_text(json.dumps(proof,indent=2,ensure_ascii=False)+'\n','utf8')
print(json.dumps({'sha256':sha(O/'package-freeze.json'),'bound_files':len(proof['bound_files'])}))
