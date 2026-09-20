"""Original Danek1996 PDF crops; no redrawing, spectrum generation or digitization."""
import json,hashlib,math,subprocess,sys
from pathlib import Path
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')
OUT=Path(__file__).resolve().parent
REVIEW=OUT.parent
SOURCE=Path('[local path redacted]')
POPPLER=Path('[local path redacted]')
DPI=300
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sourcehash=sha(SOURCE)
assert sourcehash=='cde428b3707ab7e0fe1a24cd747e6c884d6903265d4d745a93e36d60e553321f'
(OUT/'source-render').mkdir(exist_ok=True)
if not all((OUT/'source-render'/f'main-{i}.png').exists() for i in range(3,9)):
    subprocess.run([str(POPPLER),'-f','3','-l','8','-r',str(DPI),'-png',str(SOURCE),str(OUT/'source-render/main')],check=True)
SPECS=[
 {'id':'figure-1','type':'figure','pdf_page':3,'box':[595,72,1078,478],
  'title':'Absorption evolution during ZnSe overgrowth of CdSe seeds',
  'caption_paraphrase':'UV/visible absorption of one reaction mixture at successive overgrowth stages, with the corresponding HRTEM particle sizes in an inset table.',
  'sample_scope':'Approximately 4.0 nm initial CdSe nuclei and samples a–d along the depicted overgrowth sequence. The source does not give the precursor dose, elapsed time or exact composition ratio for each of a–d.',
  'panels':[{'label':'a','scope':'Initial/earliest reaction-mixture trace; inset size 4.0 nm, s=±12%.'},{'label':'b','scope':'Overgrowth-stage trace; inset size 4.4 nm, s=±11%.'},{'label':'c','scope':'Overgrowth-stage trace; inset size 5.0 nm, s=±13%.'},{'label':'d','scope':'Overgrowth-stage trace; inset size 6.8 nm, s=±13%.'}],
  'quantitative_context':['The short-wavelength part carries an original ×0.1 scaling annotation; preserve it when comparing traces.','The body identifies s as the size-distribution standard deviation, but describes the initial spread as approximately 10%, whereas the inset prints ±12%. Do not silently replace either value.','Inset values are particle sizes, not independently measured core diameter plus shell thickness. No point coordinates or spectrum were digitized.'],
  'evidence_type':'original_absorption_spectra_with_embedded_measurement_table'},
 {'id':'figure-1-size-table','type':'embedded_table','parent_id':'figure-1','pdf_page':3,'box':[855,90,1031,177],
  'title':'Original HRTEM size table embedded in Figure 1',
  'caption_paraphrase':'Sample-letter and particle-size table from the absorption-overgrowth figure.',
  'sample_scope':'This is an enlarged crop of the same source table already retained in Figure 1, not a separate experimental series or independently counted dataset.',
  'table_rows':[{'source_sample_label':'a','particle_size_nm':4.0,'reported_s_percent':12},{'source_sample_label':'b','particle_size_nm':4.4,'reported_s_percent':11},{'source_sample_label':'c','particle_size_nm':5.0,'reported_s_percent':13},{'source_sample_label':'d','particle_size_nm':6.8,'reported_s_percent':13}],
  'quantitative_context':['The literal table uses s=±12%, ±11%, ±13%, ±13%; body text calls s a standard deviation.','No individual count, sizing method detail, dosing time, or exact precursor dose per row is supplied here.'],
  'evidence_type':'original_embedded_measurement_table'},
 {'id':'reaction-1','type':'unnumbered_reaction','pdf_page':3,'box':[84,499,563,582],
  'title':'Unfavorable aqueous cation-displacement comparison',
  'caption_paraphrase':'Zn²⁺(aq) + CdSe(s) ⇌ Cd²⁺(aq) + ZnSe(s), discussed as thermodynamically unfavorable with ΔG°=56.0 kJ/mol.',
  'sample_scope':'Explanatory comparison used to motivate heterogeneous overgrowth. This is not the operational TOP/DEZn/TOPSe synthesis reaction, not an aqueous recipe and not measured reaction calorimetry.',
  'quantitative_context':['The displayed equation is unnumbered in the source.','The free-energy statement is part of the authors’ mechanistic discussion; no experimental sample is attached to it.'],
  'evidence_type':'original_contextual_chemical_equation'},
 {'id':'figure-2','type':'figure','pdf_page':4,'box':[84,76,563,730],
  'title':'HRTEM of ZnSe-overcoated CdSe particles',
  'caption_paraphrase':'Lattice-resolved electron micrograph of derivatized CdSe/ZnSe particles with approximately 2.5 ZnSe/CdSe composition ratio.',
  'sample_scope':'The structural-characterization population has [ZnSe/CdSe]≈2.5 and approximately 6.8 nm overall size in the adjoining discussion and Figure 3. The micrograph is not a uniquely identified batch or single fully resolved core/shell interface.',
  'quantitative_context':['Original 5.0 nm scale bar retained.','The source describes an approximately 1.3 aspect ratio for the approximately 6.8 nm particles.','Coherent fringes in some particles are consistent with epitaxial growth, but the authors explicitly state that the images do not significantly locate the CdSe/ZnSe interface.','Some particle peripheries lack diffraction contrast; amorphous/disordered overlayer is offered as an interpretation, not a uniquely determined phase.'],
  'evidence_type':'original_hrtem_micrograph'},
 {'id':'figure-3','type':'figure','pdf_page':4,'box':[596,72,1078,548],
  'title':'Particle XRD and separate wurtzite reference lines',
  'caption_paraphrase':'X-ray patterns compare overcoated particles and initial CdSe nanocrystals against bulk wurtzite ZnSe and CdSe line positions.',
  'sample_scope':'Trace a: approximately 6.8 nm CdSe/ZnSe particles, [ZnSe/CdSe]≈2.5. Trace b: approximately 4.0 nm CdSe particles. Panels c and d: wurtzite reference line sets, not additional synthesized sample spectra.',
  'panels':[{'label':'a','scope':'Measured overcoated-particle pattern.'},{'label':'b','scope':'Measured initial CdSe particle pattern.'},{'label':'c','scope':'Wurtzite ZnSe reference powder lines.'},{'label':'d','scope':'Wurtzite CdSe reference powder lines.'}],
  'quantitative_context':['The horizontal axis is 2θ; normalized intensity is plotted. Original reference panels and captions remain together.','The broad composite features do not directly coincide with either pure reference. The paper calls for detailed pattern simulation; it does not provide refined atomic coordinates or a solved shell structure.','Poor crystallinity/disorder and lattice-spacing variation from mismatch are considered; do not label the ZnSe shell as an experimentally established perfect wurtzite lattice.'],
  'evidence_type':'original_xrd_patterns_plus_external_reference_lines'},
 {'id':'figure-4','type':'figure','pdf_page':4,'box':[596,556,1078,958],
  'title':'Optical absorption before and after film annealing',
  'caption_paraphrase':'Room-temperature absorption of a solution-deposited film of overcoated particles before and after helium annealing, with a calculated bulk-alloy band-gap marker.',
  'sample_scope':'Film of CdSe/ZnSe particles with [ZnSe/CdSe]=2.5, deposited from solution onto a glass slide for the annealing comparison. This is distinct from the later ES-OMCVD composite-film series.',
  'panels':[{'label':'a','scope':'Before annealing.'},{'label':'b','scope':'After helium annealing.'}],
  'quantitative_context':['Temperature conflict: caption prints approximately 450 °C; adjoining body text prints approximately 400 °C for approximately 30 min in He. Preserve both with their source locators.','The Zn0.7Cd0.3Se marker is a calculated bulk band gap, not the experimentally refined composition or crystal structure of an individual particle.','The post-anneal short-wavelength absorption supports the authors’ alloying interpretation. It is not proof of a defect-free pre-anneal shell.'],
  'evidence_type':'original_absorption_comparison_with_calculated_reference_marker'},
 {'id':'figure-5','type':'figure','pdf_page':5,'box':[84,75,563,740],
  'title':'Solution absorption and quantum-yield-scaled photoluminescence',
  'caption_paraphrase':'Room-temperature absorption and emission of bare and overcoated particles dispersed in pyridine.',
  'sample_scope':'Optical samples were isolated at different stages of a single preparation from identical initial CdSe particles. a is bare CdSe; b–d have [ZnSe/CdSe] ratios 3.6, 4.3 and 4.8. Do not equate these letters with the different size sequence in Figure 1.',
  'panels':[{'label':'a','scope':'Bare CdSe; caption φ≈0.05%.'},{'label':'b','scope':'Ratio 3.6; φ≈0.4%.'},{'label':'c','scope':'Ratio 4.3; φ≈0.4%.'},{'label':'d','scope':'Ratio 4.8; φ≈0.3%.'}],
  'quantitative_context':['Photoluminescence excitation is 480 nm; the figure retains both emission and absorption panels with the original ×0.1 absorption scaling.','Body text reports approximately 4 nm absorption red shift, approximately 2–4 nm band-edge-emission red shift and approximately 10 nm Stokes shift. These describe the solution optical series, not the ES-OMCVD films.','Absolute yields were estimated against rhodamine 590 in methanol; bare pyridine-capped yield is also discussed as approximately 0–0.05%.','The roughly 10% TOP/TOPO-capped CdSe yield cited in the prose belongs to prior work, not this pyridine sample series.'],
  'evidence_type':'original_solution_absorption_and_photoluminescence'},
 {'id':'figure-6','type':'figure','pdf_page':5,'box':[596,75,1078,495],
  'title':'Solution photoluminescence-excitation spectra',
  'caption_paraphrase':'Room-temperature excitation spectra compare bare CdSe with the ratio 3.6, 4.3 and 4.8 overcoated solution samples.',
  'sample_scope':'Same source-defined solution optical comparison as Figure 5: a filled circles is bare CdSe; b filled diamonds ratio 3.6; c open triangles ratio 4.3; d open squares ratio 4.8.',
  'quantitative_context':['Emission detection is 570 nm; spectra are normalized to intensity at excitation wavelength 550 nm.','Short-wavelength excitation efficiency is not monotonic with added overlayer; the ratio 4.8 sample decreases relative to the intermediate samples.','These normalized excitation curves are not absorption spectra, absolute quantum yield measurements, or proof that every particle has an intact interface.'],
  'evidence_type':'original_solution_photoluminescence_excitation'},
 {'id':'figure-7','type':'figure','pdf_page':6,'box':[596,76,1078,725],
  'title':'Room-temperature emission of ES-OMCVD composite films',
  'caption_paraphrase':'Bare-dot and overcoated-dot composite films show different band-edge and deep-trap emission at three deposition-temperature comparisons.',
  'sample_scope':'ES-OMCVD films incorporating bare CdSe (dotted) versus pre-overcoated dots (solid), with the caption explicitly stating [ZnSe/CdSe]=0.4 for the overcoated dots. This 0.4 must not be silently changed to the 4.0 used in Figure 10.',
  'panels':[{'label':'a','scope':'Both film types deposited at 150 °C.'},{'label':'b','scope':'Both film types deposited at 200 °C.'},{'label':'c','scope':'Bare-dot film deposited at 250 °C; overcoated-dot film at 270 °C.'}],
  'quantitative_context':['Measurement is room temperature; excitation is 480 nm.','Original normalized intensities and ×5 annotation are retained; do not compare plotted amplitudes as unscaled absolute yields.','The caption notes minor nanocrystallite-size differences between experiments. A single common initial particle diameter is not specified for this figure.'],
  'evidence_type':'original_composite_film_photoluminescence'},
 {'id':'figure-8','type':'figure','pdf_page':7,'box':[84,74,563,704],
  'title':'10 K emission of ES-OMCVD composite films',
  'caption_paraphrase':'Low-temperature spectra compare bare-dot and overcoated-dot composite films across deposition temperatures.',
  'sample_scope':'Caption-defined counterpart of the Figure 7 film comparison: bare dots versus overcoated dots with [ZnSe/CdSe]=0.4, measured at 10 K. Minor particle-size variations between experiments remain explicit.',
  'panels':[{'label':'a','scope':'150 °C deposition.'},{'label':'b','scope':'200 °C deposition.'},{'label':'c','scope':'250 °C for bare-dot film; 270 °C for overcoated-dot film.'}],
  'quantitative_context':['Excitation is 480 nm. Retain all ×10, ×15, ×1.5, ×68 and ×6.8 graphical scaling annotations and line styles.','Body text describes approximately 8 nm blue shift across 150–270 °C for overcoated-dot films.','The approximately 5–60 min thermal-exposure range is a depth-dependent history of particles incorporated during film growth, not a unique synthesis time assigned to every curve.'],
  'evidence_type':'original_low_temperature_composite_photoluminescence'},
 {'id':'figure-9','type':'figure','pdf_page':7,'box':[596,74,1078,513],
  'title':'Bare-dot film excitation spectra at 300 K and 10 K',
  'caption_paraphrase':'Excitation spectra of a 200 °C-deposited composite film containing bare CdSe, with cubic-ZnSe band-gap markers.',
  'sample_scope':'Bare-dot ES-OMCVD composite deposited at 200 °C. Filled circles: 300 K, detection 554 nm. Open squares: 10 K, detection 546 nm. Open diamonds: 10 K, detection 710 nm.',
  'quantitative_context':['Band-gap arrows are cubic-ZnSe reference values at 300 K and 10 K, not a new diffraction refinement of this film or the ZnSe shell.','The 710 nm-detected excitation curve supports assignment of deep-level emission to CdSe dots.','No corresponding bare-dot core diameter or uniquely identified synthesis batch is supplied in this caption.'],
  'evidence_type':'original_composite_excitation_with_bulk_bandgap_markers'},
 {'id':'figure-10','type':'figure','pdf_page':7,'box':[596,520,1078,952],
  'title':'Overcoated-dot film excitation spectra at 300 K and 10 K',
  'caption_paraphrase':'Excitation spectra of a 200 °C-deposited film containing overcoated approximately 3.7 nm initial CdSe dots.',
  'sample_scope':'This film is expressly assigned initial CdSe size approximately 3.7 nm and [ZnSe/CdSe]=4.0. It is distinct from the ratio 0.4 captions in Figures 7–8 and the ratio 2.5 structural/annealing set.',
  'quantitative_context':['Filled circles: 300 K, emission detection 576 nm. Open squares: 10 K, emission detection 570 nm.','Cubic-ZnSe bulk band-gap arrows are reference markers, not experimental atomic coordinates.','The authors interpret short-wavelength suppression as inefficient matrix-to-dot excitation due to recombination in the polycrystalline matrix. This is an interpretation, not a direct defect count.'],
  'evidence_type':'original_composite_excitation_with_bulk_bandgap_markers'},
 {'id':'figure-11','type':'figure','pdf_page':8,'box':[84,78,563,552],
  'title':'Relative film photoluminescence versus calculated ZnSe coverage',
  'caption_paraphrase':'Band-edge-emission yield of composite films is compared with model-derived ZnSe monolayer coverage at two deposition temperatures.',
  'sample_scope':'Film series deposited at 200 °C (filled circles) and 260 °C (open squares), incorporating bare and passivated CdSe dots. Coverage is calculated from composition and initial particle size under a symmetric core/shell assumption.',
  'quantitative_context':['Excitation is 500 nm. The relative-yield axis is logarithmic, not an absolute quantum-yield percentage.','Body text reports more than one order of magnitude improvement near approximately 0.6 monolayer and approximately 100-fold near approximately 3 monolayers.','Coverage is not directly imaged or an integer shell-layer count. Earlier AES evidence suggests nonuniform shells, so preserve the stated symmetric-shell calculation assumption.','No plotted points were digitized; source lines are retained without inventing fit parameters or uncertainty.'],
  'evidence_type':'original_relative_yield_plot_with_model_derived_coverage'}]
items=[]
for spec in SPECS:
    spec=dict(spec);box=spec.pop('box');p=spec['pdf_page'];preview=Image.open(REVIEW/f'main-{p}.png');w0,h0=preview.size
    assert (w0,h0)==(1190,1540)
    im=Image.open(OUT/'source-render'/f'main-{p}.png');w,h=im.size
    norm=[box[0]/w0,box[1]/h0,box[2]/w0,box[3]/h0]
    actual=[math.floor(norm[0]*w),math.floor(norm[1]*h),math.ceil(norm[2]*w),math.ceil(norm[3]*h)]
    crop=im.crop(actual);path=OUT/(spec['id']+'.png');crop.save(path)
    spec.update({'printed_page':172+p,'source_doi':'10.1021/cm9503137','source_file':SOURCE.name,'source_sha256':sourcehash,
     'render_dpi':DPI,'coordinate_origin':'top-left','source_render_dimensions_px':[w,h],'selection_preview_dimensions_px':[w0,h0],
     'selection_preview_bbox_px':box,'crop_normalized':norm,'bbox_px':actual,'dimensions_px':list(crop.size),'file':path.name,'sha256':sha(path),
     'original_panels_kept_together':True,'caption_axes_labels_retained':True,'raw_data_digitized':False,'eligible_training':False,
     'visual_review':'pending final crop inspection'})
    items.append(spec)
manifest={'source_doi':'10.1021/cm9503137','source_title':'Synthesis of Luminescent Thin-Film CdSe/ZnSe Quantum Dot Composites Using CdSe Quantum Dots Passivated with an Overlayer of ZnSe',
 'journal':'Chemistry of Materials','year':1996,'volume':8,'printed_pages':'173–180','source_file':SOURCE.name,'source_sha256':sourcehash,'page_count':8,
 'renderer':'Poppler pdftoppm','render_dpi':DPI,'coordinate_origin':'top-left',
 'scope':'All eight supplied main pages read in full and visually inspected. This task covers original visual assets and source-scoped reuse planning; no SI or cited paper was retrieved.',
 'counts':{'numbered_figures':11,'standalone_tables':0,'embedded_unnumbered_tables':1,'numbered_schemes':0,'numbered_equations':0,'unnumbered_reactions':1,'assets':len(items),'independent_visual_items':12},
 'items':items,'pages':[{'pdf_page':i,'printed_page':172+i,'text_read':True,'visual_reviewed':True,'text_file':f'plain-page-{i}.txt','text_sha256':sha(REVIEW/f'plain-page-{i}.txt'),
 'original_visual_item_ids':[x['id'] for x in items if x['pdf_page']==i]} for i in range(1,9)],
 'absent_visuals':['No SAED pattern is displayed.','No Raman spectrum is displayed.','AES and X-ray-fluorescence composition measurements are described in text but no raw AES/XRF spectra are plotted.','No ES-OMCVD apparatus diagram or atomistic core/shell model is supplied.','No experimentally refined CIF or atomic coordinates are supplied.'],
 'global_limits':['Figure letters are local to each figure and must not be treated as universal sample IDs.','Particle-overgrowth dispersions, drop-deposited annealing films and ES-OMCVD composite films are distinct specimen states.','The source often provides family-level conditions without doses or exact run linkage for individual samples.','The separate crop of the Figure 1 inset must not be counted as an independent dataset.'],
 'no_enhancement':True,'no_curve_digitization':True,'no_site_changes':True}
dump(OUT/'manifest.json',manifest)
print(json.dumps({'assets':len(items),'source_sha256':sourcehash,'items':[(x['id'],x['dimensions_px']) for x in items]},ensure_ascii=False))
