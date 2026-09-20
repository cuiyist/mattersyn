"""Read-only project packaging inventory; no credentials or PDF contents read."""
from pathlib import Path
from collections import Counter,defaultdict
import os,json
ROOT=Path('[local path redacted]');OUT=ROOT/'research-assets/github-inventory.json'
skip={'.git','node_modules','__pycache__','.sites-runtime','rdkit-runtime','runtime','python-packages','.venv','venv'}
counts=Counter();sizes=Counter();large=[];total=0;denied=[]
for directory,dirs,files in os.walk(ROOT,onerror=lambda e:denied.append(str(e.filename))):
 dirs[:]=[d for d in dirs if d not in skip]
 for name in files:
  p=Path(directory)/name;rel=p.relative_to(ROOT);n=p.stat().st_size
  category='downloaded_papers' if rel.parts[0]=='downloaded_papers' else 'deployment_archives' if name.endswith(('.tar.gz','.zip','.tar','.bundle')) else 'site' if rel.parts[0]=='recipe-atlas' else 'project_work'
  if len(rel.parts)>1 and rel.parts[:2]==('recipe-atlas','dist'):category='website_output'
  counts[category]+=1;sizes[category]+=n;total+=1
  if n>50*1024*1024:large.append({'path':rel.as_posix(),'bytes':n})
result={'root':str(ROOT),'counts':dict(counts),'bytes':dict(sizes),'files_over_50_mib':large,'excluded_runtime_directories':sorted(skip),'unreadable_directories':denied}
OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps(result,indent=2))
