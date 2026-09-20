"""Braun 2001 original figure/table/method crops. Private local preparation only."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
import pypdfium2 as pdfium
from PIL import Image
B=Path(__file__).resolve().parents[1];O=B/'reader-assets';O.mkdir(exist_ok=True)
info=json.loads((B/'source-manifest.json').read_text(encoding='utf8'));src=Path(info['source_path'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(src)==info['sha256']
specs=[
('figure-1','figure',2,(92,79,516,687),'Figure 1 · Three radial QDQW architectures and schematic carrier wavefunctions'),
('figure-2','figure',3,(92,80,517,957),'Figure 2 · Step-resolved absorption spectra for systems I–III'),
('figure-3','figure',3,(550,80,976,825),'Figure 3 · Photoluminescence spectra for systems I–III'),
('figure-4','figure',4,(92,80,515,1010),'Figure 4 · Transient-absorption decay times and kinetic insets'),
('preparation-start','source_note',1,(550,941,976,1269),'Sample preparation · Step A core nucleation, first part'),
('preparation-continuation','source_note',2,(92,702,516,1317),'Sample preparation · Steps A–C and system I'),
('system-ii-iii','source_note',2,(550,79,976,615),'Sample preparation · System II and III layer sequence and dimensions'),
('optical-methods','source_note',1,(550,493,976,938),'Experimental methods · Ultrafast transient absorption and photoluminescence'),
]

doc=pdfium.PdfDocument(src);cache={}
manifest={'schema_version':'1.0','source_id':'braun2001','doi':'10.1021/jp010002l','created_at':datetime.now(timezone.utc).isoformat(),'review_status':'private_proposal_pending_independent_audit','page_inspection':{'main':list(range(1,5)),'text_read':True,'visual_reviewed':True},'sources':[{'role':'main','source':str(src),'sha256':info['sha256'],'page_count':4}],'supporting_information':{'status':'not_located_or_matched','claim':'No SI declaration seen in the four supplied main pages; no locally matched SI is asserted.'},'assets':[]}
for key,kind,n,bbox,label in specs:
 if n not in cache:
  page=doc[n-1];cache[n]=(page.render(scale=300/72).to_pil().copy(),page.get_size())
 full,psize=cache[n];base=Image.open(B/f'main-{n}.png')
 norm=[bbox[0]/base.width,bbox[1]/base.height,bbox[2]/base.width,bbox[3]/base.height]
 px=tuple(round(v*(full.width if i%2==0 else full.height)) for i,v in enumerate(norm));crop=full.crop(px);output=O/(key+'.png');crop.save(output)
 manifest['assets'].append({'id':key,'source_asset_type':kind,'label':label,'relative_asset':output.name,'public_asset':f'assets/figures/braun2001/{output.name}','sha256':sha(output),'source_role':'main','source_pdf_page':n,'source_filename':src.name,'source_sha256':info['sha256'],'crop_bbox_reference_pixels_125dpi':bbox,'reference_render_size':list(base.size),'crop_bbox_pdf_points_top_left':[v*psize[i%2] for i,v in enumerate(norm)],'crop_normalized':norm,'render_dpi':300,'pixel_dimensions':list(crop.size),'transformation':'Original PDF rendered with PDFium at 300 dpi and rectangularly cropped only. Original curves, colors, glyphs and author image processing preserved. No reconstruction or redraw.','text_reviewed':True,'visual_reviewed':False,'reviewed':False,'reader_render_verified':False})
(O/'crop-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('Prepared',len(manifest['assets']),'original assets')
