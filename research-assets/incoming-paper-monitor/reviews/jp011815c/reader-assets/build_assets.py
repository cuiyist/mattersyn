"""Faithful original 300 dpi source crops; private proposal only."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json
import pypdfium2 as pdfium
from PIL import Image
B=Path(__file__).resolve().parents[1]
O=B/'reader-assets';O.mkdir(exist_ok=True)
srcinfo=json.loads((B/'source-manifest.json').read_text(encoding='utf8'))
src=Path(srcinfo['source'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(src)==srcinfo['sha256']
specs=[
('figure-1','figure',2,(108,90,624,459),'Figure 1 · High-pressure synthesis apparatus'),
('table-1','table',2,(655,89,1171,384),'Table 1 · Silver nanocrystal experiments A–I'),
('figure-2','figure',3,(108,90,624,1218),'Figure 2 · Silver nanocrystal TEM and lattice fringes'),
('figure-3','figure',3,(657,90,1172,610),'Figure 3 · Mean silver diameter versus precursor concentration'),
('figure-4','figure',3,(657,614,1172,1088),'Figure 4 · Mean silver diameter versus temperature'),
('figure-5','figure',4,(107,91,1021,687),'Figure 5 · Silver size distributions A–I'),
('figure-6','figure',4,(108,690,624,1082),'Figure 6 · Silver nanocrystal energy-dispersive X-ray spectrum'),
('figure-7','figure',4,(657,688,1172,1220),'Figure 7 · Comparative silver UV–visible absorption spectra'),
('figure-8','figure',6,(107,90,624,1020),'Figure 8 · Iridium and platinum nanocrystal TEM'),
('figure-9','figure',6,(107,1027,624,1483),'Figure 9 · Scaled silver particle-volume distributions'),
('figure-10','figure',6,(657,90,1172,572),'Figure 10 · Cumulative scaled distributions and coagulation model'),
('figure-11','figure',7,(107,90,1172,1013),'Figure 11 · Silver nanocrystal internal grain boundaries'),
('equation-1','equation',4,(657,1368,1172,1500),'Equation 1 · Core–core van der Waals interaction'),
('equation-2','equation',5,(168,224,624,311),'Equation 2 · Hamaker constant approximation'),
('equation-3','equation',5,(245,596,624,649),'Equation 3 · Combining relation for Hamaker constants'),
('scaled-distribution-definitions','equation',5,(655,876,1173,1325),'Scaled particle-volume distribution definitions'),
('moment-ratios','equation',6,(107,1484,624,1600),'Moment ratios: beginning of the main-text definition'),
('mean-radius-definitions','equation',6,(657,582,1172,755),'Mean-radius definitions and coagulation thresholds'),
('cumulative-distribution-definitions','equation',6,(657,760,1172,1154),'Cumulative particle-volume distribution definitions'),
('note-32','source_note',8,(657,460,1172,581),'Note 32 · Prior thiol-to-metal ratios'),
('experimental-procedure','source_note',2,(107,794,625,1506),'Experimental procedure · Cell charging, hydrogen addition and recovery'),
]
doc=pdfium.PdfDocument(src);cache={}
manifest={'schema_version':'1.0','source_id':'shah2001','doi':'10.1021/jp011815c',
'created_at':datetime.now(timezone.utc).isoformat(),'review_status':'private_proposal_pending_independent_audit',
'page_inspection':{'main':list(range(1,9)),'text_read':True,'visual_reviewed':True},
'sources':[{'role':'main','source':str(src),'sha256':srcinfo['sha256'],'page_count':8}],
'supporting_information':{'status':'not_located_or_matched','claim':'No SI file has been matched for this review. This is not proof that no SI exists.'},'assets':[]}
for key,kind,n,bbox,label in specs:
 if n not in cache:
  page=doc[n-1];cache[n]=(page.render(scale=300/72).to_pil().copy(),page.get_size())
 full,psize=cache[n];base=Image.open(B/f'main-{n:02}.png')
 normalized=[bbox[0]/base.width,bbox[1]/base.height,bbox[2]/base.width,bbox[3]/base.height]
 px=tuple(round(v*(full.width if i%2==0 else full.height)) for i,v in enumerate(normalized))
 assert 0<=px[0]<px[2]<=full.width and 0<=px[1]<px[3]<=full.height
 output=O/(key+'.png');crop=full.crop(px);crop.save(output)
 manifest['assets'].append({'id':key,'source_asset_type':kind,'label':label,
 'relative_asset':output.name,'public_asset':f'assets/figures/shah2001/{output.name}',
 'sha256':sha(output),'source_role':'main','source_pdf_page':n,'source_filename':src.name,'source_sha256':srcinfo['sha256'],
 'crop_bbox_reference_pixels_150dpi':bbox,'reference_render_size':list(base.size),
 'crop_bbox_pdf_points_top_left':[v*psize[i%2] for i,v in enumerate(normalized)],
 'crop_normalized':normalized,'render_dpi':300,'pixel_dimensions':list(crop.size),
 'transformation':'Original PDF rasterized by PDFium at 300 dpi; rectangular crop only. No recoloring, resampling, curve redrawing or content synthesis.',
 'text_reviewed':True,'visual_reviewed':False,'reviewed':False,'reader_render_verified':False})
(O/'crop-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'assets':len(manifest['assets']),'path':str(O/'crop-manifest.json')}))
