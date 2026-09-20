"""Dantas 2002 original crops, local preparation only."""
from pathlib import Path
import json,hashlib
import pypdfium2 as pdfium
from PIL import Image
B=Path(__file__).resolve().parents[1];O=B/'reader-assets';O.mkdir(exist_ok=True)
info=json.loads((B/'source-manifest.json').read_text(encoding='utf8'));src=Path(info['source_path'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(src)==info['sha256']
specs=[
('figure-1','figure',2,(92,78,516,402),'Figure 1 · SG2 absorption with SG1 inset'),
('figure-2','figure',2,(551,78,977,413),'Figure 2 · Optical absorption across the SG annealing series'),
('figure-3','figure',3,(92,80,516,740),'Figure 3 · Calculated PbS energy levels versus dot radius'),
('figure-4','figure',4,(92,80,979,1177),'Figure 4 · AFM images and height distributions of AFM1 and AFM2'),
('figure-5','figure',5,(92,78,518,490),'Figure 5 · Room-temperature photoluminescence of the SG series'),
('figure-6','figure',5,(92,500,518,849),'Figure 6 · SG1 ASPL power dependence and proposed mechanism'),
('figure-7','figure',5,(92,858,518,1177),'Figure 7 · SG1 absorption and near-excitation emission'),
('glass-preparation','source_note',1,(550,1144,979,1270),'Glass preparation · Reported components and fusion conditions'),
('annealing-acquisition','source_note',2,(92,419,517,794),'Sample preparation · Quench, two anneals, cohorts and optical acquisition'),
('model-assumptions','source_note',2,(550,608,979,1318),'Electronic model · Assumptions, quantum labels and optical size inference'),
('two-photon-continuation','source_note',4,(92,1181,979,1318),'Proposed mechanism · Photon recycling and sublinear power law'),
]
doc=pdfium.PdfDocument(src);cache={}
manifest={'schema_version':'1.0','source_id':'dantas2002','doi':'10.1021/jp0208743','review_status':'private_proposal_pending_independent_audit','page_inspection':{'main':list(range(1,6)),'text_read':True,'visual_reviewed':True},'sources':[{'role':'main','source':str(src),'sha256':info['sha256'],'page_count':5}],'supporting_information':{'status':'not_located_or_matched','claim':'No SI declaration identified in five supplied main pages; no matched SI asserted.'},'assets':[]}
for key,kind,n,bbox,label in specs:
 if n not in cache:
  page=doc[n-1];cache[n]=(page.render(scale=300/72).to_pil().copy(),page.get_size())
 full,psize=cache[n];base=Image.open(B/f'main-{n}.png');norm=[bbox[0]/base.width,bbox[1]/base.height,bbox[2]/base.width,bbox[3]/base.height]
 px=tuple(round(v*(full.width if i%2==0 else full.height)) for i,v in enumerate(norm));crop=full.crop(px);output=O/(key+'.png');crop.save(output)
 manifest['assets'].append({'id':key,'source_asset_type':kind,'label':label,'relative_asset':output.name,'public_asset':f'assets/figures/dantas2002/{output.name}','sha256':sha(output),'source_role':'main','source_pdf_page':n,'source_filename':src.name,'source_sha256':info['sha256'],'crop_bbox_reference_pixels_125dpi':bbox,'reference_render_size':list(base.size),'crop_bbox_pdf_points_top_left':[v*psize[i%2] for i,v in enumerate(norm)],'crop_normalized':norm,'render_dpi':300,'pixel_dimensions':list(crop.size),'transformation':'Original PDF rendered with PDFium at 300 dpi and rectangularly cropped only. Original curves, glyphs and author image processing preserved; no redraw or reconstruction.','text_reviewed':True,'visual_reviewed':True,'reviewed':False,'reader_render_verified':False})
(O/'crop-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('Prepared',len(manifest['assets']),'original assets')
