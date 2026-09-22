from pathlib import Path
import json,shutil
W=Path(__file__).resolve().parent;D=W.parents[1]/'recipe-atlas/dist';C=W/'crystal-proposal'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
p=D/'assets/crystal-references/registry.json';data=read(p)
ext=read(C/'cdse-wurtzite-binding-extension.json');ref=next(r for r in data['entries'] if r['id']==ext['id'])
ref['record_ids']=sorted(set(ref['record_ids']+ext['add_record_ids']));ref.setdefault('bindingScopes',{}).update(ext['bindingScopes'])
ref['sourceType']=ext['sourceType']
new=read(C/'cdse-zinc-blende-registry-addition.json')['entries'][0];data['entries']=[r for r in data['entries'] if r['id']!=new['id']]+[new]
shutil.copytree(C/'cdse-adapter-assets/crystal-references',D/'assets/crystal-references',dirs_exist_ok=True)
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Restored independently qualified CdSe phase references without changing sample assignments.')
