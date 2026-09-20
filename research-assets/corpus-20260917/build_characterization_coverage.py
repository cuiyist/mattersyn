import copy
import hashlib
import json
from pathlib import Path
from pypdf import PdfReader

ROOT=Path('[local path redacted]')
R=ROOT/'research-assets'
OUT=R/'corpus-20260917'
old=json.loads((R/'murray1993-characterization.json').read_text(encoding='utf-8'))
manifest=json.loads((OUT/'crop-manifest.json').read_text(encoding='utf-8'))
for asset in manifest['figures']:
    asset['visually_verified']=True
    asset['visual_review']='Compared source page and 300-dpi crop; axes, ticks, panel keys, original indexing and/or scale bars are intact. Original caption is supplied separately as a paraphrase.'
(OUT/'crop-manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
existing=json.loads((R/'murray1993-figures/figure-manifest.json').read_text(encoding='utf-8'))
assetmap={a['figure']:a for a in manifest['figures'] if a['source_key']=='murray1993'}
existingmap={a['figure']:a for a in existing['figures']}
category={1:'absorption_and_fractionation',2:'absorption_composition_comparison',3:'absorption_size_series',4:'optical_transition_experiment_vs_theory',5:'absorption_and_photoluminescence',6:'TEM_size_shape',7:'TEM_stacking_faults',8:'TEM_orientation_and_stacking_faults',9:'TEM_particle_assembly',10:'XRD_composition_comparison',11:'XRD_size_series',12:'XRD_phase_models_vs_experiment',13:'XRD_shape_models_vs_experiment',14:'XRD_small_particle_models_vs_experiment',15:'XRD_surface_disorder_model_vs_experiment'}
figs=[]
for x in old['optical_properties']+old['structural_experiments']+old['structural_model_comparisons']:
    if 'figure' not in x: continue
    n=x['figure']
    evidence=copy.deepcopy(x)
    # These local identifiers are evidence locators, not reported batch/sample labels.
    local_id=evidence.pop('sample_id',None)
    figs.append({
        'id':f'murray1993-figure-{n:02}', 'figure':n, 'category':category[n],
        'caption_paraphrase':x['caption_paraphrase'], 'source':x['source'],
        'sample':{'source_assigned_batch_id':None,'source_assigned_sample_label':None,'source_figure_label':f'Figure {n}','curator_evidence_locator':local_id or f'figure_{n}_comparison','recipe_link_status':'unresolved','linked_recipe_record_ids':[], 'cross_figure_identity':'not established; equal reported size alone does not establish identity or difference'},
        'eligible_training':False,
        'training_exclusion_reason':'No exact figure-specimen-to-Method-1/Method-2 operating conditions are assigned by this article. Retain as characterization evidence, not a recipe target. Model curves are additionally excluded from experimental labels.',
        'scoped_quantitative_facts_and_findings':{k:v for k,v in evidence.items() if k not in ['id','figure','source','evidence_kind','caption_paraphrase']},
        'evidence_kind':x['evidence_kind'],
        'already_on_site':{'original_figure_visible':n in existingmap,'structured_characterization_metadata':True,'assessment_scope':'Read-only snapshot of the two Murray method pages before this coverage integration; existing original-figure tabs are 3,5,6,11,15. Text or metadata may already mention other figures.'},
        'original_figure_asset':assetmap.get(n,existingmap.get(n)),
    })
figs.sort(key=lambda x:x['figure'])

methods=copy.deepcopy(old['methods'])
methods['xrd']['additional_as_printed_parameters']={
    'accelerating_voltage':{'value':250,'unit':'kV','status':'reported_as_printed','warning':'Potential source error: unusually high for the stated instrument. Preserve as printed with this flag; no silent correction or SOP endorsement.'},
    'current':{'value':200,'unit':'mA','status':'reported'},
    'scatter_and_diffraction_slits':{'value':0.50,'unit':'degree','status':'reported'},
    'collection_slit':{'value':0.15,'unit':'mm','status':'reported'},
}
extra=[
 {'id':'growth_absorption_width_proxy','source':{'pdf_page':3,'printed_page':8708,'section':'Nucleation and Growth'},'category':'process_monitoring_observation','finding':'During growth, absorption widths are used only as a crude indicator of size-distribution width. Typical linewidth is 50 nm FWHM; this is not the numerical linewidth of Figure 5.','quantities':[{'value':50,'unit':'nm','qualifier':'typically','property':'absorption FWHM during growth'}]},
 {'id':'growth_feature_bottleneck_interpretation','source':{'pdf_page':3,'printed_page':8708,'section':'Nucleation and Growth'},'category':'author_interpretation','finding':'Sharper features near selected sizes are proposed as possible kinetic or thermodynamic growth bottlenecks. These are not assigned reaction-time endpoints or a validated magic-size series.','quantities':[{'value':[12,20,35,45,51],'unit':'angstrom','property':'major-axis sizes discussed'}]},
 {'id':'surface_exchange_effect','source':{'pdf_page':4,'printed_page':8709,'section':'Surface Exchange'},'category':'qualitative_surface_and_dispersion_observation','finding':'Pyridine exchange enables polar/aromatic dispersion and causes a slight decrease in mean size and a small broadening. The proposed loss of Cd/Se-containing species is an author explanation; no numerical etching rate or ligand inventory is measured.'},
 {'id':'surface_relaxation_model','source':{'pdf_page':9,'printed_page':8714,'section':'Structural Simulations, left column'},'category':'model_assumptions','finding':'The authors model undercoordinated surface ions with radial shifts, conserving approximately bulk average bond length. The selected relaxation is explicitly nonunique and does not determine an actual surface structure.','quantities':[{'value':0.40,'unit':'angstrom','property':'modeled surface-cation inward displacement toward cylinder axis'},{'value':0.20,'unit':'angstrom','property':'modeled surface-anion outward displacement'},{'value':0.005,'unit':'angstrom','property':'model average-bond-length deviation bound from bulk','qualifier':'plus/minus'},{'value':50,'unit':'angstrom','property':'size above which modeled surface-disorder effect becomes imperceptible','qualifier':'greater than'}]},
 {'id':'xrd_fit_design','source':{'pdf_page':9,'printed_page':8714,'section':'Structural summary'},'category':'model_fit_design','finding':'Seven parameters: lattice constant, thermal disorder, crystallite size, aspect ratio, stacking-fault density, surface disorder and constant background. Bulk lattice and TEM size constrain two; four are fitted on one size then fixed across sizes; average fault density may vary. This is a working structural description, not a measured atomic-coordinate reconstruction.'},
 {'id':'smallest_particle_phase_scope','source':{'pdf_page':7,'printed_page':8712,'section':'X-ray Diffraction'},'category':'interpretation_boundary','finding':'For the approximately 12-angstrom species, authors say too few atoms exist to define a core crystal structure meaningfully as wurtzite versus zinc blende. Do not label the 1.2-nm case as an experimentally determined bulk polytype.'},
 {'id':'xrd_size_estimation_scope','source':{'pdf_page':7,'printed_page':8712,'section':'Structural Simulations'},'category':'measurement_interpretation','finding':'Finite size and faults broaden/convolve peaks; first-feature peak position alone is unreliable for lattice spacing or size. Authors recommend the (110) feature for crude Scherrer estimates rather than the merged (100)/(002)/(101) feature.'},
]
for x in extra:
    x['sample_link_status']='unassigned_article_level_or_model'
    x['eligible_training']=False

nak_asset=next(x for x in manifest['figures'] if x['source_key']=='nak2017_si')
nak_main=ROOT/'downloaded_papers/10.1021_acs.chemmater.7b00354.pdf'
nak_si=ROOT/'downloaded_papers/10.1021_acs.chemmater.7b00354_si_1.pdf'
peng=ROOT/'downloaded_papers/35003535.pdf'
cross={
 'peng2000':{
  'title':'Shape control of CdSe nanocrystals','doi':'10.1038/35003535','main_pdf':str(peng),'sha256':hashlib.sha256(peng.read_bytes()).hexdigest(),'inspected_pdf_pages':[1,2,3],
  'saed':{'status':'no SAED image in the inspected main article','figures':None,'not_to_confuse_with':'Figure 2 on printed page 59 is powder X-ray diffraction (experimental and simulated). Figures 1 and 3 are TEM images.'},
  'figures':[{'id':'Figure 1','pdf_page':1,'printed_page':59,'kind':'TEM','scope':'CdSe rods: low-resolution a-c; high-resolution d/e correspond to sample a and f/g to sample c.'},{'id':'Figure 2','pdf_page':1,'printed_page':59,'kind':'XRD experiment/model comparison','scope':'CdSe rods 5.6 x 4.2 nm and 9.1 x 4.5 nm; not electron diffraction.'},{'id':'Figure 3','pdf_page':2,'printed_page':60,'kind':'TEM','scope':'Three-dimensional rod orientation and assembly; not a measured growth-time sequence.'},{'id':'Figure 4','pdf_page':2,'printed_page':60,'kind':'optical absorption, PL, polarization','scope':'a/b bare dot/rod optical comparison; c core/shell rod shell-growth spectra; d aligned rods in stretched polymer at 4.7 K. Shell-dependent yield cannot be attributed to the bare-core recipe.'}],
  'matching_si_status':'not located or verified locally; statement is limited to supplied main PDF',
  'eligible_training':False,
 },
 'nakonechnyi2017':{
  'title':'Mechanistic Insights in Seeded Growth Synthesis of Colloidal Core/Shell Quantum Dots','doi':'10.1021/acs.chemmater.7b00354','main_pdf':str(nak_main),'si_pdf':str(nak_si),'main_sha256':hashlib.sha256(nak_main.read_bytes()).hexdigest(),'si_sha256':hashlib.sha256(nak_si.read_bytes()).hexdigest(),
  'si_match_evidence':'Title and author list on SI first page match the main article; SAED section explicitly identifies these article core/shell systems.',
  'saed':{'status':'real published SAED patterns found and visually verified','source':{'figure':'S2','pdf_page':3,'printed_page':'S3','section':'S2 Quantum Dots by Seeded Growth, Selected Area Diffraction'},'caption_paraphrase':'Four core/shell products show overall wurtzite or zinc-blende order corresponding to the phase of their CdSe seeds.','panels':[{'panel':'a','core':'wurtzite CdSe','shell':'CdS','product':'wz-CdSe/CdS'},{'panel':'b','core':'zinc-blende CdSe','shell':'CdS','product':'zb-CdSe/CdS'},{'panel':'c','core':'wurtzite CdSe','shell':'ZnSe','product':'wz-CdSe/ZnSe'},{'panel':'d','core':'zinc-blende CdSe','shell':'ZnSe','product':'zb-CdSe/ZnSe','source_caption_spelling':'zb-CdSe-ZnSe'}],'original_figure_asset':nak_asset,'scope_warning':'These patterns characterize seeded-growth core/shell products used for TEM analysis. None is an SAED pattern of the selected bare CdSe core recipe. Do not use any of the four patterns as that core record\'s observed phase label.','sample_link_status':'core/shell sample-family linkage explicit; individual batch IDs and transfer to selected core recipe not established','eligible_training':False},
  'other_si_scope':'Figure S1, PDF page 2/printed S2, contains blank seeded-growth optical controls. Table S1 belongs to reaction simulations, not measured recipe parameters.',
 }
}

doc={
 'audit_date':'2026-09-17','scope':'Complete 10-page Murray main-article characterization audit plus bounded SAED verification of Peng main and matching Nakonechnyi main/SI. No website source files changed.',
 'source':{**old['source'],'downloaded_pdf':str(ROOT/'downloaded_papers/10.1021_ja00072a025.pdf'),'sha256':hashlib.sha256((R/'murray1993-main.pdf').read_bytes()).hexdigest(),'downloaded_and_research_copy_identical':True,'visual_inspection_pdf_pages':list(range(1,11))},
 'inventory':{'main_figure_count':15,'main_table_count':0,'original_figure_images_already_visible':[3,5,6,11,15],'newly_extracted_original_figures':[1,2,4,7,8,9,10,12,13,14],'main_equations':'Discrete Debye scattering equation on printed p. 8712; mathematical model, not an experimental synthesis operation.','si_status':'not located or verified; no SAED or Raman claim is made about an unseen SI'},
 'evidence_rules':old['evidence_rules']+['A figure-evidence locator is not a newly invented experimental batch.','All figure evidence remains ineligible for recipe-target training until an explicit sample-to-protocol mapping is established.','No exact spectral maxima, lattice spacings or coordinate pairs have been inferred from graph pixels.'],
 'figures':figs,'measurement_methods':methods,
 'text_only_and_prior_work_evidence':old['other_structural_evidence'],
 'additional_article_evidence':extra+[x for x in old['optical_properties'] if 'figure' not in x],
 'not_reported_in_inspected_main':old['not_reported_in_inspected_main'],
 'saed_conclusion':{'status':'reported qualitatively in text; pattern not shown','source':{'pdf_page':6,'printed_page':8711,'section':'Transmission Electron Microscopy, lower left column'},'finding':'Selected-area electron diffraction is said to confirm predominantly wurtzite structure. Nonrandom orientation on carbon complicates line-shape interpretation; electron microdiffraction is proposed as a potential alternative and cited, not reported as a new figure.','display_recommendation':'Show a clearly labeled text-only evidence card, not a generated SAED image or an XRD graph mislabeled SAED.','eligible_training':False},
 'related_paper_saed_check':cross,'crop_manifest':str(OUT/'crop-manifest.json'),
}
for item in doc['additional_article_evidence']:
    item.setdefault('eligible_training',False)
    item.setdefault('sample_link_status','unassigned_article_level')
(OUT/'murray-characterization-coverage.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding='utf-8')
assert [x['figure'] for x in figs]==list(range(1,16))
assert all(x['eligible_training'] is False for x in figs)
assert all(Path(x['original_figure_asset'].get('file') if x['figure'] in assetmap else x['original_figure_asset']['path']).is_file() for x in figs)
print('Wrote coverage:',len(figs),'figures;',len(extra),'additional evidence capsules; Nak SI SAED preserved with core/shell boundary.')
