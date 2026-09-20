"""Gerion 2001 original figure/table/method crops. Private local preparation only."""
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
('figure-1','figure',3,(92,74,975,754),'Figure 1 · Silanization mechanism and functional-group schematic'),
('figure-2','figure',4,(550,79,974,797),'Figure 2 · Absorption and emission across color cohorts'),
('table-1','table',4,(550,805,974,1046),'Table 1 · Silanized quantum-dot optical properties'),
('figure-3','figure',5,(92,79,514,837),'Figure 3 · Fluorescence stability over one month'),
('figure-4','figure',5,(550,79,974,501),'Figure 4 · Continuous-illumination photostability'),
('figure-5','figure',6,(92,78,514,945),'Figure 5 · Yellow-particle TEM and AFM distributions'),
('table-2','table',6,(92,955,514,1186),'Table 2 · Core, core/shell and coating-associated sizes'),
('figure-6','figure',6,(550,78,975,651),'Figure 6 · HPLC and gel comparison of two green silanization preparations'),
('figure-7','figure',7,(92,78,975,743),'Figure 7 · pH, salt stability and electrophoretic fractionation'),
('note-27-start','source_note',11,(92,639,514,671),'Note 27 · AFM histogram exclusions, first column'),
('note-27-continuation','source_note',11,(550,78,974,171),'Note 27 · AFM histogram exclusions, continuation'),
('note-28','source_note',11,(550,170,974,332),'Note 28 · Residual ZnS-particle diagnostic comparisons'),
('note-34','source_note',11,(550,477,974,612),'Note 34 · Qualitative scattering observations'),
('silanization-start','source_note',2,(92,1182,514,1315),'Silanization method · Initial precipitation and MPS charging'),
('silanization-continuation','source_note',2,(550,77,974,908),'Silanization method · Priming, shell growth, quenching and purification'),
('mpa-coating','source_note',2,(550,912,974,1275),'MPA coating method · Ligand exchange and recovery'),
('reagent-inventory','source_note',2,(92,568,514,1027),'Source reagent, purification-device and buffer inventory'),
]
doc=pdfium.PdfDocument(src);cache={}
manifest={'schema_version':'1.0','source_id':'gerion2001','doi':'10.1021/jp0105488','created_at':datetime.now(timezone.utc).isoformat(),'review_status':'private_proposal_pending_independent_audit','page_inspection':{'main':list(range(1,12)),'text_read':True,'visual_reviewed':True},'sources':[{'role':'main','source':str(src),'sha256':info['sha256'],'page_count':11}],'supporting_information':{'status':'declared_not_located_or_matched','declaration_locator':'Main PDF p.10, printed8870, Supporting Information Available: HRTEM and AFM figures of silanized nanocrystals.','claim':'SI explicitly declared in the main; no SI asset is reconstructed from prose.'},'assets':[]}
for key,kind,n,bbox,label in specs:
 if n not in cache:
  page=doc[n-1];cache[n]=(page.render(scale=300/72).to_pil().copy(),page.get_size())
 full,psize=cache[n];base=Image.open(B/f'main-{n:02}.png')
 norm=[bbox[0]/base.width,bbox[1]/base.height,bbox[2]/base.width,bbox[3]/base.height]
 px=tuple(round(v*(full.width if i%2==0 else full.height)) for i,v in enumerate(norm));crop=full.crop(px);output=O/(key+'.png');crop.save(output)
 manifest['assets'].append({'id':key,'source_asset_type':kind,'label':label,'relative_asset':output.name,'public_asset':f'assets/figures/gerion2001/{output.name}','sha256':sha(output),'source_role':'main','source_pdf_page':n,'source_filename':src.name,'source_sha256':info['sha256'],'crop_bbox_reference_pixels_125dpi':bbox,'reference_render_size':list(base.size),'crop_bbox_pdf_points_top_left':[v*psize[i%2] for i,v in enumerate(norm)],'crop_normalized':norm,'render_dpi':300,'pixel_dimensions':list(crop.size),'transformation':'Original PDF rendered with PDFium at 300 dpi and rectangularly cropped only. Original curves, colors, glyphs and author image processing preserved. No reconstruction or redraw.','text_reviewed':True,'visual_reviewed':False,'reviewed':False,'reader_render_verified':False})
(O/'crop-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('Prepared',len(manifest['assets']),'original assets')
