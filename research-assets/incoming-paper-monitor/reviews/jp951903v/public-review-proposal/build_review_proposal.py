"""Private Heath1996 source-ledger proposal; no Site, queue or source mutation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re

OUT=Path(__file__).resolve().parent
ROOT=OUT.parent
SOURCE='heath1996'
DOI='10.1021/jp951903v'
VAR100='heath-1996-ge-100nm-wells'
VAR150='heath-1996-ge-150nm-wells'
CHAR='heath-1996-ge-characterization'
CONTEXT='heath-1996-ge-unpatterned-growth-context'
EXPECTED=[VAR100,VAR150,CHAR,CONTEXT]
SHARED='Both template arrays were patterned on the same substrate and exposed together; template variants and individual wells are not independent synthesis runs. The wafer was diced after CVD; exact piece-to-analysis identity is not fully resolved.'

def read(path):return json.loads(path.read_text(encoding='utf-8'))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def locator(page,section):return f'Main PDF p. {page}, printed p. {3143+page}, {section}'
def evidence(page,section):return {'source_id':SOURCE,'locator':locator(page,section),'document_role':'main','pdf_page':page,'printed_page':3143+page}

sections={key:{'id':key,'title':title,'items':[]} for key,title in [
    ('precursors','Precursors'),('protocol','Synthesis protocol'),('structures','Final structures'),
    ('properties','Properties'),('intuition','Chemical intuition'),('sources','Sources and limitations')]}

def item(section,id,title,text,page,where,kind='reported_source_fact',records=(),templates=(),state='source context',notes=(),extra=()):
    ev=[evidence(page,where)]+[evidence(p,w) for p,w in extra]
    value={'id':id,'title':title,'text':text,'claim_type':kind,
        'sample_scope':{'template_diameters_nm':list(templates),'state':state,'physical_batch_id':None,
            'link_limit':SHARED if templates else 'Source-level context; no additional run or physical-specimen identity is inferred.'},
        'evidence':ev,'source_locators':[x['locator'] for x in ev],
        'canonical_links':[{'record_id':r,'json_pointer':'','relation':'Expected canonical record; linkage remains a private proposal pending canonical audit.'} for r in records],
        'notes':list(notes),'facts':[],'training_eligible':False}
    sections[section]['items'].append(value)
    return value


def prepare_items():
    item('precursors','substrate-and-mask','Substrate, oxide and resist',
        'The substrate is Si(100), initially cleaned and thermally oxidized to approximately 20 nm SiO2, then coated with 70 nm PMMA. Cleaning chemistry, oxidation conditions, coating formulation and molecular-weight specification are not supplied.',1,'Process Methodology',records=(VAR100,VAR150),templates=(100,150),state='template preparation')
    item('precursors','germane-stock','Germane in helium',
        'The feed is 10% GeH4 in He, delivered at 90 sccm as the mixture. The percentage basis and standard-volume reference conditions are not stated. This is not 90 sccm of pure GeH4.',2,'Process Methodology continuation',records=(VAR100,VAR150),templates=(100,150),state='CVD feed')
    item('precursors','developer','Developer and resist-removal solvent',
        'The developer contains isopropyl alcohol and methyl isobutyl ketone in the printed 3:1 order; its ratio basis and development time/temperature are not stated. An acetone rinse later removes PMMA.',1,'Process Methodology',records=(VAR100,VAR150),templates=(100,150),state='lithography and workup',extra=((2,'Process Methodology continuation'),))
    item('precursors','etch-chemicals','Dry and wet etchants',
        'Reactive-ion etching uses CF4/CHF3, with no reported gas ratio, flow, pressure, power or etch time. A brief dip in 10% HF removes native oxide from exposed Si before CVD; the percentage basis, solvent, exact duration and rinse/drying sequence are not specified.',1,'Process Methodology',records=(VAR100,VAR150),templates=(100,150),state='template etching',extra=((2,'Process Methodology continuation'),))
    item('protocol','lithography','Lithographic template formation',
        'Bake the 70 nm PMMA layer at 80 °C for 1 h. The IBM Vector Scan electron-beam system operates at 25 keV. Point-exposure pitches are 200 or 400 nm over areas from 1 mm² to 1 cm²; dose spans 50–75 µC/cm² and is controlled by beam dwell time. Development produces approximately 60 and 100 nm resist openings. Exact dose/dwell/pitch/area assignments to each template are not given.',1,'Process Methodology',records=(VAR100,VAR150),templates=(100,150),state='resist pattern',notes=('Figure 1 caption gives approximately 60–150 nm resist wells, while methods specify 60 and 100 nm openings; preserve the wording conflict rather than assigning 150 nm to a resist recipe.',))
    item('protocol','rie-templates','Two etched-well geometries',
        'CF4/CHF3 RIE transfers the openings through SiO2 to Si. Partial loss of etch anisotropy enlarges the final openings to 100 and 150 nm. RIE lag slows etching in smaller openings. No endpoint detection is used. The 150 nm wells are over-etched by about 10 nm and are approximately 30 nm deep; the 100 nm wells are approximately 17 nm deep. The later oxide-selective HF dip is invoked to expose their Si bases. These are geometrical variants on the same substrate, not separately optimized CVD conditions.',1,'Process Methodology',records=(VAR100,VAR150),templates=(100,150),state='etched templates',extra=((2,'Process Methodology continuation'),(5,'100 nm Wells')))
    item('protocol','strip-hf-load','Resist removal and loading',
        'Remove PMMA with acetone, briefly dip the shared patterned wafer in 10% HF, and introduce it into the UHV/CVD load lock. The chamber base pressure is below 5 × 10⁻⁶ Torr. Base pressure is distinct from deposition pressure; no HF dip time or complete cleaning/loading SOP is reconstructed.',2,'Process Methodology continuation',records=(VAR100,VAR150),templates=(100,150),state='pre-CVD substrate')
    item('protocol','shared-cvd','Shared selective Ge deposition',
        'Expose the wafer to 10% GeH4 in He at 90 sccm, deposition pressure 1–2 mTorr, and 600 °C for 5.0 min. Afterwards dice the wafer into several pieces for analysis. No separate condition set is supplied for the 100 and 150 nm arrays, and no cooling, wafer size, total gas consumption or run-resolved yield is reported.',2,'Process Methodology continuation',records=(VAR100,VAR150),templates=(100,150),state='as-grown patterned wafer')
    item('structures','instrumentation','Microscopy and dimensional calibration',
        'Plan-view TEM uses a JEOL 4000 at 400 kV. Particle sizes and center-to-center nearest-neighbor distances for 150 nm wells are measured from relatively low-resolution TEM, with well-center spacing as the length standard. AFM uses a Topometrix TMX 2010 MultiView in contact mode with a high-aspect-ratio carbon-whisker supertip on a silicon-nitride tip. Probe/sample convolution remains significant.',2,'Analysis of the Ge Quantum Dots',records=(CHAR,),templates=(100,150),state='diced characterization specimens')
    item('structures','fig2-scope','Figure 2 template-size conflict',
        'The methods describe Figure 2 as a low-resolution AFM image of a 25 µm² region of 100 nm wells. The Figure 2 caption calls the wells 150 nm. Its scale bar is 600 nm. Show the original image as a patterned-well overview with ambiguous template size and incompletely assigned growth state; it cannot establish either template-specific outcome.',2,'Process Methodology continuation and Figure 2 caption',kind='source_conflict',records=(CHAR,),state='ambiguous template overview')
    item('structures','150nm-outcomes','150 nm wells: islands and epitaxial alignment',
        'The source reports 2–4 Ge dots per 150 nm well, commonly at the perimeter where RIE over-etching introduced defects. Figure 3 dark-field TEM enhances Ge/Si contrast while amorphous-SiO2 boundaries are difficult to see; no explicit scale bar is visible. Moiré fringes indicate crystalline particles aligned with the Si substrate; some larger particles show fringe discontinuities interpreted as misfit dislocations. This is not a refined coordinate model or an independently measured CIF.',3,'150 nm Wells and Figure 3',records=(VAR150,CHAR),templates=(150,),state='as-grown islands',extra=((1,'Abstract and Introduction'),(2,'Analysis of the Ge Quantum Dots')))
    item('structures','150nm-statistics','Island distances in 50 wells',
        'Figure 4 uses data from 50 wells and compares first/second-island center separation with their size ratio r₂/r₁. The geometry and minimum island sizes limit possible center distances to 15–135 nm; the possible maximum is closer to 125 nm for most wells. These are geometric limits, not an observed raw-data range. Only three measured nearest-neighbor distances are below 100 nm. Error bars are plotted but their definition is not supplied. The lack of correlation underlies an effective-diffusion-field interpretation, not a direct measurement of D or a time series.',3,'150 nm Wells, final paragraph',records=(VAR150,CHAR),templates=(150,),state='TEM-derived spatial statistics',extra=((4,'Figure 4 and opening paragraphs'),))
    item('structures','100nm-imaged-cohort','100 nm wells: small AFM cohort',
        'Plan-view TEM preparation destroyed or insufficiently thinned the 100 nm regions, so four wells were examined by supertip AFM. Three show a single central structure and one no apparent island. Sharp walls and lack of wall-slope broadening differ from larger wells. The reported 3/4 observed occupancy is a four-well microscopy result, not a fabrication success probability.',5,'100 nm Wells',records=(VAR100,CHAR),templates=(100,),state='AFM cohort')
    item('structures','100nm-size-bounds','AFM size bounds and Figure 6',
        'Tip convolution makes a particle in a well appear wider and lower. Similar side-view TEM islands, not uniquely these AFM specimens, are described as faceted hemispheres with height approximately equal to radius. Thus twice AFM height is a diameter lower bound and AFM width an upper bound. Figure 6 reports 1.4 nm height and 33 nm width; body text reports 3.0–34 nm for one well and 3.0–35 nm for a second. These are bounds for individual objects, not a mean, distribution or synthesis target.',5,'100 nm Wells and Figure 6',records=(VAR100,CHAR),templates=(100,),state='individual AFM wells',notes=('Do not average bounds or collapse the figure-caption and body-text values into one exact diameter.',))
    item('structures','study-size-wording','Study-level size wording',
        'The introduction describes approximately 6–30 nm arrays and also 6–25 nm selective growth; the conclusion summarizes the 100 nm-well result as 3–30 nm. Preserve these source-level statements alongside the detailed Figure 6/body bounds. They are not interchangeable sample measurements or prospectively requested sizes.',1,'Introduction',kind='reported_study_context',records=(CHAR,),extra=((5,'100 nm Wells'),(6,'Summary and Conclusions')))
    item('properties','reported-spectroscopic-checks','Raman and near-IR checks reported in prose',
        'Micro-Raman spectroscopy detects the Ge LO phonon at 301 cm⁻¹ only on patterned substrate regions. Near-IR absorption identifies a Ge surface-state feature at 5890 cm⁻¹. The article reports these as crystallinity checks but supplies no plotted Raman or near-IR spectrum, instrument settings, line widths or raw arrays. Keep these textual observations; do not fabricate spectra or assign a feature to a particular well diameter or individual island.',2,'Analysis of the Ge Quantum Dots',records=(CHAR,),templates=(100,150),state='patterned-region spectroscopy')
    item('intuition','motivation','Why combine lithography with confined growth?',
        'The authors seek precise spatial placement, crystalline orientation and substrate contact for dots smaller than lithographic resolution. The introduction contrasts sub-50 nm fabrication with often sub-20 nm device needs, prior 2–20 nm chemically prepared structures, approximately ±0.2 nm size control, Langmuir–Blodgett arrays and 30 nm InAs islands on unpatterned GaAs. Prior epitaxial orientation or close substrate contact did not establish precise dot positioning. These comparisons motivate chemical confinement; they neither import prior recipes nor prove electrical-device performance here.',1,'Introduction',kind='author_rationale_and_cited_context',notes=('References 1–5 are background citations; any existing Murray/Littau atlas pages remain separate evidence sources.',))
    item('intuition','growth-mode','Surface energy, strain and growth modes',
        'The discussion contrasts Frank–van der Merwe layer growth, Volmer–Weber islands and Stranski–Krastanov layer-then-island growth. Cited calculations put Ge(100) surface free energy about 30% below Si(100), favoring layer growth, while approximately 4% lattice mismatch increases strain and favors S–K growth. Cited UHV/CVD context describes a transition from layer growth below T₀ = 350 °C to S–K and/or V–W modes above it. These are rationale/background values, not alternative settings demonstrated for the two patterned variants.',2,'Results and Discussion, growth-mode paragraphs',kind='author_model_and_cited_context',notes=('References 6–8 remain citation-only, not independently imported measurements.',))
    item('intuition','unpatterned-comparison','Unpatterned growth used to choose the exposure',
        'The authors screened planar unpatterned Si(100) at multiple temperatures and durations and analyzed cross sections by TEM. The most uniform islands occurred at 560–600 °C. Near 600 °C, incubation just under 5 min preceded island formation; after 8 or 9 min, islands were approximately 0.1 µm and coverage 70–90%. The patterned-wafer 5.0 min exposure therefore probes early growth. Exact screening protocols, run identities and numeric distributions are absent; this context is not an extra reconstructed recipe.',2,'Results and Discussion, unpatterned-film paragraph',kind='reported_contextual_observation',records=(CONTEXT,),state='unpatterned comparison wafers')
    item('intuition','kinetic-proxy','Island size as a relative nucleation-order proxy',
        'Equation 1 models activated nucleation followed by diffusion-controlled growth. Exponents n = 2, 3 and 4 are discussed through citations; n = 3 is judged most likely for the present system. The model assumes larger islands in a given well nucleated earlier. Smaller islands can grow faster after site saturation, narrowing distributions; the authors also report narrowing on unpatterned Si. This inference gives relative nucleation order, not measured timestamps for individual dots.',3,'Results and Discussion, Equation 1 and following paragraphs',kind='author_kinetic_model',records=(CHAR,CONTEXT),notes=('Do not turn preferred n = 3 into an independently fitted exponent.',))
    item('intuition','model-assumptions','Assumptions separating the wells',
        'The analysis assumes growth kinetics do not change with island size and that 600 °C overcomes strain-related defect-formation barriers. It also assumes GeH4 landing on SiO2 does not feed islands in wells. The source cites selective Si growth below 0.1 Torr and says its GeH4 partial pressure is about 1000-fold lower to keep oxide monomer coverage low. Preserve this rationale separately from the measured total deposition pressure and stock composition.',3,'Results and Discussion, two implicit assumptions',kind='author_model_assumption',records=(VAR100,VAR150),templates=(100,150),notes=('Selectivity threshold and factor-of-1000 comparison are author/citation context, not a new gas recipe.',))
    item('intuition','diffusion-boundaries','Effective diffusion fields and boundary reflection',
        'Equations 2–3 describe an unconfined steady-state radial diffusion model with screening length ξ = (D/k)½. Typical diffusion fields extend roughly 2–4 island radii from an island perimeter. In the wells the authors infer an effective field reaching the boundary and call its radius limit the 150 nm well diameter; do not convert that wording into a measured 75 nm radius. Reflection at oxide boundaries, rather than a measured increase in microscopic diffusion coefficient, is proposed. Several-micron Ge-adatom travel at 600 °C is cited background; lossy walls would reduce the apparent field. The confinement crossover for larger wells is not determined.',4,'Figure 4, Equations 2–3 and diffusion-field discussion',kind='author_model_and_interpretation',records=(VAR150,CHAR),templates=(150,))
    item('intuition','incubation-alternatives','Incubation and competing nucleation mechanisms',
        'The approximately 5 min incubation may reflect critical monomer buildup, but slow removal of residual oxide by GeH4 may contribute. In the paper’s limiting heterogeneous case defects eliminate the activation barrier, critical nucleus is one atom, and growth starts without later incubation; initial island-formation rate is called convex-up. In “assisted homogeneous” nucleation defects lower but retain a barrier; concentration-dependent fluctuations yield an initially concave-up rate. Both later saturate and decay. These are model interpretations, not separately observed reaction steps.',4,'Nucleation-kinetics discussion',kind='author_model_comparison',records=(CHAR,),templates=(150,))
    item('intuition','figure5-model','Figure 5: inferred initial nucleation behavior',
        'For isolated wells, the largest island in each well is used as the first-nucleation proxy. Figure 5 plots island counts against R_L³ − R_i³, labelled time, using assumed dr/dt = k r⁻². Radius/size measurements have approximately 5 nm resolution. A hypothetical R_L at t = 0 is chosen a few nanometers above the largest observed island (printed size 40 nm with unresolved radius/diameter meaning); R_L is not 40 nm. A nonlinear curve is fitted to the rising edge without a supplied fit function or parameters. The authors interpret concave-up early behavior as assisted homogeneous nucleation and S–K-type growth. This is not time-resolved kinetics; Figure 5 well count is not specified.',5,'Figure 5 and preceding discussion',kind='author_derived_kinetic_interpretation',records=(CHAR,),templates=(150,),notes=('No physical time calibration, reaction rate constant or model error bars are supplied. Equation 1 and Figure 5 reuse k symbolically; under the same k definition the integrated constants differ by a factor of three. Do not combine them to calculate time.',))
    item('intuition','small-well-outlook','Smaller wells and device outlook',
        'The lack or reduced density of perimeter defects in 100 nm wells may change the nucleation kinetics and favor a single island. The authors acknowledge that four-well AFM data give limited mechanistic insight. They propose precisely positioned, contacted and confined dots as a route toward ambient-operation Coulomb-blockade devices; no electrical transport or functioning-device measurement is reported.',5,'100 nm Wells',kind='author_hypothesis_and_outlook',records=(VAR100,CHAR),templates=(100,),extra=((6,'Summary and Conclusions'),))
    item('sources','reporting-gaps','Unreported information and reader limits',
        'Missing details include wafer dimensions/count/doping, cleaning/oxidation/coating conditions, lithography assignments, RIE settings, HF basis/time/rinse/transfer, gas percentage and standard-volume bases/purity, temperature measurement and thermal history, cooling/storage, exact diced-piece/measurement joins, AFM probe settings, full spectroscopy acquisition, raw data and measured atomic coordinates. No Raman/near-IR plots, XRD, SAED, PL, electrical performance or CIF is supplied. Figure 4/5 curves have not been digitized. SI is not located or verified. Missing information is not a failed synthesis or proof that unpublished data do not exist.',1,'Process Methodology',kind='review_gap_assessment',extra=((2,'Methodology and analysis'),(3,'150 nm Wells'),(4,'Figures 4 and equations'),(5,'Figures 5–6'),(6,'References and Notes')))
    item('sources','source-date-conflict','Printed chronology conflict',
        'The title block prints Received July 6, 1995 and In Final Form November 6, 1994, while the journal publication is 1996 and the advance-abstract footnote is January 15, 1996. Preserve this chronology conflict; do not silently correct a printed year.',1,'Title block and advance-abstract footnote',kind='source_conflict')


PAGE_SECTIONS={
    1:['Title/authors/abstract; introduction and cited motivation','Process Methodology: substrate, PMMA, lithography, development, RIE'],
    2:['Methodology continuation: well depth, strip/HF, shared-wafer UHV/CVD','Analysis: Raman, near-IR, TEM and AFM','Growth-mode rationale and unpatterned screening','Figures 1–2'],
    3:['Kinetic model and assumptions','150 nm wells: dark-field TEM, epitaxy and distances','Figure 3 and Equation 1'],
    4:['50-well statistics and effective diffusion field','Unconfined diffusion model and boundary assumptions','Alternative nucleation mechanisms','Figure 4 and Equations 2–3'],
    5:['Initial-nucleation proxy and model interpretation','100 nm well imaging, cohort and AFM bounds','Figures 5–6'],
    6:['Small-well limitations; summary and outlook','Acknowledgment; references 1–17; manuscript code'],
}

def reference_entries():
    text=(ROOT/'plain-page-6.txt').read_text(encoding='utf-8').split('References and Notes',1)[1].split('JP951903V',1)[0]
    matches=list(re.finditer(r'^\((\d+)\)\s',text,re.M))
    assert [int(m.group(1)) for m in matches]==list(range(1,18))
    roles={1:'Wet-chemical nanostructure review background',2:'Gas-phase nanostructure precedents; subentry 2c is Littau1993',3:'Murray1993 size-control precedent',4:'Langmuir–Blodgett array context; printed as in press',5:'Unpatterned InAs-island precedent',6:'Growth-mode classification',7:'Calculated Ge/Si surface-energy context',8:'Ge/Si UHV/CVD growth-mode context',9:'Growth-law exponent discussion',10:'Experimental growth-law precedent',11:'Diffusion-field aspect-ratio context',12:'Distribution-narrowing kinetics',13:'Strain/defect growth-barrier context',14:'Barrier/kinetic-limit discussion',15:'Selective deposition threshold context',16:'Private communication underlying diffusion-model discussion',17:'Ge-adatom diffusion-distance context'}
    entries=[]
    for i,m in enumerate(matches):
        n=int(m.group(1));citation=' '.join(text[m.end():matches[i+1].start() if i+1<len(matches) else len(text)].split())
        r={'reference_number':n,'citation_reader_item_id':f'reference-{n}','role':roles[n],
            'source_locators':[locator(6,f'References and Notes, entry {n}')],
            'evidence_class':'citation_only','cited_work_independently_reviewed_in_this_task':False,
            'import_experimental_evidence':False}
        if n==2:r['existing_atlas_context']={'subentry':'2c','source_id':'littau1993','doi':'10.1021/j100108a019','note':'Existing separate atlas review; the citation does not import its recipe or measurements into Heath1996.'}
        if n==3:r['existing_atlas_context']={'source_id':'murray1993','doi':'10.1021/ja00072a025','note':'Existing separate atlas entry; the citation does not import its recipe or measurements into Heath1996.'}
        entries.append(r)
        item('sources',f'reference-{n}',f'Reference {n}',citation,6,f'References and Notes, entry {n}',kind='citation_only',notes=(roles[n],'No cited experimental parameters are imported by this reference.'))
    return entries


def main():
    prepare_items()
    references=reference_entries()
    identity=read(ROOT/'source-identity.json')
    asset_manifest=read(ROOT/'crop-assets/manifest.json')
    audit_path=ROOT/'source-audit.json'
    if not audit_path.exists():
        candidates=[p for p in ROOT.glob('*audit*.json') if p.name not in ['source-identity.json']]
        assert len(candidates)==1,'Need exact independent source audit path'
        audit_path=candidates[0]
    audit=read(audit_path)
    assert audit['status']=='independent_supplied_main_text_and_visual_review_complete'
    assert audit['source']['sha256']==identity['main_sha256']==asset_manifest['source_sha256']
    assert len(audit['page_review'])==6
    for page in audit['page_review']:
        assert page['text_reviewed'] and page['visual_reviewed']
        assert digest(ROOT/page['text_file'])==page['text_sha256']
        assert digest(ROOT/page['image_file'])==page['image_sha256']
    figures=[];equations=[]
    asset_files={}
    for asset in asset_manifest['items']:
        aid=asset['id'];is_equation=asset['type']=='equation' or aid.startswith('equation')
        number=int(re.search(r'(\d+)$',aid).group(1))
        apath=ROOT/'crop-assets'/asset['file']
        if not apath.exists():apath=ROOT/asset['file']
        assert apath.exists() and digest(apath)==asset['sha256']
        asset_files[aid]={'private_path':str(apath),'sha256':asset['sha256']}
        links=([VAR100,VAR150] if number==1 else [CHAR] if number==2 else [VAR150,CHAR] if number in [3,4,5] else [VAR100,CHAR]) if not is_equation else [CHAR]
        public={
            'id':aid,'label':('Equation ' if is_equation else 'Figure ')+str(number),
            'document_role':'main','page':asset['pdf_page'],'printed_page':asset['printed_page'],
            'source_locators':[locator(asset['pdf_page'],('Equation ' if is_equation else 'Figure ')+str(number))],
            'caption_paraphrase':asset['caption_paraphrase'],'sample_scope':asset['sample_scope'],
            'sample_links':links,'sample_linkage':'Source-context link; exact piece, well or physical batch is not inferred.',
            'evidence_class':asset['evidence_type'],
            'public_asset':'assets/figures/heath1996/'+apath.name,'public_asset_sha256':asset['sha256'],
            'asset_provenance':{'source_file':'10.1021_jp951903v.pdf','source_sha256':identity['main_sha256'],
                'source_pdf_page':asset['pdf_page'],'crop_bbox_px_top_left':asset['bbox_px'],
                'render_dpi':asset_manifest['render_dpi'],'source_render_dimensions_px':asset['source_render_dimensions_px'],
                'transformation':'Original PDF raster crop; no synthetic data or redrawing.'},
            'quantitative_context':asset.get('quantitative_context',[]),
            'reviewed':False,'text_reviewed':True,'visual_reviewed':True,'reader_render_verified':False,
            'training_eligible':False,
        }
        if is_equation:
            public.update({
                'expression':{1:'R^n - R_0^n = k(t - t_0)',2:'∂C/∂t - D∇²C = S - kC',3:'C(r) = C_b[1 - K_0(r/ξ)/K_0(a/ξ)]'}[number],
                'claim_type':'author_model_not_measured_recipe_parameter',
                'assumptions':{
                    1:'Growth after a critical nucleus, with unchanged kinetics. n = 3 is preferred context; n = 2 and 4 are discussed, not separately fitted here.',
                    2:'Unconfined radial monomer model. S is flux times sticking coefficient; kC averages other-island sinks. ξ = (D/k)^(1/2). No numerical D or k is supplied.',
                    3:'Two-dimensional steady state; C(a)=0 and C approaches C_b at large r. K_0 is the modified Bessel function of the second kind. The later reflective-well interpretation is distinct from this unconfined analytical model.'}[number]})
            equations.append(public)
        else:
            public['formulation_labels']={1:['100 nm','150 nm'],2:[],3:['150 nm'],4:['150 nm'],5:['150 nm'],6:['100 nm']}[number]
            if number==2:public['limitations']=['Body text assigns 100 nm wells; caption assigns 150 nm. No forced template-specific sample join.']
            figures.append(public)
    assert len(figures)==6 and len(equations)==3
    recipe_inventory=[]
    for rid,label,rtype,scope,pages in [
        (VAR100,'Ge islands in 100 nm SiO2-bounded Si wells','protocol_variant','Same-substrate 100 nm template; four-well AFM cohort and individual size bounds do not establish a population yield.',[1,2,5]),
        (VAR150,'Ge islands in 150 nm SiO2-bounded Si wells','protocol_variant','Same-substrate 150 nm over-etched template; TEM spatial statistics and author kinetics remain separate.',[1,2,3,4,5]),
        (CHAR,'Microscopy, spectroscopy and model-linked characterization','procedure','Supporting characterization and interpretation only; not an additional synthesis.',[2,3,4,5]),
        (CONTEXT,'Unpatterned Ge growth comparison','observation','Screening and incubation context with no complete reconstructed protocol.',[2,3])]:
        recipe_inventory.append({'id':rid,'label':label,'record_ids':[rid],'record_type':rtype,'status':'private_proposal_canonical_review_pending',
            'source_locators':[locator(p,'Process Methodology / Results and Discussion') for p in pages],'scope':scope,'gaps':['Canonical source-join audit and reader integration remain pending.','Matching SI is not located or verified.']})
    ledger={
        'schema_version':'1.0','paper_id':SOURCE,'doi':DOI,'title':identity['title'],
        'paper':{'doi':DOI,'title':identity['title'],'journal':identity['journal'],'year':1996,'volume':100,'issue':8,'pages':'3144–3149','authors':'; '.join(identity['authors']),'url':'https://doi.org/'+DOI},
        'source_group':SOURCE,'corpus_paper_id':identity['existing_identity']['paper_id'],'corpus_document_id':identity['existing_identity']['document_id'],
        'review_scope':'supplied_main_only_si_unverified','supporting_information':{'status':'not_located_or_verified','note':'No matched SI is supplied or verified. Absence from local metadata and no located declaration do not prove that SI never existed.'},
        'documents':[{'role':'main','source_file':'10.1021_jp951903v.pdf','sha256':identity['main_sha256'],'page_count':6,
            'identity_verification':'Rendered title and final pages corroborate bibliographic identity and printed manuscript code JP951903V; two supplied folder copies have identical actual SHA256.',
            'pages':[{'page':p,'printed_page':3143+p,'text_read':True,'visual_review':True,'sections':PAGE_SECTIONS[p],'unresolved':[]} for p in range(1,7)]}],
        'document_identity_verification':'Existing corpus paper/document IDs retained; 1996 and nine authors verified from supplied main. Full DOI binding is local filename/metadata plus printed suffix, not a new publisher lookup.',
        'coverage_status':'private_main_source_coverage_proposal; canonical_audit_reader_integration_pending; SI_unverified',
        'independent_audit':'Independent source audit recorded in private provenance; canonical and reader audits remain separate pending gates.',
        'audit_details':{'source_audit_status':audit.get('status'),'scope_note':'This proposal does not promote canonical source_reviewed status or training/publication eligibility.'},
        'publication_status':'private_proposal_not_published','training_eligible':False,'source_review_promoted':False,
        'training_note':'No source-ledger or proposed record is enabled for training by this artifact. Two template variants share a wafer; characterization and unpatterned comparison are separate non-recipe contexts.',
        'recipe_inventory':recipe_inventory,'characterization_inventory':{'reader_item_ids':[i['id'] for s in ['structures','properties'] for i in sections[s]['items']]},
        'figures':sorted(figures,key=lambda f:f['id']),'tables':[],'equations':sorted(equations,key=lambda f:f['id']),'schemes':[],
        'reader_sections':list(sections.values()),
        'record_formulation_labels':{VAR100:['100 nm'],VAR150:['150 nm'],CHAR:['100 nm','150 nm'],CONTEXT:[]},
        'record_formulation_scope_note':SHARED+' Spectroscopy is patterned-region context without template-specific assignment; Figure 2 retains ambiguous template size.',
        'evidence_conflicts':[{'id':c['id'],'text':c['text'],'severity':c['severity'],'source_locators':[locator(ev['pdf_page'],ev['locator']) for ev in c['evidence']]} for c in audit['conflicts_and_semantic_hazards']],
        'remaining_gaps':['Matching SI not located or verified.','Complete initial cleaning/oxidation/lithography/RIE/HF conditions and exact processing assignments are absent.','Same wafer does not establish exact diced-piece, spectroscopy, microscopy and individual-island identity.','Raman 301 cm⁻¹ and near-IR 5890 cm⁻¹ are prose-only observations; no plotted spectra supplied.','No measured atomic coordinates or CIF; no electrical-device performance measurement.','No digitized source plots, raw arrays, full model fit parameters or numerical diffusion coefficient.','Canonical source-join audit, item-coverage approval and final reader/asset integration remain pending.'],
        'referenced_methods':references,
        'chemical_intuition':{'reader_item_ids':[i['id'] for i in sections['intuition']['items']],'scope':'Author rationale, observations and model assumptions remain differentiated by each reader item claim_type.'},
        'simulation_inventory':{'status':'Analytical kinetic/diffusion models only; no simulation dataset or executable fitted model is supplied.','equation_ids':[e['id'] for e in equations],'model_reader_items':['kinetic-proxy','model-assumptions','diffusion-boundaries','incubation-alternatives','figure5-model']},
        'reader_contract':{'version':'1.0','section_ids':list(sections),'item_fields':['id','title','text','claim_type','sample_scope','evidence','source_locators','canonical_links','notes','facts','training_eligible'],
            'coverage_rule':'Compact semantic source-unit coverage. Each scientific unit is represented once in a reader item or original asset/equation/reference; cross-links do not duplicate experiments. This is not a claim of approved canonical or rendered coverage.'},
    }
    coverage=[]
    for sec in ledger['reader_sections']:
        for i,it in enumerate(sec['items']):coverage.append({'source_item_id':it['id'],'source_locators':it['source_locators'],'disposition':'reader_item','target':f'/reader_sections/{list(sections).index(sec["id"])}/items/{i}','claim_type':it['claim_type']})
    for key in ['figures','equations']:
        for i,it in enumerate(ledger[key]):coverage.append({'source_item_id':it['id'],'source_locators':it['source_locators'],'disposition':'original_asset_and_context','target':f'/{key}/{i}','claim_type':it.get('claim_type',it['evidence_class'])})
    ledger['reader_item_coverage']=coverage
    ledger['reader_exclusions']=[{'source_item_id':'download-watermark','reason':'Institution/download timestamp and sharing footer are not experimental metadata.'},{'source_item_id':'acknowledgment-funding','reason':'Acknowledgments/funding are inventoried on page 6 but not treated as synthesis parameters.'}]
    targets={x['source_item_id']:x['target'] for x in coverage}
    source_map={
        'shared_protocol':{'substrate':['substrate-and-mask'],'resist':['substrate-and-mask','lithography'],'lithography':['lithography'],'development':['developer','lithography'],'oxide_etch':['etch-chemicals','rie-templates'],'resist_strip':['developer','strip-hf-load'],'HF_clean':['etch-chemicals','strip-hf-load'],'UHV_CVD':['germane-stock','shared-cvd'],'dicing':['shared-cvd']},
        'template_variants':{'wells_150nm':['rie-templates','150nm-outcomes'],'wells_100nm':['rie-templates','100nm-imaged-cohort']},
        'characterization':{'raman':['reported-spectroscopic-checks'],'TEM_instrument':['instrumentation','150nm-outcomes'],'near_IR':['reported-spectroscopic-checks'],'AFM_instrument':['instrumentation','100nm-size-bounds'],'TEM_length_calibration':['instrumentation','150nm-statistics'],'150nm_neighbor_statistics':['150nm-statistics'],'Fig6_AFM_dimensions':['100nm-size-bounds','figure-6'],'100nm_body_diameter_bounds':['100nm-size-bounds'],'four_well_AFM_sample':['100nm-imaged-cohort'],'paper_size_summaries':['study-size-wording']},
        'author_models_and_intuition':{'growthlaw':['kinetic-proxy','equation-1'],'growth_assumptions':['model-assumptions'],'selectivity':['model-assumptions'],'nucleation_order':['kinetic-proxy'],'screening_equations':['diffusion-boundaries','equation-2','equation-3'],'reflective_boundaries':['diffusion-boundaries'],'incubation_alternatives':['incubation-alternatives'],'nucleation_models':['incubation-alternatives'],'Fig5_reconstruction':['figure5-model','figure-5'],'100nm_interpretation':['small-well-outlook'],'device_outlook':['motivation','small-well-outlook']},
    }
    audited_units=[]
    def covered(pointer,unit_id,reader_ids):
        assert all(rid in targets for rid in reader_ids),(pointer,reader_ids)
        audited_units.append({'source_audit_pointer':pointer,'source_item_id':unit_id,'reader_item_ids':reader_ids,'public_targets':[targets[rid] for rid in reader_ids],'status':'represented_pending_independent_join_approval'})
    chemical_targets={'silicon':'substrate-and-mask','silicon dioxide':'substrate-and-mask','poly(methyl methacrylate)':'substrate-and-mask','isopropyl alcohol':'developer','methyl isobutyl ketone':'developer','tetrafluoromethane':'etch-chemicals','trifluoromethane':'etch-chemicals','acetone':'developer','hydrofluoric acid':'etch-chemicals','germane':'germane-stock','helium':'germane-stock','silicon nitride':'instrumentation','carbon':'instrumentation'}
    for n,chemical in enumerate(audit['chemical_inventory']):covered(f'/chemical_inventory/{n}',chemical['name'],[chemical_targets[chemical['name']]])
    for category,mapping in source_map.items():
        for n,unit in enumerate(audit[category]):covered(f'/{category}/{n}',unit['id'],mapping[unit['id']])
    covered('/optimization_context',audit['optimization_context']['id'],['unpatterned-comparison','kinetic-proxy'])
    for n,unit in enumerate(audit['figure_inventory']):covered(f'/figure_inventory/{n}',unit['id'],[unit['id'].replace('_','-')])
    for n,unit in enumerate(audit['conflicts_and_semantic_hazards']):
        audited_units.append({'source_audit_pointer':f'/conflicts_and_semantic_hazards/{n}','source_item_id':unit['id'],'public_targets':[f'/evidence_conflicts/{n}'],'status':'represented_pending_independent_join_approval'})
    for n,unit in enumerate(audit['reference_contexts']):covered(f'/reference_contexts/{n}',f'reference-{unit["reference_number"]}',[f'reference-{unit["reference_number"]}'])
    for n,unit in enumerate(audit['missing_information']):covered(f'/missing_information/{n}',f'source-gap-{n+1}',['reporting-gaps'])
    paths={f'plain-page-{p}.txt':digest(ROOT/f'plain-page-{p}.txt') for p in range(1,7)}
    paths.update({'source-identity.json':digest(ROOT/'source-identity.json'),str(audit_path.relative_to(ROOT)):digest(audit_path),'crop-assets/manifest.json':digest(ROOT/'crop-assets/manifest.json')})
    report={'status':'private_proposal_validated_structurally','created_utc':datetime.now(timezone.utc).isoformat(),'source_audit_status':audit.get('status'),
        'counts':{'pages':6,'figures':len(figures),'equations':len(equations),'tables':0,'separate_schemes':0,'numbered_reference_entries':len(references),'reader_items':sum(len(s['items']) for s in sections.values()),'semantic_coverage_units':len(coverage),'source_audit_units_mapped':len(audited_units),'expected_canonical_records':4},
        'input_sha256':paths,'asset_file_provenance':asset_files,'promotion':{'training':False,'canonical_source_reviewed':False,'reader_audit_complete':False,'published':False},
        'pending':['Root independent canonical-to-ledger/science join audit','Complete source audit findings reconciliation','Copy nine original assets to proposed public destinations only after review','Check proposed canonical IDs exist and sample joins remain source-scoped','Final rendered source/item/figure audit and publication'],
        'limitations':['Reference text preserves source spelling/volume/year anomalies without external correction.','Original assets are proposed destinations, not files already copied to the Site.']}
    ids=[i['id'] for s in sections.values() for i in s['items']]
    assert len(ids)==len(set(ids)) and len(coverage)==len(set(x['source_item_id'] for x in coverage))
    assert [r['reference_number'] for r in references]==list(range(1,18))
    assert set(x['record_ids'][0] for x in recipe_inventory)==set(EXPECTED)
    assert all(not i['training_eligible'] for s in sections.values() for i in s['items'])
    assert not any(d['role']=='si' for d in ledger['documents'])
    serialized=json.dumps(ledger,ensure_ascii=False)
    assert 'C:\\' not in serialized and 'research-assets/' not in serialized
    OUT.mkdir(parents=True,exist_ok=True)
    for name,value in [('heath1996.json',ledger),('source-item-coverage.json',{'scope':'Compact source semantics and original evidence, pending independent integration approval','source_audit_unit_map':audited_units,'reader_units':coverage,'administrative_scope_note':'Audit identity/relevance is represented in ledger metadata; page review is represented in documents. OCR cautions and new-parameter concepts are editorial audit guidance, not additional experimental outcomes. Acknowledgments and watermark are explicitly excluded from scientific parameters.'}),('validation.json',report)]:
        (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report['counts']))

if __name__=='__main__':main()
