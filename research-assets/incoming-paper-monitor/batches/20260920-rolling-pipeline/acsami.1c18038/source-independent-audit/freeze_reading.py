from pathlib import Path
import hashlib,json,datetime,sys,subprocess
P=Path(__file__).resolve().parents[1]
ROOT=Path('[local path redacted]')
sys.path.insert(0,str(ROOT/'research-assets/corpus-20260917/runtime'))
import pymupdf
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def bound(p): return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
sources=[]; coverage=[]
for role,suffix,count,expected in [('main','',8,'4a351221c8398d31f804d2af3d9f8327931c43e6e275e481ce84d7a67522a692'),('si','_si_1',26,'a98d80fda37e0d7fd148e5da33b318ba382dd179117613c80f04b01c52659bf4')]:
    p=ROOT/'downloaded_papers'/f'10.1021_acsami.1c18038{suffix}.pdf'
    b=bound(p); assert b['sha256']==expected
    with pymupdf.open(p) as doc: assert len(doc)==count
    sources.append({**b,'role':role,'pdf_pages':count})
    for n in range(1,count+1):
        coverage.append({'role':role,'pdf_page':n,'text_read':True,'image_visually_inspected':True,'reader':'/root/norberg2004_extract','text':bound(P/'private/text'/f'{role}-{n:02d}.txt'),'render':bound(P/'source-render'/f'{role}-{n:02d}.png')})
roots=[ROOT/'downloaded_papers',Path('[local path redacted]')]
files=subprocess.run(['rg','--files',*[str(p) for p in roots]],capture_output=True,text=True,check=True).stdout.splitlines()
matches=[p for p in files if '1c18038' in p.lower()]
d={'schema':'mattersyn.independent_source_reading.v1','paper_doi':'10.1021/acsami.1c18038','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'auditor':'/root/norberg2004_extract','author':'/root/backlog_eta','status':'independent_reading_complete_extraction_comparison_pending','independence':{'author_scientific_typed_extraction_opened':False,'source_derived_text_and_images_reused':True},'sources':sources,'actual_page_coverage':coverage,'counts':{'main_pages_text_read_and_viewed':8,'si_pages_text_read_and_viewed':26,'total':34,'si_tables':9,'si_figures':15,'main_numbered_figures':5,'main_schemes':1},'local_attachment_search':{'method':'rg --files then case-insensitive filename substring 1c18038 (also matches am1c18038)','roots':[str(p) for p in roots],'matching_paths':matches,'declared_zip_found':False,'declared_mp4_found':False,'scope':'Local filenames only; online availability not assessed.'},'reading_notes':bound(P/'source-independent-audit/independent-reading-v1.md'),'restrictions':['No source-extraction pass before frozen author comparison','No canonical, viewer, training, exact-pair, integration or publication approval','Partial non-H bulk atomic tables are present; missing original crystal ZIP does not mean no source coordinates exist'],'next_action':'Compare immutable full extraction against these independently recorded source readings and source pixels, including every typed table cell.'}
out=P/'source-independent-audit/independent-reading-v1.json'
assert not out.exists(), 'Preserve first independent reading checkpoint'
out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'path':str(out),'sha256':sha(out),'page_count':len(coverage),'local_matches':matches}))
