from pathlib import Path
import sys,json,hashlib
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;ROOT=O.parents[6]
sys.path[:0]=[str(ROOT/'research-assets/corpus-20260917/runtime'),str(ROOT/'research-assets/rdkit-runtime')]
import pymupdf
from PIL import Image,ImageDraw
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((O/'scene-manifest.json').read_text());out=[];(O/'review').mkdir(exist_ok=True)
for row in manifest['scenes']:
 p=O/row['svg_file'];assert sha(p)==row['svg_sha256'];doc=pymupdf.open(stream=p.read_bytes(),filetype='svg');q=O/'review'/f'{row["scene_kind"]}.png';doc[0].get_pixmap(matrix=pymupdf.Matrix(1.25,1.25),alpha=False).save(str(q));out.append({'operation_id':row['operation_id'],'svg_file':row['svg_file'],'svg_sha256':sha(p),'png_file':str(q.relative_to(O)).replace('\\','/'),'png_sha256':sha(q)})
contacts=[]
for first in range(0,len(out),4):
 subset=out[first:first+4];canvas=Image.new('RGB',(1440,1080),'#eef4f7')
 for i,row in enumerate(subset):
  im=Image.open(O/row['png_file']);im.thumbnail((700,515));canvas.paste(im,((i%2)*720+10,(i//2)*540+10))
 p=O/'review'/f'contact-{first//4+1:02d}.png';canvas.save(p);contacts.append({'path':str(p.relative_to(O)).replace('\\','/'),'sha256':sha(p)})
(O/'render-validation.json').write_text(json.dumps({'schema':'mattersyn-private-apparatus-previews/1','renderer':'PyMuPDF SVG rasterization','scene_manifest_sha256':sha(O/'scene-manifest.json'),'files':out,'contact_sheets':contacts,'actual_visual_inspection':'pending author inspection; rasterization alone is not review'},indent=2)+'\n')
print(json.dumps({'previews':len(out),'contact_sheets':len(contacts)}))
