from pathlib import Path
import sys,json
sys.dont_write_bytecode=True
sys.path.insert(0,'[local path redacted]')
sys.path.insert(0,'[local path redacted]')
import pymupdf
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent/'apparatus-review';manifest=json.loads((R/'scene-manifest.json').read_text());items=[];warnings=[]
for e in manifest['rows']:
 raw=(R/e['svg']).read_bytes();doc=pymupdf.open(stream=raw,filetype='svg');pdf=pymupdf.open('pdf',doc.convert_to_pdf());p=pdf[0]
 for b in p.get_text('dict')['blocks']:
  for l in b.get('lines',[]):
   for s in l['spans']:
    x0,y0,x1,y1=s['bbox']
    if x0<0 or x1>600 or y0<0 or y1>408:warnings.append({'record':e['record_id'],'operation':e['operation_id'],'text':s['text'],'bbox':s['bbox']})
 pix=p.get_pixmap(matrix=pymupdf.Matrix(1,1),alpha=False);im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
 can=Image.new('RGB',(620,440),'white');can.paste(im,(10,28));ImageDraw.Draw(can).text((10,6),e['record_id']+' / '+e['operation_id'],fill='black');items.append(can)
for i in range(0,len(items),6):
 sheet=Image.new('RGB',(1240,1320),'#dbe4eb')
 for n,im in enumerate(items[i:i+6]):sheet.paste(im,(n%2*620,n//2*440))
 sheet.save(R/('contact-'+str(i//6+1).zfill(2)+'.png'))
(R/'render-validation.json').write_text(json.dumps({'rendered_all_operations':len(manifest['rows']),'unique_review_frames':len(items),'contact_sheets':(len(items)+5)//6,'out_of_bounds_text':warnings},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'review_frames':len(items),'sheets':(len(items)+5)//6,'text_bounds_warnings':len(warnings)}))
