from pathlib import Path
import json,sys,hashlib
sys.dont_write_bytecode=True
sys.path.insert(0,r'[local path redacted]')
sys.path.insert(0,r'[local path redacted]')
import pymupdf
from PIL import Image,ImageDraw
V=Path(__file__).resolve().parent
m=json.loads((V/'scene-manifest.json').read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
images=[];checks=[];overflows=[]
for scene in m['scenes']:
    svg=V/scene['svg_file'];assert sha(svg)==scene['svg_sha256']
    vector=pymupdf.open(stream=svg.read_bytes(),filetype='svg')
    pdf=pymupdf.open('pdf',vector.convert_to_pdf());page=pdf[0]
    assert tuple(page.rect)==(0,0,760,540)
    px=page.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False)
    filename=f"review/{scene['scene_kind']}.png";px.save(V/filename)
    im=Image.frombytes('RGB',(px.width,px.height),px.samples).resize((760,540),Image.Resampling.LANCZOS)
    tile=Image.new('RGB',(800,590),'#e4edf2');tile.paste(im,(20,32))
    ImageDraw.Draw(tile).text((20,8),scene['record_id']+'/'+scene['operation_id'],fill='#173c4b')
    images.append(tile)
    spans=[x for block in page.get_text('dict')['blocks'] if 'lines' in block for line in block['lines'] for x in line['spans']]
    outside=[{'text':x['text'],'bbox':x['bbox']} for x in spans if x['bbox'][0]<0 or x['bbox'][2]>760 or x['bbox'][1]<0 or x['bbox'][3]>540]
    if outside:overflows.append({'scene':scene['scene_kind'],'outside':outside})
    checks.append({'scene':scene['scene_kind'],'svg_sha256':scene['svg_sha256'],'png_file':filename,'png_sha256':sha(V/filename),'pixels':[px.width,px.height],'viewport':[760,540],'text_spans':len(spans),'text_outside_viewport':outside})
sheets=[]
for start in range(0,len(images),6):
    sheet=Image.new('RGB',(1600,1770),'#e4edf2')
    for i,im in enumerate(images[start:start+6]):sheet.paste(im,((i%2)*800,(i//2)*590))
    name=f'review/contact-{start//6+1:02d}.png';sheet.save(V/name)
    sheets.append({'file':name,'sha256':sha(V/name),'scene_ids':[x['scene_kind'] for x in m['scenes'][start:start+6]]})
out={'schema':'mattersyn.private-scene-render-validation.v1','module_sha256':m['module_sha256'],'scene_manifest_sha256':sha(V/'scene-manifest.json'),'renderer_sha256':sha(Path(__file__)),'scene_count':len(checks),'scenes':checks,'contact_sheets':sheets,'text_overflows':overflows,'author_visual_check':'pending actual inspection','independent_visual_audit':'pending'}
(V/'render-validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'scenes':len(checks),'contact_sheets':len(sheets),'text_overflows':overflows},ensure_ascii=False))
