"""Independent manual source reading versus frozen SI9–10 author data."""
from pathlib import Path
from decimal import Decimal
from datetime import datetime,timezone
import sys,json,csv,hashlib,io
sys.dont_write_bytecode=True
sys.path[:0]=[r'[local path redacted]',r'[local path redacted]']
import pymupdf
from PIL import Image
R=Path(__file__).resolve().parent;read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();dump=lambda p,x:Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
fields=['h','k','l','Fcal2','Fobs2','sigma_Fobs2','marker'];checks=[];bound={}
def ck(ok,label):
 checks.append({'passed':bool(ok),'label':label})
 if not ok:raise AssertionError(label)
def bind(p,h=None):
 p=Path(p);digest=sha(p);ck(h is None or h==digest,'Frozen hash '+p.name);bound[str(p)]=digest
expected=sys.argv[1];expected_manifest=sys.argv[2];cp=R/'si-pages09-10-author-checkpoint.json';bind(cp,expected);checkpoint=read(cp);trans=read(R/'si-pages09-10-transcription.json');author=read(R/'si-pages09-10-author-blocks.json');assets=read(R/'si-pages09-10-assets.json');own=read(R/'si-pages09-10-independent-assets.json');independent=read(R/'si-pages09-10-independent-reading-resolved.json')['blocks'];table=list(csv.DictReader((R/'si-pages09-10-reflections.tsv').open(encoding='utf-8',newline=''),delimiter='\t'))
bind(R/'si-pages09-10-manifest.json',expected_manifest)
freeze=read(R/'si-pages09-10-manifest.json')
for category in ['files','original_evidence']:
 for p,h in freeze[category].items():bind(p,h)
ck(checkpoint['author']!='/root/norberg2004_extract' and trans['author']==checkpoint['author'],'Distinct author and independent auditor')
ck(trans['pages']==[9,10] and trans['field_order']==fields,'Exact two-page field schema')
ck(not trans['complete_document_transcription'] and not trans['training_eligible'] and not trans['published'],'No full-document/training/publication assertion')
for category in ['bound_files','bound_original_evidence','preserved_prior_files']:
 for p,h in checkpoint.get(category,{}).items():bind(p,h)
for name in ['si-pages09-10-independent-reading.py','si-pages09-10-independent-reading.json','si-pages09-10-independent-reading-resolved.json','si-pages09-10-independent-comparison-initial.json','si-pages09-10-independent-resolution-history.json','resolve_si_pages09_10_independent.py','si-pages09-10-independent-assets.json','prepare_si_pages09_10_independent.py','prepare_si_pages09_10_disagreement_details.py','si-pages09-10-disagreement-detail-manifest.json','audit_si_pages09_10_independent.py']:bind(R/name)
history=read(R/'si-pages09-10-independent-resolution-history.json')
initial=read(R/'si-pages09-10-independent-reading.json')['blocks']
own_deltas=[{'block':b,'row':i+1,'field':fields[j],'old':x,'new':y} for b in initial for i,(old,new) in enumerate(zip(initial[b],independent[b])) for j,(x,y) in enumerate(zip(old,new)) if x!=y]
ck(own_deltas==[{'block':'9R','row':22,'field':'sigma_Fobs2','old':'11777.73','new':'11177.73'}],'Only the documented auditor typing error resolved')
for label in ['initial_reading','initial_comparison','resolved_reading']:bind(history[label]['path'],history[label]['sha256'])
archive=R/'si-pages09-10-author-revision-1'
bind(archive/'si-pages09-10-manifest.json',history['initial_author_manifest_sha256'])
bind(archive/'si-pages09-10-author-checkpoint.json',history['initial_author_checkpoint_sha256'])
oldfreeze=read(archive/'si-pages09-10-manifest.json')
for p,h in oldfreeze['files'].items():bind(archive/Path(p).name,h)
for p,h in oldfreeze['original_evidence'].items():bind(p,h)
for name in ['si-pages09-10-correction-history.json','si-pages09-10-correction-validation.json']:bind(R/name)
author_history=read(R/'si-pages09-10-correction-history.json')
for category in ['prior_files','corrected_files']:
 for p,h in author_history[category].items():bind(p,h)
oldauthor=read(archive/'si-pages09-10-author-blocks.json')
author_deltas=[{'block':b,'row':i+1,'field':fields[j],'old':x,'new':y} for b in oldauthor for i,(old,new) in enumerate(zip(oldauthor[b],author[b])) for j,(x,y) in enumerate(zip(old.split(),new.split())) if x!=y]
expected_deltas=[{'block':'9R','row':13,'field':'Fobs2','old':'60085.61','new':'50085.61'},{'block':'10R','row':24,'field':'Fcal2','old':'216556.06','new':'216566.06'}]
ck(author_deltas==expected_deltas,'Exactly the two source-confirmed author tokens changed')
def leaves_diff(old,new,p=''):
 if isinstance(old,dict)and isinstance(new,dict):
  ck(set(old)==set(new),'Identical object keys '+p)
  return sum([leaves_diff(old[k],new[k],p+'/'+k)for k in old],[])
 if isinstance(old,list)and isinstance(new,list):
  ck(len(old)==len(new),'Identical list size '+p)
  return sum([leaves_diff(x,y,p+'/'+str(i))for i,(x,y)in enumerate(zip(old,new))],[])
 return []if old==new else[[p,old,new]]
typed_deltas=leaves_diff(read(archive/'si-pages09-10-transcription.json'),trans)
expected_typed=[['/rows/57/raw_cells/Fobs2','60085.61','50085.61'],['/rows/57/cells/4/raw_text','60085.61','50085.61'],['/rows/57/cells/4/numeric_value',60085.61,50085.61],['/rows/158/raw_cells/Fcal2','216556.06','216566.06'],['/rows/158/cells/3/raw_text','216556.06','216566.06'],['/rows/158/cells/3/numeric_value',216556.06,216566.06]]
ck(typed_deltas==expected_typed,'Exactly six corresponding raw and typed JSON leaves changed; all other source fields retained')
oldtsv=list(csv.DictReader((archive/'si-pages09-10-reflections.tsv').open(encoding='utf-8',newline=''),delimiter='\t'))
tsv_deltas=leaves_diff(oldtsv,table)
ck(tsv_deltas==[['/57/Fobs2','60085.61','50085.61'],['/158/Fcal2','216556.06','216566.06']],'Exactly two corresponding TSV cells changed')
details=read(R/'si-pages09-10-disagreement-detail-manifest.json')
for a in details:
 bind(a['output'],a['sha256']);base=Image.open(R/'reader-assets'/'si-pages09-10-independent'/a['source_crop']).convert('L');box=a['source_crop_box'];crop=base.crop(box);enlarged=crop.resize((crop.width*2,crop.height*2),Image.Resampling.NEAREST);actual=Image.open(a['output']).convert('L');ck(enlarged.size==actual.size and enlarged.tobytes()==actual.tobytes(),'Unmodified nearest-neighbor source detail '+a['label'])
ck(sha(trans['source_path'])==trans['source_sha256']==assets['source_sha256']==own['source_sha256']==checkpoint['source_pdf_sha256'],'Same original SI PDF');bind(trans['source_path'])
doc=pymupdf.open(trans['source_path']);native={}
for page in [9,10]:
 imgs=doc[page-1].get_images(full=True);ck(len(imgs)==1,'One original page scan '+str(page));native[page]=Image.open(io.BytesIO(doc.extract_image(imgs[0][0])['image'])).convert('L')
for package,owned in [(assets,False),(own,True)]:
 ck(len(package['assets'])==12,'Twelve '+('auditor'if owned else'author')+' assets')
 for a in package['assets']:
  page=a.get('source_pdf_page',a.get('page'));box=a.get('original_image_box',a.get('native_crop_box'));im=native[page]if box is None else native[page].crop(box);actual=Image.open(a['path']).convert('L');ck(actual.size==im.size and actual.tobytes()==im.tobytes(),'Exact original pixels '+Path(a['path']).name);bind(a['path'],a['sha256'])
doc.close();assetby={a['id']:a for a in assets['assets']};rows={r['row_id']:r for r in trans['rows']};tsv={(int(r['page']),r['block'],int(r['row'])):r for r in table};differences=[];manual=[];negative=[];zero=[]
ck(len(rows)==len(table)==sum(len(v)for v in independent.values())==180,'All180 unique rows');ck(all(len(v)==45 for v in independent.values()),'Four45-row blocks');ck(len({c['cell_id']for r in trans['rows']for c in r['cells']})==1260,'1260 unique field IDs')
for block,lines in independent.items():
 page=int(block[:-1]);side=block[-1]
 for n,tokens in enumerate(lines,1):
  rid=f'si-p{page:02d}-{side}-r{n:03d}';r=rows[rid];tab=tsv[(page,side,n)];auth=author[block][n-1].split();ck(len(tokens)==len(auth)==7,'Seven source fields '+rid)
  for field,u,v in zip(fields,tokens,auth):
   if u!=v:differences.append({'row_id':rid,'field':field,'independent_source_reading':u,'author_reading':v})
  if tokens!=auth:continue
  ck(r['hkl']==[int(x)for x in tokens[:3]],'Exact hkl '+rid)
  # Candidate top crop includes rows1–25; auditor crops independently split1–23/24–45.
  crop=f'si-{page:02d}-'+('left'if side=='L'else'right')+('-top'if n<=25 else'-bottom')
  manual.append({'row_id':rid,'pdf_page':page,'printed_page':40+page,'block':side,'row':n,'raw_tokens':tokens,'independent_crop':f'p{page}-{side}'+('top'if n<=23 else'bottom')+'.png','candidate_crop_id':crop,'status':'all seven tokens manually read from native pixels and exactly compared'})
  for field,token,c in zip(fields,tokens,r['cells']):
   cid=rid+'-'+field;e=c['evidence'];ck(token==tab[field]==r['raw_cells'][field]==c['raw_text'],'Exact raw tokens '+cid);ck(c['cell_id']==cid,'Field identity '+cid);ck(c['numeric_value']is None if field=='marker'else Decimal(str(c['numeric_value']))==Decimal(token),'Exact typed decimal '+cid)
   ck(e['pdf_page']==page and e['printed_page']==40+page and e['column_block']==side and e['row_in_block']==n and e['column_key']==field and e['supporting_table']==1,'Cell source locator '+cid)
   ck(e['original_crop_id']==crop and e['original_crop_sha256']==assetby[crop]['sha256'] and e['original_crop_path']==assetby[crop]['path'] and e['source_sha256']==trans['source_sha256'],'Cell crop/source binding '+cid)
   unit_status='not_applicable_index'if field in ['h','k','l']else'not_applicable_marker'if field=='marker'else'unreported';ck(c['unit']is None and c['unit_status']==unit_status,'No invented unit '+cid)
   if field=='Fobs2' and Decimal(token)<=0:(negative if Decimal(token)<0 else zero).append({'cell_id':cid,'raw_text':token,'numeric_value':c['numeric_value']})
  ck(tokens[-1]=='o'and r['cells'][-1]['numeric_value']is None,'Uninterpreted o-like marker '+rid)
dump(R/'si-pages09-10-independent-comparison-final.json',{'author_checkpoint_sha256':expected,'independent_reading_sha256':sha(R/'si-pages09-10-independent-reading-resolved.json'),'differences':differences,'matched_rows':len(manual)})
bind(R/'si-pages09-10-independent-comparison-final.json')
if differences:print(json.dumps({'status':'source_disagreements_require_reinspection','differences':differences}));sys.exit(0)
ck(negative==trans['negative_observations'],'All negative observations preserved');ck(len(zero)==1 and zero[0]['cell_id']=='si-p10-R-r010-Fobs2','Printed zero preserved as numeric zero')
ck(len({tuple(r['hkl'])for r in rows.values()})==180,'Unique reflections within chunk')
prior_names=['si-reflections-transcription.json','si-pages03-04-transcription.json','si-pages05-06-transcription.json','si-pages07-08-transcription.json'];prior=[]
for name in prior_names:
 p=R/name;bind(p);data=read(p);prior+=data['rows'];ck(not {tuple(r['hkl'])for r in data['rows']} & {tuple(r['hkl'])for r in trans['rows']},'No prior reflection duplicate '+name)
ck(prior[-1]['hkl']==[0,12,24] and trans['rows'][0]['hkl']==[2,12,24],'Prior boundary0,12,24 to2,12,24')
sequence=[(r['hkl'][2],r['hkl'][1],r['hkl'][0])for r in trans['rows']];ck(sequence==sorted(sequence),'Printed l/k/h continuity across four blocks without filling missing reflections')
for name in ['si-pages-1-2-independent-audit.json','si-pages-3-4-independent-audit.json','si-pages-5-6-independent-audit.json','si-pages-7-8-independent-audit.json']:bind(R/name)
for p,h in bound.items():ck(sha(p)==h,'Unchanged at audit close '+Path(p).name)
limits=['These are squared reflection amplitudes/intensities, not atomic coordinates, a measured doped unit cell, CIF or DFT structure.','Units and scales of Fcal²/Fobs²/sigma are not printed and remain unknown.','The o-like trailing glyph is retained without verified Unicode or interpretation; not acceptance, numeric zero or success.','The original ©2002 J.Phys.Chem.A/Heo jp0219348 header and printed49–50 are preserved; existing main/SI header discrepancy is not silently repaired.','No author, earlier chunk, source, Site or ledger file was changed by this audit.','Only SI9–10 receive manual numerical approval here. SI11–14 remain outside this audit.']
resolutions=[dict(x,final_author_value=rows[x['row_id']]['raw_cells'][x['field']],status='resolved; final author raw token and typed value rechecked') for x in history['differences']]
out={'schema':'mattersyn-independent-si-numerical-audit/1','source_id':'heo2003','auditor':'/root/norberg2004_extract','transcription_author':trans['author'],'audited_at':datetime.now(timezone.utc).isoformat(),'status':'passed_for_si_pages_9_10_only','author_checkpoint_sha256':expected,'author_manifest_sha256':expected_manifest,'actual_manual_scope':{'pdf_pages':[9,10],'printed_pages':[49,50],'body_rows':180,'numeric_cells':1080,'uninterpreted_marker_cells':180,'own_native_assets_viewed':12,'additional_disagreement_detail_assets_viewed':3,'method':'Independent full manual transcription from twelve own native scan/full-page/header/crop assets before author rows were consulted; every field exactly compared. Three initial disagreements re-read in magnified native pixels: two author corrections and one auditor typing correction. Initial readings retained. Own crops cover1–23top/24–45bottom; author crop locators use1–25top/26–45bottom.','row_checks':manual},'mechanical_scope':{'check_count':len(checks),'checks':checks,'manual_check_count':False,'pixel_verification':'All twelve author and twelve auditor assets exactly equal embedded original PDF scan pixels/crops. The three inspected details are exact nearest-neighbor enlargements of native scan rectangles.'},'negative_observations':negative,'zero_observations':zero,'open_findings':[],'correction_resolution':resolutions,'bound_files':bound,'prior_pages':{'preserved':True,'repeat_manual_audit':False},'full_si_numerical_audit':False,'pages_outside_this_audit':[1,2,3,4,5,6,7,8,11,12,13,14],'limits':limits,'training_eligible':False,'published':False}
out['independent_revision_check']={'initial_author_manifest_sha256':history['initial_author_manifest_sha256'],'author_raw_token_changes':author_deltas,'typed_json_leaf_changes':typed_deltas,'tsv_changes':tsv_deltas,'auditor_typing_change':own_deltas,'unchanged_author_tokens':1258,'comparison_method':'Independent recursive comparison of archived initial and final author JSON/TSV; author delta checker was not used as evidence for these assertions.'}
dump(R/'si-pages-9-10-independent-audit.json',out)
(R/'si-pages-9-10-independent-audit.md').write_text(f'''# Heo SI pages9–10 independent numerical audit

Passed for this two-page chunk only. Independently read all 180 rows, 1,080 numeric cells and 180 uninterpreted o-like markers from original scan pixels before consulting the author values. All {len(negative)} negative Fobs² observations and the one printed zero remain intact.

Three initial disagreements were re-read in native magnified pixels. Two author errors were corrected: page 9 right row 13 Fobs², 60085.61 → 50085.61; page 10 right row 24 Fcal², 216556.06 → 216566.06. The third was an auditor typing error: page 9 right row 22 sigma, 11777.73 → 11177.73; the author value was already correct. Initial readings, comparison and correction history are preserved. The final raw and typed values match the original source.

The original headers, printed pages 49–50, four 45-row blocks and boundary from prior page 8 were checked. All 12 author and 12 independent source assets match native PDF pixels exactly. The three additional inspected details are faithful nearest-neighbor magnifications. The {len(checks)} mechanical checks verify raw tokens, typed decimals, units/missingness, every field locator/hash, prior-file integrity and row uniqueness; this is separate from manual reading.

Author checkpoint SHA256: `{expected}`. Manifest SHA256: `{expected_manifest}`. Exact bound files and per-row readings are in the JSON. SI 11–14 remain outside this audit. Reflection values are not atomic coordinates or a CIF; no training, browser or publication approval is asserted. Earlier chunks and source files remain unchanged.
''',encoding='utf-8')
print(json.dumps({'status':out['status'],'checks':len(checks),'negative':len(negative),'zero':len(zero),'bound_files':len(bound),'audit_sha256':sha(R/'si-pages-9-10-independent-audit.json')}))
