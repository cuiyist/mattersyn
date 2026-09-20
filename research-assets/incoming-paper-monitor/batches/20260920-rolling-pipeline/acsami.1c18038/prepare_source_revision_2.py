"""Preserve revision1; clarify TGA atmosphere and disambiguate inventory unit identifiers."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
old='Acquire XPS and TGA under N2';new='Acquire XPS; acquire TGA under N2'
m=json.loads((P/'package-freeze.json').read_bytes())
assert m['revision']==1
for path,digest in m['bound_files'].items():assert sha(path)==digest,path
archive=P/'source-extraction-revision-1';archive.mkdir(exist_ok=False)
mapping={}
for item in sorted(P.iterdir()):
 if item.is_file()and item.name in{Path(x).name for x in m['bound_files']if Path(x).parent.resolve()==P.resolve()}|{'package-freeze.json'}:
  dst=archive/item.name;shutil.copy2(item,dst);assert sha(dst)==sha(item);mapping[str(item)]={'archived_path':str(dst),'sha256':sha(dst)}
write(archive/'preservation-map.json',{'schema':'mattersyn-preserved-source-revision/1','author':'/root/backlog_eta','preserved_at':datetime.now(timezone.utc).isoformat(),'original_freeze_sha256':sha(archive/'package-freeze.json'),'changed_document_snapshots':mapping,'unchanged_large_files':'Original full-page/text/crop files remain bound at their original paths with unchanged hashes; no huge binary duplication was necessary.'})
deltas=[]
for name in['source-facts.json','source-inventory.json']:
 path=P/name;data=json.loads(path.read_bytes());before=sha(path);found=[]
 for ip,pr in enumerate(data['protocols']):
  for io,op in enumerate(pr['operations']):
   if op['id']=='bulk-xps-tga':
    assert op['action']==old;op['action']=new;found.append(f'/protocols/{ip}/operations/{io}/action')
 assert len(found)==1
 if name=='source-inventory.json':
  identity_changes=[]
  for iu,u in enumerate(data['inventory_units']):
   prior=u['id'];u['source_object_id']=prior;u['id']=u['type']+':'+prior
   identity_changes.append({'unit_index':iu,'old_id':prior,'new_id':u['id'],'source_object_id':prior,'json_pointer_unchanged':u['json_pointer']})
  assert len({u['id']for u in data['inventory_units']})==len(data['inventory_units'])
  deltas.append({'file':name,'scope':'/inventory_units','allowed_delta':'Prefix unit IDs by object type and retain explicit unchanged source_object_id. All scientific object IDs/pointers unchanged.','identity_changes':identity_changes})
 write(path,data);deltas.append({'file':name,'json_pointer':found[0],'before':old,'after':new,'before_sha256':before,'after_sha256':sha(path)})
script=P/'build_extraction.py';txt=script.read_text(encoding='utf-8');assert txt.count(old)==1;script.write_text(txt.replace(old,new),encoding='utf-8')
txt=script.read_text(encoding='utf-8');oldcode="units.append({'id':item['id'],'type':kind,";newcode="units.append({'id':kind+':'+item['id'],'source_object_id':item['id'],'type':kind,";assert txt.count(oldcode)==1;script.write_text(txt.replace(oldcode,newcode),encoding='utf-8')
history={'schema':'mattersyn-source-correction-history/1','author':'/root/backlog_eta','requesting_independent_reviewer':'/root/norberg2004_extract','corrected_at':datetime.now(timezone.utc).isoformat(),'from_revision':1,'to_revision':2,'original_freeze_sha256':sha(archive/'package-freeze.json'),'reason':'Main p7 assigns N2 only to TGA; clarify action grammar. Inventory units reused three material/sample IDs; add globally unique type-prefixed unit IDs and retain unchanged scientific object IDs explicitly.','scientific_value_change':False,'deltas':deltas,'pre_first_freeze_note':'Reviewer also flagged unprinted PS Mw unit. The first frozen revision already has reported unit null, approximate280000 unchanged.','unchanged_science':['All57fact claims/134quantities','All9tables/891cells','Source hashes','All53crop bytes','Materials/stocks/samples/figures/equations/references','Operation inputs/outputs and all quantities; only the specified action wording changed.']}
write(P/'source-correction-history.json',history)
print(json.dumps({'preserved_freeze':str(archive/'package-freeze.json'),'correction_history_sha256':sha(P/'source-correction-history.json'),'next':'Run updated freeze_extraction.py revision2 after all bounded findings are finalized.'}))
