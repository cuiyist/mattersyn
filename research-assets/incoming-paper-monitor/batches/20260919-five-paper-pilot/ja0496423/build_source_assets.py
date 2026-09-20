"""Original source crops; no retouching or reconstructed experimental curves."""
import hashlib
import json
from pathlib import Path
import pypdfium2 as pdfium

B = Path(__file__).resolve().parent
OUT = B / 'reader-assets'
OUT.mkdir(exist_ok=True)
docs = {d['role_candidate']: d for d in json.loads((B/'intake-manifest.json').read_bytes())['documents']}
# Normalized bounds are recorded against each complete original page.
specs = [
 ('scheme-1','main',1,[.514,.236,.899,.378],'Scheme 1','Authors’ proposed stages 1–4; conceptual geometry, not an atomic structure.'),
 ('figure-1','main',2,[.085,.052,.886,.217],'Figure 1A–D','FePt 1 TEM; final product 4 TEM/HRTEM and SAED. Scale bars and indexed rings retained.'),
 ('figure-2','main',2,[.086,.222,.911,.391],'Figure 2A–D','Product 4 magnetization, absorption/fluorescence and photograph; all axes/inset/caption retained.'),
 ('magnetic-model','main',2,[.084,.398,.485,.672],'Magnetic anisotropy estimate and optical interpretation','Complete magnetic/optical paragraphs, including source equation and parameters; anisotropy is an author estimate.'),
 ('si-general','si',1,[.080,.232,.930,.342],'SI S1 General','Reported reagent grades, suppliers, inert atmosphere and fluorescence standard.'),
 ('si-cdacac-preparation','si',1,[.080,.355,.930,.449],'SI S1 Synthesis of Cd(acac)2','Entire upstream preparation including isolation and vacuum drying.'),
 ('si-heterodimer-preparation','si',1,[.080,.455,.930,.744],'SI S1 Synthesis of 4','Complete one-pot synthesis, fraction-selective purification and nitrogen storage.'),
 ('figure-s1','si',2,[.310,.041,.687,.281],'Figure S-1','Original XRF spectrum of 4 with elemental table; table not silently reconciled to main ratio.'),
 ('figure-s2','si',2,[.231,.295,.774,.547],'Figure S-2','UV–visible absorption of FePt 1 in hexane; original trace retained without digitization.'),
 ('figure-s3','si',2,[.229,.558,.777,.833],'Figure S-3','ZFC/FC of FePt 1; field not supplied by SI caption.'),
 ('figure-s4','si',3,[.302,.041,.700,.287],'Figure S-4','TEM of isolated intermediate 2; 2 nm scale and S/FePt labels.'),
 ('figure-s5','si',3,[.276,.297,.724,.573],'Figure S-5','TEM of isolated intermediate 3; 20 nm scale and CdS/FePt labels.'),
]
renders = {}
assets=[]
for aid,role,page,box,label,note in specs:
 d=docs[role]; p=Path(d['path']); digest=hashlib.sha256(p.read_bytes()).hexdigest()
 if digest != d['sha256']: raise ValueError('Source changed: '+str(p))
 if (role,page) not in renders:
  pdf=pdfium.PdfDocument(p); image=pdf[page-1].render(scale=300/72).to_pil();renders[(role,page)]=image
 image=renders[(role,page)];w,h=image.size
 pixels=[round(box[0]*w),round(box[1]*h),round(box[2]*w),round(box[3]*h)]
 target=OUT/(aid+'.png');image.crop(pixels).save(target)
 assets.append({'id':'gu2004-'+aid,'source_role':role,'pdf_page':page,'printed_page':str(5663+page) if role=='main' else 'S'+str(page),'locator':label,'caption_scope':note,'source_path':str(p),'source_sha256':digest,'path':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'renderer':'pypdfium2/PDFium','render_dpi':300,'normalized_bbox':box,'pixel_bbox':pixels,'full_page_dimensions':[w,h],'asset_dimensions':[pixels[2]-pixels[0],pixels[3]-pixels[1]],'original_data':True,'retouched':False,'digitized':False,'independent_review_status':'pending'})
(OUT/'crop-manifest.json').write_text(json.dumps({'source_id':'gu2004','assets':assets,'scope':'Twelve original source excerpts/figures. Cropping only; all curves remain source images.'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'assets':len(assets),'manifest':str(OUT/'crop-manifest.json')}))
