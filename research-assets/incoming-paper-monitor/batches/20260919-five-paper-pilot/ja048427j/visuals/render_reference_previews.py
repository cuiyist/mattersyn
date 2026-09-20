from pathlib import Path
import json,sys,hashlib,math
sys.dont_write_bytecode=True
sys.path.insert(0,r'[local path redacted]');sys.path.insert(0,r'[local path redacted]')
import pymupdf
from PIL import Image,ImageDraw
V=Path(__file__).resolve().parent;M=V/'molecules';P=V/'products';read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
outputs=[];outside=[]
def render(path,dest,label):
    vector=pymupdf.open(stream=path.read_bytes(),filetype='svg');doc=pymupdf.open('pdf',vector.convert_to_pdf());page=doc[0];px=page.get_pixmap(matrix=pymupdf.Matrix(1.4,1.4),alpha=False);px.save(dest)
    spans=[s for b in page.get_text('dict')['blocks']if 'lines'in b for line in b['lines']for s in line['spans']];bad=[{'text':s['text'],'bbox':s['bbox']}for s in spans if s['bbox'][0]<0 or s['bbox'][1]<0 or s['bbox'][2]>page.rect.width or s['bbox'][3]>page.rect.height]
    if bad:outside.append({'path':str(path),'outside':bad})
    im=Image.frombytes('RGB',(px.width,px.height),px.samples);im.thumbnail((880,560),Image.Resampling.LANCZOS);tile=Image.new('RGB',(920,610),'#e5edf2');tile.paste(im,((920-im.width)//2,34));ImageDraw.Draw(tile).text((15,10),label,fill='#173c4b')
    outputs.append({'label':label,'svg':str(path),'svg_sha256':sha(path),'png':str(dest),'png_sha256':sha(dest),'text_outside':bad});return tile
def project(model,path,title,finite=False):
    atoms=model['atoms'];coords=[]
    for a in atoms:
        x,y,z=[a[k]for k in ['x','y','z']];coords.append((.85*x-.45*y,.28*x+.5*y-.82*z,.4*x+.75*y+.55*z))
    corners=[]
    if model.get('cellVectors') and not finite:
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    x,y,z=[sum([i,j,k][l]*model['cellVectors'][l][a]for l in range(3))for a in range(3)]
                    corners.append((.85*x-.45*y,.28*x+.5*y-.82*z,.4*x+.75*y+.55*z))
    bounds=coords+corners
    xmin,xmax=min(p[0]for p in bounds),max(p[0]for p in bounds);ymin,ymax=min(p[1]for p in bounds),max(p[1]for p in bounds);scale=min(590/max(xmax-xmin,1),350/max(ymax-ymin,1))
    locate=lambda p:(350+(p[0]-(xmin+xmax)/2)*scale,250+(p[1]-(ymin+ymax)/2)*scale,p[2])
    positions=[locate(p)for p in coords]
    colors={'H':'#c8d0d7','C':'#556573','N':'#637bb4','O':'#cc7679','S':'#cba745','P':'#b489bd','Zn':'#6d94b3','Mn':'#9a779f'}
    svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 520"><rect width="720" height="520" rx="16" fill="#f5f9fc"/>'+f'<text x="22" y="32" font-family="Arial" font-size="20" fill="#173c4b">{title}</text>'
    if corners:
        for i in range(8):
            for bit in [1,2,4]:
                j=i^bit
                if j>i:
                    a,c=locate(corners[i]),locate(corners[j]);svg+=f'<path d="M{a[0]} {a[1]}L{c[0]} {c[1]}" stroke="#a5b4bf" stroke-width="1.5"/>'
    bonds=model.get('bonds',[])
    if finite:bonds=[{'a':i,'b':j,'order':1}for i,a in enumerate(atoms)for j in a['bonds']if j<i]
    for b in bonds:
        a,c=positions[b['a']],positions[b['b']];svg+=f'<path d="M{a[0]} {a[1]}L{c[0]} {c[1]}" stroke="#a4b8c4" stroke-width="{2.0 if finite else 3.4}"/>'
    for i in sorted(range(len(atoms)),key=lambda i:positions[i][2]):
        a=atoms[i];x,y,z=positions[i];e=a.get('element',a.get('elem'));radius=4 if e=='H' else 6 if finite else 9;svg+=f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{colors.get(e,"#91a7b5")}" stroke="#fff" stroke-width=".7"/>'
    svg+='<text x="22" y="491" font-family="Arial" font-size="14" fill="#426271">Actual JSON coordinate projection · reference geometry, not a measured Norberg sample</text></svg>';path.write_text(svg,encoding='utf-8')
    return path
def sheets(tiles,folder,prefix):
    out=[]
    for start in range(0,len(tiles),4):
        im=Image.new('RGB',(1840,1220),'#e5edf2')
        for j,t in enumerate(tiles[start:start+4]):im.paste(t,((j%2)*920,(j//2)*610))
        p=folder/f'{prefix}-{start//4+1:02d}.png';im.save(p);out.append({'file':str(p),'sha256':sha(p)})
    return out
tiles=[]
qual=read(M/'reuse-qualification.json')
for q in qual['entries']:
    rid=q['registry_id'];svg=next(a for a in q['assets']if a['key']=='svgPath');tiles.append(render(Path(svg['private_path']),M/'review'/f'{rid}-2d.png',rid+' · existing 2D'))
for e in read(M/'registry-additions.json')['entries']:
    tiles.append(render(M/e['svgPath'],M/'review'/f"{e['id']}-2d.png",e['name']))
contacts=sheets(tiles,M/'review','molecule-2d-contact')
tiles=[]
for q in qual['entries']:
    row=next((a for a in q['assets']if a['key']=='model3dPath'),None)
    if row:
        model=read(Path(row['private_path']));svg=project(model,M/'review'/f"{q['registry_id']}-projection.svg",q['registry_id']+' · free-compound reference');tiles.append(render(svg,M/'review'/f"{q['registry_id']}-3d.png",q['registry_id']+' · existing 3D coordinates'))
contacts+=sheets(tiles,M/'review','molecule-3d-contact')
tiles=[]
for e in read(P/'product-registry-additions.json')['entries']:tiles.append(render(P/e['svgPath'],P/'review'/f"{e['id']}.png",e['name']))
contacts+=sheets(tiles,P/'review','product-contact')
tiles=[]
for filename,title,finite in [('norberg-undoped-zno-unit-cell.json','External ZnO cell · 4 sites, no Mn',False),('norberg-undoped-zno-finite-reference.json','Illustrative ZnO block · 192 atoms, no Mn',True)]:
    model=read(P/'models'/filename);svg=project(model,P/'review'/filename.replace('.json','.svg'),title,finite);tiles.append(render(svg,P/'review'/filename.replace('.json','.png'),title))
contacts+=sheets(tiles,P/'review','host-reference-contact')
out={'schema':'mattersyn.private-reference-preview-manifest.v1','outputs':outputs,'contacts':contacts,'count':len(outputs),'text_overflows':outside,'author_visual_check':'pending actual inspection','independent_audit':'pending','source_files_unchanged':True};(V/'reference-preview-manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'previews':len(outputs),'contacts':len(contacts),'text_overflows':outside}))
