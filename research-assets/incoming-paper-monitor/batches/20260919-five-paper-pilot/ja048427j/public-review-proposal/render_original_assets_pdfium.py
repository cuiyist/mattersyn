"""Reader-specific faithful rerender; frozen extraction assets are read only."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import hashlib,json,sys
sys.dont_write_bytecode=True
sys.path.append(r'[local path redacted]')
sys.path.insert(0,r'[local path redacted]')
sys.path.insert(0,r'[local path redacted]')
import pypdfium2 as pdfium
from PIL import Image,ImageOps,ImageDraw
O=Path(__file__).resolve().parent;B=O.parent;OUT=O/'original-assets-pdfium';OUT.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
oldpath=B/'reader-assets/asset-manifest.json';old=json.loads(oldpath.read_bytes());bound={str(oldpath):sha(oldpath)}
for s in old['sources']:
    for k,hk in [('path','sha256'),('identical_copy','identical_copy_sha256')]:assert sha(s[k])==s[hk];bound[s[k]]=s[hk]
for a in old['assets']:assert sha(B/a['path'])==a['sha256'];bound[str(B/a['path'])]=a['sha256']
pages={};pagefiles={};scale=old['dpi']/72
for s in old['sources']:
    doc=pdfium.PdfDocument(s['path'])
    for n in range(len(doc)):
        page=doc[n];bm=page.render(scale=scale);im=bm.to_pil().convert('RGB');path=OUT/'pages'/f"{s['role']}-{n+1:02}.png";path.parent.mkdir(exist_ok=True);im.save(path);pages[(s['role'],n+1)]=im;pagefiles[(s['role'],n+1)]=path;bm.close();page.close()
    doc.close()
assets=[]
for a in old['assets']:
    im=pages[(a['source_role'],a['pdf_page'])];new=deepcopy(a)
    if a['kind']=='full_page':p=pagefiles[(a['source_role'],a['pdf_page'])];assert list(im.size)==a['dimensions']
    else:
        assert list(im.size)==a['crop']['page_dimensions'];bounds=a['crop']['bounds'];crop=im.crop(bounds);assert list(crop.size)==a['dimensions'];p=OUT/(a['id']+'.png');crop.save(p)
    new.update(path=str(p.relative_to(B)),sha256=sha(p),dimensions=list(Image.open(p).size),reader_specific_rerender=True,replaces_asset={'path':a['path'],'sha256':a['sha256'],'original_manifest_sha256':sha(oldpath),'renderer':old['render_engine']},content_status='Unchanged original PDF content rendered with PDFium to preserve source glyphs; exact original crop boundaries; no redraw or numerical alteration')
    new.pop('text_cache',None);new.pop('text_cache_sha256',None);assets.append(new)
contacts=[]
for group,subset in [('crops',[a for a in assets if a['kind']!='full_page']),('pages',[a for a in assets if a['kind']=='full_page'])]:
    for start in range(0,len(subset),4):
        canvas=Image.new('RGB',(1440,2000),'#e8edf4');draw=ImageDraw.Draw(canvas)
        for j,a in enumerate(subset[start:start+4]):
            im=Image.open(B/a['path']).convert('RGB');im.thumbnail((690,930));x=(j%2)*720+(720-im.width)//2;y=(j//2)*1000+50;canvas.paste(im,(x,y));draw.text(((j%2)*720+18,(j//2)*1000+14),a['id']+' | '+str(a['dimensions']),fill='black')
        p=OUT/f'{group}-contact-{start//4+1}.png';canvas.save(p);contacts.append({'group':group,'asset_ids':[a['id'] for a in subset[start:start+4]],'path':str(p),'sha256':sha(p),'status':'pending_author_visual_check'})
for p,h in bound.items():assert sha(p)==h
manifest={'schema':'mattersyn-reader-original-assets-pdfium/1','author':'/root/norberg2004_extract','created_at':datetime.now(timezone.utc).isoformat(),'render_engine':'PDFium via pypdfium2 '+str(pdfium.PYPDFIUM_INFO)+'; PDFium '+str(pdfium.PDFIUM_INFO),'dpi':old['dpi'],'scale':scale,'sources':old['sources'],'original_asset_manifest_sha256':sha(oldpath),'reason':'Independent reader reviewer detected incorrect degree-C glyphs in prior Poppler renders. Uniform rerender from same PDFs preserves accurate glyphs without editing source or scientific data.','assets':assets,'contact_sheets':contacts,'frozen_originals':bound,'render_script_sha256':sha(__file__),'frozen_source_or_canonical_modified':False,'author_visual_review_status':'pending_actual_visual_check','independent_reader_asset_review':'pending','published':False}
(O/'reader-original-assets-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'assets':len(assets),'contacts':len(contacts),'renderer':manifest['render_engine'],'manifest_sha256':sha(O/'reader-original-assets-manifest.json')}))
