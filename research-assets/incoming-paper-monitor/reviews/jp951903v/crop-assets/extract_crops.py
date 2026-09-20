"""Faithful original-source crops; no enhancement, redraw or curve digitization."""
import sys,json,hashlib,math,subprocess
from pathlib import Path
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')
OUT=Path(__file__).resolve().parent
REVIEW=OUT.parent
SOURCE=Path('[local path redacted]')
POPPLER=Path('[local path redacted]')
DPI=300
(OUT/'source-render').mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
source_hash=sha(SOURCE)
assert source_hash=='016e78158e4f83837f13b1412f3e08d5f7134724a3758d14468a41ff926e156a'
if not all((OUT/'source-render'/('main-'+str(p)+'.png')).exists() for p in range(2,6)):
 subprocess.run([str(POPPLER),'-f','2','-l','5','-r',str(DPI),'-png',str(SOURCE),str(OUT/'source-render/main')],check=True)

# Boxes were selected on the supplied 1190x1540 full-page previews after reading
# all six pages. Normalize to the actual preview dimensions before applying at 300 dpi.
SPECS=[
 ('figure-1','figure',2,[85,75,568,687], 'Lithography, etching and selective Ge growth',
  'Three-step original schematic: pattern the resist, etch the oxide to expose silicon sites, then remove resist and grow Ge selectively on the exposed substrate.',
  'Shared fabrication sequence for 100 and 150 nm well arrays, not an apparatus photograph or nanoscale atomic structure.',
  'original_author_schematic',
  ['The caption says approximately 60–150 nm wells in photoresist; methods p.1 describes approximately 60 and 100 nm resist holes that become 100 and 150 nm after RIE. Preserve this distinction/conflict.',
   'The cartoon labels PMMA resist, 20 nm oxide and silicon(100); it is schematic rather than a dimensional cross-section.']),
 ('figure-2','figure',2,[85,694,568,1209], 'AFM overview of patterned wells',
  'Supertip AFM overview of the patterned well array illustrating parallel nanosurface fabrication.',
  'Unresolved well-size assignment: caption says 150 nm wells, while the adjacent methods text identifies a 25 square-micrometer area patterned with 100 nm wells. Do not resolve this discrepancy silently or use this panel as an unambiguous product-size label.',
  'original_afm_image',
  ['Original 600 nm scale bar retained.','This is an overview of wells; it does not give a measured diameter for each Ge quantum dot.']),
 ('figure-3','figure',3,[596,74,1078,733], 'Dark-field TEM of Ge islands in 150 nm wells',
  'Dark-field TEM emphasizes crystalline Ge islands against the silicon substrate. Moire fringes support epitaxial registry; most islands lie near the defect-rich well perimeter.',
  '150 nm well arrays after selective growth. A subset of larger islands shows fringe discontinuities described as misfit dislocations. Not a 100 nm-well image and not a SAED pattern.',
  'original_tem_image',
  ['No scale bar is printed inside this figure. Do not add one.','The source states that well-to-well centers were the length standard for size/distance measurements.',
   'The paper attributes perimeter preference to defects caused by RIE over-etch; it does not supply refined atomic coordinates.']),
 ('figure-4','figure',4,[85,76,568,767], 'Relative island size and first-to-second island separation',
  'Plot of center-to-center separation against the size ratio of the second and first inferred nucleation events. The absence of a clear correlation supports the authors\' confinement interpretation.',
  'Analysis of 50 separate 150 nm wells. Nucleation order is inferred from relative island size under stated kinetic assumptions, not measured by real-time imaging.',
  'original_plot_with_author_derived_variables',
  ['Only three measured nearest-neighbor distances were below 100 nm.','Center-to-center distances are bounded by island/well geometry: 15–135 nm possible, usually about 125 nm maximum.',
   'The plotted uncertainty marks are retained without assigning an unreported error-bar statistic.','No numerical points were digitized.']),
 ('figure-5','figure',5,[84,74,568,818], 'Author-derived initial nucleation time dependence',
  'Island counts are plotted against a radius-cubed growth-time proxy. A nonlinear curve on the rising edge illustrates the authors\' assisted-homogeneous-nucleation interpretation.',
  '150 nm-well largest-island analysis, using an assumed growth law and an arbitrary reference island. This is not directly measured elapsed-time data or a time-resolved synthesis trajectory.',
  'original_analysis_plot_and_model_curve',
  ['The horizontal expression R_L^3−R_i^3 is a time proxy, not time in seconds or minutes.','The caption assumes dr/dt=k r^−2; source island-size resolution is approximately 5 nm.',
   'The source sets R_L to a hypothetical island a few nanometers larger than the largest observed island and mentions 40 nm in that sentence; do not silently recast this as an exact physical critical radius or measured recipe time.',
   'No fit constants, curve data or plotted points were extracted/digitized.']),
 ('figure-6','figure',5,[595,75,1079,751], 'Single-dot 100 nm well: AFM image and height profile',
  'The upper AFM view shows a single central feature in an approximately 100 nm well. The lower panel preserves the measured height-distance profile across the well base.',
  'One depicted 100 nm well. Three of four imaged wells contained one central feature; one appeared empty. This small observation set is not a wafer-wide yield. Keep upper image and lower profile together.',
  'original_afm_image_and_profile',
  ['Caption reports measured height 1.4 nm as a lower bound on radius and measured width 33 nm as an upper bound on diameter, given probe convolution and a hemispherical-like morphology assumption.',
   'Do not label the particle as exactly 33 nm in diameter.','Adjacent prose gives first-well diameter bounds 3.0–34 nm and a second-well range 3.0–35 nm; summary rounds to 3–30 nm. These are distinct scopes, not values to average.',
   'The original embedded AFM raster is intrinsically soft; no sharpening or recreated axes were applied.']),
 ('equation-1','equation',3,[235,558,570,601], 'Island growth law',
  'R^n−R_0^n=k(t−t_0), the source growth-law relation.',
  'Author modeling discussion: n=3 is proposed as the likely growth description, with n=2 and 4 discussed through prior work. Not a fitted exponent measured from these arrays.',
  'original_author_equation',
  ['R denotes growing-island size; R_0 is critical island size; t−t_0 is elapsed time after critical size is reached.']),
 ('equation-2','equation',4,[219,1239,571,1279], 'Unconfined-surface diffusion equation',
  '∂C/∂t−D∇²C=S−kC, the source monomer diffusion-and-sink model.',
  'Comparison model for an unconfined surface, used to interpret spatial confinement; not a numerical simulation of the measured wells.',
  'original_author_equation',
  ['S is incident monomer flux times sticking coefficient; kC represents the averaged sink of other islands.','The source cites a private communication for this formulation; no independently retrieved derivation is claimed.']),
 ('equation-3','equation',4,[700,74,1079,113], 'Steady-state radial monomer profile',
  'C(r)=C_b[1−K_0(r/ζ)/K_0(a/ζ)], the source steady-state two-dimensional solution.',
  'Analytical unconfined-surface comparison with C(a)=0 and far-field C=C_b. The screening length ζ=(D/k)^(1/2) and island radius a are model variables; no measured diffusion constants are supplied here.',
  'original_author_equation',
  ['K_0 is the zeroth-order modified Bessel function of the second kind.','Do not promote this expression to experimentally measured concentrations or a quantitative prediction for each confined well.'])]
items=[]
for id,kind,page,box,title,caption,scope,evidence_type,quant in SPECS:
 preview=Image.open(REVIEW/f'main-{page}.png');w0,h0=preview.size
 assert (w0,h0)==(1190,1540),(w0,h0)
 image=Image.open(OUT/'source-render'/f'main-{page}.png');width,height=image.size
 normalized=[box[0]/w0,box[1]/h0,box[2]/w0,box[3]/h0]
 actual=[math.floor(normalized[0]*width),math.floor(normalized[1]*height),math.ceil(normalized[2]*width),math.ceil(normalized[3]*height)]
 crop=image.crop(tuple(actual));path=OUT/(id+'.png');crop.save(path)
 items.append({'id':id,'type':kind,'pdf_page':page,'printed_page':3143+page,'title':title,
 'caption_paraphrase':caption,'sample_scope':scope,'evidence_type':evidence_type,'quantitative_context':quant,
 'source_doi':'10.1021/jp951903v','source_file':SOURCE.name,'source_sha256':source_hash,
 'render_dpi':DPI,'coordinate_origin':'top-left','source_render_dimensions_px':[width,height],
 'selection_preview_dimensions_px':[w0,h0],'selection_preview_bbox_px':box,'crop_normalized':normalized,
 'bbox_px':actual,'dimensions_px':list(crop.size),'file':path.name,'sha256':sha(path),
 'original_panels_kept_together':True,'caption_axes_labels_retained':True,
 'raw_data_digitized':False,'eligible_training':False,'visual_review':'passed; original images, captions, axes and equation symbols visually inspected at final crop resolution'})
manifest={'source_doi':'10.1021/jp951903v','source_title':'Spatially Confined Chemistry: Fabrication of Ge Quantum Dot Arrays',
 'journal':'Journal of Physical Chemistry','year':1996,'volume':100,'printed_pages':'3144–3149',
 'source_file':SOURCE.name,'source_sha256':source_hash,'page_count':6,
 'renderer':'Poppler pdftoppm','render_dpi':DPI,'coordinate_origin':'top-left',
 'scope':'All six supplied main pages read and visually inspected for original figures, tables, schemes and equations. No SI inspected in this task.',
 'counts':{'numbered_figures':6,'tables':0,'separate_numbered_schemes':0,'numbered_equations':3,'assets':len(items)},
 'items':items,'pages':[{'pdf_page':i,'printed_page':3143+i,'text_read':True,'visual_reviewed':True,
 'text_file':f'plain-page-{i}.txt','text_sha256':sha(REVIEW/f'plain-page-{i}.txt'),
 'original_visual_item_ids':[x['id'] for x in items if x['pdf_page']==i]} for i in range(1,7)],
 'absent_visuals':['No Raman spectrum plotted; 301 cm−1 Ge LO phonon reported in text.',
 'No near-IR spectrum plotted; 5890 cm−1 feature reported in text.','No SAED pattern, XRD trace or experimentally refined CIF supplied in these six pages.'],
 'no_enhancement':True,'no_curve_digitization':True,'no_site_changes':True}
dump(OUT/'manifest.json',manifest)
print(json.dumps({'assets':len(items),'source_sha256':source_hash,'items':[(i['id'],i['dimensions_px']) for i in items]},ensure_ascii=False))

