"""Private, evidence-linked Stiger 1999 reader proposal. No Site writes."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib, json, re

OUT = Path(__file__).resolve().parent
B = OUT.parent
SID = 'stiger1999'
P = 'stiger-1999-'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
audit = read(B/'source-audit.json')
identity = read(B/'source-identity.json')
char = read(B/'characterization-draft.json')
manifest = read(B/'crop-assets/manifest.json')
units = {u['id']: u for u in audit['units']}
rows = {r['id'].removeprefix('char-'): r for r in char['measurement_rows']}
drafts = {p.stem: read(p) for p in (B/'canonical-drafts').glob('*.json')}
assert identity['main_sha256'] == char['source']['sha256'] == manifest['source_sha256']
keys = ['electrodeposition', 'cyclic-voltammetry', 'current-transients', 'afm', 'tem-saed',
        'open-circuit-control', 'silver-free-pulse-control', 'characterization']
sections = [{'id': s, 'title': t, 'items': []} for s, t in [
    ('precursors','Precursors'), ('protocol','Synthesis protocol'), ('structures','Final structures'),
    ('properties','Properties'), ('intuition','Chemical intuition'), ('sources','Sources and limitations')]]
mapping = {}
row_mapping = {}
def cats(cat, *nums): return [f'{cat}-{n:02}' for n in nums]
def ev(p, loc):
    return {'source_id': SID, 'document_role': 'main', 'pdf_page': p, 'printed_page': 789+p,
            'locator': loc if loc.startswith('Main PDF') else f'Main PDF p. {p}, printed p. {789+p}, {loc}'}
def fact(row):
    q = row.get('quantity')
    value = q.get('value') if q else row['fact']
    if q and 'lower_bound' in q: value = f"{q['lower_bound']}–{q['upper_bound']}"
    notes = [row.get('source_condition'), row.get('caveat')]
    if q and q.get('raw_text'): notes.insert(0, 'Source wording: '+q['raw_text'])
    return {'id': row['id'], 'label': row['property'].replace('_',' ').capitalize(), 'value': value,
            'unit': q.get('unit') if q else None, 'approximate': q.get('approximate',False) if q else False,
            'basis': row['basis'], 'qualifier': ' '.join(x for x in notes if x),
            'evidence': [ev(e['pdf_page'],e['locator']) for e in row['evidence']]}
def item(sec, key, title, text, source_units=(), records=(), row_keys=(), samples=(),
         kind='reported_source_fact', scope='source_cohort', notes=(), evidence=()):
    ee = []
    for uid in source_units:
        assert uid in units, uid
        mapping.setdefault(uid, []).append(key)
        ee += [ev(e['pdf_page'],e['locator']) for e in units[uid]['evidence']]
    for rk in row_keys:
        assert rk in rows, (key,rk)
        row_mapping.setdefault(rk,[]).append(key)
        ee += [ev(e['pdf_page'],e['locator']) for e in rows[rk]['evidence']]
    ee += [ev(p,l) for p,l in evidence]
    ee = list({json.dumps(e,sort_keys=True):e for e in ee}.values())
    assert ee,key
    records = list(dict.fromkeys(records))
    if row_keys and 'characterization' not in records: records.append('characterization')
    sample_ids = list(samples)
    for rk in row_keys:
        s=rows[rk]['sample_id']; s='shared-'+'-and-'.join(s) if isinstance(s,list) else s
        if s not in sample_ids: sample_ids.append(s)
    limits = {
      'source_cohort': 'Source figure, substrate, control or aggregate-series association only. Author batch IDs and exact cross-instrument specimen identity are not established.',
      'model_context': 'Author model or calculated interpretation, with named cohorts indicating application. This does not define an independently measured specimen, band structure or synthesis outcome.',
      'method_context': 'Instrument, analysis or acquisition setting. This context does not define an independent material or measured product property.',
      'cited_context': 'Earlier work or a reference value reported by this inspected source. The cited work was not independently read here and cannot fill missing current-recipe fields.',
      'source_metadata': 'Source identity, bibliography or documented qualification; no additional physical specimen or experimental result is introduced.',
      'author_outlook': 'An application or hypothesis proposed by the source authors, not an experiment or demonstrated performance in this article.',
      'curator_interpretation': 'Curator interpretation of evidence or data representation, explicitly separate from reported source observations.',
      'curator_outlook': 'Curator-proposed follow-up measurements; not performed in the source and not used to supply missing values.'}
    links = [{'record_id':P+r,'json_pointer':'','relation':limits[scope]} for r in records]
    joins=[]
    for r in records:
        for n,prod in enumerate(drafts.get(P+r,{}).get('products',[])):
            if prod['sample_id'] in sample_ids:
                joins.append({'record_id':P+r,'sample_id':prod['sample_id'],'json_pointer':f'/products/{n}',
                              'relation':limits[scope]})
    sample_scope={'formulations':sample_ids,'physical_batch_id':None,'scope_kind':scope,
                  'state':title,'link_limit':limits[scope]}
    if joins: sample_scope['canonical_sample_links']=joins
    d={'id':key,'title':title,'text':text,'claim_type':kind,'sample_scope':sample_scope,'evidence':ee,
       'source_locators':[e['locator'] for e in ee],'canonical_links':links,'notes':list(notes),
       'facts':[fact(rows[r]) for r in row_keys],'training_eligible':False}
    next(s for s in sections if s['id']==sec)['items'].append(d)
    return d
def selected(prefix): return tuple(k for k in rows if k.startswith(prefix))

item('sources','article-identity','Article identity and reviewed scope',
     'R. M. Stiger, S. Gorer, B. Craft and R. M. Penner published this article in Langmuir 1999, 15(3), 790–798. It was received July 1, 1998, revised to final form October 27, 1998, and published online December 9, 1998. The journal year is 1999; the legacy catalog year 1997 is incorrect. All nine supplied main pages were read as text and inspected visually. The two local main copies are byte-identical. No matching SI was located or verified by the documented local checks.',
     cats('identity',1,2,3),scope='source_metadata',kind='reviewed_source_identity',
     notes=('No matching local SI is not proof that publisher SI never existed.','The full DOI is printed on page 1; the article ends with LA980800B.'))
item('precursors','silicon-substrates','Silicon substrates and doping',
     'Wacker Silitronic supplies the two antimony-doped, one-side-polished Si(100) wafer types. The degenerately doped n++ material has an impurity concentration of 10²⁰ cm⁻³; the nondegenerate n material has 10¹⁵ cm⁻³. The preparative pulse series uses n++ Si, while cyclic voltammetry compares both types. The 5 in wafer diameter, 1.0 cm² coupon area and 0.28 cm² exposed electrode area describe different geometrical quantities.',
     cats('chemical_inventory',1),records=('electrodeposition','cyclic-voltammetry'),row_keys=('npp-doping','n-doping','exposed-area'))
item('precursors','back-contact','Ohmic back-contact materials',
     'A diamond scribe scratches the unpolished rear surface. The scratch receives a gallium–indium eutectic, then colloidal silver paint. This contact silver is separate from the nanocrystals subsequently grown on the polished front surface. Alloy ratio, paint formulation, amounts and drying time are not reported.',
     cats('chemical_inventory',2),records=('electrodeposition',))
item('precursors','oxidation-acid','Sulfuric acid oxidation bath',
     'The oxidation bath uses Fisher trace-metal-grade sulfuric acid, supplied at 95–98%. The source heats the treatment to 80 °C for approximately 10 min. It does not add hydrogen peroxide; this is not a stated piranha mixture. Acid volume and concentration basis are not specified.',
     cats('chemical_inventory',3),records=('electrodeposition',))
item('precursors','hf-ethanol','HF / ethanol oxide-stripping mixture',
     'Fisher reagent-grade 49% HF is mixed with ethanol from Quantum Chemical in a 1:1 volume ratio. The oxide-stripping exposure lasts 5 min. The 49% value belongs to the supplied HF reagent; a measured final mixture concentration is not given. Etchant volume and temperature remain unknown.',
     cats('chemical_inventory',4),records=('electrodeposition',))
item('precursors','rinse-water','Water rinses',
     'A brief Nanopure-water rinse follows sulfuric-acid oxidation, and another water rinse follows HF / ethanol stripping. Rinse volumes and durations are not quantified. Hydrophobicity after etching is reported as a property of the treated surface.',
     cats('chemical_inventory',5),records=('electrodeposition',))
item('precursors','silver-stock','Silver precursor and preparative electrolyte',
     'The general plating electrolyte contains 1 mM AgClO₄ and 0.1 M LiClO₄ in acetonitrile. The silver reagent is Alfa AgClO₄·H₂O, 99.9%; its hydration state is retained. No bath volume, weighed mass, dissolution sequence or concentration assay is supplied.',
     cats('chemical_inventory',6),records=('electrodeposition',))
item('precursors','supporting-electrolyte','Supporting electrolyte and solvent',
     'Aldrich LiClO₄, 99.99%, supplies 0.1 M supporting electrolyte; no hydrate is specified. Acetonitrile from Burdick & Jackson is high purity and is also used as the pure-solvent rinse after deposition. Atmospheric water was not rigorously excluded.',
     cats('chemical_inventory',7,8),records=('electrodeposition','cyclic-voltammetry','current-transients'))
item('precursors','nitrogen-and-electrodes','Gas and electrochemical electrodes',
     'Nitrogen purges the electrolyte before use. A silver-wire reference is used with silver-containing solutions, a saturated calomel reference with silver-free solutions, and a platinum-wire counter electrode throughout. All published potentials are expressed on the silver reference scale. The SCE-to-silver conversion offset, gas grade, flow and purge duration are absent.',
     cats('chemical_inventory',9,10),records=('electrodeposition','cyclic-voltammetry','current-transients'))
item('precursors','analytical-supports','TEM support and diffraction reference',
     'Ted Pella carbon-coated gold grids receive particles mechanically transferred from silicon. Single-crystal highly oriented pyrolytic graphite flakes provide diffraction patterns for correcting microscope astigmatism. The grid is not copper, and graphite is an analytical reference here rather than the current growth substrate.',
     cats('chemical_inventory',11,12),records=('tem-saed',))
item('precursors','source-specific-electrolytes','Electrolyte composition by source context',
     'The general synthesis bath is 1 mM AgClO₄. The cyclic-voltammetry introduction and Figure 2 caption specify 10 mM, but the detailed discussion specifies 1 mM; Scheme 1 also labels 1 mM. Figure 3 separately specifies 1.5 mM. These scopes remain distinct. Silver-free control electrolyte contains 0.10 M LiClO₄ in acetonitrile; the open-circuit exposure control uses the silver bath.',
     cats('chemical_inventory',13,14),records=('cyclic-voltammetry','current-transients','open-circuit-control','silver-free-pulse-control'),
     notes=('The unresolved CV concentration is not selected by majority vote.','Neither the 10 mM nor 1.5 mM context automatically replaces the general 1 mM synthesis bath.'))
item('precursors','residual-water','Residual water in the electrochemical interpretation',
     'The authors invoke approximately 1 mM residual water when discussing the cathodic response. This is not a metered water addition or a reported moisture-assay result. Water reduction can contribute to the measured current once silver particles catalyze hydrogen evolution.',
     cats('chemical_inventory',15),records=('cyclic-voltammetry','current-transients'),row_keys=('water-residual',),kind='original_author_estimate')

item('protocol','coupon-contact','Coupon preparation and back contact',
     'Cut the one-side-polished 5 in wafer into 1.0 cm² coupons. Scratch the unpolished side with a diamond scribe, paint the scratch with Ga–In eutectic, cover it with colloidal silver paint and air-dry. The source does not specify the cutting implement, drying temperature or elapsed drying time.',
     cats('procedure',1,2),records=('electrodeposition',))
item('protocol','surface-treatment','Front-surface oxidation and hydrogen termination',
     'Expose the polished face to sulfuric acid at 80 °C for approximately 10 min and briefly rinse in Nanopure water. Strip the oxide for 5 min in 1:1 v/v HF / ethanol, then rinse in water. The resulting surface is hydrophobic and described as hydrogen-terminated. No intermediate drying, exact etch temperature or postetch transfer delay is stated.',
     cats('procedure',3,4),records=('electrodeposition',))
item('protocol','cell-preparation','Electrolyte preparation and cell assembly',
     'Prepare the general 1 mM AgClO₄ / 0.1 M LiClO₄ electrolyte in acetonitrile and purge with nitrogen before use. A Teflon holder exposes 0.28 cm² of the freshly etched polished face in a glass cell. Use the source-appropriate reference electrode and a platinum-wire counter electrode. Bath temperature, volume, electrode separation, illumination and stirring are not reported.',
     cats('procedure',5,6,7),records=('electrodeposition',))
item('protocol','electronic-control','Potentiostat, pulse generation and current recording',
     'An EG&E Model M273 potentiostat, as printed, controls cyclic voltammetry and potential steps. A Hewlett-Packard 33120A pulse generator and relay provide short-pulse triggering; a Nicolet 310 digital-storage oscilloscope records the current transients. Sampling rate, electrical bandwidth, timing response and current-integration method are not stated.',
     cats('characterization_method',1),records=('electrodeposition','cyclic-voltammetry','current-transients'),scope='method_context')
item('protocol','potentiostatic-pulse','Preparative potential pulse',
     'Starting at open circuit, apply −800 mV versus Ag / Ag⁺ for a selected duration from 2 to 25 ms. The four Figure 5 durations are 2, 7, 12 and 22 ms; the four displayed Figure 7 histograms are associated by caption order with 5, 10, 15 and 25 ms. They are discrete source cohorts within one reported method, not eight fully established independent batches or a periodic pulse train.',
     cats('procedure',9),records=('electrodeposition',),
     notes=('No pulse frequency, duty cycle, off-time sequence or repeated-pulse count is specified.','Charge-unit conflicts prevent an unqualified charge-based recipe target.'))
item('protocol','postdeposition-handling','Return to open circuit, rinse and dry',
     'Promptly return the electrode to open circuit, immediately remove the working-electrode holder, rinse the silicon in pure acetonitrile and air-dry. Open circuit is not a specified 0 V hold. Rinse quantity, duration, drying time and storage conditions are not given.',
     cats('procedure',10),records=('electrodeposition',))
item('protocol','cv-procedure','Cyclic-voltammetry comparison',
     'Figure 2 compares both silicon doping classes with and without silver at 20 mV/s. Repeated scans are retained in their own source panels. The source does not enumerate a common numerical sweep window, hold duration or repeat-count protocol in the method text. The silver concentration and panel-d doping conflicts remain explicit.',
     cats('procedure',8),records=('cyclic-voltammetry',),row_keys=('cv-scan-rate',),scope='method_context')
item('protocol','transient-procedure','Potential-dependent current transients',
     'Figure 3 compares −600, −800 and −1000 mV versus Ag / Ag⁺ in nitrogen-sparged acetonitrile containing 1.5 mM AgClO₄ and 0.1 M LiClO₄. Its displayed 200 ms window does not identify these traces with the 2–25 ms preparative specimens. Figure 4 replots a −800 mV transient through 25 ms and fits only its early rising portion.',
     cats('procedure',11,12),records=('current-transients',),
     notes=('Figure 4 and source note 43 use a separate analytical context; exact identity with a Figure 3 run is unestablished.',))
item('protocol','open-circuit-control','Open-circuit exposure control',
     'Expose etched silicon to the silver plating solution at open circuit, rinse with acetonitrile and inspect by noncontact AFM. The source reports an average object density of 1.0 µm⁻², equivalent to 10⁸ cm⁻², at the usual background contamination level. Images are not shown. The objects are not chemically identified as silver; exposure duration and precise control doping are unreported.',
     cats('procedure',13)+cats('observation',16),records=('open-circuit-control',),row_keys=('open-circuit-background',))
item('protocol','silver-free-control','Silver-free pulse control',
     'Apply a potential pulse in 0.10 M LiClO₄ / acetonitrile without silver and inspect the surface. Most areas remain unchanged; some show RMS roughness below 10 Å. The roughening mechanism is unknown and the authors judge that it does not obscure 2–20 nm silver particles. The control pulse potential and duration are not independently enumerated.',
     cats('procedure',14)+cats('observation',17),records=('silver-free-pulse-control',),row_keys=('silver-free-roughness','control-roughening'),
     notes=('This deliberate control is not a calibrated synthesis-failure label or evidence that no surface reaction occurred.',))
item('protocol','tem-transfer','Mechanical transfer for TEM and SAED',
     'Mechanically transfer the deposited particles from silicon to carbon-coated gold TEM grids. The implement, force, sampled fraction, any transfer solvent and exact deposition duration are not reported. Diffraction from single-crystal HOPG flakes corrects microscope astigmatism; no numerical calibration uncertainty is given.',
     cats('procedure',15,16),records=('tem-saed',))
item('protocol','afm-analysis','AFM acquisition and image analysis',
     'Correct image curvature using Park Scientific software, then use NIH Image SXM 1.61 to extract heights and areal densities from flattened noncontact AFM images. Analyze all visible particles in five randomly selected 3 × 3 µm fields per sample. Exact particle counts, raw lists, flattening settings and the histogram bin data are absent.',
     cats('procedure',17)+cats('characterization_method',10),records=('afm',),row_keys=('histogram-regions','histogram-image-side'),scope='method_context')
item('protocol','day-groups','Day-grouped experiment design',
     'The density and height-versus-charge analysis comprises 15 deposition experiments: three groups of five obtained on three days. Fresh etching solutions are prepared each day and all silicon surfaces for that day are etched in one batch. Plot symbols identify day groups, not known calendar dates or exact independent preparation IDs.',
     cats('procedure',18),records=('afm',),row_keys=('density-experiments','density-days','density-day-size'),
     notes=('The five imaging fields per sample are spatial subsamples, distinct from the five deposition experiments in a day group.',))
item('protocol','contact-imaging','Contact-mode perturbation',
     'Contact AFM gives lower apparent particle densities than noncontact imaging of comparable surfaces. Successive contact images contain progressively fewer particles, supporting removal by the tip. These observations are not independent nondestructive replicates and no quantitative removal correction is supplied.',
     cats('procedure',19)+cats('observation',32),records=('afm',),row_keys=('contact-disturbance',))

item('structures','substrate-topography','Hydrogen-terminated substrate topography',
     'Figure 1 shows the freshly etched silicon before silver deposition. The 3 × 3 µm noncontact AFM field has monatomic steps reported as 1.3 ± 0.4 Å; the meaning of the uncertainty statistic is not named. A separate cited comparison gives 1.35 Å for Si(100) steps. These dimensions are substrate topography, not silver particle size.',
     cats('characterization_method',7)+cats('observation',3),records=('electrodeposition','afm'),row_keys=('si-step-height','si-step-uncertainty','si-step-reference'))
item('structures','miscut-calculation','Source estimate of surface miscut',
     'The authors count approximately 40 steps across a 42,400 Å diagonal and use (1.3 Å per step × 40 steps / 42,400 Å) × 100% ≈ 0.1%. This is a calculated percent slope, not a reported angle of 0.1°. It does not supply a wafer orientation tolerance measured independently.',
     cats('observation',4),records=('afm',),row_keys=('si-miscut','si-step-count','si-traverse'),kind='original_author_calculation')
item('structures','afm-instrument','AFM instrument and probe information',
     'The instrument is a Park Scientific Instruments LS multimode microscope. Contact-mode Ultralevers are described by 0.6 µm and noncontact Ultralevers by 2 µm, with a 90–120 kHz resonance range. The source does not identify which lever dimension those lengths represent; tip radius, force constant, load, angle and scan rate remain unknown.',
     cats('characterization_method',4),records=('afm',),row_keys=('afm-contact-lever','afm-nc-lever','afm-nc-frequency'),scope='method_context')
item('structures','height-versus-width','Particle height and lateral-width distinction',
     'Noncontact AFM height is the primary particle-size metric. Apparent lateral widths are broadened by tip convolution and cannot be treated as true diameters without a deconvolution model. The authors use an approximately spherical-particle argument, supported by earlier comparisons, when relating height to diameter. Their later hemispherical model instead treats height as a radius.',
     cats('characterization_method',5,6),records=('afm',),row_keys=('height-width',),kind='measurement_interpretation',
     notes=('No exact same-particle TEM / AFM correlation or measured particle-shape distribution is supplied.',))
item('structures','tem-instrument','TEM and selected-area diffraction settings',
     'A Philips EM-200 microscope is described with an accelerating voltage of 200 keV, preserving the source’s energy-unit wording. The camera length is 500 mm and the selected-area aperture diameter is 10 µm. That aperture dimension is not automatically a 10 µm projected specimen area.',
     cats('characterization_method',2,3),records=('tem-saed',),row_keys=('tem-beam','saed-camera-length','saed-aperture'),scope='method_context')
item('structures','transferred-particles','Transferred-particle TEM population',
     'Figure 6a is a 260 × 260 nm TEM field containing approximately 100 transferred particles. The body reports diameters of 10–25 Å. The parent silicon was plated at −800 mV, but pulse duration is not stated. Mechanical transfer can select a population; these particles are not assigned to a specific Figure 5 image or Figure 7 histogram.',
     cats('characterization_method',8)+cats('observation',19),records=('tem-saed','electrodeposition'),row_keys=('tem-field','tem-count','tem-diameter'))
item('structures','saed-indexing','Experimental SAED and FCC silver assignment',
     'Figure 6b contains the actual electron-diffraction pattern; Figure 6c is the authors’ ring-indexing schematic. Four experimental spacings are assigned to FCC metallic silver. Table 1 separates experimental spacings from ICDD 03-0931 reference spacings and reference relative intensities. The latter intensities are not measured intensities of this specimen.',
     cats('characterization_method',9)+cats('observation',20)+cats('table',1,2,3,4),records=('tem-saed','electrodeposition'),
     row_keys=selected('saed-')+selected('reference-d-')+selected('reference-intensity-')+('metallic-phase',),
     notes=('The expected (111) spacing remains 2.32 Å as printed; it is not replaced by a familiar bulk-silver value.','No XRD pattern, refined atomic coordinates, solved Ag / Si interface or experimental CIF is supplied.'))
item('structures','bounded-air-stability','Metallicity after analysis handling',
     'Preparing and analyzing the TEM / diffraction specimen requires at least 1 h in air, after which metallic silver diffraction is observed. This supports survival of a metallic fraction through that handling interval. It does not establish an oxidation fraction, a kinetic lifetime, indefinite air stability or metallicity of every deposited particle.',
     records=('tem-saed',),row_keys=('air-exposure','air-stability'),kind='reported_observation_and_author_interpretation')

for n,(letter,t) in enumerate(zip('abcd',[2,7,12,22]),21):
    values={'a':('1.6','0.007'),'b':('3.6','0.016'),'c':('8.3','0.037'),'d':('18.7','0.084')}[letter]
    item('structures',f'afm-figure5-{letter}',f'Figure 5{letter}: {t} ms pulse',
         f'The −800 mV, {t} ms source image and height profile cover 3 × 3 µm. The printed charge density is {values[0]} mC/cm² and the author-calculated equivalent coverage is {values[1]} monolayers. No exact mean particle height is tabulated for this panel. Its cohort remains separate from the Figure 7 histogram series.',
         cats('observation',n),records=('electrodeposition','afm'),row_keys=selected(f'f5-{letter}-'),
         notes=('Printed mC/cm² conflicts with µC/cm² in Figures 7 and 9.','Equivalent coverage is an upper limit under an assumed 100% current efficiency, not a measured atomic coverage.'))
item('structures','coverage-islanding','Equivalent coverage and three-dimensional islands',
     'The source assumes 100% current efficiency and prints 222 mC/cm² per equivalent Ag monolayer. Its coverage values are therefore stated as upper limits, particularly because hydrogen evolution can contribute to the charge. At equivalent coverage below one monolayer, separated islands are much taller than the illustrative atomic-layer height of approximately 0.25 nm, supporting Volmer–Weber three-dimensional growth. The image discussion gives a broad particle-density context of 2 × 10⁸ to 2 × 10⁹ cm⁻², without assigning an exact density to each panel.',
     cats('observation',18,25,26),records=('electrodeposition','afm'),row_keys=('coverage-calibration','coverage-efficiency','atomic-layer-height','island-growth'),kind='author_calculated_bounds_and_growth_interpretation')
for n,(t,mean,sigma,charge) in enumerate([(5,2.2,2.4,2.8),(10,7.5,4.3,7.8),(15,13.5,5.3,17.6),(25,17.1,6.1,38.1)],1):
    item('structures',f'histogram-{n}',f'Figure 7 histogram {n}: caption-associated {t} ms',
         f'The displayed histogram labels a charge density of {charge} µC/cm², a mean noncontact AFM height of {mean} nm and a distribution σ of {sigma} nm. The caption’s top-to-bottom order associates this panel with {t} ms at −800 mV. Five randomly selected image fields are analyzed per sample; these are not five independent reactions.',
         cats('observation',27+n),records=('electrodeposition','afm'),row_keys=selected(f'f7-{n}-'),
         notes=('The four displayed histograms and four listed pulse times are retained. The caption’s statement of five samples does not justify creating a fifth cohort.','σ is a height-distribution spread, not a standard error or relative percentage.'))
item('structures','histogram-prose-conflict','Histogram text and source-summary differences',
     'The body describes a smallest mean height of 2.4 nm with a standard deviation of 2 nm, whereas the top plotted histogram labels 2.2 nm and σ = 2.4 nm. The largest spread is about 6 nm in the body and 6.1 nm in the plot. The prose abbreviation RSD accompanies quantities in nanometers and is not interpreted as a relative percentage.',
     cats('observation',27),records=('afm',),row_keys=('histogram-small-body-height','histogram-small-body-spread','histogram-large-body-spread'),kind='source_conflict')

item('properties','cv-blank','Silver-free cyclic voltammetry',
     'Both doping classes show anodic current onset near +150 mV and cathodic onset near −350 mV versus Ag in the silver-free electrolyte. Amplitudes vary between surfaces and decrease with successive scans. The authors assign the anodic process to silicon oxidation in residual water and the cathodic process to hydrogen evolution. No current-density detection threshold is reported.',
     cats('observation',6),records=('cyclic-voltammetry',),row_keys=selected('cv-npp-blank-')+selected('cv-n-blank-')+('blank-scan-passivation',),kind='reported_response_and_author_assignment')
item('properties','cv-degenerate','Silver-containing CV on degenerately doped silicon',
     'For the body-assigned n++ case, the first scan has a silver-deposition peak near −450 mV and a residual-water-reduction peak near −700 mV. Silver deposition begins near −300 mV and ceases on the positive-going scan near −110 mV. The authors infer a 190 mV nucleation overpotential and a 110 mV internal overpotential. Silver stripping is initially present; deposition, hydrogen evolution and stripping decay until the fourth scan has no discernible faradaic response, interpreted as passivation.',
     cats('observation',7,8),records=('cyclic-voltammetry',),row_keys=tuple(k for k in selected('cv-npp-') if '-blank-' not in k),kind='reported_response_and_author_interpretation')
item('properties','cv-nondegenerate','Silver-containing CV on nondegenerate silicon',
     'The discussion assigns Figure 2d to nondegenerate n-Si, although its caption repeats n++ Si. On the body assignment, the silver peak is near −600 mV, about 150 mV more negative than for n++. Deposition onset is near −470 mV and positive-going cessation near −220 mV, giving an author-inferred 250 mV nucleation overpotential. The internal barrier is discussed near 200 mV. No silver stripping is seen and cathodic peaks decline on repeated scans.',
     cats('observation',9),records=('cyclic-voltammetry',),row_keys=tuple(k for k in selected('cv-n-') if '-blank-' not in k),kind='reported_response_with_source_doping_conflict')
item('properties','electroless-observation','Electroless deposition observation',
     'The authors report no observed electroless silver deposition on either silicon doping class. They explain this using the position of the silver redox level relative to silicon bands. No exposure-time limit, detection threshold or calibrated zero deposition rate is supplied.',
     cats('observation',10),records=('cyclic-voltammetry','open-circuit-control'),row_keys=('electroless-absence',))
item('properties','transient-potential-effects','Potential-dependent transient response',
     'The −600 mV trace has one peak near 50 ms, interpreted as a regime favoring silver deposition before substantial hydrogen evolution. At −800 and −1000 mV, the early rise is faster for t < 30 ms and another feature appears near 50 ms. Silver-catalyzed hydrogen evolution makes the later transients unsuitable for a simple silver-only reduced-variable analysis.',
     cats('observation',11,12),records=('current-transients',),row_keys=('transient-600-peak','transient-negative-peak','transient-fast-rise'),kind='reported_current_and_author_interpretation')
item('properties','transient-background','Silver-free current background',
     'In 0.10 M LiClO₄ / acetonitrile without silver, current falls below 1 mA/cm² within 3 ms. This supports restricting the growth-model comparison to the early part of the silver-containing transient, but it does not prove that all early current is silver deposition or establish 100% Faradaic efficiency.',
     cats('observation',13),records=('current-transients','silver-free-pulse-control'),row_keys=('blank-transient-current','blank-transient-decay'))
item('properties','transient-fit','Early-time nucleation-model comparison',
     'The current plotted against t¹ᐟ² has no suitable linear regime with a near-zero intercept. Against t³ᐟ², a linear region spans 2–28 ms³ᐟ², corresponding to 1.6–9.2 ms. The body reports R = 0.999 and intercept 0.19, while the inset reports slope 0.043315 and R = 0.99947. Current-density and transformed-time units are inferred from the axes and identified as such. This is a fit to the current response, not an independent measurement of particle number.',
     cats('observation',14),records=('current-transients',),row_keys=selected('transient-fit-')+('instantaneous-fit-failure',),kind='reported_model_fit')
item('properties','transient-density-model','Density inferred from current model',
     'The authors calculate an asymptotic nucleation density of 2.32 × 10¹⁰ cm⁻² using Equation 2 and note 43, approximately an order of magnitude above the AFM results. Undefined parameters in the printed equation prevent treating the value as exactly reproducible from the supplied inputs. It is not a measured long-time surface count.',
     cats('observation',15),records=('current-transients',),row_keys=('transient-site-density',),kind='original_author_model_result',scope='model_context')
item('properties','density-time-series','Areal density and pulse duration',
     'The Figure 8 ordinate and discussion show particle density versus pulse duration for three day groups. The caption instead describes mean height and height-distribution error bars; the error-bar meaning for density is therefore unresolved. All groups show progressive nucleation, but slopes and apparent plateau densities vary. The body gives rates of 7.6 × 10⁷–2.2 × 10⁹ cm⁻² ms⁻¹, near-constant density after roughly 15–25 ms, and apparent plateaus of 1.3–2.3 × 10⁹ cm⁻². Lines guide the eye; no exact slope is assigned to a plotted day symbol by digitization.',
     cats('characterization_method',11)+cats('observation',33,34),records=('afm','electrodeposition'),row_keys=('nucleation-rate-body','density-saturation-time','density-saturation-range','density-etch-variation'),kind='reported_series_and_author_derived_ranges')
item('properties','induction-time-limits','Induction and limits of the time window',
     'The three day groups show an apparent 2–3 ms induction interval before particles are observed. The origin is unknown, and Figure 5 separately includes a 2 ms image near this detection boundary. Densities were not measured for pulses longer than 30 ms. The authors allow slower progressive nucleation to continue on a seconds time scale, so the apparent plateau does not prove that every site is exhausted.',
     cats('observation',35,36),records=('afm','electrodeposition'),row_keys=('density-induction','density-time-limit'))
item('properties','height-charge-series','Mean height versus deposited charge',
     'Figure 9 uses the same 15 experiments as the density study and plots mean height against charge in µC/cm². Error bars are the stated height-distribution σ. The Equation 3 curve uses a best-fit N of 4 × 10⁸ cm⁻², with comparison bounds of 10⁸ and 10⁹ cm⁻². Those curves are geometric model comparisons, not additional experiments or measured constant densities during a progressive process.',
     cats('characterization_method',12)+cats('observation',37),records=('afm','electrodeposition'),row_keys=selected('height-Q-'),kind='measured_series_with_model_comparison')
item('properties','summary-scope','Abstract and conclusion ranges',
     'The abstract summarizes mean heights of approximately 2–20 nm over 2–25 ms and densities increasing from 1–3 × 10⁸ to 2–2.5 × 10⁹ cm⁻². The introduction targets 0.005–0.20 equivalent monolayers. The conclusion separately gives maximum mean heights of 15–20 nm near 20 ms, asymptotic densities of 10⁸–2 × 10⁹ cm⁻², and rates of 8 × 10⁷–2 × 10⁹ cm⁻² s⁻¹. Its seconds-based rate unit conflicts with the milliseconds-based body values. It also describes nucleation ceasing near 20 ms before Cottrellian decay near 30 ms; the body’s restricted time window qualifies this assertion.',
     cats('observation',1,2,38,39),records=('electrodeposition','afm','current-transients'),row_keys=selected('summary-')+selected('abstract-')+('coverage-study-range',),kind='source_summary_with_explicit_conflicts')

item('intuition','solvent-choice','Why acetonitrile is used',
     'The authors choose acetonitrile for the stability of hydrogen-terminated silicon and to reduce the rapid oxidation encountered for very small silver particles in aqueous plating solutions. Their discussion describes particles below 5 nm oxidizing within seconds in aqueous solution at open circuit, on silicon and graphite, and calls the product AgO; a later contrast uses Ag₂O. This earlier context is not a complete aqueous synthesis or an oxide product established in the current preparation.',
     cats('observation',5)+cats('intuition',1),records=('electrodeposition',),row_keys=('aqueous-instability',),kind='author_rationale_with_prior_context',scope='cited_context')
item('intuition','surface-energy-islanding','Surface termination and island growth',
     'The authors connect coordinatively saturated, low-energy surfaces with Volmer–Weber three-dimensional nucleation. Tall separated islands at low equivalent coverage support that interpretation. A graphite basal-plane surface energy near 35 dyn/cm is a cited comparison, not a measurement of the present silver / silicon interface.',
     cats('author_model',1)+cats('intuition',2),records=('electrodeposition',),row_keys=('graphite-surface-energy',),kind='original_author_interpretation',scope='model_context')
item('intuition','band-position','Qualitative energy-level alignment',
     'Band edges are not measured. From the voltammetry, the authors place the Ag⁺ / Ag formal potential approximately 200–500 mV positive of the silicon conduction-band edge. Scheme 1 compares n++ panels a–c and n panels d–f at equilibrium, negative bias and positive bias. Its 1 mM solution labels belong to this model context, not a resolution of the CV concentration conflict.',
     cats('author_model',2,5),records=('cyclic-voltammetry',),row_keys=('band-offset','electroless-absence'),kind='original_author_band_model',scope='model_context')
item('intuition','doping-and-tunneling','Doping, tunneling and silver stripping',
     'For n++ silicon, a depletion layer of roughly 2 nm permits cathodic tunneling around −100 mV and allows stripping through a thin barrier under positive bias. For nondegenerate n-Si, the clean-interface barrier is discussed near 200 mV, while silver islands form a larger Schottky barrier that suppresses stripping. The body prints approximately 600 mV and Scheme 1 prints approximately 600 meV; these are retained as separate source forms. The qualitative model motivates the heavily doped preparative substrate.',
     cats('author_model',3,4)+cats('intuition',3),records=('cyclic-voltammetry','electrodeposition'),row_keys=('tunnel-width','tunnel-threshold','schottky-barrier-body','schottky-barrier-scheme'),kind='original_author_band_model',scope='model_context',
     notes=('A body reference to forward-bias Scheme 1d differs from the visually corresponding negative-bias panel e.','No measured band structure, depletion profile, work function or DFT calculation is supplied.'))
item('intuition','early-current-models','Instantaneous and progressive nucleation models',
     'Equations 1 and 2 contrast I ∝ t¹ᐟ² for instantaneous nucleation with I ∝ t³ᐟ² for progressive nucleation. They use electron number z, nucleation density N or N∞, metal molar mass M, diffusion coefficient D, concentration C and density ρ. Equation 1 contains Faraday’s constant F. Equation 2 instead prints an undefined A and a starred concentration, with no visible F; neither is silently repaired. The model is applied to the early rising edge where silver is hoped to dominate, not the full hydrogen-coupled trace.',
     cats('author_model',6)+cats('equation',1,2),records=('current-transients',),kind='original_author_nucleation_model',scope='model_context')
item('intuition','source-note43','Source note 43: model inputs',
     'The directly inspected note gives CAg = 1.0 × 10⁻⁶ mol/cm³, DAg = 1.25 × 10⁻⁵ cm²/s and ρAg = 10.5 g/cm³. The diffusivity is described as measured in-house in 0.1 M LiClO₄ / acetonitrile; its method, temperature and uncertainty are not provided. Density is a model input, not a measured nanocrystal density. The stated concentration corresponds to the 1 mM analytical input rather than Figure 3’s explicit 1.5 mM.',
     cats('author_model',7),records=('current-transients',),row_keys=('fit-silver-concentration','fit-diffusion','silver-density-model'),kind='direct_source_note_with_model_inputs',scope='model_context',
     notes=('Note 43 does not define every Equation 2 parameter; the reported N∞ is not independently reproduced here.',))
item('intuition','pulse-tradeoff','Short pulses and competing current',
     'Short potential steps restrict growth to the early transient. Increasing cathodic overpotential accelerates nucleation but also promotes silver-catalyzed hydrogen evolution. The total integrated charge therefore cannot be treated as an independently measured silver-conversion yield, even when equivalent monolayers are calculated.',
     cats('intuition',4),records=('electrodeposition','current-transients'),kind='original_author_interpretation',scope='model_context')
item('intuition','self-avoiding-nucleation','Local depletion and spatial separation',
     'The authors propose that Ag⁺ depletion near an existing growing particle lowers the probability of new nucleation nearby, producing progressive, spatially self-avoiding growth. This is a mechanistic interpretation of the separated islands, not an experimentally mapped ion-concentration profile or a fitted local reaction order.',
     cats('author_model',8),records=('electrodeposition','afm'),kind='original_author_hypothesis',scope='model_context')
item('intuition','width-and-day-effects','Size spread and preparation history',
     'Continuing nucleation broadens heights relative to earlier instantaneous-growth graphite examples. Conversely, the authors find silver / silicon nucleation density more reproducible than the cited graphite case, whose densities varied by three orders between crystals. Differences between the three present day groups are attributed to subtle etching chemistry that is not evident in AFM; no direct chemical assay tests that explanation.',
     cats('author_model',9,10)+cats('observation',40)+cats('intuition',5,6),records=('afm','electrodeposition'),kind='original_author_interpretation_with_cited_comparison',scope='model_context')
item('intuition','height-charge-model','Hemispherical height–charge model',
     'Equation 3 treats a particle as a hemisphere and relates its height / radius to QAg¹ᐟ³. It assumes z = 1 and a fixed N appropriate strictly to instantaneous nucleation. The source uses the model as a geometric consistency comparison for the progressive series. This radius is not interchangeable with the full-sphere diameter approximation used for AFM interpretation, and the source reference to model curves in Figure 8 actually corresponds to Figure 9.',
     cats('author_model',11)+cats('equation',3),records=('afm','current-transients'),kind='original_author_geometric_model',scope='model_context')
item('intuition','termination-hypotheses','Possible limits to continuing nucleation',
     'The discussion considers metal-cluster interfacial states mediating electron transfer, drawing on GaAs literature, and overlapping diffusion zones that deplete silver ions across the surface. The latter argument assumes first-order dependence on Ag⁺ concentration. No local-state measurement, reaction-order fit or discriminating experiment establishes which mechanism controls the observed plateau.',
     cats('author_model',12,13),records=('current-transients','afm'),kind='original_author_hypotheses',scope='model_context')
item('intuition','measurement-provenance','Measurement mode as a synthesis-data variable',
     'Noncontact imaging limits tip-induced removal, and height is less distorted by tip shape than lateral width. The dataset therefore retains probe mode, image processing, substrate treatment day, count area, transferred-specimen scope, charge units and height statistics alongside a synthesis recipe. These are curator data-design implications of the reported evidence.',
     cats('intuition',7),records=('afm','tem-saed'),kind='curator_dataset_interpretation',scope='curator_interpretation')
item('intuition','author-outlook','Prospective materials and interfaces',
     'The authors suggest that growth control could extend to other metals and catalytically active silicon interfaces. This article does not report a Pt / Si synthesis or catalytic performance test. A useful future experiment would separately measure silver deposition efficiency and inspect matched AFM / TEM populations to clarify the charge and size ambiguities; that last suggestion is curator outlook, not a completed source experiment.',
     cats('intuition',8),kind='author_outlook_with_explicit_curator_extension',scope='author_outlook')
item('sources','prior-vapor-growth','Earlier vapor-deposited silver on silicon',
     'References 1–6 discuss vapor-deposited silver at submonolayer coverage on reconstructed Si(100) 2 × 1. That surface and process differ from the present solution electrodeposition on hydrogen-terminated Si(100); no vapor-growth procedure is imported.',
     cats('cited_prior_context',1),kind='cited_prior_context',scope='cited_context')
item('sources','prior-high-coverage','Earlier semiconductor electrodeposition',
     'The introduction discusses Pt, Cu and Au on Si(100) and n-GaAs(100), and Pb, Cu, Ag and Ni growth, often above 10 monolayers with three-dimensional islands. These metals, substrates and high coverages are cited background, not additional materials synthesized in the present article.',
     cats('cited_prior_context',2),kind='cited_prior_context',scope='cited_context')
item('sources','prior-graphite-growth','Earlier short-pulse growth on graphite',
     'Cited Pt, Ag, Cu, Cd and Zn studies use dilute aqueous metal-ion solutions near 1 mM, overpotentials above 400 mV and 10–200 ms plating periods. The source summarizes prior particles of 1–15 nm and densities of 10⁹–10¹⁰ cm⁻². These are earlier-work ranges, not replacements for the current acetonitrile / silicon procedure or new complete recipe records.',
     cats('cited_prior_context',3),kind='cited_prior_context',scope='cited_context')

# Remaining explicit source qualifications: concise, academically spaced prose.
CONFLICTS = [
('Publication dates','The journal year is 1999. The 1998 manuscript and online dates, and the legacy catalog year 1997, must not replace it. Author initials are retained without guessed expansions.'),
('Doping typography','The abstract prints n²+-Si(100), whereas the experimental section and body use n++ with 10²⁰ cm⁻³ doping. The methods anchor the preparative substrate; the typography difference remains documented.'),
('Silver concentration by experiment','The shared synthesis uses 1 mM silver; the CV introduction and caption say 10 mM but detailed discussion says 1 mM; Scheme 1 labels 1 mM; Figure 3 says 1.5 mM. No universal concentration is selected.'),
('Figure 2d doping assignment','The Figure 2d caption says n++ silicon while the discussion identifies nondegenerate n-Si. Numerical observations use the body assignment with this conflict visible.'),
('Figure 2 potential axis','Figure 2 labels potential in V while ticks run through hundreds and the body interprets millivolts. The original image is retained; source-context millivolt readings do not silently correct its axis.'),
('Reference-electrode conversion','Silver-free solutions physically use SCE, but all published potentials are referred to silver. The conversion offset is unknown, so published potentials are not raw SCE readings.'),
('TEM beam units','The source calls 200 keV an accelerating voltage. The printed energy unit is retained; a 200 kV voltage would be a curator normalization and is not silently substituted.'),
('Aqueous silver-oxide naming','The aqueous-instability discussion names AgO; a later comparison names Ag₂O. These compounds are not interchangeable and neither is established as the product of the current metallic-silver preparation.'),
('Charge-unit conflict','Figure 5 and nearby prose print mC/cm², whereas Figures 7 and 9 print µC/cm². Current density in mA/cm² integrated over milliseconds would suggest µC/cm², but dimensional reasoning is not permission to overwrite the source.'),
('Charge and equivalent coverage','The monolayer reference is printed as 222 mC/cm², and the body sometimes calls charge values Γ. Q denotes charge density; Γ denotes equivalent monolayers. They remain distinct quantities.'),
('Assumed current efficiency','The 100% value is an assumed conversion maximum, not a measured Ag current fraction. Hydrogen evolution occurs concurrently at −800 mV. Reported equivalent coverages are upper bounds.'),
('TEM and AFM specimen joins','TEM diameters are printed as 10–25 Å for a transferred population of unknown pulse duration. AFM heights belong to different named figures. No join or unit correction is made on the basis of size plausibility.'),
('Reference diffraction spacing','Table 1 prints expected (111) spacing 2.32 Å and experimental spacing 2.37 Å. The reference value is preserved without external substitution; reference relative intensity is not measured specimen intensity.'),
('Four displayed histograms','Figure 7 has four panels and lists 5, 10, 15 and 25 ms, although the caption says five samples. Only the four shown cohorts are represented; the fifth is unknown.'),
('Histogram text versus labels','The body’s smallest mean / spread is 2.4 / 2 nm; the top inset gives 2.2 / 2.4 nm. The largest spread is approximately 6 nm in prose versus 6.1 nm in the plot. Both source forms remain available.'),
('Absolute spread, not RSD percent','The body calls a standard deviation RSD but gives nanometer values. The plotted σ is retained as an absolute height-distribution spread, not a relative percentage or standard error.'),
('Figure 8 ordinate and error bars','Figure 8 and its discussion concern particle density, but the caption names height and height-distribution σ. The density interpretation is visible; density uncertainty statistics remain unresolved.'),
('Nucleation-rate units','The body gives 7.6 × 10⁷–2.2 × 10⁹ cm⁻² ms⁻¹; the conclusion prints 8 × 10⁷–2 × 10⁹ cm⁻² s⁻¹. These conflicting units and ranges are not normalized into a single kinetic label.'),
('Summary and time-window scope','The abstract, body and conclusion give partly different density ranges and plateau times. A 2–3 ms induction claim coexists with a 2 ms image. No exact onset or universal plateau time is reconstructed.'),
('Incomplete Equation 2 parameters','Equation 2 contains undefined A and starred C and lacks the F visible in Equation 1. Note 43 supplies C, D and ρ but not every parameter. The reported N∞ is retained as an author calculation, not a reproduced result.'),
('Early fit and current selectivity','Later current includes hydrogen evolution; early silver dominance is an assumption. Body R = 0.999 differs in precision from inset R = 0.99947. Intercept and slope dimensions come from the plotted axes, not explicit units next to the numbers.'),
('Sphere versus hemisphere','The AFM interpretation uses height approximately as full-sphere diameter; Equation 3 models height as a hemispherical radius. These geometries do not support an interchangeable diameter label.'),
('Model-curve cross-reference','The body refers to Equation 3 predictions in Figure 8, but the visible curves appear in Figure 9. The reader links the actual model plot while documenting the source typo.'),
('Unspecified probe dimension','The 0.6 µm and 2 µm Ultralever descriptions do not identify a tip radius, cantilever thickness or another named dimension. No force constant, load, angle or scan rate is inferred.'),
('Unreported experimental settings','Bath volume and temperature, gas flow, illumination, stirring, pulse frequency and timing response, transfer history and calendar dates are absent. Unknown settings are not filled with laboratory defaults.'),
('Bounded metallicity observation','Metallic SAED after at least 1 h in air does not measure oxidation fraction, long-term lifetime or the state of every particle. No universal stability target is derived.'),
('Characterization not supplied','The paper supplies electrochemical properties, AFM, TEM and SAED. It does not supply UV–visible absorption, PL, Raman, catalytic performance, an XRD pattern, an experimental CIF or an atomistic interface structure.'),
('SI scope','No matching local SI or availability declaration was identified in the nine supplied pages and targeted local identity checks. This does not prove that publisher SI never existed.')]
for n,(title,text) in enumerate(CONFLICTS,1):
    item('sources',f'conflict-{n:02}',title,text,cats('conflict',n),scope='source_metadata',kind='source_conflict_or_semantic_limit')

REFS = [
('Brodde et al. J. Vac. Sci. Technol. B 1991, 9, 920–923.','Vapor-deposited Ag / Si(100) background.'),
('Doraiswamy; Jayaram; Marks. Phys. Rev. B 1995, 51, 10167–10170.','Vapor-deposited Ag / Si background.'),
('Hashizume et al. J. Vac. Sci. Technol. B 1990, 8, 249–250.','Vapor-deposited Ag / Si background.'),
('Samsavar et al. Phys. Rev. Lett. 1989, 63, 2830–2833.','Vapor-deposited Ag / Si background.'),
('Naik et al. J. Vac. Sci. Technol. A 1994, 12, 1832–1837.','Vapor-deposited Ag / Si background.'),
('Borensztein; Alameh. Appl. Surf. Sci. 1993, 65, 735–741.','Vapor-deposited Ag / Si background.'),
('Oskam; Long; Natarajan; Searson. J. Phys. D 1998, 31, 1927.','Review of semiconductor electrodeposition and progressive nucleation.'),
('Oskam et al. Symp. Electrochem. Synth. Mod. Mater. 1997, 257–266.','Earlier metal electrodeposition.'),
('Koinuma; Uosaki. J. Electroanal. Chem. 1996, 409, 45–50.','Earlier semiconductor-supported metal growth.'),
('Allongue; Souteyrand. J. Vac. Sci. Technol. B 1987, 5, 1644–1649.','Earlier metal / semiconductor electrodeposition.'),
('Allongue; Souteyrand. Electrochim. Acta 1989, 34, 1717–1722.','Earlier, longer-time nucleation.'),
('Allongue; Souteyrand. J. Electroanal. Chem. 1989, 269, 361–374.','GaAs interfacial-state comparison.'),
('Allongue; Souteyrand. J. Electroanal. Chem. 1990, 286, 217–237.','GaAs and longer-time nucleation.'),
('Allongue; Blonkowski; Lincot. J. Electroanal. Chem. 1991, 300, 261–281.','N-type semiconductor electrodeposition.'),
('Allongue; Blonkowski; Souteyrand. Electrochim. Acta 1992, 37, 781–797.','N-type semiconductor electrodeposition.'),
('Allongue; Souteyrand. J. Electroanal. Chem. 1993, 362, 79–87.','GaAs metal-cluster interfacial states.'),
('Allongue; Souteyrand; Allemand. J. Electroanal. Chem. 1993, 362, 89–95.','GaAs metal-cluster interfacial states.'),
('Bindra; Gerischer; Kolb. J. Electrochem. Soc. 1977, 124, 1012–1018.','N-type semiconductor and longer-time nucleation.'),
('Hart et al. Appl. Phys. Lett. 1995, 67, 1316–1318.','Earlier semiconductor-supported metal growth.'),
('Oskam et al. J. Appl. Phys. 1993, 74, 3238–3245.','Earlier semiconductor electrochemistry.'),
('Uosaki et al. Appl. Surf. Sci. 1997, 121, 102–106.','Earlier growth and contact-AFM comparison.'),
('Smilgies et al. Surf. Sci. 1996, 367, 40–44.','Earlier metal growth.'),
('Scherb; Kolb. J. Electroanal. Chem. 1995, 396, 151–159.','Earlier growth and reduced-variable current analysis.'),
('Zangwill. Physics at Surfaces; Cambridge University Press, 1988.','Surface-energy and growth-mode argument.'),
('Zoval; Lee; Gorer; Penner. J. Phys. Chem. B 1998, 102, 1166–1175.','Prior Pt / HOPG, pulse apparatus, height comparison and instantaneous growth.'),
('Zoval; Stiger; Biernacki; Penner. J. Phys. Chem. 1996, 100, 837–844.','Prior Ag / HOPG, pulses and aqueous oxidation.'),
('Hsiao et al. J. Am. Chem. Soc. 1997, 119, 1439–1448.','Prior copper growth on graphite.'),
('Anderson; Gorer; Penner. J. Phys. Chem. B 1997, 101, 5895–5899.','Prior cadmium growth on graphite.'),
('Gorer; Ganske; Hemminger; Penner. J. Am. Chem. Soc. 1998, 120, 9584–9593.','Prior cadmium growth on graphite.'),
('Nyffenegger et al. Chem. Mater. 1998, 10, 1120.','Prior zinc growth on graphite.'),
('Kolb, editor. Advances in Electrochemistry and Electrochemical Engineering; Wiley, 1978; Vol. 2.','Metal-on-metal growth background; volume follows the inspected bibliography.'),
('Morcos. J. Chem. Phys. 1972, 57, 1801.','Graphite surface energy near 35 dyn/cm.'),
('Wierenga; Kubby; Griffith. Phys. Rev. Lett. 1987, 19, 2169, as printed.','Earlier 1.35 Å Si(100) steps. The printed volume is not independently corrected.'),
('Dijkkamp et al. Appl. Phys. Lett. 1990, 56, 39.','Earlier UHV Si(100) steps.'),
('Houbertz; Memmert; Behm. Appl. Phys. Lett. 1991, 58, 1027.','Fluoride-etched silicon in 0.1 M sulfuric acid.'),
('Lewis. Acc. Chem. Res. 1990, 23, 176.','Hydrogen-terminated silicon stability in acetonitrile.'),
('Gerischer. Electrochim. Acta 1990, 35, 1677–1699.','Semiconductor energy-level interpretation.'),
('Sze. The Physics of Semiconductor Devices, 2nd ed.; Wiley, 1981.','Schottky barriers, tunneling and saturation current; not a measured barrier in this study.'),
('Scharifker; Hill. Electrochim. Acta 1983, 28, 879–889.','Nucleation and current-transient theory.'),
('Gunawardena et al. J. Electroanal. Chem. 1982, 138, 225–239.','Nucleation and current-transient theory.'),
('Vereecken; Gomes. J. Electroanal. Chem. 1997, 433, 19–31.','Nucleation and current-transient theory.'),
('Hills; Schiffrin; Thompson. Electrochim. Acta 1974, 19, 657.','Early-current equations for instantaneous and progressive nucleation.'),
('Direct source note 43.','The inspected note supplies CAg = 10⁻⁶ mol/cm³, in-house DAg = 1.25 × 10⁻⁵ cm²/s in 0.1 M LiClO₄ / acetonitrile, and model density ρAg = 10.5 g/cm³. It is not an unread external reference.'),
('Vereecken et al. J. Chem. Soc., Faraday Trans. 1996, 92, 4069–4075.','Earlier contact-AFM work on Cu / GaAs.')]
refs=[]
for n,(bib,text) in enumerate(REFS,1):
    d=item('sources',f'reference-{n:02}',f'Reference / note {n}',text,cats('reference',n),
           kind='direct_source_note' if n==43 else 'cited_reference_context',
           scope='model_context' if n==43 else 'cited_context',
           notes=(bib, 'Bibliographic context from the inspected article; the cited work was not independently opened for this review.' if n!=43 else 'The model-input note is directly inspected; undefined Equation 2 parameters remain unresolved.'))
    refs.append({'id':f'reference-{n}','reference_number':n,'bibliography':[bib],'context':text,
                 'direct_source_note_reviewed':n==43,'cited_work_independently_reviewed_in_this_task':False,
                 'import_experimental_evidence':False,'source_locators':d['source_locators']})

# Original figures and equations remain source crops, never synthetic substitutes.
assets={c:[] for c in ['figures','tables','schemes','equations','source_notes']}
asset_map={}
char_fig={f['id']:f for f in char['figures']}
for a in manifest['assets']:
    path=B/'crop-assets'/a['relative_asset']
    assert sha(path)==a['sha256'] and a['visually_reviewed'], a['id']
    aid=re.sub(r'^(figure|table|scheme|equation)-0',r'\1-',a['id'])
    cat={'figure':'figures','table':'tables','scheme':'schemes','equation':'equations'}.get(a['type'],'source_notes')
    records=['characterization']
    if cat=='figures': records += ['electrodeposition']
    if aid in ['figure-1','figure-5','figure-7','figure-8','figure-9']: records += ['afm']
    if aid in ['figure-2','scheme-1']: records += ['cyclic-voltammetry']
    if aid in ['figure-3','figure-4','equation-1','equation-2']: records += ['current-transients']
    if aid in ['figure-6','figure-6b-saed','table-1']: records += ['tem-saed']
    if aid=='equation-3': records += ['afm']
    ff=char_fig.get(aid,{})
    v={'id':aid,'label':(aid.replace('-',' ').capitalize()+': '+a['title']),
       'document_role':'main','page':a['pdf_page'],'printed_page':a['printed_page'],
       'source_locators':[ev(a['pdf_page'],a['title'])['locator']],
       'caption_paraphrase':a['caption_paraphrase'],'sample_scope':a['sample_scope'],
       'sample_links':[P+k for k in dict.fromkeys(records)],
       'sample_linkage':'Source-cohort or model-context association only. No exact cross-instrument specimen identity is inferred.',
       'evidence_class':a['evidence_type'],'public_asset':f"assets/figures/{SID}/{a['relative_asset']}",
       'public_asset_sha256':a['sha256'],
       'asset_provenance':{'source_file':a['source_file'],'source_sha256':a['source_sha256'],
          'source_pdf_page':a['pdf_page'],'crop_bbox_pdf_points_top_left':a['bbox_pdf_points_top_left'],
          'crop_normalized':a['crop_normalized'],'render_dpi':a['dpi'],'pixel_dimensions':a['pixel_dimensions'],
          'renderer':a['renderer'],'transformation':'Faithful rectangular crop only; no synthesis, recoloring or curve digitization.'},
       'quantitative_context':a['scope_caveats']+ff.get('limits',[]), 'panels':a.get('panels',[]),
       'notes':a['scope_caveats'],'text_reviewed':True,'visual_reviewed':True,
       'reviewed':False,'reader_render_verified':False,'training_eligible':False,'source_asset_type':a['type']}
    if ff:
        v['structured_contexts']=ff.get('structured_contexts',[])
        v['axes']=ff.get('axes',[])
    if aid=='figure-2':
        v['quantitative_context'] += ['Original current-scale arrows: panel a, 4 µA/cm²; panel b, 200 µA/cm²; panel c, 4 µA/cm²; panel d, 100 µA/cm². These are graphical scale references, not measured peak currents.',
            'Sequential-scan styles: scan 1 is solid, scan 2 dotted and scan 3 short dashed. These styles identify scans, not separate synthesized populations.']
    if aid=='figure-6':
        v['quantitative_context'].append('The caption calls panel a transmission electron diffraction, but the visual panel is a TEM image. Panel b is the actual SAED pattern; panel c is an author indexing schematic. The caption terminology conflict does not change these evidence classes.')
    if cat=='equations':
        v['expression']=next(e['expression'] for e in char['equations'] if e['id']==aid)
    if cat=='tables': v['structured_rows']=char['tables'][0]['rows']
    if a['type']=='figure_panel': v['parent_id']='figure-6';v['duplicate_detail_crop']=True
    assets[cat].append(v);asset_map[aid]={'private_file':str(path),'sha256':a['sha256']}
    target = ('saed-indexing' if aid=='figure-6b-saed' else 'early-current-models' if aid in ['equation-1','equation-2'] else
              'height-charge-model' if aid=='equation-3' else 'band-position' if aid=='scheme-1' else
              'saed-indexing' if aid=='table-1' else None)
    if target:
        it=next(i for s in sections for i in s['items'] if i['id']==target)
        it.setdefault('original_assets',[]).append({'id':aid,'label':'Open original '+a['title'],
                       'public_asset':v['public_asset'],'sha256':a['sha256']})
for n in range(1,10): mapping[f'figure-{n:02}']=[f'figure-{n}']
mapping['scheme-01']=['scheme-1','band-position','doping-and-tunneling']
for n in range(1,4): mapping[f'equation-{n:02}'].append(f'equation-{n}')
for n in range(1,5): mapping[f'table-{n:02}'].append('table-1')

inventory=[]
for key in keys:
    r=drafts.get(P+key)
    assert r, 'Canonical draft missing: '+P+key
    inventory.append({'id':P+key,'label':r['title'],'record_ids':[P+key], 'record_type':r['record_type'],
        'status':'private_source_context_prepared','scope':'One reported synthesis method with explicitly scoped pulse options.' if key=='electrodeposition' else
        'Supporting procedure, deliberate control or source-scoped observation; not an additional synthesis route.',
        'gaps':['Matching SI not located or verified.','Exact physical batch and cross-instrument identity not established.'],
        'canonical_draft_present':True})
ledger={'schema_version':'1.0','paper_id':SID,'doi':identity['doi'],'title':identity['title'],
    'paper':{'authors':identity['authors'],'journal':'Langmuir','year':1999,'volume':15,'issue':3,'pages':'790–798'},
    'source_group':SID,'corpus_paper_id':identity['existing_identity']['papers'][0]['paper_id'],
    'corpus_document_id':identity['cached_identity_reuse'][0]['document_id'],
    'review_scope':'supplied_main_only_si_unverified','supporting_information':identity['si'],
    'documents':[{'role':'main','filename':'10.1021_la980800b.pdf','sha256':identity['main_sha256'],'page_count':9,
        'pages':[{'page':p,'printed_page':789+p,'text_read':True,'visual_review':True,
                  'sections':[f'All text, graphics, captions, notes and references on supplied main page {p}']} for p in range(1,10)]}],
    'document_identity_verification':{'method':'Printed DOI, title, byline and running headers corroborate two byte-identical local main copies.','full_doi_printed':True},
    'coverage_status':'All nine supplied main pages read and visually inspected; all 202 independent source units have explicit reader or original-asset destinations.',
    'independent_audit':'Independent source audit completed; canonical, rendered-reader, apparatus and publication acceptance are tracked separately.',
    'publication_status':'private_proposal_not_published','source_review_promoted':False,'training_eligible':False,
    'training_note':'One source method, four supporting procedures, two deliberate controls and one contextual observation remain separate. Model inputs, curve fits, cited data, AFM height and transferred TEM diameters are not interchangeable training labels.',
    'recipe_inventory':inventory,'characterization_inventory':{'reader_item_ids':[i['id'] for s in sections if s['id'] in ['structures','properties'] for i in s['items']]},
    'record_formulation_labels':{rid:[p['sample_id'] for p in r['products']] for rid,r in drafts.items()},
    'record_formulation_scope_note':'Curator cohort and context IDs are not author batch identifiers. Figure 5, Figure 7, TEM, CV and model contexts retain their own sample scope.',
    'chemical_intuition':{'reader_item_ids':[i['id'] for s in sections if s['id']=='intuition' for i in s['items']],
       'scope':'Original author explanations, cited inputs and explicitly identified curator implications remain distinct.'},
    'reader_contract':{'version':'1.0','section_ids':[s['id'] for s in sections],
       'item_fields':['id','title','text','claim_type','sample_scope','evidence','source_locators','canonical_links','notes','facts','training_eligible']},
    'reader_sections':sections,**assets,'referenced_methods':refs,
    'remaining_gaps':['Matching SI not located or verified.','Charge, rate, doping, concentration and source-caption conflicts remain explicit.',
        'Missing physical batch IDs, raw particle lists, curve tables, exact current efficiency, atomic coordinates and unreported instrument / bath conditions are not supplied by inference.',
        'Canonical-to-reader acceptance and deployment are independently tracked; this proposal does not assert publication.'],
    'material_evidence_records':{},
    'evidence_conflicts':[{'id':i['id'],'text':i['text'],'source_locators':i['source_locators']} for s in sections for i in s['items'] if i['id'].startswith('conflict-')],
    'counts':{}}

# Exact source-to-reader and quantitative-row coverage, checked against actual pointers.
targets={}
for si,s in enumerate(sections):
    for ii,i in enumerate(s['items']): targets[i['id']]=f'/reader_sections/{si}/items/{ii}'
for cat,aa in assets.items():
    for n,a in enumerate(aa): assert a['id'] not in targets;targets[a['id']]=f'/{cat}/{n}'
assert set(mapping)==set(units), {'missing':sorted(set(units)-set(mapping)),'extra':sorted(set(mapping)-set(units))}
assert set(row_mapping)==set(rows), {'missing_rows': sorted(set(rows)-set(row_mapping))}
assert len(targets)==sum(len(s['items']) for s in sections)+15
mapped=[]
for n,u in enumerate(audit['units']):
    for target in mapping[u['id']]: assert target in targets, (u['id'],target)
    mapped.append({'source_unit_id':u['id'],'source_audit_json_pointer':f'/units/{n}',
        'category':u['category'],'reader_item_ids':mapping[u['id']],
        'reader_json_pointers':[targets[k] for k in mapping[u['id']]],
        'disposition':'Original asset plus readable source context' if u['category'] in ['figure','table','scheme','equation'] else
          'Cited background or direct source note, explicitly scoped' if u['category'] in ['reference','cited_prior_context'] else
          'Source-scoped readable evidence with limitations; no automatic training promotion',
        'evidence':u['evidence']})
checks=[]
def check(name,ok):
    checks.append({'name':name,'passed':bool(ok)})
    assert ok,name
check('202 independent units all mapped',len(mapped)==202)
check('143 typed rows all represented',len(row_mapping)==143)
check('44 references and direct note 43',len(refs)==44 and refs[42]['direct_source_note_reviewed'])
check('9 figures, 1 table, 1 scheme, 3 equations, 1 duplicate SAED detail',list(map(len,[assets[c] for c in assets]))==[9,1,1,3,1])
check('Eight canonical IDs with one synthesis route',len(inventory)==8 and sum(x['record_type']=='literature_protocol' for x in inventory)==1)
check('Every figure accessible from parent route',all(P+'electrodeposition' in x['sample_links'] for x in assets['figures']))
check('Main-only SI unverified',ledger['review_scope']=='supplied_main_only_si_unverified')
check('No private proposal training promotion',not ledger['training_eligible'] and all(not i['training_eligible'] for s in sections for i in s['items']))
counts={'reader_items':sum(len(s['items']) for s in sections),'source_audit_units':len(mapped),'typed_characterization_rows':len(rows),
        'figures':9,'tables':1,'table_rows':4,'schemes':1,'numbered_equations':3,'unnumbered_calculations':1,
        'original_assets':15,'duplicate_detail_assets':1,'references_and_notes':44,'records':8,
        'record_types':dict(Counter(x['record_type'] for x in inventory)),'supplied_main_pages':9,'matched_si_pages':0}
ledger['counts']=counts
coverage={'source_audit_sha256':sha(B/'source-audit.json'),'source_audit_unit_map':mapped,
          'measurement_row_map':[{'row_id':'char-'+k,'reader_item_ids':v,'reader_json_pointers':[targets[t] for t in v]} for k,v in row_mapping.items()],
          'scope':'Every independent source-audit unit and typed row has a reader destination. This is private extraction coverage, not publication acceptance.'}
for filename,value in [('stiger1999.json',ledger),('source-item-coverage.json',coverage),
                       ('validation.json',{'status':'passed','created_utc':datetime.now(timezone.utc).isoformat(),
                            'counts':counts,'checks':checks,'input_hashes':{str(p.name):sha(p) for p in [B/'source-audit.json',B/'characterization-draft.json',B/'crop-assets/manifest.json']},'asset_files':asset_map})]:
    (OUT/filename).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'HANDOFF.md').write_text('# Stiger 1999 private reader proposal\n\n'+json.dumps(counts,indent=2)+
    '\n\nAll nine main pages read as text and visually inspected. SI remains unverified. The source ledger has six academic sections, all 202 independent unit destinations, all 143 typed characterization rows and all 15 original assets. The extra SAED detail is an enlarged crop of Figure 6b, not a new experiment. The unnumbered surface-miscut calculation remains text context, not a fourth numbered equation.\n\nOne route is distinct from four procedures, two controls and one observation. Every figure links to the parent route for navigation, with source-cohort limits. Exact current efficiency, physical batch joins, corrected charge/rate units, band structure and a refined Ag/Si interface are not invented.\n\nRun this builder after the canonical draft set changes to refresh actual sample pointers and inventory titles. Private-only: canonical/source promotion, rendered reader review and publication are root-owned independent gates.\n',encoding='utf-8')
print(json.dumps({'status':'passed','counts':counts,'ledger_sha256':sha(OUT/'stiger1999.json')}))
