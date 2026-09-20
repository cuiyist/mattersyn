import sys,json,hashlib,xml.etree.ElementTree as ET,math
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,'[local path redacted]')
sys.path.insert(0,'[local path redacted]')
import pymupdf
from PIL import Image,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parent
inventory=json.loads((OUT/'scene-inventory.json').read_text(encoding='utf-8'))
(OUT/'renders').mkdir(exist_ok=True)
rows=[];seen=set();reps=[]
for row in inventory['operations']:
 if not row['covered']:continue
 path=OUT/row['file'];svg=path.read_bytes();ET.fromstring(svg)
 doc=pymupdf.open(stream=svg,filetype='svg');pdf=pymupdf.open('pdf',doc.convert_to_pdf());page=pdf[0]
 spans=[{'text':s['text'],'bbox':s['bbox']} for b in page.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']]
 overflow=[s for s in spans if s['bbox'][0]<-.5 or s['bbox'][2]>page.rect.width+.5 or s['bbox'][1]<-.5 or s['bbox'][3]>page.rect.height+.5]
 dest=OUT/'renders'/(path.stem+'.png');page.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False).save(dest)
 rows.append({'record_id':row['record_id'],'operation_id':row['operation_id'],'action':row['action'],'render':dest.relative_to(OUT).as_posix(),'render_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'text_spans':spans,'out_of_page_spans':overflow})
 # Keep action representatives plus bare/coated film pairs, distinct aliquot states.
 key=row['action']
 if key not in seen or row['action'] in ['electrospray_omcvd','omcvd_layer','redispersion','cosolvent_addition','dilution','filtration','repeated_precipitation']:
  reps.append((row,Image.open(dest).convert('RGB')));seen.add(key)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
for number in range(math.ceil(len(reps)/6)):
 batch=reps[number*6:number*6+6];sheet=Image.new('RGB',(1240,math.ceil(len(batch)/2)*440),'white');draw=ImageDraw.Draw(sheet)
 for k,(row,im) in enumerate(batch):
  x=(k%2)*620;y=(k//2)*440;im.thumbnail((610,394))
  draw.text((x+8,y+8),row['record_id'].replace('danek-1996-','')+' / '+row['operation_id'],font=font,fill='black');sheet.paste(im,(x+5,y+35))
 sheet.save(OUT/'renders'/f'contact-{number+1}.png')
(OUT/'render-inspection.json').write_text(json.dumps({'renderer':'PyMuPDF SVG to PDF; static only','rows':rows,'representative_count':len(reps),'contact_sheets':math.ceil(len(reps)/6)},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'renders':len(rows),'representatives':len(reps),'contacts':math.ceil(len(reps)/6),'overflow':[{'record_id':r['record_id'],'operation_id':r['operation_id'],'spans':r['out_of_page_spans']} for r in rows if r['out_of_page_spans']]}))
