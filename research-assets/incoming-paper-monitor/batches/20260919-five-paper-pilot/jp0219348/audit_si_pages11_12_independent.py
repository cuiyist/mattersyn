"""Independent native-source reading versus a frozen, separate author chunk."""
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timezone
import sys,json,csv,hashlib,io
sys.dont_write_bytecode=True
sys.path[:0]=[r'[local path redacted]',r'[local path redacted]']
import pymupdf
from PIL import Image
R=Path(__file__).resolve().parent
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
dump=lambda p,x:Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
fields=['h','k','l','Fcal2','Fobs2','sigma_Fobs2','marker'];checks=[];bound={}
def ck(ok,label):
 checks.append({'passed':bool(ok),'label':label})
 if not ok:raise AssertionError(label)
def bind(p,h=None):
 p=Path(p);digest=sha(p);ck(h is None or h==digest,'Frozen hash '+p.name);bound[str(p)]=digest
expected=sys.argv[1];expected_manifest=sys.argv[2]
cp=R/'si-pages11-12-author-checkpoint.json';bind(cp,expected);checkpoint=read(cp)
mp=R/'si-pages11-12-manifest.json';bind(mp,expected_manifest);freeze=read(mp)
trans=read(R/'si-pages11-12-transcription.json');author=read(R/'si-pages11-12-author-blocks.json')
assets=read(R/'si-pages11-12-assets.json');own=read(R/'si-pages11-12-independent-assets.json')
initial_reading=R/'si-pages11-12-independent-reading.json';bind(initial_reading,'87749f4bd8a488749479d039da489794e0c0e4c1e39bb43d8019812dfec59317');independent=read(initial_reading)['blocks']
table=list(csv.DictReader((R/'si-pages11-12-reflections.tsv').open(encoding='utf-8',newline=''),delimiter='\t'))
ck(checkpoint['author']!='/root/norberg2004_extract'and trans['author']==checkpoint['author'],'Distinct author and independent auditor')
ck(trans['pages']==[11,12]and trans['field_order']==fields,'Exact two-page field schema')
ck(not trans['complete_document_transcription']and not trans['training_eligible']and not trans['published'],'No full-document/training/publication assertion')
for category in ['bound_files','bound_original_evidence','preserved_prior_files']:
 for p,h in checkpoint.get(category,{}).items():bind(p,h)
for category in ['files','original_evidence']:
 for p,h in freeze.get(category,{}).items():bind(p,h)
for name in ['si-pages11-12-independent-reading.py','si-pages11-12-independent-assets.json','prepare_si_pages11_12_independent.py','si-pages11-12-independent-detail-manifest.json','prepare_si_pages11_12_details.py','si-pages11-12-source-sign-note.md','si-pages11-12-independent-comparison-initial.json','si-pages11-12-independent-resolution-history.json','preserve_si_pages11_12_findings.py','audit_si_pages11_12_independent.py']:bind(R/name)
history=read(R/'si-pages11-12-independent-resolution-history.json')
bind(history['initial_comparison']['path'],history['initial_comparison']['sha256'])
ck(sha(trans['source_path'])==trans['source_sha256']==assets['source_sha256']==own['source_sha256']==checkpoint['source_pdf_sha256'],'Same original SI PDF');bind(trans['source_path'])
doc=pymupdf.open(trans['source_path']);native={}
for page in [11,12]:
 imgs=doc[page-1].get_images(full=True);ck(len(imgs)==1,'One original page scan '+str(page));native[page]=Image.open(io.BytesIO(doc.extract_image(imgs[0][0])['image'])).convert('L')
for package,owned in [(assets,False),(own,True)]:
 ck(len(package['assets'])==12,'Twelve '+('auditor'if owned else'author')+' assets')
 for a in package['assets']:
  page=a.get('source_pdf_page',a.get('page'));box=a.get('original_image_box',a.get('native_crop_box'));im=native[page]if box is None else native[page].crop(box);actual=Image.open(a['path']).convert('L');ck(actual.size==im.size and actual.tobytes()==im.tobytes(),'Exact original pixels '+Path(a['path']).name);bind(a['path'],a['sha256'])
doc.close()
for a in read(R/'si-pages11-12-independent-detail-manifest.json'):
 bind(a['output'],a['sha256']);base=Image.open(R/'reader-assets'/'si-pages11-12-independent'/a['source_crop']).convert('L');crop=base.crop(a['source_crop_box']);enlarged=crop.resize((crop.width*a['scale'],crop.height*a['scale']),Image.Resampling.NEAREST);actual=Image.open(a['output']).convert('L');ck(enlarged.size==actual.size and enlarged.tobytes()==actual.tobytes(),'Unmodified source detail '+a['label'])
assetby={a['id']:a for a in assets['assets']};rows={r['row_id']:r for r in trans['rows']};tsv={(int(r['page']),r['block'],int(r['row'])):r for r in table}
differences=[];manual=[];negative=[];zero=[];uncertain=[]
source_signs={'si-p11-R-r035-Fobs2':'1965.46','si-p12-L-r012-Fcal2':'3757.09'}
ck(len(rows)==len(table)==sum(len(v)for v in independent.values())==180,'All 180 unique rows');ck(all(len(v)==45 for v in independent.values()),'Four 45-row blocks');ck(len({c['cell_id']for r in trans['rows']for c in r['cells']})==1260,'1,260 unique field IDs')
for block,lines in independent.items():
 page=int(block[:-1]);side=block[-1]
 for n,tokens in enumerate(lines,1):
  rid=f'si-p{page:02d}-{side}-r{n:03d}';r=rows[rid];tab=tsv[(page,side,n)];auth=author[block][n-1].split();ck(len(tokens)==len(auth)==7,'Seven independently read and author fields '+rid)
  ck(r['hkl']==[int(x)for x in tokens[:3]],'Exact hkl '+rid)
  crop=f'si-{page:02d}-'+('left'if side=='L'else'right')+('-top'if n<=25 else'-bottom')
  row_differences=[]
  for field,token,atoken,c in zip(fields,tokens,auth,r['cells']):
   cid=rid+'-'+field;e=c['evidence'];ck(c['cell_id']==cid,'Field identity '+cid)
   ck(atoken==tab[field]==r['raw_cells'][field]==c['raw_text'],'Exact author block/TSV/JSON raw-token agreement '+cid)
   if cid in source_signs:
    # Degraded source prefixes remain uncertain; initial signed readings were provisional.
    ck(c['numeric_value']is None,'Unresolved sign withheld as null signed numeric value')
    digits=source_signs[cid];magnitude=float(digits)
    ck(c['raw_text']=='[sign_unresolved]'+digits and c['visible_digits']==digits,'Clear source digits separated from editorial prefix '+cid)
    ck(c['magnitude_value']==magnitude and c['signed_value_candidates']==[-magnitude,magnitude],'Both signed candidates retained without selecting either '+cid)
    ck(c['sign_status']=='unresolved_from_retained_scan'and c['transcription_status']=='source_sign_unresolved'and c['source_comparison_status']=='visually_compared_sign_unresolved','Unresolved sign not mislabeled verified '+cid)
    ck(c['raw_text_includes_editorial_annotation']is True and 'not printed source text'in c['editorial_annotation']and 'withheld'in c['uncertainty_note'],'Editorial prefix and withheld signed value explicitly explained '+cid)
    uncertain.append({'cell_id':cid,'hkl':r['hkl'],'initial_provisional_auditor_token':token,'final_author_cell':c,'flat_export_token':tab[field]})
   else:
    if token!=c['raw_text']:row_differences.append({'row_id':rid,'field':field,'independent_source_reading':token,'author_reading':c['raw_text']})
    ck(c['numeric_value']is None if field=='marker'else Decimal(str(c['numeric_value']))==Decimal(c['raw_text']),'Exact typed decimal '+cid)
   ck(e['pdf_page']==page and e['printed_page']==40+page and e['column_block']==side and e['row_in_block']==n and e['column_key']==field and e['supporting_table']==1,'Cell source locator '+cid)
   ck(e['original_crop_id']==crop and e['original_crop_sha256']==assetby[crop]['sha256']and e['original_crop_path']==assetby[crop]['path']and e['source_sha256']==trans['source_sha256'],'Cell crop/source binding '+cid)
   ck(e['row_in_selected_crop']==(n if n<=25 else n-24),'Exact row locator within native crop '+cid)
   unit_status='not_applicable_index'if field in ['h','k','l']else'not_applicable_marker'if field=='marker'else'unreported';ck(c['unit']is None and c['unit_status']==unit_status,'No invented unit '+cid)
   if field=='Fobs2'and c['numeric_value']is not None and Decimal(c['raw_text'])<=0:(negative if Decimal(c['raw_text'])<0 else zero).append({'cell_id':cid,'raw_text':c['raw_text'],'numeric_value':c['numeric_value']})
  ck(tokens[-1]=='o'and r['cells'][-1]['numeric_value']is None,'Uninterpreted o-like marker '+rid)
  differences+=row_differences
  manual.append({'row_id':rid,'pdf_page':page,'printed_page':40+page,'block':side,'row':n,'initial_manual_tokens':tokens,'independent_crop':f'p{page}-{side}'+('top'if n<=23 else'bottom')+'.png','candidate_crop_id':crop,'source_sign_exception':rid in ['si-p11-R-r035','si-p12-L-r012'],'exact_resolved_field_match':not row_differences})
comparison={'author_checkpoint_sha256':expected,'author_manifest_sha256':expected_manifest,'independent_reading_sha256':sha(initial_reading),'differences':differences,'matched_rows':sum(not any(d['row_id']==r['row_id']for d in differences)for r in manual),'known_source_sign_exceptions':uncertain}
dump(R/'si-pages11-12-independent-comparison-final.json',comparison);bind(R/'si-pages11-12-independent-comparison-final.json')
if differences:print(json.dumps({'status':'source_disagreements_require_reinspection','differences':differences}));sys.exit(0)
ck(negative==trans['negative_observations'],'All confirmed negative observations preserved');ck(len(negative)==36 and len(zero)==0,'36 confirmed negatives and no observed zero; uncertain sign excluded')
ck(len(uncertain)==2 and {u['cell_id']for u in uncertain}==set(source_signs),'Exactly the two known source sign exceptions are present')
ck(sum(c['numeric_value']is not None for r in trans['rows']for c in r['cells'])==1078,'1,078 resolved numeric values; two signed values withheld')
ck(len({tuple(r['hkl'])for r in rows.values()})==180,'Unique reflections within chunk')
prior_names=['si-reflections-transcription.json','si-pages03-04-transcription.json','si-pages05-06-transcription.json','si-pages07-08-transcription.json','si-pages09-10-transcription.json'];prior=[]
for name in prior_names:
 p=R/name;bind(p);data=read(p);prior+=data['rows'];ck(not {tuple(r['hkl'])for r in data['rows']} & {tuple(r['hkl'])for r in trans['rows']},'No prior reflection duplicate '+name)
ck(prior[-1]['hkl']==[8,14,26]and trans['rows'][0]['hkl']==[10,14,26],'Prior page 10 boundary to page 11 follows printed hkl order')
sequence=[(r['hkl'][2],r['hkl'][1],r['hkl'][0])for r in trans['rows']];ck(sequence==sorted(sequence),'Printed l/k/h continuity across four blocks without filling missing reflections')
for name in ['si-pages-1-2-independent-audit.json','si-pages-3-4-independent-audit.json','si-pages-5-6-independent-audit.json','si-pages-7-8-independent-audit.json','si-pages-9-10-independent-audit.json']:bind(R/name)
archive=R/'si-pages11-12-author-revision-1'
bind(archive/'si-pages11-12-manifest.json',history['initial_author_manifest_sha256'])
bind(archive/'si-pages11-12-author-checkpoint.json',history['initial_author_checkpoint_sha256'])
oldfreeze=read(archive/'si-pages11-12-manifest.json')
for p,h in oldfreeze['files'].items():bind(archive/Path(p).relative_to(R),h)
for p,h in oldfreeze['original_evidence'].items():bind(p,h)
bind(R/'si-pages11-12-correction-history.json','acc86e4637b1ae04b9ba4941093506a70f9fdf5fa9aad8ebec8edaf19d204894')
author_history=read(R/'si-pages11-12-correction-history.json')
for category in ['prior_files','corrected_files']:
 for p,h in author_history[category].items():bind(p,h)
def block_deltas(old,new):
 ck(set(old)==set(new),'Same block universe for revision')
 for k in old:ck(len(old[k])==len(new[k])==45,'Same 45 rows in revision '+k)
 return [{'block':b,'row':i+1,'field':fields[j],'old':x,'new':y}for b in old for i,(before,after)in enumerate(zip(old[b],new[b]))for j,(x,y)in enumerate(zip(before.split(),after.split()))if x!=y]
oldauthor=read(archive/'si-pages11-12-author-blocks.json')
author_deltas=block_deltas(oldauthor,author)
expected_deltas=[{'block':'11R','row':33,'field':'sigma_Fobs2','old':'7604.83','new':'7694.83'},{'block':'12L','row':12,'field':'Fcal2','old':'3757.09','new':'[sign_unresolved]3757.09'}]
ck(author_deltas==expected_deltas,'Exactly one corrected digit token and one explicit source-sign qualification; 1,258 tokens unchanged')
prefreeze=read(archive/'si-pages11-12-author-prefreeze-reading/si-pages11-12-author-blocks.json')
prefreeze_deltas=block_deltas(prefreeze,oldauthor)
ck(prefreeze_deltas==[{'block':'11R','row':35,'field':'Fobs2','old':'1965.46','new':'[sign_unresolved]1965.46'}],'Historical first sign qualification is the only prefreeze token change')
oldtsv=list(csv.DictReader((archive/'si-pages11-12-reflections.tsv').open(encoding='utf-8',newline=''),delimiter='\t'))
ck(len(oldtsv)==len(table)==180,'Same TSV row universe')
tsv_deltas=[[i,k,old[k],new[k]]for i,(old,new)in enumerate(zip(oldtsv,table))for k in old if old[k]!=new[k]]
ck(tsv_deltas==[[77,'sigma_Fobs2','7604.83','7694.83'],[101,'Fcal2','3757.09','[sign_unresolved]3757.09']],'Exact two TSV fields changed, including explicit nonnumeric unknown-sign export')
oldtrans=read(archive/'si-pages11-12-transcription.json');restored=json.loads(json.dumps(trans))
restored['rows'][77]['raw_cells']['sigma_Fobs2']=oldtrans['rows'][77]['raw_cells']['sigma_Fobs2']
for k in ['raw_text','numeric_value']:restored['rows'][77]['cells'][5][k]=oldtrans['rows'][77]['cells'][5][k]
restored['rows'][101]['raw_cells']['Fcal2']=oldtrans['rows'][101]['raw_cells']['Fcal2']
restored['rows'][101]['cells'][3]=oldtrans['rows'][101]['cells'][3]
for k in ['status','counts','unresolved_numeric_tokens_in_chunk']:restored[k]=oldtrans[k]
restored['policies']['uncertain_sign']=oldtrans['policies']['uncertain_sign']
ck(restored==oldtrans,'Restoring only approved correction/uncertainty scopes reconstructs the entire initial transcription exactly')
ck(trans['counts']=={'rows':180,'numeric_cells':1080,'resolved_numeric_cells':1078,'unresolved_sign_cells':2,'markers':180,'total_cells':1260,'unambiguously_negative_Fobs2':36,'zero_Fobs2':0},'Accurate final counts')
ck(trans['status']=='author_source_compared_two_signs_unresolved_independent_numerical_audit_pending','Current status explicitly preserves two uncertain signs')
ck(len(trans['unresolved_numeric_tokens_in_chunk'])==2 and trans['unresolved_numeric_tokens_in_chunk'][0]==oldtrans['unresolved_numeric_tokens_in_chunk'][0],'Original sign uncertainty unchanged; exactly one second uncertainty added')
for entry in trans['unresolved_numeric_tokens_in_chunk']:
 c=next(c for r in trans['rows']for c in r['cells']if c['cell_id']==entry['cell_id'])
 for key in ['cell_id','visible_digits','raw_text','numeric_value','magnitude_value','signed_value_candidates','evidence']:ck(entry[key]==c[key],'Uncertainty summary links exact source cell '+entry['cell_id']+' '+key)
 ck(entry['reason']==c['uncertainty_note'],'Uncertainty summary preserves reason '+entry['cell_id'])
ck('Two clear magnitudes'in trans['policies']['uncertain_sign']and'null'in trans['policies']['uncertain_sign']and'neither token may be parsed as a positive measurement'in trans['policies']['uncertain_sign'],'Dataset policy withholds both uncertain signs')
for p,h in bound.items():ck(sha(p)==h,'Unchanged at audit close '+Path(p).name)
limits=[
 'Two source signs remain unresolved. Neither signed numeric value is approved: Fobs² magnitude 1965.46 at SI11R35 and Fcal² magnitude 3757.09 at SI12L12. Both signs remain candidates and numeric_value is null.',
 'The [sign_unresolved] prefix is editorial, not a verbatim source glyph. Exact clear digits, original crops and uncertainty notes are retained.',
 'Only SI pages 11–12 were independently read in this audit. Pages 13–14 remain outside this audit; prior pages 1–10 were preserved and hash-checked, not re-audited visually here.',
 'These are reflection indices and squared structure factors/uncertainties, not atomic coordinates, a CIF or a DFT-ready crystal structure.',
 'The unheaded o-like marker is retained without interpretation or verified Unicode; it is not numeric zero, acceptance or success.',
 'Original ©2002 ACS/J. Phys. Chem. A/Heo jp0219348 headings and printed pages 51–52 are retained; the known main/SI header discrepancy is not silently repaired.',
 'No units/scales, signs, missing reflections or symmetry expansion were inferred. No source, author, prior-chunk, Site or ledger file was changed by this auditor.'
]
source_findings=[{'cell_id':u['cell_id'],'type':'source_sign_uncertainty','status':'unresolved in retained source; correctly preserved and signed value withheld','visible_digits':u['final_author_cell']['visible_digits'],'numeric_value':None,'signed_value_candidates':u['final_author_cell']['signed_value_candidates'],'evidence':u['final_author_cell']['evidence']}for u in uncertain]
out={'schema':'mattersyn-independent-si-numerical-audit/1','source_id':'heo2003','auditor':'/root/norberg2004_extract','transcription_author':trans['author'],'audited_at':datetime.now(timezone.utc).isoformat(),'status':'passed_for_si_pages_11_12_with_two_explicit_source_sign_uncertainties','author_checkpoint_sha256':expected,'author_manifest_sha256':expected_manifest,
 'actual_manual_scope':{'pdf_pages':[11,12],'printed_pages':[51,52],'body_rows':180,'numeric_cell_positions_read':1080,'resolved_signed_numeric_values':1078,'clear_magnitudes_with_unresolved_sign':2,'uninterpreted_marker_cells':180,'own_native_assets_viewed':12,'additional_native_detail_assets_viewed':3,'method':'Independently read and typed every body cell from native scan crops before consulting author row values; both original headers/full-page scans and all eight body crops viewed. Three details were magnified from unchanged native pixels. One author digit typo corrected, two degraded source signs explicitly withheld. Independent initial readings and comparison remain unchanged.','row_checks':manual},
 'mechanical_scope':{'check_count':len(checks),'checks':checks,'manual_check_count':False,'pixel_verification':'All twelve author and twelve auditor source assets equal original embedded scan pixels/crops; all three details are exact nearest-neighbor magnifications.'},
 'negative_observations':negative,'zero_observations':zero,'open_transcription_findings':[],'unresolved_source_findings':source_findings,'open_findings':source_findings,'correction_resolution':{'author_digit_error':{'cell_id':'si-p11-R-r033-sigma_Fobs2','before':'7604.83','after':'7694.83','status':'source-confirmed and final raw/typed fields rechecked'},'source_sign_qualifications':source_findings,'initial_independent_provisional_signs_retained':True,'initial_positive_interpretation_of_p12_L12_source_sign_note_superseded_by_explicit_uncertainty':True},
 'independent_revision_check':{'initial_author_manifest_sha256':history['initial_author_manifest_sha256'],'author_raw_token_changes':author_deltas,'prefreeze_sign_qualification':prefreeze_deltas,'tsv_changes':tsv_deltas,'unchanged_tokens_since_first_freeze':1258,'whole_transcription_restoration':'Restoring only row77 sigma raw/numeric fields, row101 Fcal raw/qualified-cell metadata and corresponding top-level status/counts/uncertainty policy/list reproduces initial JSON exactly. Semantic checks independently validate all changed final fields. Author validation output is bound for provenance, not used as independent evidence.'},
 'bound_files':bound,'prior_pages':{'preserved':True,'repeat_manual_audit':False},'full_si_numerical_audit':False,'pages_outside_this_audit':[1,2,3,4,5,6,7,8,9,10,13,14],'limits':limits,'training_eligible':False,'published':False}
dump(R/'si-pages-11-12-independent-audit.json',out)
(R/'si-pages-11-12-independent-audit.md').write_text(f'''# Heo SI pages 11–12 independent numerical audit

Passed for this chunk with two explicitly preserved source-sign uncertainties. All 180 rows, 1,080 numeric positions and 180 o-like markers were independently read from native scan pixels before consulting the author values. There are 1,078 resolved numeric values, 36 definite negative Fobs² observations and no printed zero observations.

One definite author digit error was corrected: page 11 right row 33, hkl (5,11,27), sigma(Fobs²), **7604.83 → 7694.83**. A native magnified detail confirms the correction.

Two degraded prefixes remain unresolved: Fobs² magnitude **1965.46** at page 11 right row 35 and Fcal² magnitude **3757.09** at page 12 left row 12. Both signed numeric values are null. Each record retains the clear digits, ± candidates, original source crop and explicitly editorial `[sign_unresolved]` flat-export token. Neither sign is approved or inferred from physics. Initial provisional auditor readings and the author's archived revisions are preserved; the initial positive interpretation of the page 12 speck is explicitly superseded.

All 12 author and 12 independent scan assets equal original PDF pixels. All three inspected details are faithful nearest-neighbor enlargements. The {len(checks):,} mechanical checks verify typed values, raw tokens, source locators, original pixels, exact revisions and prior-file hashes separately from the manual reading. Exactly one digit token and one new sign qualification changed since the first freeze; the other 1,258 tokens and the original page 11 sign qualification remained unchanged. There are no open transcription corrections; two source uncertainties remain.

Final manifest SHA256: `{expected_manifest}`. Author checkpoint SHA256: `{expected}`. The JSON contains the exact bound files and per-row audit.

Earlier pages 1–10 and all sources remain unchanged. SI pages 13–14 remain outside this audit. This is no claim of complete SI review, atomic coordinates/CIF, training eligibility or website publication.
''',encoding='utf-8')
print(json.dumps({'status':out['status'],'checks':len(checks),'negative':len(negative),'zero':len(zero),'uncertain_signs':2,'bound_files':len(bound),'audit_sha256':sha(R/'si-pages-11-12-independent-audit.json')}))
