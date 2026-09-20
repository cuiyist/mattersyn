"""Apply only two independently detected digits after root source reinspection."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,csv,shutil
B=Path(__file__).resolve().parent;stem='si-pages07-08'
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
names=[stem+s for s in ['-author-blocks.json','-reflections.tsv','-transcription.json','-author-checkpoint.json']]
archive=B/(stem+'-author-revision-1');archive.mkdir(exist_ok=False)
old={n:sha(B/n) for n in names}
for n in names:shutil.copyfile(B/n,archive/n);assert sha(archive/n)==old[n]
blocks=read(B/names[0]);typed=read(B/names[2]);cp=read(B/names[3])
with (B/names[1]).open(encoding='utf8',newline='') as f:tsv=list(csv.DictReader(f,delimiter='\t'))
columns=typed['field_order'];changes=[]
for key,rn,column,before,after,hkl in [('7L',43,'Fcal2','70796.77','79796.77',[14,14,22]),('7R',35,'sigma_Fobs2','14787.45','14797.45',[16,22,22])]:
    tokens=blocks[key][rn-1].split();idx=columns.index(column);assert tokens[idx]==before and [int(x) for x in tokens[:3]]==hkl
    tokens[idx]=after;blocks[key][rn-1]=' '.join(tokens)
    rowid=f'si-p{int(key[:-1]):02d}-{key[-1]}-r{rn:03d}'
    row=next(r for r in typed['rows'] if r['row_id']==rowid);assert row['hkl']==hkl and row['raw_cells'][column]==before
    row['raw_cells'][column]=after;c=next(c for c in row['cells'] if c['cell_id']==rowid+'-'+column);assert c['raw_text']==before;c['raw_text']=after;c['numeric_value']=float(after)
    t=next(r for r in tsv if r['page']=='7' and r['block']==key[-1] and r['row']==str(rn));assert t[column]==before;t[column]=after
    changes.append({'cell_id':c['cell_id'],'hkl':hkl,'before':before,'after':after,'source_crop':c['evidence']['original_crop_path'],'source_crop_sha256':c['evidence']['original_crop_sha256'],'reason':'Distinct auditor found digit discrepancy; root reopened native full and narrow source crops and confirmed the corrected glyph.'})
prior_t=read(archive/names[2]);diff=[(r['row_id'],k,a,b) for r,s in zip(prior_t['rows'],typed['rows']) for k,a in r['raw_cells'].items() for b in [s['raw_cells'][k]] if a!=b]
assert len(diff)==2
save(B/names[0],blocks);save(B/names[2],typed)
with (B/names[1]).open('w',encoding='utf8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['page','block','row']+columns,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(tsv)
for p,h in cp['preserved_prior_files'].items():assert sha(p)==h,p
for p,h in cp['bound_original_evidence'].items():assert sha(p)==h,p
cp['bound_files']={p:sha(p) for p in cp['bound_files']}
cp['bounded_correction']={'history':str(B/(stem+'-correction-history.json')),'prior_checkpoint_sha256':old[names[3]],'printed_tokens_corrected':2,'other_printed_tokens_unchanged':1258,'independent_recheck':'pending'}
save(B/names[3],cp)
history={'schema':'mattersyn-si-numerical-correction-history/1','at':datetime.now(timezone.utc).isoformat(),'source_id':'heo2003','transcription_author':'/root','finding_auditor':'/root/backlog_eta','status':'author_corrected_awaiting_distinct_final_recheck','chunk_pages':[7,8],'changes':changes,'prior_files':{str(archive/n):h for n,h in old.items()},'corrected_files':{str(B/n):sha(B/n) for n in names},'original_and_prior_chunks_unchanged':True,'other1258printed_tokens_unchanged':True,'narrow_detail_crops':[]}
for name,box in [('si-07-left-bottom-review-detail.png',[0,985,770,1045]),('si-07-right-bottom-review-detail.png',[0,590,758,650])]:
    p=B/'reader-assets/si-numerical-pages07-08'/name;parent=p.with_name(name.replace('-review-detail',''))
    history['narrow_detail_crops'].append({'path':str(p),'sha256':sha(p),'parent_path':str(parent),'parent_sha256':sha(parent),'parent_pixel_box':box,'operation':'Unaltered rectangular crop; no scaling or digit editing.'})
save(B/(stem+'-correction-history.json'),history)
print(json.dumps({'corrected_cells':len(changes),'checkpoint_sha256':sha(B/names[3]),'history_sha256':sha(B/(stem+'-correction-history.json'))}))
