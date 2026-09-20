"""Two source-confirmed audit corrections; preserve initial freeze and all prior chunks."""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal
import json,hashlib,csv,shutil
B=Path(__file__).resolve().parent;stem='si-pages09-10'
read=lambda p:json.loads(Path(p).read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
save=lambda p,x:Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
manifest=read(B/(stem+'-manifest.json'));initial_manifest_sha=sha(B/(stem+'-manifest.json'))
assert initial_manifest_sha=='f9fe21b0b42271a5368facbce0332bad0d2019c696e6bb2a211d682c74e86e84'
for p,h in manifest['files'].items():assert sha(p)==h,p
for p,h in manifest['original_evidence'].items():assert sha(p)==h,p
archive=B/(stem+'-author-revision-1');archive.mkdir(exist_ok=False)
initial={}
for p,h in list(manifest['files'].items())+[(str(B/(stem+'-manifest.json')),initial_manifest_sha)]:
 p=Path(p);out=archive/p.name;shutil.copy2(p,out);assert sha(out)==h;initial[str(out)]=h
blocks=read(B/(stem+'-author-blocks.json'));typed=read(B/(stem+'-transcription.json'));cp=read(B/(stem+'-author-checkpoint.json'))
with (B/(stem+'-reflections.tsv')).open(encoding='utf8',newline='') as f:tsv=list(csv.DictReader(f,delimiter='\t'))
author=B/'author_si_pages09_10.py';script=author.read_text(encoding='utf8');columns=typed['field_order'];changes=[]
for key,rn,col,before,after,hkl,detail in [
 ('9R',13,'Fobs2','60085.61','50085.61',[8,24,24],'p9-R13-detail.png'),
 ('10R',24,'Fcal2','216556.06','216566.06',[6,6,26],'p10-R24-detail.png')]:
 tokens=blocks[key][rn-1].split();idx=columns.index(col)
 assert tokens[idx]==before and list(map(int,tokens[:3]))==hkl
 beforeline=' '.join(tokens);tokens[idx]=after;afterline=' '.join(tokens);blocks[key][rn-1]=afterline
 assert script.count(beforeline)==1;script=script.replace(beforeline,afterline)
 rid=f'si-p{int(key[:-1]):02d}-{key[-1]}-r{rn:03d}'
 row=next(x for x in typed['rows'] if x['row_id']==rid);assert row['hkl']==hkl and row['raw_cells'][col]==before
 row['raw_cells'][col]=after;cell=next(c for c in row['cells'] if c['cell_id']==rid+'-'+col)
 assert cell['raw_text']==before;cell['raw_text']=after;cell['numeric_value']=float(after)
 t=next(x for x in tsv if x['page']==str(int(key[:-1])) and x['block']==key[-1] and x['row']==str(rn));assert t[col]==before;t[col]=after
 detailpath=B/'reader-assets/si-pages09-10-independent'/detail
 changes.append({'cell_id':cell['cell_id'],'hkl':hkl,'before':before,'after':after,'reason':'Independent auditor detected a digit discrepancy; transcription author reopened both native parent crop and magnified original-pixel detail and confirmed the corrected value.','source_crop':cell['evidence']['original_crop_path'],'source_crop_sha256':cell['evidence']['original_crop_sha256'],'auditor_detail_crop':str(detailpath),'auditor_detail_sha256':sha(detailpath)})
old=read(archive/(stem+'-transcription.json'))
def diff(a,b,p=''):
 if type(a)!=type(b):return [(p,a,b)]
 if isinstance(a,dict):
  assert a.keys()==b.keys();return [d for k in a for d in diff(a[k],b[k],p+'/'+k)]
 if isinstance(a,list):
  assert len(a)==len(b);return [d for i,(x,y) in enumerate(zip(a,b)) for d in diff(x,y,p+'/'+str(i))]
 return [] if a==b else [(p,a,b)]
deltas=diff(old,typed)
assert len(deltas)==6 and all(any(d[0].endswith(t) for t in ['/raw_cells/Fobs2','/raw_cells/Fcal2','/raw_text','/numeric_value']) for d in deltas)
changed_raw=[(a['row_id'],k,a['raw_cells'][k],b['raw_cells'][k]) for a,b in zip(old['rows'],typed['rows']) for k in columns if a['raw_cells'][k]!=b['raw_cells'][k]]
assert len(changed_raw)==2
checks=[]
for r in typed['rows']:
 for c in r['cells']:
  ok=c['raw_text']==r['raw_cells'][c['evidence']['column_key']]
  if c['numeric_value'] is not None:ok=ok and Decimal(c['raw_text'])==Decimal(str(c['numeric_value']))
  else:ok=ok and c['raw_text']=='o'
  checks.append({'cell_id':c['cell_id'],'passed':bool(ok)});assert ok
for p,h in cp['preserved_prior_files'].items():assert sha(p)==h,p
for p,h in cp['bound_original_evidence'].items():assert sha(p)==h,p
save(B/(stem+'-author-blocks.json'),blocks);save(B/(stem+'-transcription.json'),typed);author.write_text(script,encoding='utf8')
with (B/(stem+'-reflections.tsv')).open('w',encoding='utf8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['page','block','row']+columns,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(tsv)
validation=B/(stem+'-correction-validation.json')
save(validation,{'schema':'mattersyn-bounded-numerical-delta-validation/1','status':'passed_author_delta_checks','source_id':'heo2003','typed_leaf_changes':deltas,'printed_tokens_changed':2,'printed_tokens_unchanged':1258,'cell_consistency_checks':checks,'cell_consistency_check_count':len(checks),'negative_observations_unchanged':old['negative_observations']==typed['negative_observations'],'zero_observations_unchanged':old['zero_observations']==typed['zero_observations'],'source_evidence_unchanged':True,'earlier_chunks_unchanged':True,'independent_recheck':'pending'})
cp['bound_files']={p:sha(p) for p in cp['bound_files']}
cp['bound_files'][str(validation)]=sha(validation);cp['bound_files'][str(Path(__file__))]=sha(Path(__file__))
cp['bounded_correction']={'history':str(B/(stem+'-correction-history.json')),'prior_checkpoint_sha256':sha(archive/(stem+'-author-checkpoint.json')),'printed_tokens_corrected':2,'other_printed_tokens_unchanged':1258,'independent_recheck':'pending'}
save(B/(stem+'-author-checkpoint.json'),cp)
history=B/(stem+'-correction-history.json')
save(history,{'schema':'mattersyn-si-numerical-correction-history/1','at':datetime.now(timezone.utc).isoformat(),'source_id':'heo2003','transcription_author':'/root/peng1998_reader_assets','finding_auditor':'/root/norberg2004_extract','status':'author_corrected_awaiting_distinct_final_recheck','chunk_pages':[9,10],'changes':changes,'prior_files':initial,'corrected_files':{str(p):sha(p) for p in [B/(stem+'-author-blocks.json'),B/(stem+'-reflections.tsv'),B/(stem+'-transcription.json'),B/(stem+'-author-checkpoint.json'),author,validation]},'source_and_prior_chunks_unchanged':True,'other1258printed_tokens_unchanged':True,'auditor_resolved_own_reading_difference':'Auditor reports page9 right row22 sigma=11177.73 already matches the author value; this cell was not changed.'})
manifest['revision']=2;manifest['prior_manifest_sha256']=initial_manifest_sha
manifest['files']={p:sha(p) for p in manifest['files']}
for p in [history,validation,Path(__file__)]:manifest['files'][str(p)]=sha(p)
manifest['bounded_correction_history']=str(history);manifest['independent_audit']='final_recheck_pending'
save(B/(stem+'-manifest.json'),manifest)
print(json.dumps({'corrected_tokens':2,'manifest_sha256':sha(B/(stem+'-manifest.json')),'checkpoint_sha256':sha(B/(stem+'-author-checkpoint.json')),'transcription_sha256':sha(B/(stem+'-transcription.json')),'tsv_sha256':sha(B/(stem+'-reflections.tsv')),'history_sha256':sha(history)},indent=2))
