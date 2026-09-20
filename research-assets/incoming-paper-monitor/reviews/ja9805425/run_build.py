"""Root-only sequential build, recording actual return codes; fails closed."""
from pathlib import Path
from datetime import datetime, timezone
import subprocess, sys, json, shutil
B=Path(__file__).resolve().parent
S=B.parents[3]/'recipe-atlas'
resume='--resume-inventory' in sys.argv
results=json.loads((B/'build-validation.json').read_text(encoding='utf-8'))['results'][:5] if resume else []
def run(args):
    p=subprocess.run(args,cwd=S,text=True,capture_output=True,encoding='utf-8',errors='replace')
    results.append({'command':args[1:],'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    (B/'build-validation.json').write_text(json.dumps({'status':'running' if p.returncode==0 else 'failed','at':datetime.now(timezone.utc).isoformat(),'results':results},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(Path(args[-1]).name, 'passed' if p.returncode==0 else 'FAILED',flush=True)
    if p.returncode:
        print(p.stdout,p.stderr)
        raise SystemExit(p.returncode)
for name in ([] if resume else ['build_dataset.py','build_reader_views.py','build_evidence_views.py','build_paper_reviews.py','build_atlas.py']):
    run([sys.executable,str(S/'scripts'/name)])
run([sys.executable,str(B/'build_inventory_actual.py')])
shutil.copy2(B/'inventory-proposal/inventory-summary.json',S/'data/inventory-summary.json')
run([sys.executable,str(S/'scripts/build_inventory.py')])
for name in ['check_site.py','check_atlas.py','check_quality.py']:
    run([sys.executable,str(S/'scripts'/name)])
run([sys.executable,'-m','unittest','discover','-s','scripts','-p','test_*.py'])
for name in ['peng1998-protocol.mjs','protocol-visuals.mjs','source-evidence.mjs','paper-review.mjs','chemical-viewer.mjs','material-hub.mjs','material-guide.mjs']:
    run(['node','--check',str(S/'dist'/name)])
(B/'build-validation.json').write_text(json.dumps({'status':'passed','at':datetime.now(timezone.utc).isoformat(),'results':results},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
