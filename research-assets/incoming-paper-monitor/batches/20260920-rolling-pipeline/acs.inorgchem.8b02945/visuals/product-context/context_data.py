"""Source-specific display prose. No source or canonical mutations."""
CARDS = {
 'conversion': ('Optically monitored MSC conversion', 'Reaction-condition context', 'Product absorption tracks conversion; complete composition and exact specimen joins remain unassigned.'),
 'acid': ('Isolated carbonyl-labelled phenylacetic acid', 'PhCH2–13CO2H · named isolated product', 'The source reports white crystals and NMR characterization. No crystal structure or conformer is supplied here.'),
 'msc-reference': ('Natural-abundance phenylacetate MSC', 'Cluster identity and reference context', 'The cited prior cluster structure does not provide current product coordinates or an atomic reconstruction.'),
 'msc-labelled': ('Carbonyl-labelled phenylacetate MSC', 'Isotopically labelled cluster reference', 'Labelling is distinguished from the natural-abundance reference. Full upstream cluster preparation is cited only.'),
 'exchange': ('MSC carboxylate-exchange solution', 'NMR solution context', 'Observed resonances and inferred exchange do not establish a unique dissolved complex or final solid product.'),
 'msc-optical': ('MSC absorption and control context', 'Optical solution measurement', 'Temperature response and additive controls retain their own scope; no QD phase or particle size is inserted.'),
 'diffraction': ('Powder diffraction · source phase components', 'Zinc-blende InP · In2O3', 'These are reported diffraction assignments. Whole-sample purity, phase fractions and exact aliquot joins remain unknown.'),
 'tem-agglomerates': ('150 °C · local microscopy specimen', 'Agglomerated structures', 'Local InP fringe evidence is distinct from the whole-powder phase mixture and from Scherrer domain estimates.'),
 'tem-spheres': ('250 °C · local microscopy specimen', 'Spherical InP particles reported', 'The reported TEM diameter and its undefined ± statistic belong to this specimen, not all reaction conditions.'),
 'tem-aging': ('300 °C · extended-time microscopy', 'Aging / aggregation context', 'The two source images have unspecified individual ages. No time-specific size or atomistic model is inferred.'),
 'domains': ('Powder · Scherrer analysis context', 'Coherent diffraction-domain estimates', 'Peak fits and source-calculated domains are distinct from TEM particle sizes; fit-box/prose conflicts remain visible.'),
 'pretreatment': ('130 °C · pretreated MSC context', 'Noncrystalline / unresolved material', 'The source describes noncrystalline material and altered spectra. A unique compound or monomer structure is not identified.'),
 'post-pretreatment': ('Conversion after MSC pretreatment', 'Subsequent 250 °C optical comparison', 'Lower semiconductor absorbance is not an isolated yield or solved composition. Pretreatment and conversion remain distinct.'),
 'thermal': ('Solid MSC · thermal-analysis context', 'Heating, cooling and cycling observations', 'Melting and surface-rearrangement assignments are source interpretations; they do not define new isolated products.'),
}

# Explicit source-context membership, independent of record material_formula.
SPECS = {}
def spec(sid,key,label,caption,facts,phase=None):
 assert sid not in SPECS
 SPECS[sid]={'key':key,'label':label,'caption':caption,'facts':facts.split(),'phase':phase}

spec('acid-isolated','acid','Isolated carbonyl-13C phenylacetic acid',
 'The isolated upstream product is carbonyl-labelled phenylacetic acid, reported as white crystals after recrystallization. This is a molecular precursor preparation, not an InP nanocrystal sample. The named isotope position is retained without constructing a geometry.', 'acid-crystallize acid-nmr')
spec('phenylacetate-reference','msc-reference','Natural-abundance phenylacetate MSC reference',
 'The source refers to the previously determined In37P20(O2CCH2Ph)51 cluster structure. That cited structure is prior evidence; no coordinate file or current atomic refinement is supplied. Figure S1 compares this natural-abundance reference with the labelled MSC. Neither context is a QD coordinate model.', 'prior-cluster si-nmr')
spec('nmr-labeled','msc-labelled','Carbonyl-13C-labelled phenylacetate MSC',
 'The labelled phenylacetate MSC is a separate reference from the natural-abundance cluster. Its preparation is cited rather than reproduced in full. Variable-temperature NMR and Figure S1 optical comparisons do not establish a current crystal structure or a uniquely determined solution geometry.', 'labeled-msc nmr-vt si-nmr')
spec('vt-absorption','msc-optical','Phenylacetate MSC · variable-temperature absorption',
 'This is the reversible variable-temperature absorption experiment on the phenylacetate MSC. Prose and figure lower-temperature endpoints differ. It is not the high-temperature myristate-MSC conversion series and receives no QD phase, size or atomic model.', 'abs-vt')
spec('nmr-acid-exchange','exchange','Natural-abundance MSC + labelled acid · NMR',
 'Natural-abundance MSCs are combined with labelled phenylacetic acid for the exchange comparison. Free acid and authentic labelled MSC are separate references. Changes in resonances support the authors’ exchange interpretation; no isolated ligand-exchanged product or unique coordination geometry is established.', 'acid-exchange')
spec('nmr-indium-exchange','exchange','Natural-abundance MSC + labelled indium salt · NMR',
 'This is the labelled indium-phenylacetate addition experiment and its NMR comparison. Excess salt signals and exchange interpretation remain distinct from a new isolated cluster or QD product. Neither free-salt speciation nor a solution complex is assigned.', 'indium-exchange si-exchange')
spec('acid-optical-control','msc-optical','MSC + myristic acid · absorption control',
 'Figure S3 compares myristic-acid additions to the MSC. The source reports a small blue shift without observed cluster decomposition in this panel; temperature and concentration are not explicit. The control does not establish high-temperature conversion or a new particle population.', 'si-acid-abs')

conv_note='This label identifies a source reaction/optical condition, not a new verified physical replicate. InP growth is followed through absorbance. No whole-specimen composition, phase fraction, TEM diameter, Scherrer domain or exact cross-technique aliquot identity is assigned to this condition.'
for t in [150,200,250,300]:
 spec(f'temp-{t}','conversion',f'{t} °C · no-additive conversion',conv_note,'temperature-series growth-time')
spec('temperature-series','conversion','Four-temperature · optical comparison',
 'This is a comparison of separately labelled no-additive temperature conditions, not a pooled product. The source tracks MSC conversion optically; lower-temperature behavior and later colloidal instability remain interpretations of the reported series. Morphology and diffraction are shown in their separate specimen contexts.', 'temperature-series growth-time')
spec('extended-300','conversion','300 °C · extended-time absorption',
 'The source interprets the later evolution of the 300 °C optical sample as Ostwald ripening and changing colloidal stability. Individual TEM image ages are not supplied and are not joined to specific optical time points. Optical changes do not provide a calibrated isolated yield or atomic structure.', 'si-ripening')
spec('extended-300-tem','tem-aging','300 °C · extended-time TEM images',
 'The two TEM images in Figure S10 belong to the extended-time experiment, but their individual ages are unspecified. Their scale bars remain in the original images. No measured diameter, particular optical time point, phase fraction or atomic envelope is invented.', 'si-ripening')
for t in [250,300]:
 spec(f'concentration-{t}','conversion',f'{t} °C · initial-MSC concentration series',
      'This compares separately labelled initial-MSC concentrations through optical growth. It is neither a pooled specimen nor an exact set of replicated representative charges. No per-condition phase, morphology or isolated yield is supplied here.', 'concentration-series')
 for raw,label in [('0p030','0.030'),('0p061','0.061'),('0p182','0.182')]:
  spec(f'c-{t}-{raw}','conversion',f'{t} °C · initial MSC {label} mM',conv_note+' Initial MSC concentration is not an isolated product concentration.','concentration-series')
for kind,temps,name in [('acid',[150,250],'myristic acid'),('indium',[150,200,250],'indium myristate')]:
 for t in temps:
  spec(f'{kind}-{t}','conversion',f'{t} °C · {name} series',
       'This compares additive conditions through optical growth and final absorption. The separately labelled conditions are not pooled. Absorbance-based approximations of yield are not isolated mass yields, and phase or particle size is not assigned to every member.','additive-series additive-effects si-additive-yield' if kind=='indium' else 'additive-series additive-effects')
  for eq in [0,10,20,50]:
   spec(f'{kind}-{t}-eq{eq}','conversion',f'{t} °C · {eq} equiv {name}',conv_note+' The additive amount is relative to the initial MSC, not a solved surface occupancy.','additive-series additive-effects')
spec('additive-250','conversion','250 °C · acid versus indium-carboxylate comparison',
 'The source compares acid and indium-myristate perturbations of conversion. The comparison does not establish the same physical aliquot, quantitative whole composition or ligand population. Proposed acid activation and monomer stabilization remain mechanistic interpretations.','additive-effects')
spec('xrd-context','diffraction','150 / 250 °C powders · phase comparison',
 'The supplied powder patterns are assigned zinc-blende InP and In2O3 components, with the latter described as a byproduct in some reactions. The source compares two temperatures and reference patterns, not a pooled specimen or measured pure product. The independently prepared indium-myristate reference is not a recovered product fraction. GPC separation is reported, but exact fractions and cross-technique aliquot joins are unspecified.','phase-result si-xrd conversion-workup','Zinc-blende InP and In2O3: source phase-component assignments in the powder comparison')
spec('temp-150-tem','tem-agglomerates','150 °C · agglomerated TEM specimen',
 'Figure 3E shows agglomerated structures from the 150 °C condition. Figure S12 provides local fringe / image-FFT evidence, with the fringe assigned to InP (200). The FFT is not an independently reported SAED acquisition. Local crystallinity does not establish a pure whole powder or a quantitative agglomerate diameter.','tem-result phase-result si-fft','Local zinc-blende InP assignment; whole-specimen composition unresolved')
spec('temp-250-tem','tem-spheres','250 °C · spherical TEM specimen',
 'Figure 3F reports spherical InP particles with mean diameter 2.6 ± 0.5 nm from 315 particles. The source does not define the ± statistic as SD or SE. This diameter is not assigned to all 250 °C additive or concentration conditions. The powder diffraction comparison and Scherrer estimates remain separate measurements; exact physical aliquot identity is unknown.','tem-result phase-result','Source InP assignment for this microscopy context; whole-specimen purity not established')
for t in [150,250]:
 spec(f'scherrer{t}','domains',f'{t} °C powder · Gaussian / Scherrer analysis',
      'This is the source-calculated coherent-domain analysis of the '+str(t)+' °C powder. Different peaks yield different estimates, and the printed Gaussian boxes and prose are retained separately where they disagree. These numbers are not TEM diameters or a solved particle boundary. No curve is refitted and no reference pattern is transformed into current atomic coordinates.','scherrer-summary si-scherrer')
spec('pretreat30','pretreatment','130 °C / 30 h · optical and NMR pretreatment',
 'The main Figure 4A discussion describes 130 °C for 30 h and changed absorption / phosphorus environments. The adjacent conversion discussion and SI use 72 h. These histories are not silently merged. The source proposes nonproductive dissolution/decomposition; no chemically unique monomer or pure crystalline QD product is identified.','pretreat pretreat72 si-pretreat')
spec('pretreat-xrd','pretreatment','130 °C · unresolved diffraction pretreatment context',
 'The main describes the prolonged-thermolysis material as noncrystalline. Figure S14 labels the heated sample 130 °C / 72 h and the comparison as oleate MSC, whereas the main discussion uses myristate MSC. The reference InP/In2O3 sticks do not establish those phases as measured products here. Ligand identity and cross-panel 30 h / 72 h joins remain unresolved.','pretreat pretreat72 si-pretreat')
spec('pretreat72-conversion','post-pretreatment','130 °C / 72 h pretreatment → 250 °C conversion',
 'The SI and main comparison describe 72 h pretreatment followed by conversion at 250 °C. This subsequent optical experiment is distinct from the 130 °C noncrystalline intermediate. The 30 h wording elsewhere remains unresolved; lower semiconductor absorbance is not a calibrated isolated yield or a new measured whole composition.','pretreat72 pretreat si-pretreat')
spec('thermal','thermal','Solid myristate MSC · TGA / DSC',
 'This solid-state thermal-analysis context retains melting, cooling and surface-rearrangement interpretations separately from solution conversion. TGA decomposition does not establish a uniquely isolated product or analytical atmosphere. No current atomic model follows from the cited prior MSC structure.','thermal-result si-thermal')
spec('thermal-cycle','thermal','Myristate MSC · repeated DSC cycles',
 'This is the cycling and reheating comparison. The malformed final ramp expression “at a rate of 1800 °C” remains literal source evidence, not an operational rate. Thermal events do not constitute additional synthesis variants or assign a final compound.','si-dsc-cycle thermal-result')

EXCLUDED_SOURCE_CONTEXTS={
 'kinetic-model':'Transformed optical kinetics and fitted models are analysis objects, not a separately synthesized product.',
 'concentration-fit':'The log-rate regression is a fit context, not a physical specimen or product.',
 'additive-fit':'The additive regression combines measurement contexts; it does not define a pooled product.',
 'author-mechanism':'Proposed monomer/fragment pathways are not isolated compounds, measured stoichiometric products or supplied atomic coordinates.',
}
