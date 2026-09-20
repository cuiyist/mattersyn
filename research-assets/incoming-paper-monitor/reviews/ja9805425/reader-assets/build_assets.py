"""Faithful original PDF crops for Peng et al. 1998. Private output only."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
import pypdfium2 as pdfium
from PIL import Image

B=Path(__file__).resolve().parents[1]
OUT=B/'reader-assets'
SRC=json.loads((B/'source-render-manifest.json').read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
specs=[
 ('figure-1','figure','main',2,(108,90,628,514),'Figure 1 · CdSe absorption and photoluminescence'),
 ('figure-2','figure','main',2,(109,523,629,984),'Figure 2 · CdSe and InAs size-distribution kinetics'),
 ('figure-3','figure','main',2,(110,992,628,1345),'Figure 3 · Faceted CdSe nanocrystals by TEM'),
 ('figure-4','figure','main',2,(660,90,1168,394),'Figure 4 · Source diffusion-controlled growth model'),
 ('si-inas-spectra','figure','si',3,(102,194,1158,1517),'Supporting Information · InAs absorption and photoluminescence'),
 ('si-cdse-calibration','table','si',2,(129,157,1100,1103),'Supporting Information · CdSe optical-peak / TEM-size calibration'),
 ('si-inas-calibration','table','si',4,(230,172,1040,1298),'Supporting Information · InAs optical-peak / TEM-size calibration'),
 ('equation-gibbs-thomson','equation','main',1,(804,974,1106,1028),'Gibbs–Thomson solubility equation'),
 ('equation-growth-rate','equation','main',2,(212,1416,581,1464),'Diffusion-controlled growth-rate equation'),
 ('note-21','source_note','main',1,(660,1169,1165,1378),'Note 21 · CdSe synthesis and aliquot characterization'),
 ('note-22','source_note','main',1,(661,1379,1165,1530),'Note 22 · InAs synthesis and aliquot characterization'),
]
manifest={'schema_version':'1.0','source_id':'peng1998','doi':'10.1021/ja9805425',
 'created_at':datetime.now(timezone.utc).isoformat(),'review_status':'private_proposal_pending_independent_audit',
 'page_inspection':{'main':[1,2],'si':[1,2,3,4],'text_read':True,'visual_reviewed':True},
 'sources':[{k:d[k] for k in ['role','source','sha256','page_count']} for d in SRC['documents']],
 'assets':[]}
docs={d['role']:d for d in SRC['documents']}
cache={}
for key,kind,role,n,bbox,label in specs:
 d=docs[role];src=Path(d['source']);assert sha(src)==d['sha256']
 if (role,n) not in cache:
  doc=pdfium.PdfDocument(src);page=doc[n-1]
  cache[(role,n)]=(page.render(scale=300/72).to_pil().copy(),page.get_size())
 full,psize=cache[(role,n)]
 base=Image.open(B/f'{role}-{n:02}.png')
 normalized=[bbox[0]/base.width,bbox[1]/base.height,bbox[2]/base.width,bbox[3]/base.height]
 px=tuple(round(v*(full.width if i%2==0 else full.height)) for i,v in enumerate(normalized))
 assert 0<=px[0]<px[2]<=full.width and 0<=px[1]<px[3]<=full.height
 output=OUT/(key+'.png');crop=full.crop(px);crop.save(output)
 manifest['assets'].append({'id':key,'source_asset_type':kind,'label':label,
  'relative_asset':output.name,'public_asset':f'assets/figures/peng1998/{output.name}',
  'sha256':sha(output),'source_role':role,'source_pdf_page':n,
  'source_filename':src.name,'source_sha256':d['sha256'],
  'crop_bbox_reference_pixels_150dpi':bbox,'reference_render_size':list(base.size),
  'crop_bbox_pdf_points_top_left':[v*psize[i%2] for i,v in enumerate(normalized)],
  'crop_normalized':normalized,'render_dpi':300,'pixel_dimensions':list(crop.size),
  'transformation':'Original PDF rasterized by PDFium at 300 dpi; rectangular crop only. No recoloring, resampling, curve redrawing or content synthesis.',
  'text_reviewed':True,'visual_reviewed':False,'reviewed':False,'reader_render_verified':False})
(OUT/'crop-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'assets':len(manifest['assets']),'path':str(OUT/'crop-manifest.json')}))
