from pathlib import Path
import sys,json,hashlib,xml.etree.ElementTree as ET
A=Path(__file__).resolve().parent
ROOT=Path(r'[local path redacted]')
sys.path.insert(0,str(ROOT/'research-assets/corpus-20260917/runtime'))
sys.path.insert(0,str(ROOT/'research-assets/rdkit-runtime'))
import pymupdf
from PIL import Image,ImageDraw,ImageFont
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for sub in ['previews','contacts']:(A/sub).mkdir(exist_ok=True)
images=[]
for s in json.loads((A/'rendered-scenes.json').read_text(encoding='utf-8')):
 p=A/'svg'/(s['kind']+'.svg');doc=pymupdf.open(stream=p.read_bytes(),filetype='svg');out=A/'previews'/(s['kind']+'.png');doc[0].get_pixmap(matrix=pymupdf.Matrix(1.2,1.2),alpha=False).save(out)
 texts=[''.join(e.itertext()) for e in ET.fromstring(p.read_bytes()).iter() if e.tag.endswith('text')]
 art=A/'svg'/(s['kind']+'--art.svg');adoc=pymupdf.open(stream=art.read_bytes(),filetype='svg');aout=A/'previews'/(s['kind']+'--art.png');adoc[0].get_pixmap(matrix=pymupdf.Matrix(1.8,1.8),alpha=False).save(aout)
 images.append({'art_svg_path':str(art.relative_to(A)),'art_svg_sha256':sha(art),'art_png_path':str(aout.relative_to(A)),'art_png_sha256':sha(aout),'scene_id':s['kind'],'record_id':s['record_id'],'operation_id':s['operation_id'],'svg_path':str(p.relative_to(A)),'svg_sha256':sha(p),'png_path':str(out.relative_to(A)),'png_sha256':sha(out),'width':Image.open(out).width,'height':Image.open(out).height,'visible_text':texts})
contacts=[]
for start in range(0,len(images),4):
 group=images[start:start+4];canvas=Image.new('RGB',(1920,2500),'#e6eef4');d=ImageDraw.Draw(canvas)
 for j,item in enumerate(group):
  im=Image.open(A/item['png_path']);im.thumbnail((930,1190));x=(j%2)*960+15;y=(j//2)*1250+20;canvas.paste(im,(x,y));d.text((x,y+1200),str(start+j+1)+' '+item['scene_id'],fill='#123047')
 out=A/'contacts'/f'contact-{start//4+1}.png';canvas.save(out);contacts.append({'path':str(out.relative_to(A)),'sha256':sha(out),'scene_ids':[x['scene_id'] for x in group]})
artcontacts=[]
for start in range(0,len(images),6):
 group=images[start:start+6];canvas=Image.new('RGB',(1800,1760),'#e6eef4');d=ImageDraw.Draw(canvas)
 for j,item in enumerate(group):
  im=Image.open(A/item['art_png_path']);im.thumbnail((570,795));x=(j%3)*600+15;y=(j//3)*880+15;canvas.paste(im,(x,y));d.text((x,y+808),str(start+j+1)+' '+item['operation_id'],fill='#123047');d.text((x,y+827),item['record_id'],fill='#123047')
 out=A/'contacts'/f'art-contact-{start//6+1}.png';canvas.save(out);artcontacts.append(dict(path=str(out.relative_to(A)),sha256=sha(out),scene_ids=[x['scene_id']for x in group]))
write(A/'preview-manifest.json',{'author':'/root/norberg2004_extract','renderer':'PyMuPDF SVG rasterization at 1.2× scale; contact sheets resized only','scene_count':len(images),'scenes':images,'contacts':contacts,'art_contacts':artcontacts,'visual_review_status':'pending_actual_author_inspection'})
print(json.dumps({'scenes':len(images),'contacts':len(contacts)}))
