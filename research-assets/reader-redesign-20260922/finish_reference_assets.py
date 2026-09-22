from pathlib import Path
import json,shutil
W=Path(__file__).resolve().parent;D=W.parents[1]/'recipe-atlas/dist';C=W/'crystal-proposal'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
p=D/'assets/crystal-references/registry.json';reg=read(p);fields=read(C/'cdse-finite-registry-fields.json')
ref=next(r for r in reg['entries'] if r['id']==fields['id']);ref.update({k:v for k,v in fields.items() if k.startswith('finite')})
p.write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
shutil.copytree(C/'cdse-finite-assets/crystal-references',D/'assets/crystal-references',dirs_exist_ok=True)
p=D/'reader-structures.mjs';s=p.read_text(encoding='utf8').replace("badge(scopeKind(ref),'reference')","badge(finite?'Illustration':scopeKind(ref),'reference')")
p.write_text(s,encoding='utf8')
print('Optional Figure 6 finite illustration restored with explicit context and original downloads.')
