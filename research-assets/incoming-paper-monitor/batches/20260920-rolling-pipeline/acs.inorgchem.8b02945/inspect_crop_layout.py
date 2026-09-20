from pathlib import Path
import sys,json
sys.path.insert(0,'[local path redacted]')
import fitz
P=Path(__file__).resolve().parent
r=fitz.open('[local path redacted]')
out=[]
for j,p in enumerate(r,1):
 if j<3:continue
 blocks=[]
 for b in p.get_text('dict',flags=0)['blocks']:
  if b['type']!=0:continue
  spans=[s for line in b['lines']for s in line['spans']if s['text'].strip()]
  tx=' '.join(s['text']for s in spans)
  if tx.startswith('Figure'):
   boxes=[s['bbox']for s in spans];blocks.append({'box':[min(z[0]for z in boxes),min(z[1]for z in boxes),max(z[2]for z in boxes),max(z[3]for z in boxes)],'text':tx})
 out.append({'page':j,'size':[p.rect.width,p.rect.height],'blocks':blocks})
(P/'source-render/crop-layout.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print([(x['page'],[(b['text'][:14],round(b['box'][1]/792,3),round(b['box'][3]/792,3))for b in x['blocks']])for x in out])
