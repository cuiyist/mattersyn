"""Established MatterSyn build order with source-specific integration checks."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,sys,shutil
H=Path(__file__).resolve().parent;O=H/'site-integration-proposal';S=Path(r'[local path redacted]')
assert (O/'site-import-manifest.json').exists()
log=[]
def run(args):
 p=subprocess.run(args,cwd=S,capture_output=True,text=True,encoding='utf8',errors='replace')
 log.append({'args':args,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
 (O/'build-check-output.json').write_text(json.dumps({'at':datetime.now(timezone.utc).isoformat(),'runs':log},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(Path(args[-1]).name,p.returncode,p.stdout[-1400:],p.stderr[-600:],flush=True)
 if p.returncode:raise SystemExit(p.returncode)
for name in ['build_dataset.py','build_reader_views.py','build_evidence_views.py','build_paper_reviews.py','build_atlas.py']:run([sys.executable,str(S/'scripts'/name)])
run([sys.executable,str(H/'build_lian_inventory.py')]);shutil.copy2(O/'inventory-summary.json',S/'data/inventory-summary.json')
for name in ['build_inventory.py','check_site.py','check_atlas.py','check_quality.py','test_quantity_bounds.py','test_review_scope.py','test_reader_role.py']:run([sys.executable,str(S/'scripts'/name)])
node=r'[local path redacted]'
for name in ['lian2021-protocol.mjs','protocol-visuals.mjs','crystal-viewer.mjs','source-evidence.mjs','illustrated-record.mjs']:run([node,'--check',str(S/'dist'/name)])
print('Established builders, scientific/static checks and source-specific reader/eligibility separation checks passed.')
