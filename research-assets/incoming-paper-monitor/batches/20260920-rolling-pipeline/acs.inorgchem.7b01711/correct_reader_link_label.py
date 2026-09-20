"""Correct a stale display label without mutating source-reviewed canonical records."""
from pathlib import Path
import hashlib,json,shutil
N=Path(__file__).resolve().parent;S=N.parents[4]/'recipe-atlas';O=N/'site-integration-proposal';p=S/'scripts/build_dataset.py'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=sha(p);shutil.copy2(p,O/'build-dataset-before-reader-label.py')
old="r['lineage']['source_group'] in {'evans2010','morrison2017'} and l['relation']=='source_reader_pending_independent_audit'"
new="(r['lineage']['source_group'],l['relation']) in {('evans2010','source_reader_pending_independent_audit'),('morrison2017','private_reader_pending_independent_review')}"
t=p.read_text(encoding='utf8');assert t.count(old)==1;p.write_text(t.replace(old,new),encoding='utf8')
(O/'reader-link-label-delta.json').write_text(json.dumps({'path':'scripts/build_dataset.py','before_sha256':before,'after_sha256':sha(p),'before':old,'after':new,'canonical_fields_unchanged':True,'reason':'Independent integration audit found the exact Morrison context-link token differs from Evans. Display neutral Source document review for that reviewed source only.'},indent=2)+'\n',encoding='utf8')
print('Corrected the source-specific display alias; canonical records unchanged.')
