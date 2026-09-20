from pathlib import Path
import json
A=Path(__file__).resolve().parent;G=A.parent;C=G/'canonical-proposal/v1';P=G/'public-review-proposal/v1'
def read(p):return json.loads(p.read_text(encoding='utf8'))
out=[]
for p in sorted(C.glob('pati-2009-*.json')):
 r=read(p);out.append({'record':p.stem,**{k:r[k] for k in ['record_type','title','intended_target','materials','stocks','operations','material_states','products']}})
(A/'canonical-reading-view.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
reader=read(P/'pati2009.json');out=[]
for s in reader['reader_sections']:
 out.append('SECTION '+s['id']+' '+s['title'])
 for i in s['items']:
  out.append('\n'+i['id']+' '+i.get('title','')+'\n'+i.get('text','')+'\nSCOPE '+json.dumps(i.get('sample_scope'),ensure_ascii=False))
  out.append('SOURCE LINKS '+json.dumps(i.get('source_audit_unit_ids'),ensure_ascii=False))
(A/'reader-prose-view.txt').write_text('\n'.join(out),encoding='utf8')
print('Views written',len(out))
