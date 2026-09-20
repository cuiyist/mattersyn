"""Lossless original-scan extraction for private SI table transcription."""
from pathlib import Path
from datetime import datetime, timezone
import sys,json,hashlib,io
sys.dont_write_bytecode=True
sys.path.insert(0,r'[local path redacted]')
sys.path.insert(0,r'[local path redacted]')
import pymupdf
from PIL import Image
B=Path(__file__).resolve().parent; O=B/'reader-assets'/'si-numerical';O.mkdir(exist_ok=True)
I=json.loads((B/'source-inventory.json').read_text(encoding='utf-8')); d=I['source_documents']['si']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(d['path'])==d['sha256']
doc=pymupdf.open(d['path']); entries=[]
for page in [1,2]:
    pg=doc[page-1]; imgs=pg.get_images(full=True);assert len(imgs)==1
    image=doc.extract_image(imgs[0][0]);im=Image.open(io.BytesIO(image['image'])).convert('L')
    p=O/f'si-{page:02d}-native.png';im.save(p)
    entries.append({'id':f'si-{page:02d}-native','source_pdf_page':page,'printed_page':40+page,'source_sha256':d['sha256'],
        'path':str(p),'sha256':sha(p),'width':im.width,'height':im.height,'operation':'Lossless extraction of embedded original monochrome scan; no resampling or numeral editing.'})
    # Boxes specified in the existing 1033 x 1381 page-render coordinate system.
    boxes=[('header',(190,145,850,316)),('left-top',(211,325,517,754)),('left-bottom',(211,749,517,1178)),
           ('right-top',(575,325,875,754)),('right-bottom',(575,749,875,1178))] if page==1 else [
           ('header',(205,195,860,235)),('left-top',(205,250,515,738)),('left-bottom',(205,734,515,1207)),
           ('right-top',(570,250,865,738)),('right-bottom',(570,734,865,1207))]
    for label,box in boxes:
        native=[round(box[0]*im.width/1033),round(box[1]*im.height/1381),round(box[2]*im.width/1033),round(box[3]*im.height/1381)]
        q=O/f'si-{page:02d}-{label}.png';im.crop(native).save(q)
        entries.append({'id':f'si-{page:02d}-{label}','source_pdf_page':page,'printed_page':40+page,'source_sha256':d['sha256'],
            'path':str(q),'sha256':sha(q),'original_image_box':native,'original_image_size':[im.width,im.height],
            'operation':'Rectangular crop of losslessly extracted scan; no resampling or content reconstruction.'})
(B/'si-numerical-assets.json').write_text(json.dumps({'schema':'mattersyn-si-numerical-evidence/1','created_at':datetime.now(timezone.utc).isoformat(),
    'source_id':'heo2003','source_path':d['path'],'source_sha256':d['sha256'],'assets':entries},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'assets':len(entries),'pages_extracted':[1,2],'sha256':d['sha256']}))
