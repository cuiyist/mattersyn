import sys,json,math,re
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,'[local path redacted]')
sys.path.insert(0,'[local path redacted]')
import pymupdf
from PIL import Image,ImageDraw,ImageFont
out=Path(__file__).resolve().parent/'apparatus-review'
manifest=json.loads((out/'manifest.json').read_text(encoding='utf-8'))
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
images=[];warnings=[]
for row in manifest['files']:
 p=out/row['file'];d=pymupdf.open(stream=p.read_bytes(),filetype='svg');pdf=pymupdf.open('pdf',d.convert_to_pdf());page=pdf[0]
 for block in page.get_text('dict')['blocks']:
  for line in block.get('lines',[]):
   for span in line['spans']:
    x0,y0,x1,y1=span['bbox']
    if x0<0 or x1>page.rect.width or y0<0 or y1>page.rect.height:warnings.append({'file':p.name,'text':span['text'],'bbox':span['bbox']})
 pix=page.get_pixmap(matrix=pymupdf.Matrix(1.2,1.2),alpha=False)
 im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
 imagepath=p.with_suffix('.png');im.save(imagepath)
 images.append((row,im))
for i in range(math.ceil(len(images)/6)):
 batch=images[6*i:6*i+6];sheet=Image.new('RGB',(1440,520*math.ceil(len(batch)/2)),'white');draw=ImageDraw.Draw(sheet)
 for n,(r,im) in enumerate(batch):
  x=n%2*720;y=n//2*520
  draw.text((x+8,y+5),r['recordId'].removeprefix('dabbousi-1997-')+' / '+r['operationId'],font=font,fill='black')
  sheet.paste(im,(x,y+35))
 sheet.save(out/f'contact-{i+1:02}.png')
(out/'render-validation.json').write_text(json.dumps({'status':'passed' if not warnings else 'review_required','rendered':len(images),'textOutsideBounds':warnings},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'rendered':len(images),'textOutsideBounds':warnings}))
