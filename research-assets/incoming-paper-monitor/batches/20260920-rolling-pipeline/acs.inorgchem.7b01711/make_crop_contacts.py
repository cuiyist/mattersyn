"""Private contact sheets for author inspection of original selected crops."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageOps
P=Path(__file__).resolve().parent
assets=json.loads((P/'original-assets-manifest.json').read_bytes())['assets']
out=P/'private'/'crop-checks';out.mkdir(parents=True,exist_ok=True)
for start in range(0,len(assets),4):
    canvas=Image.new('RGB',(1800,2400),'#dddddd');draw=ImageDraw.Draw(canvas)
    for i,a in enumerate(assets[start:start+4]):
        x=(i%2)*900;y=(i//2)*1200
        with Image.open(a['path'])as im:
            resized=ImageOps.contain(im,(880,1150))
            canvas.paste(resized,(x+10+(880-resized.width)//2,y+35))
        draw.text((x+15,y+10),a['id']+' '+a['sha256'][:12],fill='black')
    path=out/f'contact-{start//4+1:02}.png';canvas.save(path);print(path)
