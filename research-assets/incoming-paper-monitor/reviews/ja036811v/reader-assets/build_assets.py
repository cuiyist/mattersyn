"""Original PDFium crops, main and matched SI; private review output only."""
from pathlib import Path
import json,hashlib
import pypdfium2 as pdfium
from PIL import Image
B=Path(__file__).resolve().parents[1];O=B/'reader-assets';O.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
info=read(B/'source-manifest.json');sources={d['role_candidate']:d for d in info['documents'] if d['role_candidate'] in ['main','si']};docs={k:pdfium.PdfDocument(v['path']) for k,v in sources.items()}
specs=[
('figure-1','figure','main',3,(550,78,973,697),'Figure 1 · ZnO formation, titration and thermal ripening'),
('figure-2','figure','main',4,(91,78,528,546),'Figure 2 · Aged undoped ZnO microscopy and electron diffraction'),
('figure-3','figure','main',4,(91,551,528,1069),'Figure 3 · Cobalt coordination during synthesis'),
('figure-4','figure','main',4,(550,77,973,601),'Figure 4 · Initial dopant concentration and band-gap response'),
('figure-5','figure','main',5,(91,77,528,545),'Figure 5 · As-grown approximately 5% Co:ZnO microscopy'),
('figure-6','figure','main',5,(550,78,973,495),'Figure 6 · Co:ZnO and Ni:ZnO absorption and MCD'),
('figure-7','figure','main',6,(91,302,528,689),'Figure 7 · High-resolution ligand-field absorption and MCD'),
('figure-8','figure','main',6,(550,77,973,612),'Figure 8 · Field and temperature responses with energy-level models'),
('figure-9','figure','main',6,(550,627,973,962),'Figure 9 · Zeeman model and Co:ZnO band-edge shifts'),
('figure-10','figure','main',7,(91,77,528,597),'Figure 10 · Co:ZnO aggregate magnetism and SEM'),
('figure-11','figure','main',7,(550,77,973,711),'Figure 11 · Spectral decomposition and cobalt intermediate'),
('scheme-1','scheme','main',8,(91,77,528,326),'Scheme 1 · Proposed dopant exclusion and incorporation'),
('table-1','table','main',6,(91,77,528,289),'Table 1 · MCD intensity ratios and transition energies'),
('table-2','table','main',12,(91,77,528,251),'Table 2 · Exchange constants with bulk-literature comparisons'),
('equation-1','equation','main',5,(704,593,973,650),'Equation 1 · C-term intensity ratio'),
('equation-2','equation','main',5,(704,986,973,1043),'Equation 2 · B-term intensity ratio'),
('equation-3','equation','main',8,(683,1066,973,1124),'Equation 3 · Curvature-dependent crystallite solubility'),
('equation-4','equation','main',10,(204,329,514,369),'Equation 4 · Nickel ligand-to-metal charge transfer'),
('equation-5','equation','main',10,(550,305,973,360),'Equation 5 · Optical-electronegativity model'),
('equation-6','equation','main',10,(640,460,973,517),'Equations 6a–b · Spin-pairing energy and Racah parameters'),
('equation-7','equation','main',11,(199,932,514,1029),'Equations 7a–b · Covalent wavefunction mixing'),
('equation-8','equation','main',11,(634,750,973,819),'Equations 8a–b · Mean-field band Zeeman splitting'),
('equation-9','equation','main',12,(192,1031,514,1107),'Equation 9 · Exchange from valence-band hybridization'),
('equation-10','equation','main',13,(686,167,973,200),'Equation 10 · Magnetization relaxation and anisotropy'),
('si-figure-1','figure','si',1,(95,193,964,945),'Figure S1 · Undoped and 2%-added-dopant kinetic comparison'),
('si-figure-2','figure','si',2,(95,147,960,563),'Figure S2 · Removal of deliberately surface-bound cobalt'),
('si-figure-3','figure','si',2,(95,600,960,979),'Figure S3 · TOPO-treated Ni:ZnO TEM and electron diffraction'),
('si-figure-4','figure','si',3,(95,235,960,585),'Figure S4 · ZnO and 2% Co:ZnO absorption and luminescence'),
('si-figure-5','figure','si',3,(95,635,960,1084),'Figure S5 · TOPO-cleaned, core/shell and bulk ligand-field spectra'),
('si-figure-6','figure','si',4,(95,153,960,519),'Figure S6 · ZnO band gap before and after TOPO processing'),
('synthesis-method','source_note','main',2,(550,599,973,929),'Source method · Alkaline growth, workup and aggregation'),
('topo-method','source_note','main',2,(550,928,973,1202),'Source method · Dodecylamine and TOPO processing'),
('note-16','source_note','main',2,(550,1218,973,1291),'Source note 16 · Technical TOPO and possible phosphonic-acid ligation'),
('physical-methods','source_note','main',3,(91,77,528,754),'Source methods · Structural, optical and magnetic measurements'),
('note-25-29','source_note','main',9,(550,1165,973,1286),'Source notes 25–29 · Fano dip and bulk low-temperature emission context'),
('note-33','source_note','main',10,(91,1236,528,1291),'Source notes 33–34 · Optical electronegativity conventions'),
('magnetism-estimate','source_note','main',13,(550,209,973,767),'Source interpretation · Aggregate domain lower bound and defect hypothesis'),
('si-declaration','source_note','main',14,(550,283,973,603),'Source declaration · Six supporting-information figures'),
]
manifest={'schema_version':'1.0','source_id':'schwartz2003','doi':'10.1021/ja036811v','review_status':'private_proposal_pending_independent_audit','page_inspection':{'main':list(range(1,15)),'si':list(range(1,5)),'text_read':True,'visual_reviewed':True},'sources':[{'role':k,'source':v['path'],'sha256':v['sha256'],'page_count':v['page_count']} for k,v in sources.items()],'supporting_information':{'status':'matched_and_reviewed','evidence':'Main p.14 explicitly lists S1–S6, all six supplied SI figures match in subject and order; SI author metadata identifies Daniel Gamelin.'},'assets':[]};cache={}
for key,kind,role,n,bbox,label in specs:
 src=Path(sources[role]['path']);assert sha(src)==sources[role]['sha256']
 if (role,n) not in cache:
  page=docs[role][n-1];cache[role,n]=(page.render(scale=300/72).to_pil().copy(),page.get_size())
 full,psize=cache[role,n];base=Image.open(B/(f'main-{n:02}.png' if role=='main' else f'si-{n}.png'));norm=[bbox[0]/base.width,bbox[1]/base.height,bbox[2]/base.width,bbox[3]/base.height];px=tuple(round(v*(full.width if i%2==0 else full.height)) for i,v in enumerate(norm));crop=full.crop(px);output=O/(key+'.png');crop.save(output)
 manifest['assets'].append({'id':key,'source_asset_type':kind,'label':label,'relative_asset':output.name,'public_asset':f'assets/figures/schwartz2003/{output.name}','sha256':sha(output),'source_role':role,'source_pdf_page':n,'source_filename':src.name,'source_sha256':sources[role]['sha256'],'crop_bbox_reference_pixels_125dpi':bbox,'reference_render_size':list(base.size),'crop_bbox_pdf_points_top_left':[v*psize[i%2] for i,v in enumerate(norm)],'crop_normalized':norm,'render_dpi':300,'pixel_dimensions':list(crop.size),'transformation':'Original PDF rendered with PDFium at 300 dpi and rectangularly cropped only. Source curves, microscopy, glyphs and author image processing preserved. No redraw or reconstruction.','text_reviewed':True,'visual_reviewed':False,'reviewed':False,'reader_render_verified':False})
(O/'crop-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('Prepared',len(manifest['assets']),'original source crops')
