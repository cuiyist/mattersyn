import argparse,json,re,hashlib,sys
from pathlib import Path
from datetime import datetime,timezone
O=Path(__file__).resolve().parent;P=O/'private'
sys.stdout.reconfigure(encoding='utf-8')
D=json.loads((P/'source-inputs.json').read_text(encoding='utf-8'))
ap=argparse.ArgumentParser();ap.add_argument('rank',type=int);ap.add_argument('--role',choices=['main','si']);ap.add_argument('--pages');ap.add_argument('--render',action='store_true');a=ap.parse_args()
s=next(x for x in D['scopes'] if x['rank']==a.rank)
events=[]
for key in s['file_keys']:
 f=D['files'][key]
 if a.role and f['historical_role']!=a.role:continue
 raw=Path(f['cached_text_path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==f['cached_text_sha256']
 parts=re.split(r'--- PAGE (\d+) ---',raw.decode('utf-8'))
 pages={int(parts[i]):parts[i+1] for i in range(1,len(parts),2)}
 print('\nSOURCE',key,f['source_sha256'],'TOTAL_PAGES',f['page_count'])
 if a.pages:
  wanted=[int(x) for x in a.pages.split(',')]
  for pno in wanted:
   t=pages[pno];print('\nPDF PAGE',pno,'\n'+'\n'.join(x.strip() for x in t.splitlines()))
   events.append({'file_key':key,'source_sha256':f['source_sha256'],'page':pno,'kind':'full_cached_page_text_displayed','characters':len(t)})
   if a.render:
    import pypdfium2 as pdfium
    pdf=pdfium.PdfDocument(f['source_path']);out=P/f"{f['source_sha256'][:12]}-p{pno:03d}.png";pdf[pno-1].render(scale=1.7).to_pil().save(out);pdf.close();print('RENDER',str(out))
 else:
  t='\n'.join(x.strip() for x in pages[1].splitlines())[:1800];print('IDENTITY_EXCERPT\n'+t)
  events.append({'file_key':key,'source_sha256':f['source_sha256'],'page':1,'kind':'identity_excerpt_displayed','characters':len(t)})
  hits={}
  for pno,t in pages.items():
   lines=[x.strip() for x in t.splitlines() if re.search(r'(experimental|synthesis|preparation|methods|diffraction|crystal structure|XRD|X-ray|TEM)',x,re.I)]
   if lines:hits[pno]=lines[:8]
  print('MACHINE_PAGE_INDEX',json.dumps(hits,ensure_ascii=False))
  events.append({'file_key':key,'source_sha256':f['source_sha256'],'kind':'machine_search_index_only','indexed_pages':len(pages),'does_not_count_as_full_page_read':True})
with (P/'read-events.jsonl').open('a',encoding='utf-8') as log:
 for e in events:log.write(json.dumps({'timestamp':datetime.now(timezone.utc).isoformat(),'scope_rank':a.rank,**e},ensure_ascii=False)+'\n')
