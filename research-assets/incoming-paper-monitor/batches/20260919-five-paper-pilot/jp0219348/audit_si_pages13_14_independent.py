"""Scoped independent native-source audit of the final two scanned SI pages."""
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
expected,expected_manifest=sys.argv[1:3]
cp=R/'si-pages13-14-author-checkpoint.json';bind(cp,expected);checkpoint=read(cp)
mp=R/'si-pages13-14-manifest.json';bind(mp,expected_manifest);freeze=read(mp)
trans=read(R/'si-pages13-14-transcription.json');author=read(R/'si-pages13-14-author-blocks.json');assets=read(R/'si-pages13-14-assets.json');own=read(R/'si-pages13-14-independent-assets.json')
initial=R/'si-pages13-14-independent-reading.json';bind(initial,'ea9c690a9a498506e812c6f1a5596ce43930fb463421a5d4b15e8e9b14714cc6');independent=read(initial)['blocks']
table=list(csv.DictReader((R/'si-pages13-14-reflections.tsv').open(encoding='utf-8',newline=''),delimiter='\t'))
ck(checkpoint['author']!='/root/norberg2004_extract'and trans['author']==checkpoint['author'],'Distinct author and auditor')
ck(trans['pages']==[13,14]and trans['field_order']==fields,'Exact two-page field schema')
ck(not trans['complete_document_transcription']and not trans['training_eligible']and not trans['published'],'No complete-SI/training/publication claim in chunk')
for category in ['bound_files','bound_original_evidence','preserved_prior_files']:
 for p,h in checkpoint.get(category,{}).items():bind(p,h)
for category in ['files','original_evidence']:
 for p,h in freeze.get(category,{}).items():bind(p,h)
for name in ['si-pages13-14-independent-reading.py','si-pages13-14-independent-assets.json','prepare_si_pages13_14_independent.py','si-pages13-14-independent-detail-manifest.json','prepare_si_pages13_14_details.py','si-pages13-14-independent-source-notes.md','audit_si_pages13_14_independent.py']:bind(R/name)
ck(sha(trans['source_path'])==trans['source_sha256']==assets['source_sha256']==own['source_sha256']==checkpoint['source_pdf_sha256']=='3b2e262af1932ed04cfddd596958c92d89c37099ab9dad8c4ce1f11254d4acc6','Original SI source identity unchanged');bind(trans['source_path'])
doc=pymupdf.open(trans['source_path']);ck(len(doc)==14,'Original PDF has fourteen pages; current scope is final two only');native={}
for page in [13,14]:
 imgs=doc[page-1].get_images(full=True);ck(len(imgs)==1,'One original scan '+str(page));native[page]=Image.open(io.BytesIO(doc.extract_image(imgs[0][0])['image'])).convert('L')
for package,owned in [(assets,False),(own,True)]:
 ck(len(package['assets'])==(10 if owned else 12),'Exact author/auditor asset count')
 for a in package['assets']:
  page=a.get('source_pdf_page',a.get('page'));box=a.get('original_image_box',a.get('native_crop_box'));im=native[page]if box is None else native[page].crop(box);actual=Image.open(a['path']).convert('L');ck(actual.size==im.size and actual.tobytes()==im.tobytes(),'Exact original pixels '+Path(a['path']).name);bind(a['path'],a['sha256'])
doc.close()
details=read(R/'si-pages13-14-independent-detail-manifest.json')
for a in details:
 bind(a['output'],a['sha256']);base=Image.open(R/'reader-assets'/'si-pages13-14-independent'/a['source_crop']).convert('L');crop=base.crop(a['source_crop_box']);enlarged=crop.resize((crop.width*a['scale'],crop.height*a['scale']),Image.Resampling.NEAREST);actual=Image.open(a['output']).convert('L');ck(enlarged.size==actual.size and enlarged.tobytes()==actual.tobytes(),'Unmodified native detail '+a['label'])
assetby={a['id']:a for a in assets['assets']};rows={r['row_id']:r for r in trans['rows']};tsv={(int(r['page']),r['block'],int(r['row'])):r for r in table}
differences=[];manual=[];negative=[];zero=[]
ck(len(rows)==len(table)==sum(len(v)for v in independent.values())==139,'All139 unique rows')
ck({k:len(v)for k,v in independent.items()}=={k:len(v)for k,v in author.items()}=={'13L':45,'13R':45,'14L':25,'14R':24},'Unequal final blocks retained exactly')
ck(len({c['cell_id']for r in trans['rows']for c in r['cells']})==973,'973 unique field IDs')
for block,lines in independent.items():
 page=int(block[:-1]);side=block[-1]
 for n,tokens in enumerate(lines,1):
  rid=f'si-p{page:02d}-{side}-r{n:03d}';r=rows[rid];tab=tsv[(page,side,n)];auth=author[block][n-1].split();ck(len(tokens)==len(auth)==7,'Seven fields '+rid)
  ck(r['hkl']==[int(x)for x in tokens[:3]],'Exact hkl '+rid)
  crop=f'si-{page:02d}-'+('left'if side=='L'else'right')+('-top'if n<=25 else'-bottom');row_differences=[]
  for field,token,atoken,c in zip(fields,tokens,auth,r['cells']):
   cid=rid+'-'+field;e=c['evidence'];ck(c['cell_id']==cid,'Field identity '+cid)
   ck(atoken==tab[field]==r['raw_cells'][field]==c['raw_text'],'Author block/TSV/JSON consistency '+cid)
   if token!=c['raw_text']:row_differences.append({'row_id':rid,'field':field,'independent_source_reading':token,'author_reading':c['raw_text']})
   ck(c['numeric_value']is None if field=='marker'else Decimal(str(c['numeric_value']))==Decimal(c['raw_text']),'Exact typed decimal '+cid)
   ck(e['pdf_page']==page and e['printed_page']==40+page and e['column_block']==side and e['row_in_block']==n and e['column_key']==field and e['supporting_table']==1,'Cell source locator '+cid)
   ck(e['original_crop_id']==crop and e['original_crop_sha256']==assetby[crop]['sha256']and e['original_crop_path']==assetby[crop]['path']and e['source_sha256']==trans['source_sha256'],'Cell crop/source binding '+cid)
   ck(e['row_in_selected_crop']==(n if n<=25 else n-24),'Exact native crop row '+cid)
   unit_status='not_applicable_index'if field in ['h','k','l']else'not_applicable_marker'if field=='marker'else'unreported';ck(c['unit']is None and c['unit_status']==unit_status,'No invented unit '+cid)
   if field=='Fobs2'and Decimal(c['raw_text'])<=0:(negative if Decimal(c['raw_text'])<0 else zero).append({'cell_id':cid,'raw_text':c['raw_text'],'numeric_value':c['numeric_value']})
  ck(tokens[-1]=='o'and r['cells'][-1]['numeric_value']is None,'Uninterpreted o-like marker '+rid)
  differences+=row_differences
  owncrop=f'p{page}-{side}'+(('top'if n<=23 else'bottom')if page==13 else'body')+'.png'
  manual.append({'row_id':rid,'pdf_page':page,'printed_page':40+page,'block':side,'row':n,'independent_manual_tokens':tokens,'independent_crop':owncrop,'candidate_crop_id':crop,'exact_field_match':not row_differences})
comparison={'author_checkpoint_sha256':expected,'author_manifest_sha256':expected_manifest,'independent_reading_sha256':sha(initial),'differences':differences,'matched_rows':sum(r['exact_field_match']for r in manual)}
dump(R/'si-pages13-14-independent-comparison.json',comparison);bind(R/'si-pages13-14-independent-comparison.json')
if differences:print(json.dumps({'status':'source_disagreements_require_reinspection','differences':differences}));sys.exit(0)
ck(negative==trans['negative_observations'],'All negative observations preserved');ck(len(negative)==22 and not zero,'22 negative Fobs² values and no observed zeros')
ck(sum(c['numeric_value']is not None for r in trans['rows']for c in r['cells'])==834,'834 resolved numeric values in this chunk')
ck(len({tuple(r['hkl'])for r in rows.values()})==139,'Unique reflection rows in chunk')
prior_names=['si-reflections-transcription.json','si-pages03-04-transcription.json','si-pages05-06-transcription.json','si-pages07-08-transcription.json','si-pages09-10-transcription.json','si-pages11-12-transcription.json'];prior=[]
for name in prior_names:
 p=R/name;bind(p);data=read(p);prior+=data['rows'];ck(not {tuple(r['hkl'])for r in data['rows']} & {tuple(r['hkl'])for r in trans['rows']},'No prior reflection duplicate '+name)
ck(prior[-1]['hkl']==[12,14,28]and trans['rows'][0]['hkl']==[14,14,28],'Prior page12 to page13 boundary')
ck(trans['rows'][-1]['hkl']==[5,27,29],'Actual final source row retained without inferred continuation')
sequence=[(r['hkl'][2],r['hkl'][1],r['hkl'][0])for r in trans['rows']];ck(sequence==sorted(sequence),'Printed l/k/h order without expansion or padding')
for name in ['si-pages-1-2-independent-audit.json','si-pages-3-4-independent-audit.json','si-pages-5-6-independent-audit.json','si-pages-7-8-independent-audit.json','si-pages-9-10-independent-audit.json','si-pages-11-12-independent-audit.json']:bind(R/name)
bind(R/'si-pages11-12-transcription.json','63783076a86e0c0ddeadaa03cb42016b1fcb7522839e4f23bb3f7957e48dfb96')
bind(R/'si-pages-11-12-independent-audit.json','bb87e62d1b76d8eb7351c876a7830508d504072e6f193d8ddf851871f5d8b031')
previous=read(R/'si-pages11-12-transcription.json')
for cid,mag in [('si-p11-R-r035-Fobs2',1965.46),('si-p12-L-r012-Fcal2',3757.09)]:
 c=next(c for r in previous['rows']for c in r['cells']if c['cell_id']==cid);ck(c['numeric_value']is None and c['signed_value_candidates']==[-mag,mag]and c['sign_status']=='unresolved_from_retained_scan','Prior source sign uncertainty untouched '+cid)
for p,h in bound.items():ck(sha(p)==h,'Unchanged at audit close '+Path(p).name)
limits=[
 'Only SI pages13–14 receive new manual numerical audit here. The preceding pages and their audits are preserved/hash-checked, not re-audited in this scope. This report does not certify the complete SI.',
 'Prior unresolved signs at SI11R35 Fobs² and SI12L12 Fcal² remain null with both signed candidates; this final chunk does not resolve them.',
 'The squared structure-factor values and reflection indices are not atomic coordinates, a CIF, atom occupancies or an exact structure–recipe pair.',
 'Printed ©2002 ACS/J.Phys.Chem.A/Heo jp0219348 headers and printed pages53–54 are retained; the previously documented main/SI identity caveat is not repaired by this audit.',
 'No units/scales, missing reflections, symmetry copies or interpretation of the unheaded o-like markers were inferred.',
 'No source, author, prior-chunk, Site, ledger, memory or GitHub file was changed by this independent audit.'
]
out={'schema':'mattersyn-independent-si-numerical-audit/1','source_id':'heo2003','auditor':'/root/norberg2004_extract','transcription_author':trans['author'],'audited_at':datetime.now(timezone.utc).isoformat(),'status':'passed_for_si_pages_13_14_only','author_checkpoint_sha256':expected,'author_manifest_sha256':expected_manifest,
 'actual_manual_scope':{'pdf_pages':[13,14],'printed_pages':[53,54],'body_rows':139,'rows_by_block':{'13L':45,'13R':45,'14L':25,'14R':24},'numeric_cells':834,'uninterpreted_marker_cells':139,'own_native_assets_viewed':10,'additional_native_detail_assets_viewed':len(details),'method':'Every body field independently read and typed from native source pixels before opening author transcription; two full-page scans and duplicated headers, four native body crops for page13 and two complete body crops for page14 viewed. Final table extent and blank area/footer inspected. All manual tokens then compared with frozen author blocks, TSV and typed JSON.','row_checks':manual},
 'mechanical_scope':{'check_count':len(checks),'checks':checks,'manual_check_count':False,'pixel_verification':'All twelve author and ten auditor source assets exactly match original embedded PDF scan pixels/crops. The separately inspected detail is a faithful nearest-neighbor enlargement.'},
 'negative_observations':negative,'zero_observations':zero,'open_findings':[],'correction_resolution':[],'native_mark_inspection':{'cell_id':'si-p14-R-r016-Fobs2','read_value':'2613.68','reason':'The separated speck is near digit tops, above the position of a normal minus glyph; numeric reading was based on original pixels rather than expected physics.','detail_path':details[0]['output']},
 'bound_files':bound,'prior_pages':{'preserved':True,'repeat_manual_audit':False,'both_known_unresolved_signs_preserved':True},'full_si_numerical_audit':False,'pages_outside_this_audit':[1,2,3,4,5,6,7,8,9,10,11,12],'limits':limits,'training_eligible':False,'published':False}
dump(R/'si-pages-13-14-independent-audit.json',out)
(R/'si-pages-13-14-independent-audit.md').write_text(f'''# Heo SI pages 13–14 independent numerical audit

Passed for these two pages only. Independently read all **139 rows, 834 numeric fields and 139 uninterpreted o-like markers** from the original scan before opening the author transcription. The four blocks contain 45, 45, 25 and 24 rows. All 22 negative Fobs² values are retained; no observed zero appears in this chunk. No correction was required after comparison.

The original PDF hash, both headers, printed pages 53–54, boundary from page 12, final hkl (5,27,29), blank area below the last table and source footer were checked. All 12 author and 10 auditor original assets match native source pixels exactly. One separately magnified pre-digit speck at page 14 right row 16 lies near the digit tops rather than at the minus-sign position; 2613.68 is retained from that glyph inspection.

The {len(checks):,} mechanical checks verify every raw token, typed decimal, source locator, crop/hash, row uniqueness and prior-file integrity separately from the manual reading. Final manifest SHA256: `{expected_manifest}`. Author checkpoint SHA256: `{expected}`. The JSON lists exact bound files and per-row readings.

SI pages 1–12 and their prior audits remain unchanged. Both unresolved signs on pages 11–12 remain null with candidate values; this audit does not resolve them. This report does not certify complete SI review, an atomic-coordinate structure, exact structure–recipe pairing, training eligibility or website publication.
''',encoding='utf-8')
print(json.dumps({'status':out['status'],'rows':139,'numeric':834,'markers':139,'checks':len(checks),'negative':len(negative),'zero':len(zero),'bound_files':len(bound),'audit_sha256':sha(R/'si-pages-13-14-independent-audit.json')}))
