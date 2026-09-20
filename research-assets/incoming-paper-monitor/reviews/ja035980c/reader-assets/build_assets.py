"""Original main/SI PDFium crops; private only, no pixel reconstruction."""
from pathlib import Path
import json,hashlib
import pypdfium2 as pdfium
from PIL import Image
B=Path(__file__).resolve().parents[1];O=B/'reader-assets';O.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
info=read(B/'source-manifest.json');sources={d['role_candidate']:d for d in info['documents'] if d['role_candidate'] in ['main','si'] and not d.get('identical_main_copy')};docs={k:pdfium.PdfDocument(v['path']) for k,v in sources.items()}
specs=[
('figure-1','figure','main',3,(90,77,974,1025),'Figure 1 · Pristine and oxidized multiwalled nanotubes'),
('figure-2','figure','main',4,(90,78,974,1048),'Figure 2 · CdTe coverage and nanotube junctions by SEM and TEM'),
('figure-3','figure','main',5,(90,77,974,1084),'Figure 3 · Nanocrystal interfaces at tips, defects and exposed edges'),
('figure-4','figure','main',6,(90,77,974,914),'Figure 4 · HRTEM junctions and original EDS inset'),
('figure-5','figure','main',7,(90,76,974,899),'Figure 5 · XPS and indexed X-ray diffraction'),
('figure-6','figure','main',7,(549,911,973,1214),'Figure 6 · Raman comparison of oxidized nanotubes and heterostructure'),
('figure-7','figure','main',8,(91,77,524,379),'Figure 7 · Electronic spectra of washings and heterostructure'),
('figure-8','figure','main',8,(549,77,974,699),'Figure 8 · Author schematic of oxidation and in situ growth'),
('si-infrared','figure','si',1,(150,118,918,671),'SI · Infrared spectrum of oxidized multiwalled nanotubes'),
('synthesis-method','source_note','main',2,(549,594,974,1220),'Source method · Nanotube processing, CdTe growth and workup'),
('characterization-methods','source_note','main',3,(90,1040,974,1290),'Source methods · Electron microscopy, XPS, XRD and start of optical acquisition'),
('optical-methods','source_note','main',4,(90,1063,525,1191),'Source methods · Optical-method continuation, infrared and Raman'),
('oxidation-controls','source_note','main',8,(90,634,525,1006),'Source control discussion · Oxidation level and CdTe coverage'),
('passivation-context','source_note','main',8,(549,718,974,1005),'Source XPS discussion · Cd binding energy, literal TeO3 and thermal interpretation'),
('diffusion-interpretation','source_note','main',7,(90,979,525,1197),'Source interpretation · Anisotropic growth and nanotube steric restriction'),
]
manifest={'schema_version':'1.0','source_id':'banerjee2003','doi':'10.1021/ja035980c','review_status':'private_proposal_pending_independent_audit','page_inspection':{'main':list(range(1,10)),'si':[1],'text_read':True,'visual_reviewed':True},'sources':[{'role':k,'source':v['path'],'sha256':v['sha256'],'page_count':v['page_count']} for k,v in sources.items()],'supporting_information':{'status':'matched_and_reviewed','evidence':'Main printed p. 10350 declares an infrared spectrum of oxidized MWNTs. Supplied SI heading matches, and PDF metadata Title embeds ja035980c.'},'assets':[]};cache={}
for key,kind,role,n,bbox,label in specs:
 src=Path(sources[role]['path']);assert sha(src)==sources[role]['sha256']
 if (role,n) not in cache:
  page=docs[role][n-1];cache[role,n]=(page.render(scale=300/72).to_pil().copy(),page.get_size())
 full,psize=cache[role,n];base=Image.open(B/f'{role}-{n}.png');norm=[bbox[0]/base.width,bbox[1]/base.height,bbox[2]/base.width,bbox[3]/base.height];px=tuple(round(v*(full.width if i%2==0 else full.height)) for i,v in enumerate(norm));crop=full.crop(px);output=O/(key+'.png');crop.save(output)
 manifest['assets'].append({'id':key,'source_asset_type':kind,'label':label,'relative_asset':output.name,'public_asset':f'assets/figures/banerjee2003/{output.name}','sha256':sha(output),'source_role':role,'source_pdf_page':n,'source_filename':src.name,'source_sha256':sources[role]['sha256'],'crop_bbox_reference_pixels_125dpi':bbox,'reference_render_size':list(base.size),'crop_bbox_pdf_points_top_left':[v*psize[i%2] for i,v in enumerate(norm)],'crop_normalized':norm,'render_dpi':300,'pixel_dimensions':list(crop.size),'transformation':'Original PDF rendered with PDFium at 300 dpi and rectangularly cropped only. Original curves, glyphs and author image processing preserved; no redraw or reconstruction.','text_reviewed':True,'visual_reviewed':False,'reviewed':False,'reader_render_verified':False})
(O/'crop-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('Prepared',len(manifest['assets']),'original source crops')
