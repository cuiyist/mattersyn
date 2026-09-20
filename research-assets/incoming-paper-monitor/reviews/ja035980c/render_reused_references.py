from pathlib import Path
import sys,json
sys.path.insert(0,'[local path redacted]')
sys.path.insert(0,'[local path redacted]')
import pymupdf
from PIL import Image,ImageDraw
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas/dist/assets/chemical-registry';V=B/'visuals/review'
entries=json.loads((B/'visuals/reused-reference-audit-input.json').read_text(encoding='utf8'))['entries'];tiles=[]
for eid,row in entries.items():
 e=row['entry'];src=pymupdf.open(str(S/e['svgPath']));doc=pymupdf.open('pdf',src.convert_to_pdf());pix=doc[0].get_pixmap(matrix=pymupdf.Matrix(1,1));im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples);im.thumbnail((680,340));tile=Image.new('RGB',(700,390),'white');tile.paste(im,((700-im.width)//2,35+(340-im.height)//2));ImageDraw.Draw(tile).text((10,10),eid,fill='black');tiles.append(tile)
for start in range(0,len(tiles),6):
 sheet=Image.new('RGB',(1400,1170),'#eeeeee')
 for j,t in enumerate(tiles[start:start+6]):sheet.paste(t,((j%2)*700,(j//2)*390))
 sheet.save(V/f'reused-contact-{start//6+1}.png')
print(len(tiles))
