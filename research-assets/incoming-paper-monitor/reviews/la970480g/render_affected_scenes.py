from pathlib import Path
import sys,json,hashlib
sys.dont_write_bytecode=True
sys.path.insert(0,'[local path redacted]');sys.path.insert(0,'[local path redacted]')
import pymupdf
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent/'apparatus-review';p=R/'correction-validation.json';d=json.loads(p.read_text());warn=[]
for c in d['changes']:
 doc=pymupdf.open(stream=(R/c['svg']).read_bytes(),filetype='svg');pdf=pymupdf.open('pdf',doc.convert_to_pdf());page=pdf[0]
 for b in page.get_text('dict')['blocks']:
  for l in b.get('lines',[]):
   for s in l['spans']:
    if s['bbox'][0]<0 or s['bbox'][2]>600 or s['bbox'][1]<0 or s['bbox'][3]>408:warn.append({'scene':c['svg'],'span':s})
 pix=page.get_pixmap(alpha=False);im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);can=Image.new('RGB',(620,440),'white');can.paste(im,(10,28));ImageDraw.Draw(can).text((10,6),c['record_id']+' / '+c['operation_id'],fill='black')
 sh=R/c['contact_sheet'];sheet=Image.open(sh).convert('RGB');n=c['index']%6;sheet.paste(can,(n%2*620,n//2*440));sheet.save(sh);c['contact_sheet_sha256']=hashlib.sha256(sh.read_bytes()).hexdigest()
d['rendered_changes']=len(d['changes']);d['text_bounds_warnings']=warn;p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'changed_renders':len(d['changes']),'out_of_bounds':len(warn)}))
