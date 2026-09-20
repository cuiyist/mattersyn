"""Apply the independently checked reader projection without changing frozen evidence."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,re,shutil
H=Path(__file__).resolve().parent
OUT=H/'site-integration-proposal';OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def at(root,pointer):
 x=root
 for k in pointer.strip('/').split('/'):
  k=k.replace('~1','/').replace('~0','~');x=x[int(k)] if isinstance(x,list) else x[k]
 return x
def parent(root,pointer):
 before,key=pointer.rsplit('/',1);return at(root,before),key.replace('~1','/').replace('~0','~')
p=read(H/'publication-projection-audit/publication-projection-proposal.json')
source=Path(p['input_reader']);assert sha(source)==p['input_reader_sha256']
r=read(source);removed=[]
for row in p['private_path_removals']:
 obj,key=parent(r,row['pointer']);assert obj[key]==row['value'];del obj[key];removed.append(row['pointer'])
for row in p['source_role_corrections']:
 obj,key=parent(r,row['pointer']);assert obj[key]==row['before'];obj[key]=row['after']
for row in p['whole_page_attachment_removals']:
 obj=at(r,row['object_pointer']);assert obj['public_asset']==row['public_asset']
 if '/original_assets/' in row['object_pointer']:
  seq,key=parent(r,row['object_pointer']);assert len(seq)==1;seq.pop(int(key))
 else:
  for key in row['remove_keys']:del obj[key]
obj,key=parent(r,p['private_dependency_path']['pointer']);del obj[key]
# Public provenance retains original stable filenames and hashes, not local absolute keys.
identity=r['document_identity_verification'];identity['source_hashes']={Path(k).name:v for k,v in identity['source_hashes'].items()}
pageids={x['asset_id'] for x in p['binary_exclusions']}
for formula,ids in r['material_original_asset_ids'].items():
 r['material_original_asset_ids'][formula]=[x for x in ids if x not in pageids]
r['counts']['original_assets']=16
r['counts']['source_page_identities_retained_without_images']=23
for sec in r['reader_sections']:
 for item in sec['items']:
  if item['id'] in {'asset-'+x for x in pageids}:
   item.setdefault('notes',[]).append('Source-page identity and extracted evidence are retained; complete page images remain local. Selected figures and tables are available separately.')
assert sum(len(s['items']) for s in r['reader_sections'])==372
assert not re.search(r'[A-Z]:[\\/]',json.dumps(r)), 'Unexpected local path remains'
urls=[]
def walk(x):
 if isinstance(x,dict):
  if x.get('public_asset'):urls.append(x['public_asset'])
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
walk(r)
assert set(urls)=={x['public_path'] for x in p['retained_selected_assets']}
write(OUT/'reader/heo2003.json',r)
for row in p['retained_selected_assets']:
 src=Path(row['private_original_path']);assert sha(src)==row['sha256']
 dst=OUT/'dist'/row['public_path'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
write(OUT/'projection-manifest.json',{'schema':'mattersyn.applied_reader_projection/1','at':datetime.now(timezone.utc).isoformat(),'author':'/root','status':'applied_audited_projection_pending_integrated_review','input_sha256':sha(source),'proposal_sha256':sha(H/'publication-projection-audit/publication-projection-proposal.json'),'independent_projection_audit_sha256':sha(H/'publication-projection-audit/publication-projection-audit.json'),'public_reader_sha256':sha(OUT/'reader/heo2003.json'),'private_path_removals':len(removed),'source_role_corrections':len(p['source_role_corrections']),'full_page_attachments_removed':23,'full_page_source_urls_removed':23,'selected_original_assets':16,'reader_items':372,'canonical_data_mutations':0,'training_promotions':0,'extra_public_metadata_changes':['Source hashes keyed by stable original filename rather than absolute local path.','23 page IDs removed from material image-gallery IDs; source notes and reader items retained.','Gallery asset count is 16; 23 separate source-page identities retained.']})
print(json.dumps({'reader_items':372,'selected_assets':16,'whole_page_assets':0,'output':str(OUT)}))
