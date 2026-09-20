from pathlib import Path
import sys,json,hashlib
sys.dont_write_bytecode=True
sys.path.insert(0,'[local path redacted]')
sys.path.insert(0,'[local path redacted]')
import pymupdf
from PIL import Image,ImageDraw
V=Path(__file__).resolve().parent
m=json.loads((V/'scene-manifest.json').read_text(encoding='utf8'));images=[];geometry=[]
tile_width,tile_height=640,472
paste_x,paste_y=20,32
for s in m['scenes']:
 d=pymupdf.open(stream=(V/s['file']).read_bytes(),filetype='svg')
 pdf=pymupdf.open('pdf',d.convert_to_pdf())
 page=pdf[0]
 assert tuple(page.rect)==(0,0,600,420),('Unexpected SVG viewport',s['file'],page.rect)
 px=page.get_pixmap(matrix=pymupdf.Matrix(1,1),clip=pymupdf.Rect(0,0,600,420),alpha=False)
 assert(px.width,px.height)==(600,420)
 assert paste_x+px.width<=tile_width and paste_y+px.height<=tile_height
 im=Image.new('RGB',(tile_width,tile_height),'#e5eef2')
 im.paste(Image.frombytes('RGB',(px.width,px.height),px.samples),(paste_x,paste_y))
 ImageDraw.Draw(im).text((paste_x,7),s['record_id']+'/'+s['operation_id'],fill='black')
 images.append(im)
 geometry.append({'scene':s['record_id']+'/'+s['operation_id'],'svg_sha256':s['svg_sha256'],'viewport':[0,0,600,420],'rendered_pixels':[px.width,px.height],'paste_origin':[paste_x,paste_y],'tile_pixels':[tile_width,tile_height],'full_viewport_retained':True})
for i in range(0,len(images),6):
 sheet=Image.new('RGB',(tile_width*2,tile_height*3),'#dde8ee')
 for j,im in enumerate(images[i:i+6]):sheet.paste(im,(j%2*tile_width,j//2*tile_height))
 sheet.save(V/'review'/f'scenes-{i//6+1:02d}.png')
(V/'contact-geometry-validation.json').write_text(json.dumps({'status':'passed','module_sha256':m['module_sha256'],'renderer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scene_count':len(geometry),'scenes':geometry},indent=2)+'\n',encoding='utf8')
print(f'{len(images)} scenes rendered in {(len(images)+5)//6} contact sheets')
