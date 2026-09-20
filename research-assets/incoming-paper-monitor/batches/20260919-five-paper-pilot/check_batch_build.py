from pathlib import Path
import subprocess,sys,json
from datetime import datetime,timezone
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';log=[]
commands=[[sys.executable,str(S/'scripts'/name)] for name in ['build_inventory.py','check_site.py','check_atlas.py','check_quality.py','test_quantity_bounds.py','test_review_scope.py']]
node='[local path redacted]'
commands += [[node,'--check',str(S/'dist'/name)] for name in ['nagasaki2004-protocol.mjs','ribeiro2004-protocol.mjs','norberg2004-protocol.mjs','protocol-visuals.mjs','chemical-viewer.mjs','crystal-viewer.mjs','material-guide.mjs']]
for args in commands:
 p=subprocess.run(args,cwd=S,capture_output=True,text=True,encoding='utf8',errors='replace');log.append({'args':args,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
 (B/'integration-proposal/build-check-final.json').write_text(json.dumps({'at':datetime.now(timezone.utc).isoformat(),'runs':log},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(Path(args[-1]).name,p.returncode,p.stdout[-2200:],p.stderr[-1000:],flush=True)
 if p.returncode:raise SystemExit(p.returncode)
