"""Validate and describe the four bounded independent source-audit corrections."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
P=Path(__file__).resolve().parent;OLD=P/'source-extraction-revision-1'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
a=read(OLD/'source-facts.json');b=read(P/'source-facts.json')
aa={f['id']:f for f in a['facts']};bb={f['id']:f for f in b['facts']}
changed=[fid for fid in aa if aa[fid]!=bb[fid]];added=list(set(bb)-set(aa))
assert set(changed)=={'morrison2017-crystal-mount','morrison2017-hot-excess','morrison2017-nmr-evolution'}
assert added==['morrison2017-precursor-yield-results']
assert a['tables']==b['tables']and a['materials']==b['materials']and a['stocks']==b['stocks']and a['figures']==b['figures']and a['references']==b['references']
assert read(OLD/'original-assets-manifest.json')==read(P/'original-assets-manifest.json')
assert all(sha(row['preserved_path'])==row['sha256']for row in read(OLD/'preservation-manifest.json')['files'])
for name in ['source_author_data.py','build_extraction.py']:
 assert(OLD/name).exists()
v=bb['morrison2017-crystal-mount']['quantities'];assert all(x['approximate']for x in v[:3]);assert v[3:]==aa['morrison2017-crystal-mount']['quantities'][3:]
v=bb['morrison2017-hot-excess']['quantities'][1];assert v['value']==15 and v['comparison']=='<='and v['raw_text']=='within 15'
v=bb['morrison2017-nmr-evolution']['quantities'][2];assert v['value']==2 and v['comparison']is None and v['raw_text']=='after 2'
v=bb[added[0]]['quantities'][0];assert v['value']==60 and v['comparison']=='>='
def delta(a,b,path=''):
 if isinstance(a,dict)and isinstance(b,dict):
  for k in sorted(set(a)|set(b)):
   if k not in a:yield{'pointer':path+'/'+k,'before':'__absent__','after':b[k]}
   elif k not in b:yield{'pointer':path+'/'+k,'before':a[k],'after':'__absent__'}
   else:yield from delta(a[k],b[k],path+'/'+k)
 elif isinstance(a,list)and isinstance(b,list)and len(a)==len(b):
  for i,(x,y)in enumerate(zip(a,b)):yield from delta(x,y,path+'/'+str(i))
 elif a!=b:yield{'pointer':path,'before':a,'after':b}
history={'schema':'mattersyn-source-correction-history/1','author':'/root/backlog_eta','requested_by_independent_reviewer':'/root/peng1998_reader_assets','created_at':datetime.now(timezone.utc).isoformat(),'previous_freeze_sha256':sha(OLD/'package-freeze.json'),'revision':2,'correction_categories':['Mark three approximate crystal-mount dimensions without changing Table 1 measured dimensions.','Preserve within 15 min as an upper bound.','Add separate Results yield >=60% without replacing the Experimental single yield.','Retain after 2 h as an observation time, not a strict onset bound; exact onset unknown and C6 retained.'],'changed_existing_facts':[{ 'fact_id':fid,'delta':list(delta(aa[fid],bb[fid]))}for fid in changed],'added_fact_ids':added,'new_source_facts_sha256':sha(P/'source-facts.json'),'derived_copies_regenerated':['protocol quantity copies','measurements','inventory units and counts'],'unchanged_science':{'all_471_table_cells_and_definitions':True,'all_30_crop_assets_and_metadata':True,'all_materials_stocks_figures_references':True,'all_other_68_existing_facts':True,'original_source_copies':True},'source_audit_pass_claimed':False}
(P/'source-correction-history.json').write_text(json.dumps(history,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Four correction categories validated; table data and original crops unchanged.')
