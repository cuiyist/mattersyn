from pathlib import Path
import sys,json,hashlib,io
sys.dont_write_bytecode=True
sys.path.insert(0,r'[local path redacted]');sys.path.insert(0,r'[local path redacted]')
import pymupdf
from PIL import Image
R=Path(__file__).resolve().parent;O=R/'reader-assets/si-pages13-14-independent';O.mkdir(exist_ok=True);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=json.loads((R/'source-inventory.json').read_text(encoding='utf-8'))['source_documents']['si'];assert sha(s['path'])==s['sha256']=='3b2e262af1932ed04cfddd596958c92d89c37099ab9dad8c4ce1f11254d4acc6';doc=pymupdf.open(s['path']);assert len(doc)==14;assets=[]
for p in [13,14]:
 images=doc[p-1].get_images(full=True);assert len(images)==1;im=Image.open(io.BytesIO(doc.extract_image(images[0][0])['image'])).convert('L');w,h=Image.open(R/f'si-{p:02}.png').size
 boxes=[('native',None),('header',(195,180,900,234))]
 boxes+= [('Ltop',(205,234,544,704)),('Lbottom',(205,684,544,1140)),('Rtop',(568,234,900,704)),('Rbottom',(568,684,900,1140))]if p==13 else [('Lbody',(205,234,544,746)),('Rbody',(568,234,900,746))]
 for name,box in boxes:
  bb=None if box is None else [round(box[0]*im.width/w),round(box[1]*im.height/h),round(box[2]*im.width/w),round(box[3]*im.height/h)];pic=im if bb is None else im.crop(bb);dest=O/f'p{p}-{name}.png';pic.save(dest);assets.append({'page':p,'printed_page':40+p,'path':str(dest),'sha256':sha(dest),'native_image_size':list(im.size),'native_crop_box':bb,'operation':'Independent lossless embedded-image extraction and rectangular crop only.'})
(R/'si-pages13-14-independent-assets.json').write_text(json.dumps({'auditor':'/root/norberg2004_extract','source_path':s['path'],'source_sha256':s['sha256'],'source_pdf_page_count':len(doc),'assets':assets},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'assets':len(assets),'source_pdf_page_count':len(doc)}))
