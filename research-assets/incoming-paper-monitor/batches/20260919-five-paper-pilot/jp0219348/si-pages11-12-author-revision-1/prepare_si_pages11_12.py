"""Extract native source scan pixels for the separately scoped SI 11-12 chunk."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,io
sys.dont_write_bytecode=True
sys.path.insert(0,'[local path redacted]')
sys.path.insert(0,'[local path redacted]')
import pymupdf
from PIL import Image
B=Path(__file__).resolve().parent;O=B/'reader-assets/si-numerical-pages11-12'
O.mkdir(exist_ok=False)
d=json.loads((B/'source-inventory.json').read_text(encoding='utf8'))['source_documents']['si']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(d['path'])==d['sha256']
preserve={str(p):sha(p) for p in B.iterdir() if p.is_file() and p.suffix in ['.json','.tsv','.md'] and not p.name.startswith('si-pages11-12')}
doc=pymupdf.open(d['path']);assets=[]
for page in [11,12]:
 pg=doc[page-1];embedded=pg.get_images(full=True);assert len(embedded)==1
 im=Image.open(io.BytesIO(doc.extract_image(embedded[0][0])['image'])).convert('L')
 rw,rh=Image.open(B/f'si-{page:02d}.png').size
 for label,box in [('native',None),('header',(190,180,895,235)),('left-top',(207,236,537,730)),('left-bottom',(207,708,537,1189)),('right-top',(570,236,895,730)),('right-bottom',(570,708,895,1189))]:
  bbox=None if box is None else [round(box[0]*im.width/rw),round(box[1]*im.height/rh),round(box[2]*im.width/rw),round(box[3]*im.height/rh)]
  crop=im if bbox is None else im.crop(bbox);p=O/f'si-{page:02d}-{label}.png';crop.save(p)
  assets.append({'id':p.stem,'path':str(p),'sha256':sha(p),'source_pdf_page':page,'printed_page':40+page,'source_sha256':d['sha256'],'original_image_box':bbox,'original_image_size':[im.width,im.height],'pixels':[crop.width,crop.height],'operation':'Lossless embedded source-scan extraction and rectangular crop only; no numeral editing or interpolation.'})
out={'schema':'mattersyn-si-numerical-evidence/1','author':'/root/peng1998_reader_assets','created_at':datetime.now(timezone.utc).isoformat(),'source_id':'heo2003','source_path':d['path'],'source_sha256':d['sha256'],'assets':assets}
(B/'si-pages11-12-assets.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
(B/'si-pages11-12-preserved-inputs.json').write_text(json.dumps(preserve,indent=2)+'\n',encoding='utf8')
print(json.dumps({'pages':[11,12],'assets':len(assets),'source_sha256':d['sha256'],'preserved_files':len(preserve)}))
