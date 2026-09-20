"""Besson 2002 original figure/table/method crops. Private local preparation only."""
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
('figure-1','figure',3,(92,66,979,610),'Figure 1 · Absorption spectra and optically inferred CdS sizes in two host matrices'),
('figure-2','figure',3,(92,633,518,913),'Figure 2 · Low-angle X-ray diffraction during pore filling'),
('figure-3','figure',4,(92,67,979,770),'Figure 3 · Cross-sectional HRTEM and image Fourier power spectrum'),
('figure-4','figure',5,(92,65,518,392),'Figure 4 · Excitation and photoluminescence spectra on silicon'),
('matrix-preparation-start','source_note',2,(92,1140,518,1283),'Matrix preparation · Acidic sol, CTAB and ethanol dilution'),
('matrix-preparation-continuation','source_note',2,(550,66,979,186),'Matrix preparation · Spin coating, calcination and host texture'),
('impregnation-precipitation','source_note',2,(550,194,979,422),'Pore filling · Cadmium complex solution, washing and H2S precipitation'),
('note-36','source_note',5,(558,1201,979,1250),'Note 36 · Spherical-pore assumption and 3.5 nm pore estimate'),
('note-38','source_note',6,(94,65,518,99),'Note 38 · Reverse-micelle colloidal reference used for loading estimate'),
('power-spectrum-definition','source_note',4,(550,993,979,1143),'Image analysis · Fourier power spectrum and mesostructure parameters'),
]

doc=pdfium.PdfDocument(src);cache={}
manifest={'schema_version':'1.0','source_id':'besson2002','doi':'10.1021/nl015685v','created_at':datetime.now(timezone.utc).isoformat(),'review_status':'private_proposal_pending_independent_audit','page_inspection':{'main':list(range(1,7)),'text_read':True,'visual_reviewed':True},'sources':[{'role':'main','source':str(src),'sha256':info['sha256'],'page_count':6}],'supporting_information':{'status':'not_located_or_matched','claim':'No SI declaration seen in the six supplied main pages; no locally matched SI is asserted.'},'assets':[]}
for key,kind,n,bbox,label in specs:
 if n not in cache:
  page=doc[n-1];cache[n]=(page.render(scale=300/72).to_pil().copy(),page.get_size())
 full,psize=cache[n];base=Image.open(B/f'main-{n}.png')
 norm=[bbox[0]/base.width,bbox[1]/base.height,bbox[2]/base.width,bbox[3]/base.height]
 px=tuple(round(v*(full.width if i%2==0 else full.height)) for i,v in enumerate(norm));crop=full.crop(px);output=O/(key+'.png');crop.save(output)
 manifest['assets'].append({'id':key,'source_asset_type':kind,'label':label,'relative_asset':output.name,'public_asset':f'assets/figures/besson2002/{output.name}','sha256':sha(output),'source_role':'main','source_pdf_page':n,'source_filename':src.name,'source_sha256':info['sha256'],'crop_bbox_reference_pixels_125dpi':bbox,'reference_render_size':list(base.size),'crop_bbox_pdf_points_top_left':[v*psize[i%2] for i,v in enumerate(norm)],'crop_normalized':norm,'render_dpi':300,'pixel_dimensions':list(crop.size),'transformation':'Original PDF rendered with PDFium at 300 dpi and rectangularly cropped only. Original curves, colors, glyphs and author image processing preserved. No reconstruction or redraw.','text_reviewed':True,'visual_reviewed':False,'reviewed':False,'reader_render_verified':False})
(O/'crop-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('Prepared',len(manifest['assets']),'original assets')
