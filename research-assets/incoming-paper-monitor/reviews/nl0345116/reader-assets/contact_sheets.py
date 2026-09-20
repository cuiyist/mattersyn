from pathlib import Path
from PIL import Image,ImageDraw
import json
O=Path(__file__).resolve().parent;m=json.loads((O/'crop-manifest.json').read_text(encoding='utf8'))
for page,start in enumerate(range(0,len(m['assets']),4),1):
 group=m['assets'][start:start+4];canvas=Image.new('RGB',(1600,2000),'#d9dfe8');draw=ImageDraw.Draw(canvas)
 for j,a in enumerate(group):
  x=(j%2)*800;y=(j//2)*1000;im=Image.open(O/a['relative_asset']).convert('RGB');im.thumbnail((780,955));canvas.paste(im,(x+(800-im.width)//2,y+35));draw.text((x+12,y+10),a['id'],fill='black')
 canvas.save(O/f'contact-{page}.png')
