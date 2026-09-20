"""Static audit projections of the actual JSON coordinates; no geometry changes."""
import json,math,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parent
FONT=Path('C:/Windows/Fonts/arial.ttf')
font=ImageFont.truetype(str(FONT),20)
small=ImageFont.truetype(str(FONT),16)
models=json.loads((OUT/'molecules-3d-additions.json').read_text(encoding='utf-8'))
canvas=Image.new('RGB',(1400,920),'white');draw=ImageDraw.Draw(canvas)
colors={'H':'#eeeeee','C':'#444444','N':'#3157d4','Zn':'#7e8d9c','Se':'#dd9a3a'}
for n,m in enumerate(models):
    x0=(n%2)*700;y0=(n//2)*460
    draw.text((x0+18,y0+15),m['name']+' · computed illustration',font=font,fill='black')
    note='ETKDG only: no complete Zn force field' if m['id']=='diethylzinc' else m['method']
    draw.text((x0+18,y0+44),note,font=small,fill='#555555')
    pts=[]
    ay=.62;ax=.41
    for a in m['atoms']:
        x,y,z=a['x'],a['y'],a['z'];xx=x*math.cos(ay)+z*math.sin(ay);zz=-x*math.sin(ay)+z*math.cos(ay)
        yy=y*math.cos(ax)-zz*math.sin(ax);zz2=y*math.sin(ax)+zz*math.cos(ax)
        pts.append([xx,yy,zz2])
    minx=min(p[0] for p in pts);maxx=max(p[0] for p in pts);miny=min(p[1] for p in pts);maxy=max(p[1] for p in pts)
    scale=min(590/max(maxx-minx,.1),320/max(maxy-miny,.1))
    xy=[(x0+350+(p[0]-(minx+maxx)/2)*scale,y0+255-(p[1]-(miny+maxy)/2)*scale) for p in pts]
    for b in m['bonds']:draw.line([xy[b['a']],xy[b['b']]],fill='#7b8490',width=5)
    for i in sorted(range(len(pts)),key=lambda i:pts[i][2]):
        a=m['atoms'][i];x,y=xy[i];radius=10 if a['element']=='H' else 17
        draw.ellipse((x-radius,y-radius,x+radius,y+radius),fill=colors[a['element']],outline='#4a4a4a',width=1)
        if a['element'] not in ['C','H']:
            box=draw.textbbox((0,0),a['element'],font=small)
            draw.text((x-(box[2]-box[0])/2,y-10),a['element'],font=small,fill='white' if a['element']=='N' else 'black')
    draw.text((x0+18,y0+427),'Projection of JSON coordinates; not experimental geometry or to scale.',font=small,fill='#555555')
canvas.save(OUT/'review/computed-models-contact-sheet.png')
print(str(OUT/'review/computed-models-contact-sheet.png'))
