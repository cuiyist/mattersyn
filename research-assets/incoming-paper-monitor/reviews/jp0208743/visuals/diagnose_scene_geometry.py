from pathlib import Path
import sys,json
sys.path.insert(0,'[local path redacted]')
import pymupdf as fitz
V=Path(__file__).resolve().parent;m=json.loads((V/'scene-manifest.json').read_text(encoding='utf8'));results=[]
for s in m['scenes']:
 raw=(V/s['file']).read_bytes();d=fitz.open(stream=raw,filetype='svg');pdf=fitz.open('pdf',d.convert_to_pdf());page=pdf[0];px=page.get_pixmap(alpha=False)
 spans=[{'text':x['text'],'bbox':x['bbox'],'size':x['size']}for b in page.get_text('dict')['blocks']if 'lines'in b for l in b['lines']for x in l['spans']]
 results.append({'scene':s['record_id']+'/'+s['operation_id'],'svg_doc_page':list(d[0].rect),'pdf_mediabox':list(page.mediabox),'pixmap':[px.width,px.height],'outside600x420':[x for x in spans if x['bbox'][0]<0 or x['bbox'][2]>600 or x['bbox'][1]<0 or x['bbox'][3]>420],'title_spans':[x for x in spans if x['size']>=20]})
(V/'scene-geometry-diagnostic.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'unique_svg_sizes':sorted(set(tuple(x['svg_doc_page'])for x in results)),'unique_pixmaps':sorted(set(tuple(x['pixmap'])for x in results)),'overflows':[x for x in results if x['outside600x420']]},ensure_ascii=False))
