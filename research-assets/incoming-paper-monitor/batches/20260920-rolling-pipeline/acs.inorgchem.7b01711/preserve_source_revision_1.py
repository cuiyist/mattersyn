"""Preserve unchanged author source revision before independent-audit corrections."""
from pathlib import Path
import json,hashlib,shutil
P=Path(__file__).resolve().parent;O=P/'source-extraction-revision-1';O.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
f=json.loads((P/'package-freeze.json').read_bytes());rows=[]
for src,h in f['bound_files'].items():
 p=Path(src)
 if p.parent==P:
  assert sha(p)==h
  dest=O/p.name;shutil.copy2(p,dest);assert sha(dest)==h
  rows.append({'original_path':str(p),'preserved_path':str(dest),'sha256':h})
shutil.copy2(P/'package-freeze.json',O/'package-freeze.json')
rows.append({'original_path':str(P/'package-freeze.json'),'preserved_path':str(O/'package-freeze.json'),'sha256':sha(O/'package-freeze.json')})
(O/'preservation-manifest.json').write_text(json.dumps({'revision':1,'files':rows,'unchanged_shared_cache_files_remain_at_original_bound_paths':True},indent=2)+'\n',encoding='utf-8')
print('Preserved',len(rows),'files')
