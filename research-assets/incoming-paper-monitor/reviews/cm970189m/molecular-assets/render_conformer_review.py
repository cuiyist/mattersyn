"""Read-only projections of actual JSON coordinates for private visual review."""
import json,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parent
models=json.loads((OUT/'molecules-3d-additions.json').read_text(encoding='utf-8'))
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
colors={'H':'#efefef','C':'#484848','N':'#3562d7','O':'#dc514b','S':'#cdb83f','Cl':'#59a754'}
for page in range(math.ceil(len(models)/6)):
 batch=models[page*6:page*6+6];canvas=Image.new('RGB',(1800,440*math.ceil(len(batch)/3)),'white');d=ImageDraw.Draw(canvas)
 for n,m in enumerate(batch):
  x0=n%3*600;y0=n//3*440;d.text((x0+12,y0+8),m['name'],font=font,fill='black');d.text((x0+12,y0+36),m['method'],font=small,fill='#555555')
  pts=[]
  for a in m['atoms']:
   x,y,z=a['x'],a['y'],a['z'];xx=x*math.cos(.47)+z*math.sin(.47);zz=-x*math.sin(.47)+z*math.cos(.47);yy=y*math.cos(.36)-zz*math.sin(.36);z2=y*math.sin(.36)+zz*math.cos(.36);pts.append((xx,yy,z2))
  xs=[p[0] for p in pts];ys=[p[1] for p in pts];scale=min(530/max(max(xs)-min(xs),.1),280/max(max(ys)-min(ys),.1))
  pos=[(x0+300+(p[0]-(max(xs)+min(xs))/2)*scale,y0+228-(p[1]-(max(ys)+min(ys))/2)*scale) for p in pts]
  for b in m['bonds']:d.line([pos[b['a']],pos[b['b']]],fill='#86929b',width=4)
  for i in sorted(range(len(pts)),key=lambda i:pts[i][2]):
   a=m['atoms'][i];x,y=pos[i];radius=8 if a['element']=='H' else 13
   d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=colors.get(a['element'],'#aaaaaa'),outline='#4a4a4a',width=1)
   label='D' if a['isotope']==2 and a['element']=='H' else a['element'] if a['element'] not in ['C','H'] else ''
   if label:d.text((x-5,y-8),label,font=small,fill='white' if a['element'] in ['N','O'] else 'black')
  d.text((x0+12,y0+407),'Computed illustration; not measured geometry or surface binding.',font=small,fill='#555555')
 canvas.save(OUT/'review'/f'conformer-contact-{page+1:02}.png')
print(len(models))
