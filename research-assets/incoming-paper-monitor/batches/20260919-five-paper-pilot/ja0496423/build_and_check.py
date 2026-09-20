"""Run established Site builds in dependency order, then bounded checks."""
from pathlib import Path
import subprocess,sys,json,shutil
from datetime import datetime,timezone
B=Path(__file__).resolve().parent;S=Path('[local path redacted]')
log=[]
def run(args,cwd=S):
    p=subprocess.run(args,cwd=cwd,capture_output=True,text=True,encoding='utf8',errors='replace')
    log.append({'args':args,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    (B/'build-check-output.json').write_text(json.dumps({'at':datetime.now(timezone.utc).isoformat(),'runs':log},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(Path(args[-1]).name,p.returncode,p.stdout[-1600:],p.stderr[-900:],flush=True)
    if p.returncode:raise SystemExit(p.returncode)
for name in ['build_dataset.py','build_reader_views.py','build_evidence_views.py','build_paper_reviews.py','build_atlas.py']:run([sys.executable,str(S/'scripts'/name)])
run([sys.executable,str(B/'build_inventory_actual.py')])
shutil.copy2(B/'inventory-proposal/inventory-summary.json',S/'data/inventory-summary.json')
for name in ['build_inventory.py','check_site.py','check_atlas.py','check_quality.py','test_quantity_bounds.py','test_review_scope.py']:run([sys.executable,str(S/'scripts'/name)])
node='[local path redacted]'
for name in ['gu2004-protocol.mjs','protocol-visuals.mjs','chemical-viewer.mjs','crystal-viewer.mjs']:run([node,'--check',str(S/'dist'/name)])
print('Established builds, scientific/static checks and changed-module syntax passed.')
