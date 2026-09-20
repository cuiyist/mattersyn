from pathlib import Path
import sys,json,hashlib
sys.dont_write_bytecode=True
sys.path.insert(0,'[local path redacted]')
sys.path.insert(0,'[local path redacted]')
import pymupdf
from PIL import Image,ImageDraw
V=Path(__file__).resolve().parent;m=json.loads((V/'scene-manifest.json').read_text(encoding='utf8'));images=[];geometry=[];diagnostics=[]
for s in m['scenes']:
 d=pymupdf.open(stream=(V/s['file']).read_bytes(),filetype='svg');pdf=pymupdf.open('pdf',d.convert_to_pdf());page=pdf[0]
 assert tuple(page.rect)==(0,0,600,450),(s['file'],page.rect)
 px=page.get_pixmap(matrix=pymupdf.Matrix(1,1),clip=pymupdf.Rect(0,0,600,450),alpha=False);assert(px.width,px.height)==(600,450)
 im=Image.new('RGB',(640,502),'#e5eef2');im.paste(Image.frombytes('RGB',(px.width,px.height),px.samples),(20,32));ImageDraw.Draw(im).text((20,7),s['record_id']+'/'+s['operation_id'],fill='black');images.append(im)
 geometry.append({'scene':s['record_id']+'/'+s['operation_id'],'svg_sha256':s['svg_sha256'],'viewport':[0,0,600,450],'rendered_pixels':[600,450],'full_viewport_retained':True})
 spans=[{'text':x['text'],'bbox':x['bbox'],'size':x['size']}for b in page.get_text('dict')['blocks']if 'lines'in b for l in b['lines']for x in l['spans']]
 diagnostics.append({'scene':s['record_id']+'/'+s['operation_id'],'outside600x450':[x for x in spans if x['bbox'][0]<0 or x['bbox'][2]>600 or x['bbox'][1]<0 or x['bbox'][3]>450]})
for i in range(0,len(images),6):
 sheet=Image.new('RGB',(1280,1506),'#e5eef2')
 for j,im in enumerate(images[i:i+6]):sheet.paste(im,((j%2)*640,(j//2)*502))
 sheet.save(V/'review'/f'scenes-{i//6+1:02d}.png')
report={'status':'passed','module_sha256':m['module_sha256'],'renderer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scene_count':len(images),'scenes':geometry}
(V/'contact-geometry-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
(V/'scene-geometry-diagnostic.json').write_text(json.dumps(diagnostics,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'scenes':len(images),'contact_sheets':(len(images)+5)//6,'overflows':[x for x in diagnostics if x['outside600x450']]},ensure_ascii=False))
