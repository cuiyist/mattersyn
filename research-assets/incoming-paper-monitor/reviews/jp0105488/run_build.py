from pathlib import Path
from datetime import datetime,timezone
import subprocess,json,sys,shutil
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';N='[local path redacted]'
results=[]
commands=[[sys.executable,'-X','utf8',str(S/'scripts'/n)]for n in ['build_dataset.py','build_reader_views.py','build_evidence_views.py','build_paper_reviews.py','build_atlas.py']]
commands+=[[sys.executable,'-X','utf8',str(B/'build_inventory_actual.py')]]
for cmd in commands:
 r=subprocess.run(cmd,cwd=S,capture_output=True,text=True,encoding='utf-8');results.append({'command':cmd[3:],'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr});print(r.stdout);print(r.stderr,end='');
 if r.returncode:break
else:
 shutil.copy2(B/'inventory-proposal/inventory-summary.json',S/'data/inventory-summary.json')
 checks=[[sys.executable,'-X','utf8',str(S/'scripts'/n)]for n in ['build_inventory.py','check_site.py','check_atlas.py','check_quality.py']]
 checks+=[[N,'--check',str(S/'dist'/n)]for n in ['gerion2001-protocol.mjs','protocol-visuals.mjs','crystal-viewer.mjs','material-guide.mjs']]
 for cmd in checks:
  r=subprocess.run(cmd,cwd=S,capture_output=True,text=True,encoding='utf-8');results.append({'command':cmd[1:],'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr});print(r.stdout);print(r.stderr,end='')
  if r.returncode:break
passed=all(x['returncode']==0 for x in results)
(B/'build-validation.json').write_text(json.dumps({'status':'passed'if passed else'failed','at':datetime.now(timezone.utc).isoformat(),'results':results},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Build and existing publication checks:', 'passed'if passed else'failed');sys.exit(0 if passed else 1)
