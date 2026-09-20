from pathlib import Path
import sys,json
sys.path.insert(0,r'[local path redacted]')
import fitz
B=Path(__file__).resolve().parent
prep=json.loads((B/'source-preparation.json').read_text('utf-8'))
for item in prep['documents'][:2]:
 d=fitz.open(item['source_path'])
 for i,p in enumerate(d):
  print(item['role_candidate'],i+1,tuple(p.rect),'images',[(tuple(round(v,1) for v in x['bbox'])) for x in p.get_image_info()])
  for b in p.get_text('blocks'):
   if any(s in b[4] for s in ['Figure','Scheme','Table','Representative Conversion','References']):print('caption',tuple(round(v,1) for v in b[:4]),b[4][:150].replace('\n',' '))
