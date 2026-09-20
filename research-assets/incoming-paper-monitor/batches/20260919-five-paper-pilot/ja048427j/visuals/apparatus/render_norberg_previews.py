from pathlib import Path
import json,sys,hashlib,math
sys.dont_write_bytecode=True
sys.path.insert(0,r'[local path redacted]')
sys.path.insert(0,r'[local path redacted]')
import pymupdf
from PIL import Image,ImageDraw
V=Path(__file__).resolve().parent;read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=read(V/'scene-manifest.json');items=[];tiles=[];overflows=[]
for i,s in enumerate(m['scenes']):
    p=V/s['svg_file'];assert sha(p)==s['svg_sha256']
    vector=pymupdf.open(stream=p.read_bytes(),filetype='svg');pdf=pymupdf.open('pdf',vector.convert_to_pdf());page=pdf[0]
    px=page.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False);name='review/'+s['scene_kind']+'.png';px.save(V/name)
    spans=[x for b in page.get_text('dict')['blocks'] if 'lines'in b for l in b['lines'] for x in l['spans']]
    outside=[{'text':x['text'],'bbox':x['bbox']} for x in spans if x['bbox'][0]<0 or x['bbox'][2]>page.rect.width or x['bbox'][1]<0 or x['bbox'][3]>page.rect.height]
    if outside:overflows.append({'scene':s['scene_kind'],'outside':outside})
    im=Image.frombytes('RGB',(px.width,px.height),px.samples);im.thumbnail((890,760),Image.Resampling.LANCZOS)
    tile=Image.new('RGB',(930,820),'#e4edf2');tile.paste(im,((930-im.width)//2,40));ImageDraw.Draw(tile).text((20,12),str(i+1)+' '+s['operation_id'],fill='#173c4b');tiles.append(tile)
    items.append({'scene_kind':s['scene_kind'],'svg_file':s['svg_file'],'svg_sha256':s['svg_sha256'],'png_file':name,'png_sha256':sha(V/name),'pixels':[px.width,px.height],'viewport':[page.rect.width,page.rect.height],'text_spans':len(spans),'text_outside_viewport':outside})
sheets=[]
for start in range(0,len(tiles),4):
    sheet=Image.new('RGB',(1860,1640),'#e4edf2')
    for j,tile in enumerate(tiles[start:start+4]):sheet.paste(tile,((j%2)*930,(j//2)*820))
    name=f'review/contact-{start//4+1:02d}.png';sheet.save(V/name);sheets.append({'file':name,'sha256':sha(V/name),'scene_ids':[x['scene_kind']for x in m['scenes'][start:start+4]]})
(V/'render-validation.json').write_text(json.dumps({'schema':'mattersyn.private-scene-render-validation.v1','scene_count':len(items),'module_sha256':m['module_sha256'],'scene_manifest_sha256':sha(V/'scene-manifest.json'),'renderer_sha256':sha(Path(__file__)),'scenes':items,'contact_sheets':sheets,'text_overflows':overflows,'author_visual_check':'pending actual inspection','independent_visual_audit':'pending'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'scenes':len(items),'sheets':len(sheets),'text_overflows':overflows},ensure_ascii=False))
