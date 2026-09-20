"""Independently compare proposed reader originals with fresh retained-PDF pixels.
Source assets and author proposal stay unchanged. Only private audit JSON is written.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
import pypdfium2 as pdfium
from PIL import Image,ImageChops
B=Path(__file__).resolve().parent;O=B/'public-review-proposal'
def rd(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
A=rd(B/'reader-assets/asset-manifest.json');P=rd(O/'reader-bindings-proposal.json');R=rd(O/'norberg2004.json')
original={a['id']:a for a in A['assets']};sources={x['role']:x for x in A['sources']}
docs={role:pdfium.PdfDocument(x['path'])for role,x in sources.items()};pages={};checks=[];bound={}
for x in A['sources']:assert sha(x['path'])==x['sha256'];bound[x['path']]=x['sha256']
for a in P['original_assets']:
 s=original[a['source_asset_id']];role=s['source_role'];page=s['pdf_page'];key=(role,page)
 if key not in pages:pages[key]=docs[role][page-1].render(scale=220/72).to_pil().convert('RGB')
 im=pages[key]
 if s['crop']:im=im.crop(s['crop']['bounds'])
 p=Path(a['private_path']);actual=Image.open(p).convert('RGB');h=sha(p);bound[str(p)]=h
 dimensions=actual.size==im.size
 pixels=dimensions and ImageChops.difference(actual,im).getbbox() is None
 checks.append({'asset_id':a['id'],'source_asset_id':s['id'],'source_role':role,'source_pdf_page':page,'source_sha256':s['source_sha256'],'crop_pixel_bounds':s['crop']['bounds']if s['crop']else None,'render_scale':220/72,'source_page_pixel_dimensions':list(pages[key].size),'actual_pixel_dimensions':list(actual.size),'proposed_asset_sha256':h,'matches_binding_sha256':h==a['sha256'],'same_dimensions':dimensions,'same_pixels_as_independent_fresh_pdfium_render':pixels,'passed':pixels and h==a['sha256']})
failed=[x for x in checks if not x['passed']]
out={'schema':'mattersyn-independent-original-pixel-audit/1','source_id':'norberg2004','auditor':'/root/peng1998_reader_assets','at':datetime.now(timezone.utc).isoformat(),'status':'passed'if not failed else 'findings','scope':'Each proposed original page or crop is compared pixel by pixel with a fresh PDFium render of the exact retained PDF at 220 dpi and the frozen extraction crop bounds. This checks rendering fidelity, not a numerical transcription or a new scientific interpretation.','reader_sha256':sha(O/'norberg2004.json'),'binding_sha256':sha(O/'reader-bindings-proposal.json'),'original_asset_manifest_sha256':sha(B/'reader-assets/asset-manifest.json'),'asset_count':len(checks),'source_pages_rerendered':{'main':sorted(p for role,p in pages if role=='main'),'si':sorted(p for role,p in pages if role=='si')},'bound_files':bound,'checks':checks,'failures':failed,'source_files_modified':False,'frozen_extraction_assets_modified':False,'canonical_modified':False}
(B/'reader-original-pixel-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':out['status'],'assets':len(checks),'failures':[x['asset_id']for x in failed]},ensure_ascii=False));raise SystemExit(bool(failed))
