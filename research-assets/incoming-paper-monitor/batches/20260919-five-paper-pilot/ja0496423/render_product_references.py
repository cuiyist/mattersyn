from pathlib import Path
import sys,json,hashlib
B=Path(__file__).resolve().parent
RESEARCH=B.parents[3]
sys.path.insert(0,str(RESEARCH/'corpus-20260917/runtime'))
import pymupdf
sys.path.insert(0,str(RESEARCH/'rdkit-runtime'))
from PIL import Image,ImageDraw,ImageFont
V=B/'visuals/products';P=V/'previews';P.mkdir(exist_ok=True)
rows=[]
for path in sorted((V/'svg').glob('*.svg')):
    doc=pymupdf.open(stream=path.read_bytes(),filetype='svg')
    target=P/(path.stem+'.png')
    doc[0].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False).save(str(target))
    doc.close()
    rows.append({'path':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'source_svg_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
canvas=Image.new('RGB',(1680,1500),'white')
draw=ImageDraw.Draw(canvas);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
for i,item in enumerate(rows):
    im=Image.open(item['path']);im.thumbnail((830,475))
    x=(i%2)*840;y=(i//2)*500
    canvas.paste(im,(x,y+25));draw.text((x+8,y+4),Path(item['path']).stem,font=font,fill='#234254')
contact=P/'contact.png';canvas.save(contact)
(V/'preview-manifest.json').write_text(json.dumps({'previews':rows,'contact_sheet':str(contact),'contact_sha256':hashlib.sha256(contact.read_bytes()).hexdigest()},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'previews':len(rows),'contact_sheet':str(contact)}))
