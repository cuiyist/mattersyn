from pathlib import Path
import sys,json
sys.dont_write_bytecode=True
sys.path.insert(0,'[local path redacted]')
sys.path.insert(0,'[local path redacted]')
import pymupdf
from PIL import Image,ImageDraw
V=Path(__file__).resolve().parent
m=json.loads((V/'scene-manifest.json').read_text(encoding='utf8'));images=[]
for s in m['scenes']:
 d=pymupdf.open(stream=(V/s['file']).read_bytes(),filetype='svg')
 pdf=pymupdf.open('pdf',d.convert_to_pdf())
 px=pdf[0].get_pixmap(matrix=pymupdf.Matrix(1,1),alpha=False)
 im=Image.new('RGB',(620,450),'white')
 im.paste(Image.frombytes('RGB',(px.width,px.height),px.samples),(10,32))
 ImageDraw.Draw(im).text((10,7),s['record_id']+'/'+s['operation_id'],fill='black')
 images.append(im)
for i in range(0,len(images),6):
 sheet=Image.new('RGB',(1240,1350),'#dde8ee')
 for j,im in enumerate(images[i:i+6]):sheet.paste(im,(j%2*620,j//2*450))
 sheet.save(V/'review'/f'scenes-{i//6+1:02d}.png')
print(f'{len(images)} scenes rendered in {(len(images)+5)//6} contact sheets')
