from pathlib import Path
import sys,json,hashlib
O=Path(__file__).resolve().parent
assert not(O/'package-freeze.json').exists()
sys.path.insert(0,r'[local path redacted]')
sys.path.insert(0,r'[local path redacted]')
import pymupdf
from PIL import Image,ImageDraw
rows=[]
for p in sorted((O/'svg').glob('*.svg')):
 doc=pymupdf.open(stream=p.read_bytes(),filetype='svg');out=O/'previews'/(p.stem+'.png');doc[0].get_pixmap(alpha=False).save(str(out));doc.close()
 rows.append({'svg':str(p),'svg_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'png':str(out),'png_sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
for start in range(0,len(rows),3):
 batch=rows[start:start+3];can=Image.new('RGB',(1100,len(batch)*680),'white')
 for i,row in enumerate(batch):can.paste(Image.open(row['png']),(0,i*680))
 can.save(O/f'contact-{start//3+1:02}.png')
(O/'render-receipt.json').write_text(json.dumps({'renderer':'PyMuPDF '+pymupdf.__version__,'rows':rows,'actual_visual_review':'pending'},indent=2)+'\n',encoding='utf8')
print(len(rows))
