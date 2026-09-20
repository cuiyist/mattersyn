from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
import json
B=Path(__file__).resolve().parent;A=B/'reader-assets';O=B/'crop-review';O.mkdir(exist_ok=True)
items=json.loads((A/'crop-manifest.json').read_text(encoding='utf-8'))['assets']
for offset in range(0,len(items),4):
 sheet=Image.new('RGB',(1600,1700),'#e4edf3')
 for i,a in enumerate(items[offset:offset+4]):
  im=Image.open(A/a['relative_asset']).convert('RGB');im.thumbnail((780,795))
  x=i%2*800;y=i//2*850;sheet.paste(im,(x+(800-im.width)//2,y+40))
  ImageDraw.Draw(sheet).text((x+15,y+10),a['id']+' | '+str(a['source_pdf_page']),fill='black')
 sheet.save(O/f'contact-{offset//4+1}.jpg',quality=92)
print(len(items),'source crops in',len(list(O.glob('contact-*.jpg'))),'inspection sheets')
