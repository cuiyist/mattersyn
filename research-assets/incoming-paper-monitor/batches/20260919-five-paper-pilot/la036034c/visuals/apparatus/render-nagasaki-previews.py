from pathlib import Path
import json,sys,hashlib
sys.dont_write_bytecode=True
sys.path.insert(0,'[local path redacted]')
sys.path.insert(0,'[local path redacted]')
import pymupdf
from PIL import Image,ImageDraw
V=Path(__file__).resolve().parent
assert not (V/'author-visual-check.json').exists()
m=json.loads((V/'scene-manifest.json').read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
images=[];checks=[];overflows=[]
for s in m['scenes']:
    svg=V/s['svg_file'];assert sha(svg)==s['svg_sha256']
    vector=pymupdf.open(stream=svg.read_bytes(),filetype='svg');pdf=pymupdf.open('pdf',vector.convert_to_pdf());page=pdf[0]
    assert page.rect.width==760
    px=page.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False)
    filename=f"review/{s['scene_kind']}.png";px.save(V/filename)
    im=Image.frombytes('RGB',(px.width,px.height),px.samples);im.thumbnail((760,720),Image.Resampling.LANCZOS)
    tile=Image.new('RGB',(800,760),'#e4edf2');tile.paste(im,((800-im.width)//2,32));ImageDraw.Draw(tile).text((20,8),s['operation_id'],fill='#173c4b');images.append(tile)
    spans=[x for b in page.get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for x in l['spans']]
    outside=[{'text':x['text'],'bbox':x['bbox']} for x in spans if x['bbox'][0]<0 or x['bbox'][2]>760 or x['bbox'][1]<0 or x['bbox'][3]>page.rect.height]
    panel=[{'text':x['text'],'bbox':x['bbox']} for x in spans if 102<x['bbox'][1]<510 and x['bbox'][0]<375<x['bbox'][2]]
    if outside or panel:overflows.append({'scene':s['scene_kind'],'outside':outside,'crossing_panel_boundary':panel})
    checks.append({'scene':s['scene_kind'],'svg_sha256':s['svg_sha256'],'png_file':filename,'png_sha256':sha(V/filename),'pixels':[px.width,px.height],'viewport':[760,page.rect.height],'text_spans':len(spans),'text_outside_viewport':outside,'crossing_panel_boundary':panel})
sheets=[]
for start in range(0,len(images),6):
    sheet=Image.new('RGB',(1600,2280),'#e4edf2')
    for i,im in enumerate(images[start:start+6]):sheet.paste(im,((i%2)*800,(i//2)*760))
    name=f'review/contact-{start//6+1:02d}.png';sheet.save(V/name);sheets.append({'file':name,'sha256':sha(V/name),'scene_ids':[x['scene_kind'] for x in m['scenes'][start:start+6]]})
(V/'render-validation.json').write_text(json.dumps({'schema':'mattersyn.private-scene-render-validation.v1','module_sha256':m['module_sha256'],'scene_manifest_sha256':sha(V/'scene-manifest.json'),'renderer_sha256':sha(Path(__file__)),'scene_count':len(checks),'scenes':checks,'contact_sheets':sheets,'text_overflows':overflows,'author_visual_check':'pending actual inspection','independent_visual_audit':'pending'},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'scenes':len(checks),'contact_sheets':len(sheets),'text_overflows':overflows}))
