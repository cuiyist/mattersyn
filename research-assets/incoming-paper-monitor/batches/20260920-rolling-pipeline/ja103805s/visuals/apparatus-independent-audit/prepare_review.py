from pathlib import Path
import sys,json,hashlib,xml.etree.ElementTree as ET
O=Path(__file__).resolve().parent;B=O.parents[1];V=O.parent/'apparatus/v1';ROOT=B.parents[4]
sys.path.insert(0,str(ROOT/'research-assets/corpus-20260917/runtime'));sys.path.insert(0,str(ROOT/'research-assets/rdkit-runtime'))
import pymupdf
from PIL import Image,ImageDraw,ImageFont
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(V/'package-freeze.json')=='474a21a8b43326cc94058063c040019aa68810567a5c2592186f997c85e41025'
f=read(V/'package-freeze.json')
for x in f['files']:assert sha(V/x['path'])==x['sha256']
for sub in ['previews','contacts']:(O/sub).mkdir(parents=True,exist_ok=True)
scenes=read(V/'rendered-scenes.json');images=[]
for idx,s in enumerate(scenes):
 p=V/'svg'/(s['operation_id']+'.svg');svg=p.read_bytes();doc=pymupdf.open(stream=svg,filetype='svg');out=O/'previews'/(s['operation_id']+'.png');doc[0].get_pixmap(matrix=pymupdf.Matrix(1,1),alpha=False).save(out)
 images.append({'index':idx+1,'operation_id':s['operation_id'],'source_svg':str(p),'source_sha256':sha(p),'preview_path':str(out),'preview_sha256':sha(out),'visible_text':[''.join(t.itertext()) for t in ET.fromstring(svg).iter() if t.tag.endswith('text')]})
contacts=[]
for i in range(0,len(images),6):
 members=images[i:i+6];canvas=Image.new('RGB',(1800,2400),'#e8eff5');draw=ImageDraw.Draw(canvas)
 for j,x in enumerate(members):
  im=Image.open(x['preview_path']);im.thumbnail((870,760));px=(j%2)*900+15;py=(j//2)*800+20;canvas.paste(im,(px,py));draw.text((px,py+765),str(x['index'])+' '+x['operation_id'],fill='#123047')
 p=O/'contacts'/f'contact-{i//6+1}.png';canvas.save(p);contacts.append({'path':str(p),'sha256':sha(p),'operation_ids':[x['operation_id'] for x in members]})
(O/'independent-render-manifest.json').write_text(json.dumps({'author':'/root/norberg2004_extract','role':'independent audit visualization','source_freeze_sha256':sha(V/'package-freeze.json'),'renderer':'PyMuPDF native SVG rasterization, without changing source SVGs','scenes':images,'contacts':contacts},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'scenes':len(images),'contacts':len(contacts)}))
