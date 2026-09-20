from pathlib import Path
import subprocess,sys,json,shutil
J=Path(__file__).resolve().parent;S=J.parents[4]/'recipe-atlas';O=J/'site-integration-proposal';runs=[]
for p in [J/'build_sasongko_inventory.py',S/'scripts/build_inventory.py',S/'scripts/check_site.py']:
 r=subprocess.run([sys.executable,'-X','utf8',str(p)],capture_output=True,text=True,encoding='utf8');runs.append({'path':str(p),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});print(p.name,r.returncode,r.stdout[-250:]);assert r.returncode==0,r.stderr
 if p.name=='build_sasongko_inventory.py':shutil.copy2(O/'inventory-summary.json',S/'data/inventory-summary.json')
(O/'post-browser-check-output.json').write_text(json.dumps({'status':'passed','runs':runs},indent=2)+'\n','utf8')
