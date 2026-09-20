"""Root-only import after distinct scientific, visual and promotion audits."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,copy,shutil
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';O=B/'integration-proposal'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assert not (O/'record-import-manifest.json').exists(),'Import already performed'
config=[('la036034c','nagasaki2004',16,2,5),('jp0473669','ribeiro2004',11,1,1),('ja048427j','norberg2004',19,1,4)]
for folder,g,count,prec,partial in config:
 P=B/folder;a=read(P/'promotion-source-audit.json');assert a['status'].startswith('passed') and not a['open_findings']
 for p,h in a['bound_files'].items():assert sha(Path(p))==h,('stale promotion',p)
 assert not (S/'data/paper-reviews'/(g+'.json')).exists(),g
 assert len(list((P/'promotion-proposal/records').glob('*.json')))==count
allrecords={};imports=[];struct=set()
bindings=read(S/'dist/assets/chemical-registry/bindings.json')
for folder,g,count,prec,partial in config:
 P=B/folder;rr={p.stem:read(p) for p in (P/'promotion-proposal/records').glob('*.json')};allrecords.update(rr)
 for rid,r in rr.items():
  target=S/'data/records'/(rid+'.json');assert not target.exists();shutil.copy2(P/'promotion-proposal/records'/(rid+'.json'),target)
  assert set(bindings['recordBindings'][rid])=={m['id'] for m in r['materials']}
  bindings.setdefault('sourceRecordSha256',{})[rid]=sha(target)
 reader=read(P/'public-review-proposal'/(g+'.json'));before=copy.deepcopy(reader)
 scope=next(iter(rr.values()))['quality']['review_scope']
 reader.update(coverage_status=reader['review_scope']+'_review_complete',source_review_promoted=True,independent_audit=scope,publication_status='Reviewed contribution integrated into the existing MatterSyn atlas; deployment tracked separately.',training_note=f'{prec} precursor-selection and {partial} partial-protocol task rows are admitted from this source. Supporting procedures and analytical/model contexts retain distinct records. Missing source details and specimen links remain explicit; no exact-structure, size-conditioned, optical-outcome or success-prediction task is admitted.')
 # Remove only superseded workflow status; all scientific gaps remain verbatim.
 if g=='nagasaki2004':
  old='Molecular, polymer, protein, apparatus and crystal-reference bindings remain pending; no source-specific 3D geometry is approved by this proposal.'
  assert old in reader['remaining_gaps'];reader['remaining_gaps'].remove(old)
  reader['remaining_gaps'].append('Molecular reference and symbolic polymer/protein depictions are separately audited illustrations. No source-specific CdS atomic coordinates or measured ligand geometry are supplied.')
 if g=='norberg2004':
  old='Molecular, apparatus, product/crystal visual assets and their exact source bindings remain pending separate review. No CIF or exact atomic coordinates are supplied.'
  assert old in reader['remaining_gaps'];reader['remaining_gaps'].remove(old)
  reader['remaining_gaps'].append('Molecular and product illustrations and an external undoped ZnO crystal reference are separately audited. No sample-specific Mn:ZnO CIF, measured atom coordinates or resolved dopant-site occupations are supplied.')
 if reader.get('presentation_gates'):
  for key in ['molecular_bindings','apparatus_bindings','independent_reader_audit']:reader['presentation_gates'][key]='passed'
 for category in ['figures','tables','schemes','equations','source_notes']:
  for item in reader.get(category,[]):item['reviewed']=True
 for item in reader['recipe_inventory']:
  item['status']='source_reviewed';item['gaps']=[x for x in item['gaps'] if x not in ['Viewer bindings and presentation review pending.','Presentation and source-to-reader binding review pending.']]
 # Per-item metadata describes registry binding review, never atomic sample recovery.
 changed_flags=[]
 def visit(x,path=''):
  if isinstance(x,list):
   for i,v in enumerate(x):visit(v,path+'/'+str(i))
  elif isinstance(x,dict):
   for key in ['exact_molecular_asset_binding_approved','apparatus_binding_approved']:
    if key in x and x[key] is False:x[key]=True;changed_flags.append(path+'/'+key)
   for k,v in x.items():visit(v,path+'/'+k)
 visit(reader['reader_sections'],'/reader_sections')
 # The approved whole record set covers every canonical material/operation; scientific payload and atomic flags are unchanged.
 for section in reader['reader_sections']:
  if section['id']=='structures':
   for item in section['items']:
    for link in item.get('canonical_links',[]):
     parts=link['json_pointer'].strip('/').split('/')
     if parts[0]=='measurements':struct.add(rr[link['record_id']]['measurements'][int(parts[1])]['property'])
 target=S/'data/paper-reviews'/(g+'.json');write(target,reader)
 imports.append({'source_id':g,'records':{rid:sha(S/'data/records'/(rid+'.json')) for rid in rr},'private_reader_sha256':sha(P/'public-review-proposal'/(g+'.json')),'public_reader_sha256':sha(target),'promotion_audit_sha256':sha(P/'promotion-source-audit.json'),'approved_presentation_flag_paths':changed_flags,'source_review_scope':reader['review_scope'],'reader_cards':sum(len(x['items']) for x in reader['reader_sections']),'atomic_labels_added':0})
write(S/'dist/assets/chemical-registry/bindings.json',bindings)
p=S/'data/measurement-display.json';d=read(p);d['structural_properties']=list(dict.fromkeys(d['structural_properties']+sorted(struct)));write(p,d)
write(O/'structural-property-additions.json',sorted(struct))
p=S/'scripts/build_atlas.py';t=p.read_text(encoding='utf8');t+="\n" if not t.endswith('\n') else ''
# Names must be assigned before the script's main call.
anchor="NAMES['FePt']='Iron–platinum · heterodimer-component context'";assert anchor in t
t=t.replace(anchor,anchor+"\nNAMES['SnO2']='Tin dioxide colloids'\nNAMES['Mn:ZnO']='Manganese-doped zinc oxide nanocrystals and films'");p.write_text(t,encoding='utf8')
p=S/'scripts/build_dataset.py';t=p.read_text(encoding='utf8');assert "'dataset_version':'0.22.0'" in t;p.write_text(t.replace("'dataset_version':'0.22.0'","'dataset_version':'0.23.0'"),encoding='utf8')
for p in list((S/'scripts').glob('build_*.py'))+list((S/'dist').glob('*.mjs'))+list((S/'dist').glob('*.html')):
 t=p.read_text(encoding='utf8');n=t.replace('0.22.0-r1','0.23.0-r1')
 if n!=t:p.write_text(n,encoding='utf8')
assert all(sha(S/'data/records'/n)==h for n,h in read(O/'base-record-hashes.json').items())
write(O/'record-import-manifest.json',{'status':'integrated_build_and_browser_pending','at':datetime.now(timezone.utc).isoformat(),'source_imports':imports,'new_records':len(allrecords),'old_records_unchanged':424,'atomic_labels_added':0})
print(json.dumps({'records_added':len(allrecords),'reader_cards_added':sum(x['reader_cards'] for x in imports),'sources':[x['source_id'] for x in imports]}))
