from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
O=Path(__file__).resolve().parent;F=O.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not (O/'package-freeze.json').exists()
p=F/'molecular-independent-audit/independent-audit-v1.json';assert sha(p)=='d0d8c341ce86ff1688362983040738d67b89403d7400372af3d26c1716f811aa'
data={'author':'/root','created_at':datetime.now(timezone.utc).isoformat(),'status':'immutable_correction_pending_independent_recheck','base_freeze':{'path':str(O.parent/'molecules/package-freeze.json'),'sha256':sha(O.parent/'molecules/package-freeze.json')},'audit_findings':{'path':str(p),'sha256':sha(p)},'bound_files':{str(p.relative_to(O)):sha(p) for p in sorted(O.rglob('*')) if p.is_file()},'author_visual_review':'Revised stock SVG rendered and viewed at full 1100-pixel width: In3+, 3x multiplicity, myristate O labels and separate ODE component legible; graph derived from frozen 14-carbon ligand. N2 reference scalar checked exactly, complete independent correction recheck pending.','no_scientific_quantity_change':True,'no_training_approval':True}
(O/'package-freeze.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n','utf8')
print(json.dumps({'sha256':sha(O/'package-freeze.json'),'bound_files':len(data['bound_files'])}))
