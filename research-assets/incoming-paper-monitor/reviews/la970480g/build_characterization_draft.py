"""Private, source-scoped characterization extraction; never writes source or Site."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent
SID = 'yao1998'
PREFIX = 'yao-1998-'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ev(page, locator):
    return {'source_id': SID, 'pdf_page': page, 'printed_page': 594 + page, 'locator': locator}
def q(value=None, unit=None, low=None, high=None, approximate=False, raw_text=None):
    out = {'value': value, 'unit': unit}
    if low is not None: out['lower_bound'] = low
    if high is not None: out['upper_bound'] = high
    if approximate: out['approximate'] = True
    if raw_text: out['raw_text'] = raw_text
    return out

rows = []
def row(key, sample, prop, value, page, locator, basis='reported', method=None, condition=None, caveat=None, record='characterization', scope='source_cohort'):
    r = {'id': 'char-' + key, 'suggested_record_id': PREFIX + record,
         'sample_id': sample, 'scope_type': scope, 'property': prop,
         'basis': basis, 'evidence': [ev(page, locator)], 'eligible_training': False}
    r['quantity' if isinstance(value, dict) else 'fact'] = value
    if method: r['method'] = method
    if condition: r['source_condition'] = condition
    if caveat: r['caveat'] = caveat
    rows.append(r)

# Method-specific values are kept separate from nanocrystal product labels.
row('host-wet-diameter', ['sample-a', 'sample-b'], 'host_polymer_particle_diameter', q(unit='um',low=100,high=110),2,'Measurements: water-dispersed absorption samples',method='absorption microspectroscopy',condition='Diameter selected for solution samples after swelling in water.',caveat='Host bead diameter, not CdS nanocrystal diameter.',record='absorption')
row('spectrum-reproducibility', ['sample-a','sample-b'],'absorption_spectrum_reproducibility',q(5,'%',raw_text='within ±5%'),2,'Results: Figure 1 discussion',method='absorption microspectroscopy',condition='Fixed host diameter and reaction time.',caveat='No replicate number or precise reproducibility statistic is reported; this is not nanocrystal size uncertainty.')
row('lamp-power',['sample-a','sample-b'],'lamp_power',q(150,'W'),2,'Measurements: Xe lamp',basis='hardware_specification',record='absorption')
row('monitor-wavelength',['sample-a','sample-b'],'absorbance_monitoring_wavelength',q(450,'nm'),3,'Results: Figure 2 discussion',basis='method_setting',condition='Nearly the excitonic shoulder; time profiles in Figures 2, 8, and 9.',caveat='Not a measured band gap, absorption onset, or peak wavelength.',record='absorption')
row('xrd-scan',['sample-a','sample-b'],'xrd_two_theta_scan_range',q(unit='degree',low=20,high=60),2,'Measurements: XRD',basis='method_setting',record='xrd')
row('xrd-radiation',['sample-a','sample-b'],'xrd_radiation_wavelength',q(.154,'nm'),2,'Measurements: Cu Kα',basis='method_setting',record='xrd')
for angle, plane, intensity, approx in [(26.5,'111','broad and intense',False),(44,'220','very weak',True),(52,'311','very weak',True)]:
    row('xrd-' + plane,['sample-a','sample-b'],'xrd_two_theta_peak',q(angle,'degree',approximate=approx),3,'Results: XRD paragraph',method='Cu Kα XRD',condition=f'Assigned by the authors to ({plane}); {intensity}.',caveat='Reported text applies to the two sample cohorts; no original XRD pattern is printed.')
row('phase',['sample-a','sample-b'],'crystal_phase','Authors assign zinc blende (cubic) CdS from the three reported XRD reflections.',3,'Results: XRD paragraph',basis='author_assignment',method='Cu Kα XRD',caveat='The CdS component is assigned a phase; the host composite is not a single crystal. No refined lattice parameters, coordinates, CIF, or phase fractions are supplied.')
for s,v in [('sample-a',3.8),('sample-b',3.1)]:
    row(s+'-xrd-mean',s,'xrd_line_broadening_mean_size',q(v,'nm'),3,'Results: Gaussian fit of 26.5° reflection and Debye–Scherrer calculation',basis='author_calculated',method='Gaussian peak fit plus XRD line-broadening formula',condition='26.5° peak; references 22 and 23.',caveat='Authors call these mean diameters. Not a TEM population mean or known local depth. FWHM, instrumental correction, shape constant, uncertainty, and specimen collection time are not supplied.')

# Cohort-level optical comparisons: no invented wavelength/absorbance readings from plotted curves.
row('30min-optical',['sample-a','sample-b'],'absorption_comparison','At 30 min, sample a has markedly lower absorbance below 500 nm than sample b.',2,'Figure 1a and Results paragraph',method='single-bead absorption',condition='Reaction time 30 min; host diameter approximately 100 um.',caveat='More CdS in b is the authors’ inference from absorbance, not an isolated yield or direct mass measurement.')
row('48h-optical',['sample-a','sample-b'],'absorption_onset_comparison','At 48 h, sample b has a blue-shifted absorption spectrum relative to sample a.',3,'Results: Figure 1b discussion',method='single-bead absorption',condition='Reaction time 48 h; Figure 1b.',caveat='No numerical onset wavelength, band gap, extinction coefficient, or absorption peak is tabulated.')
row('first2h-optical',['sample-a','sample-b'],'absorption_time_course','Both samples show a rapid increase in absorbance over the first 2 h.',3,'Results: Figure 2',method='450 nm absorption',caveat='Optical reaction-progress proxy, not direct nucleus counting.')
row('sample-b-plateau','sample-b','optical_formation_plateau_time',q(2,'h',raw_text='finished within 2 h'),3,'Results: Figure 2 discussion',basis='author_interpretation',method='450 nm absorption',caveat='Upper-time wording refers to the optical formation profile; it does not override the preparative 2 h stirring followed by 2 days standing.')
row('sample-a-continuation','sample-a','continued_optical_growth_observation_time',q(48,'h',raw_text='continued gradually for up to 48 h'),3,'Results: Figure 2 discussion',method='450 nm absorption',caveat='An observed time extent, not an exact completion time or fitted kinetic lifetime.')
row('early-shape',['sample-a','sample-b'],'early_absorption_shape_comparison','The absorption-band shapes at a given early time were nearly the same for the two samples.',5,'Electrolyte Effects on Nanocrystal Distributions: Figure 8 discussion',method='absorption microspectroscopy',condition='Detailed early-time measurements at t < 10 min.',caveat='Similar particle size is an author inference; no time-resolved numerical sizes are reported.')
for s,v in [('sample-a',4.6e-3),('sample-b',8.9e-3)]:
    row(s+'-sqrt-time-slope',s,'absorbance_vs_sqrt_time_slope',q(v,'s^(-1/2)'),5,'Figure 8 discussion: linear fit slopes',basis='fitted',method='450 nm absorption versus sqrt(time)',condition='Early-time experiment described as t < 10 min; Figure 8 abscissa sqrt(time)/(sec)^(1/2).',caveat='An absorbance slope, not a diffusion coefficient, reaction-order rate constant, or d(absorbance)/dt.')

# Spatial quantities are depth in a polymer host, not dimensions of individual CdS particles.
for s,lo,hi,figure in [('a-depth4um',4,5,'Figures 3b and 4b'),('a-depth8um',8,9,'Figure 3c'),('b-depth9um',9,10,'Figure 7b'),('b-depth15um',15,16,'Figure 7c')]:
    row(s+'-depth',s,'depth_below_polymer_surface',q(unit='um',low=lo,high=hi,approximate=True),4 if s.startswith('a-') else 6,figure,method='cross-sectional TEM',caveat='A region coordinate, not crystallite size or an independently synthesized batch.')
row('a-layer-end','sample-a','cds_distribution_layer_terminal_depth',q(unit='um',low=8,high=10,approximate=True),3,'Dispersion Textures: Figure 3 discussion',method='cross-sectional TEM',caveat='CdS formation terminates at approximately this depth in the inspected host; no CdS crystals were seen in the central region.')
row('a-center','sample-a','central_region_observation','No crystals were observed at the center of the polymer particle.',3,'Dispersion Textures: Figure 3 discussion',method='cross-sectional TEM',caveat='Source-reported observation; no detection limit or sampled volume is supplied.')
row('a-surface-flocculation','a-surface','dispersion_state','No CdS flocculation was observed near the polymer surface.',3,'Figure 4a discussion',method='high-magnification TEM')
row('a-inner-crystals','a-depth4um','local_nanocrystal_diameter',q(unit='nm',low=4,high=7,approximate=True),3,'Figure 4b discussion',method='high-magnification TEM',caveat='Sizes of constituent nanocrystals; aggregates are described separately.')
row('a-inner-aggregates','a-depth4um','aggregate_size_description','Flocculated particles reach several tens of nanometers.',3,'Figure 4b discussion',method='high-magnification TEM',caveat='Qualitative size phrase retained; no arbitrary numerical range is invented.')
row('a-surface-hist-mean','a-surface','tem_distribution_mean_diameter',q(2.7,'nm'),5,'Figure 5a caption',basis='fitted',method='TEM histogram, log-normal fit',caveat='Local surface population, not XRD mean; exact number of counted crystals is not stated.')
row('a-surface-hist-sd','a-surface','lognormal_fit_reported_standard_deviation',q(.4,None,raw_text='a standard deviation of 0.4'),5,'Figure 5a caption',basis='fitted',method='TEM histogram, log-normal fit',caveat='Unit and parameterization are not printed. Do not relabel as 0.4 nm or percentage without additional evidence.')
row('a-inner-hist-depth','a-depth4um','histogram_region_depth',q(4,'um',approximate=True),5,'Figure 5b caption',method='TEM histogram',caveat='Caption says approximately 4 um; related TEM images use a 4–5 um region.')
row('a-inner-hist-mean','a-depth4um','tem_distribution_mean_diameter',q(4.6,'nm'),5,'Figure 5b caption',basis='fitted',method='TEM histogram, normal fit')
row('a-inner-hist-sd','a-depth4um','tem_distribution_standard_deviation',q(1.8,'nm'),5,'Figure 5b caption',basis='fitted',method='TEM histogram, normal fit',caveat='Distribution spread, not uncertainty of the mean or uncertainty of every individual particle.')
row('a-surface-qual-size','a-surface','qualitative_nanocrystal_size_context',q(3,'nm',approximate=True),4,'Discussion beneath Figure 4',basis='author_summary',caveat='Qualitative discussion of many small surface crystals; do not treat as an independent numerical experiment.')
row('a-inner-qual-size','a-depth4um','qualitative_nanocrystal_size_context',q(5,'nm',approximate=True),4,'Discussion beneath Figure 4',basis='author_summary',caveat='Qualitative description of fewer, larger interior crystals; not a second measured size mean.')
row('a-ring-depth','sample-a','optical_ring_depth',q(8,'um',approximate=True),3,'Figure 6 discussion',method='optical microscopy',caveat='Surface-to-ring distance estimates dispersion-layer width L, not the CdS crystal diameter or a separate core–shell nanocrystal.')
row('l-definition',['sample-a','sample-b'],'dispersion_layer_width_definition','L is the distance from the polymer-particle surface to the optically visible ring marking the inner edge of the CdS-containing layer.',3,'Figure 6 discussion and Figure 6b schematic',method='optical microscopy',caveat='Identification with the CdS-layer edge is supported by comparison with the TEM cross section; apparent ring position is not a direct HS− concentration measurement.')
row('sample-b-surface','b-surface','dispersion_state','No flocculation was observed near the polymer surface.',3,'Figure 7a discussion',method='cross-sectional TEM')
row('sample-b-middle','b-depth9um','dispersion_state','Slight flocculation is present at 9–10 um, but CdS remains comparatively homogeneously distributed.',3,'Figure 7b discussion',method='cross-sectional TEM',caveat='The sample is not completely aggregation-free.')
row('sample-b-deep','b-depth15um','dispersion_state','At 15–16 um, clear flocculation coexists with isolated small nanocrystals.',3,'Figure 7c discussion',method='cross-sectional TEM',caveat='15–16 um is an imaged region, not a reported terminal layer thickness.')
row('b-larger-L',['sample-a','sample-b'],'dispersion_layer_width_comparison','Sample b has a wider CdS distribution layer than sample a.',3,'Dispersion Textures: comparison with Figure 7',method='TEM and optical microscopy',caveat='No single numerical terminal L for sample b is reported.')
row('l-resolution',['sample-a','sample-b'],'optical_layer_width_precision_limit',q(4,'um',raw_text='L < 4 um'),5,'Figure 9 discussion',method='optical microscopy',caveat='Below this scale the ring is difficult to establish, so direct L measurement is not precise; this is not an instrument pixel-size specification.')
row('a-L-correlation',['sample-a','sample-b'],'absorbance_layer_width_relation','The two samples follow the same approximately linear relation between 450 nm absorbance and observed L.',5,'Figure 9 discussion, continued on page 6',basis='fitted',method='optical microscopy plus absorption',caveat='No numerical calibration slope or intercept is printed; common CdS density at a given absorbance is the authors’ interpretation.')
row('earliest-optical-limit',['sample-a','sample-b'],'initial_absorption_proxy_limitation','For very small crystals at the earliest times, 450 nm absorbance cannot be treated as a measure of excitonic absorption.',6,'Source note 27',caveat='The optical-to-L inference is restricted to the time and L regions discussed, not universally valid at t approaching zero.')
for s,v in [('sample-a',2.5e-10),('sample-b',1.1e-9)]:
    row(s+'-effective-HS-diffusion',s,'optically_inferred_hydrosulfide_diffusion_coefficient',q(v,'cm^2 s^-1'),6,'Text below Figures 8–9',basis='author_calculated',method='450 nm absorption-to-L correlation plus L = sqrt(2Dt)',caveat='Effective value derived using a quasi-linear diffusion assumption and an optical layer-width proxy, not direct tracer diffusion or a measured precursor diffusivity in free water.')

# Model/citation contexts must never become experimentally measured product targets.
for k,v,label in [('no-salt',-390,'[NaCl] = 0'),('salt',-10,'[NaCl] = 0.5 M')]:
    row('donnan-'+k,'donnan-model-'+k,'donnan_potential',q(v,'mV'),7,'Top-right model calculation',basis='author_calculated_model',condition=label+'; fixed charge X = 0.4 equiv/L wet polymer.',caveat='A model estimate, not a measured electrical potential; model temperature and exact external background-electrolyte concentration are not supplied.',scope='model_context')
row('donnan-swelling','donnan-model-one-third-swelling','donnan_potential_as_printed',q(-26,'meV',raw_text='−26 meV'),7,'Top-right hypothetical swelling calculation',basis='author_calculated_model',condition='NaCl case, assuming swelling reduced to one-third of its original swollen-state value.',caveat='The source prints an energy unit for a potential. Retain the conflict; do not silently convert to mV. This is a hypothetical swelling assumption, not a measured shrinkage.',scope='model_context')
row('donnan-fixed-charge','donnan-model-context','fixed_charge_concentration',q(.4,'equiv/L'),7,'Top-right model calculation; reference 18',basis='cited_model_input',condition='Wet polymer.',caveat='Instruction-manual value reproduced in this source; reference 18 itself has not been inspected here.',scope='cited_context')
row('na-diffusion','pretreatment-context','sodium_diffusion_coefficient',q(1.2e-7,'cm^2 s^-1'),2,'Preparation of sample b; reference 19',basis='cited_context',condition='Cited Chelex 100 Na+ value 1.2e-7 cm^2/s; Dowex A-1 is described as similar.',caveat='The parenthetical value follows Chelex 100 in the source. Not a measured CdS property or the HS− coefficient inferred in this paper.',scope='cited_context')
row('selectivity','donnan-model-context','cadmium_sodium_selectivity_ratio',q(1e7,None,approximate=True),7,'Left-column Donnan explanation; reference 18',basis='cited_context',caveat='Approximate relative selectivity invoked in the mechanism, not a measured loading yield.',scope='cited_context')
row('other-electrolytes','other-electrolytes','electrolyte_comparison','LiCl, KCl, and tetramethylammonium chloride at the source label 0.5 M gave visible absorption and L similar to those of the NaCl sample.',4,'Source note 25',basis='reported_qualitative_comparison',condition='1:1 electrolytes; NaCl comparison labelled 0.5 M.',caveat='No separate curves, exact absorbances, L values, full preparation quantities, or sample-specific sizes are supplied. The authors infer limited ion-specific effects only for this tested class.',record='other-electrolytes')

methods = [
 {'id':'absorption','record_id':PREFIX+'absorption','name':'Single-particle absorption microspectroscopy','apparatus':['Nikon Optiphoto 2 optical microscope','Oriel Multispec 257 polychromator','Princeton Instruments ICCD-576E/G multichannel detector','150 W Xe lamp, Hamamatsu L2273'],'preparation':'Dried CdS/polymer particles were redispersed in water to reduce scattering. Water-swollen particles of 100–110 um diameter were selected.','settings':'Figure 1 displays 400–600 nm spectra; kinetic monitoring is at 450 nm.','unreported':['Spectral resolution','Collection aperture and optical path length','Absorbance calibration or scattering correction details','Raw spectral arrays','Replicate count'],'evidence':[ev(2,'Measurements and Figure 1'),ev(3,'Figure 2 discussion')],'upstream_references':[20,21]},
 {'id':'optical-microscopy','record_id':PREFIX+'optical-microscopy','name':'Single-particle optical microscopy','apparatus':['Sony DXC-930 CCD video camera attached to microscope','Mitsubishi CP-11 video printer'],'observable':'Surface-to-ring distance L; Figure 6 photograph has a 25 um scale bar.','unreported':['Image analysis algorithm','Ring localization uncertainty','Number of host particles analyzed'],'evidence':[ev(2,'Measurements'),ev(5,'Figure 6')],'upstream_references':[]},
 {'id':'xrd','record_id':PREFIX+'xrd','name':'X-ray diffraction','apparatus':['Rigaku RINT 2000'],'settings':'Cu Kα wavelength 0.154 nm; 2θ 20–60°. Gaussian fit of the 26.5° peak followed by a Debye–Scherrer-type size estimate.','unreported':['Original XRD plot','Raw intensities','FWHM','Step size and counting time','Shape constant','Instrumental-broadening subtraction','Lattice refinement and uncertainty'],'evidence':[ev(2,'Measurements'),ev(3,'XRD result paragraph')],'upstream_references':[6,22,23]},
 {'id':'tem','record_id':PREFIX+'tem','name':'Cross-sectional transmission electron microscopy','apparatus':['Hitachi H-300 (low magnification)','JEOL JEM 2010 (high magnification)'],'preparation':'Thin cross sections of the CdS/polymer particles were prepared; the authors note difficulty associated with water-swelling of the host.','settings':'Figures 3 and 7: 250 nm scale bars; Figure 4: 50 nm scale bars.','unreported':['Section thickness','Embedding resin','Cutting instrument and orientation protocol','Electron accelerating voltage','Exact numbers of crystals and particles counted','Lattice-fringe or SAED analysis'],'evidence':[ev(2,'Measurements'),ev(3,'Dispersion Textures'),ev(4,'Figures 3–4'),ev(6,'Figure 7')],'upstream_references':[]},
]

figures = []
def fig(n,page,title,samples,panels,context,axes=None,limits=None):
    figures.append({'id':f'figure-{n}','pdf_page':page,'printed_page':594+page,'title':title,'sample_ids':samples,'panels':panels,'quantitative_context':context,'axes':axes or [],'limitations':limits or [],'evidence':[ev(page,f'Figure {n} and caption')],'eligible_training':False,'original_asset_status':'Original source page visually reviewed; crop binding belongs to root asset integration.'})
fig(1,2,'Absorption spectra at 30 min and 48 h',['sample-a','sample-b'],[
 {'panel':'a','reaction_time':q(30,'min'),'identity':'Both samples; a is no-NaCl and b is NaCl-labelled 0.5 M. Figure panel a is a time point, not sample a.'},
 {'panel':'b','reaction_time':q(48,'h'),'identity':'Both samples; blue shift of salt-treated sample relative to no-salt sample.'}],
 'Host beads approximately 100 um. Retain original curve annotations. No curve digitization.',
 ['Wavelength / nm (displayed 400–600)','Absorbance (panel a 0–0.60; panel b 0–0.80)'],['Displayed axis limits are not fitted onsets or measured maxima.'])
fig(2,3,'Absorbance time profiles',['sample-a','sample-b'],[{'identity':'NaCl 0.5 M: filled circles; no NaCl: open circles. This marker assignment differs from Figures 8–9.'}],
 'Monitoring wavelength 450 nm; sample b approaches a plateau within 2 h, sample a continues changing to 48 h.',
 ['Reaction time / h (displayed 0–50)','Absorbance at 450 nm (displayed 0–0.6)'],['No tabulated points or kinetic model parameters.'])
fig(3,4,'Low-magnification TEM across the no-salt host',['a-surface','a-depth4um','a-depth8um'],[
 {'panel':'a','sample_id':'a-surface','region':'Near the polymer surface','scale_bar':q(250,'nm')},
 {'panel':'b','sample_id':'a-depth4um','region':'Approximately 4–5 um inward','scale_bar':q(250,'nm')},
 {'panel':'c','sample_id':'a-depth8um','region':'Approximately 8–9 um inward, near the inner CdS edge','scale_bar':q(250,'nm')}],
 'All panels are sample a. The lower image side points toward the polymer interior. A layered size/distribution gradient is visible.',limits=['Cross-sectional regions are not independent synthesis variants.'])
fig(4,4,'High-magnification TEM of no-salt surface and interior',['a-surface','a-depth4um'],[
 {'panel':'a','sample_id':'a-surface','region':'Near surface','scale_bar':q(50,'nm')},
 {'panel':'b','sample_id':'a-depth4um','region':'Approximately 4–5 um inward','scale_bar':q(50,'nm')}],
 'Interior constituent crystals of approximately 4–7 nm form aggregates described as several tens of nanometers.',limits=['No lattice-fringe indexing or diffraction pattern is supplied.'])
fig(5,5,'Regional CdS size histograms and distribution fits',['a-surface','a-depth4um'],[
 {'panel':'a','sample_id':'a-surface','fit':'Log-normal, solid curve','mean':q(2.7,'nm'),'reported_standard_deviation':q(.4,None),'scope':'Near surface'},
 {'panel':'b','sample_id':'a-depth4um','fit':'Normal, dashed curve','mean':q(4.6,'nm'),'standard_deviation':q(1.8,'nm'),'scope':'Approximately 4 um inward'}],
 'Histogram observations and fitted curves must remain distinguishable. No separate table or raw histogram counts were provided.',
 ['Nanocrystal diameter / nm (0–10)','Number of crystals (0–25)'],['Do not sum bars from the image to invent an exact sample size.','The unit/definition of log-normal SD 0.4 is unspecified.'])
fig(6,5,'Optical image and definition of CdS-layer width',['sample-a'],[
 {'panel':'a','kind':'Optical micrograph','scale_bar':q(25,'um')},
 {'panel':'b','kind':'Schematic','definition':'L is surface-to-ring distance; ring marks the inner edge of CdS formation.'}],
 'A ring approximately 8 um inside the surface is described in the body text. The schematic is not another measurement.',limits=['Image morphology is the micron-scale polymer host, not a single CdS crystal shape.'])
fig(7,6,'Low-magnification TEM across the salt-treated host',['b-surface','b-depth9um','b-depth15um'],[
 {'panel':'a','sample_id':'b-surface','region':'Near surface','scale_bar':q(250,'nm')},
 {'panel':'b','sample_id':'b-depth9um','region':'Approximately 9–10 um inward','scale_bar':q(250,'nm')},
 {'panel':'c','sample_id':'b-depth15um','region':'Approximately 15–16 um inward','scale_bar':q(250,'nm')}],
 'Sample b. Surface has no observed flocculation; 9–10 um has slight flocculation; 15–16 um has clear flocculation alongside small isolated crystals.',limits=['Deepest imaged depth is not an established terminal distribution width.'])
fig(8,6,'Early absorbance versus square root of time',['sample-a','sample-b'],[
 {'sample_id':'sample-a','marker':'Filled circle','line':'Solid','slope':q(4.6e-3,'s^(-1/2)')},
 {'sample_id':'sample-b','marker':'Open circle','line':'Dashed','slope':q(8.9e-3,'s^(-1/2)')}],
 'Early-time experiment described as t < 10 min. The fitted ordinate is absorbance, not its time derivative.',
 ['sqrt(time) / (sec)^(1/2) (0–25)','Absorbance at 450 nm (0–0.20)'],['No numerical point arrays or fit uncertainties are supplied.'])
fig(9,6,'Absorbance correlated with observed dispersion-layer width',['sample-a','sample-b'],[
 {'sample_id':'sample-a','marker':'Filled circle','salt_label':'0 M'},
 {'sample_id':'sample-b','marker':'Open circle','salt_label':'0.5 M'}],
 'Both samples lie near the same straight line. This empirical correlation is used to infer L(t) and then diffusion coefficients.',
 ['Observed CdS layer width L / um (0–12)','Absorbance at 450 nm (0–0.20)'],['Direct L below 4 um is imprecise.','No printed numerical slope/intercept.','Note 27 excludes the very earliest tiny-crystal regime from interpreting 450 nm as excitonic absorption.'])

equations = [
 {'id':'equation-1','number':'1','expression':'Δφ = φ_i − φ_o = −(RT/F) ln(B_i/B_o) = −(RT/F) ln(A_o/A_i)','kind':'Donnan equilibrium relation','evidence':[ev(7,'Equation 1')],'references':[29,30]},
 {'id':'equation-2','number':'2','expression':'B_i = A_i + X; B_o = A_o ≡ C','kind':'Electroneutrality and outside-solution concentration definitions','evidence':[ev(7,'Equation 2')],'references':[]},
 {'id':'equation-3','number':'3','expression':'Δφ = −(RT/F) ln[X/(2C) + sqrt(1 + (X/(2C))^2)]','kind':'Fixed-charge Donnan potential model','evidence':[ev(7,'Equation 3')],'references':[30,32]},
 {'id':'diffusion-length-relation','number':None,'expression':'Δ = sqrt(2Dt); subsequently L = sqrt(2Dt)','kind':'Unnumbered diffusion-length relation, used with optical layer-width proxy','evidence':[ev(5,'Text following Figure 8 slope discussion'),ev(6,'Paragraph below Figures 8–9')],'references':[]},
]
model = {
 'variables':{'φ':'Electric potential','B':'Counterion (cation) concentration','A':'Co-ion (anion) concentration','i':'Polymer phase','o':'Water phase','X':'Fixed-charge concentration in wet polymer','C':'Outside 1:1 electrolyte concentration','R':'Gas constant','T':'Temperature; numerical value not specified','F':'Faraday constant','D':'Hydrosulfide diffusion coefficient in host polymer','Δ':'Diffusion length','L':'Observed CdS dispersion-layer width, used as a diffusion-length proxy'},
 'assumptions':['Equilibrium partitioning of a 1:1 electrolyte in a fixed-charge cation-exchange host.','Quasi-linear diffusion-length scaling is applied to a reactive, radially nonuniform bead.','Absorbance-to-L mapping is used only over the discussed optical/time regime.','Fixed charge X changes with swelling; the one-third swelling example is hypothetical.'],
 'author_interpretations':[
 {'id':'intuition-surface-nucleation','text':'HS− is consumed while entering the bead. High local surface supersaturation produces many small nuclei; lower interior HS− favors fewer nuclei and more growth. Surface ligation and local Cd2+ depletion may restrict growth.','evidence':[ev(4,'Discussion below Figure 4'),ev(5,'Top-left continuation')],'references':[14,26]},
 {'id':'intuition-ring','text':'A refractive-index and scattering contrast associated with the nonuniform, partly flocculated CdS distribution makes its inner boundary optically visible.','evidence':[ev(3,'Figure 6 discussion')],'references':[24]},
 {'id':'intuition-salt-screening','text':'Added NaCl reduces the magnitude of a negative Donnan barrier, allowing deeper HS− entry. Faster entry favors more nuclei, smaller CdS crystals, and earlier depletion near growing particles.','evidence':[ev(6,'Model introduction'),ev(7,'Donnan analysis')],'references':[18,29,30,31,32,33]},
 {'id':'intuition-swelling-alternative','text':'The authors reject suppressed swelling as the main explanation because smaller pores would normally slow diffusion, whereas their optical-derived HS− diffusion increases with NaCl.','evidence':[ev(6,'Donnan analysis introduction')],'references':[28],'limitation':'No direct pore-size or swelling-ratio measurement is supplied.'},
 {'id':'intuition-matrix-specific','text':'Salt reduces the severity of flocculation in this confined matrix compared with the no-salt preparation, despite the contrasting salt-induced aggregation expected in homogeneous aqueous colloids.','evidence':[ev(1,'Introduction'),ev(3,'Figure 7 discussion')],'references':[17],'limitation':'The homogeneous-solution contrast is cited background, not a separately measured control here.'},
 {'id':'intuition-design-context','text':'The authors propose electrolyte concentration as an additional control of CdS size and penetration alongside injection method and host bead size discussed in their earlier work.','evidence':[ev(7,'Conclusion')],'references':[14],'limitation':'No device, nonlinear optical, photocatalytic, or electrical performance is measured in this article.'},
 ],
 'limitations':['No measured potential is reported; −390 and −10 mV are author calculations.','For NaCl-labelled zero, Eq. 3 still requires finite total external electrolyte C; the precise background-electrolyte choice is not supplied. Do not substitute C = 0 and claim a reproduced finite result.','The −26 meV unit is inconsistent with the surrounding potential units and remains as printed.','Note 33 invokes a positively charged polymer, whereas the main system is described as a cation-exchange resin. Preserve this textual sign-context mismatch.','Note 33 says exact theoretical diffusion values could not be estimated because Q0 and t0 were not precisely available. D0 is the noncharged-polymer diffusion coefficient, Q0 the distribution coefficient, and t0 the transport number.','Reference-based model context does not establish exact polymer molecular coordinates, a unit cell, or independently validated structure targets.'],
}

contexts = [
 {'id':'context-concentrated-sulfide','text':'Earlier work cited as reference 14 used approximately 10^-2 M aqueous Na2S and found CdS more homogeneously throughout the bead. The present source uses this to argue against host/Cd-loading inhomogeneity as the primary reason for its gradient.','evidence':[ev(4,'Bottom discussion')],'references':[14],'disposition':'Cited prior experiment; not a complete new recipe, direct control batch, or measured result of the present study.'},
 {'id':'context-hs-speciation','text':'Source note 15 states that the aqueous Na2S solution contains Na+, HS−, and OH− under these conditions.','evidence':[ev(1,'Note 15')],'references':[15],'disposition':'Source speciation statement; not a measured pH or speciation fraction.'},
 {'id':'context-no-specific-ion-effect','text':'Source note 25 reports qualitatively similar visible absorption and L for 0.5 M LiCl, KCl, and tetramethylammonium chloride compared with 0.5 M NaCl.','evidence':[ev(4,'Note 25')],'references':[25],'disposition':'Supporting observation with missing method amounts and numerical outcomes, not three fully specified recipes.'},
]

conflicts = [
 {'id':'salt-concentration','text':'The recipe explicitly pretreats with 10 mL of 0.5 M NaCl and then adds 100 mL aqueous sulfide, while figures/model retain a 0.5 M label. The final reaction-mixture concentration is not clearly reconciled.','evidence':[ev(2,'Preparation of sample b'),ev(7,'Model calculation')],'resolution':'Preserve stock/preload concentration and source cohort label; do not silently calculate or impose a final 0.5 M concentration.'},
 {'id':'histogram-sd-unit','text':'Figure 5a gives log-normal SD 0.4 without unit or parameter definition.','evidence':[ev(5,'Figure 5a caption')],'resolution':'Store value with unit null and raw wording; avoid converting it into diameter error bars.'},
 {'id':'potential-energy-unit','text':'The hypothetical swelling calculation prints −26 meV although surrounding Δφ values use mV.','evidence':[ev(7,'Top-right model paragraph')],'resolution':'Keep original unit and mark the dimension conflict.'},
 {'id':'zero-salt-model-C','text':'A finite −390 mV is reported for zero added NaCl, but the outside concentration C used for background ions is not explicitly given.','evidence':[ev(7,'Equations 2–3 and model values')],'resolution':'Do not claim a numerically reproduced model without this input.'},
 {'id':'note33-charge-sign','text':'Note 33 refers to anions in a positively charged polymer; main model describes a cation-exchange resin.','evidence':[ev(7,'Main Donnan model and note 33')],'resolution':'Keep this as source-context ambiguity, not corrected physical proof.'},
 {'id':'rate-versus-extent','text':'The abstract describes a formation rate proportional to sqrt(time), but Figure 8 and body fit absorbance itself against sqrt(time).','evidence':[ev(1,'Abstract'),ev(5,'Figure 8 discussion'),ev(6,'Figure 8')],'resolution':'Represent the observed ordinate as absorbance; do not turn its slope into dA/dt.'},
 {'id':'figure-markers','text':'Figure 2 uses filled circles for salt and open circles for no salt; Figures 8–9 use the reverse.','evidence':[ev(3,'Figure 2'),ev(6,'Figures 8–9')],'resolution':'Bind marker identity separately for each figure.'},
 {'id':'figure-panel-vs-sample','text':'Figure 1 panels a/b mean 30 min/48 h, whereas the preparation sample labels a/b mean no salt/salt.','evidence':[ev(2,'Figure 1 and caption')],'resolution':'Keep both independent dimensions of identity.'},
 {'id':'size-method-region','text':'XRD means, TEM fitted regional means, constituent-crystal ranges, and aggregate descriptions concern different methods/scopes.','evidence':[ev(3,'XRD and TEM paragraphs'),ev(5,'Figure 5')],'resolution':'No single universal size target and no invented exact specimen joins.'},
 {'id':'layer-size-host','text':'100–110 um is host diameter; micrometer depths/L describe CdS location in that host; nanometer sizes describe CdS constituent crystals.','evidence':[ev(2,'Measurements'),ev(3,'Dispersion Textures'),ev(5,'Figures 5–6')],'resolution':'Use separate typed properties, not one size field.'},
 {'id':'reaction-time-vs-plateau','text':'The optical plateau within 2 h for b is not the end of the preparative 2 h stir plus 2 day standing sequence.','evidence':[ev(2,'Preparation'),ev(3,'Figure 2 discussion')],'resolution':'Store protocol durations separately from the observed optical-progress interpretation.'},
 {'id':'diffusion-measurement-model','text':'The HS− coefficients use an optical L proxy and diffusion scaling; Na+ diffusion is a cited resin-context value associated with Chelex 100, and Donnan potential values are model calculations.','evidence':[ev(2,'Sample b pretreatment'),ev(6,'Diffusion coefficients'),ev(7,'Donnan calculations')],'resolution':'Keep separate species, methods, and evidence classes.'},
 {'id':'no-absolute-optical-yield','text':'Absorbance trends and similar early spectral shapes support qualitative formation/size interpretations, not absolute CdS yields or exact spectral peak targets.','evidence':[ev(2,'Results'),ev(5,'Early-time discussion'),ev(6,'Note 27')],'resolution':'No curve digitization, mass-yield inference, band-gap conversion, or universal 450 nm calibration.'},
]

manifest = json.loads((BASE/'source-render-manifest.json').read_text(encoding='utf-8'))
actual_sha = sha(manifest['source'])
assert actual_sha == manifest['sha256']
payload = {
 'schema_version':'private-characterization-extraction/1.0',
 'generated_at':datetime.now(timezone.utc).isoformat(),
 'source':{'source_id':SID,'doi':'10.1021/la970480g','title':'Electrolyte Effects on CdS Nanocrystal Formation in Chelate Polymer Particles: Optical and Distribution Properties','authors':['Hiroshi Yao','Yukako Takada','Noboru Kitamura'],'journal':'Langmuir','year':1998,'volume':14,'pages':'595–601','path':manifest['source'],'sha256':actual_sha,'review_scope':'All seven supplied main-article pages read as text and visually; SI identity/content not verified by this bounded characterization task.'},
 'review_status':{'source_extraction':'private completed draft','canonical_integration':'not performed','reader_render_audit':'not performed','publication':'not performed','eligible_training':False},
 'page_review':[{'pdf_page':n,'printed_page':594+n,'text_read':True,'visually_reviewed':True,'text_sha256':sha(BASE/f'page-{n}.txt'),'render_sha256':sha(BASE/f'page-{n}.png')} for n in range(1,8)],
 'sample_scope':{'material':'CdS nanocrystals embedded in Chelex 100 polymer particles; not isolated CdS powder','source_cohorts':{'sample-a':'No NaCl addition','sample-b':'NaCl-pretreated; source labels 0.5 M'},'regional_product_ids':['a-surface','a-depth4um','a-depth8um','b-surface','b-depth9um','b-depth15um'],'link_policy':'These are source-cohort and spatial-region links only. No exact bead, aliquot, preparation batch, or cross-instrument specimen identity is supplied. The 30 min and 48 h spectra and time courses must remain distinct time contexts. Model/cited rows are not measured product properties.'},
 'measurement_methods':methods,'measurement_rows':rows,'figures':figures,
 'tables':[],'table_disposition':'No table appears in the seven supplied main pages; Figure 5 contains histogram plots, not a tabulated dataset.',
 'equations':equations,'model_context':model,'supporting_contexts':contexts,'conflicts_and_limitations':conflicts,
 'not_reported':['Photoluminescence spectra or quantum yield','Raman spectra','SAED pattern','HRTEM lattice-spacing or indexing result','Original XRD pattern graphic or raw XRD data','Refined lattice parameters, atomic coordinates, unit cell or CIF','Exact optical absorption onset/peak energies','Raw spectral/histogram arrays','Exact sample-specific crystal count','Measured Donnan potential','Measured swelling ratio or pore-size distribution','Device, electrical, photocatalytic, or nonlinear-optical performance'],
 'upstream_reference_policy':'Referenced methods and models remain citation-only context; no upstream paper has been read as part of this bounded extraction. Source notes 15, 25, 27, and 33 are present-source text, with their scopes preserved.',
 'counts':{'pages':7,'figures':len(figures),'tables':0,'numbered_equations':3,'unnumbered_relation_contexts':1,'measurement_rows':len(rows),'methods':len(methods),'conflicts_and_limitations':len(conflicts)},
}

checks = []
def check(name, condition):
    checks.append({'name':name,'passed':bool(condition)})
    assert condition, name
check('source hash matches rendered manifest',actual_sha == manifest['sha256'])
check('all seven text and visual page reviews',len(payload['page_review']) == 7)
check('all nine original figures', [x['id'] for x in figures] == [f'figure-{n}' for n in range(1,10)])
check('three numbered and one unnumbered relation context',len(equations)==4 and sum(x['number'] is not None for x in equations)==3)
check('measurement IDs unique',len({x['id'] for x in rows})==len(rows))
check('all rows have bounded page locators',all(x['evidence'] and all(1<=e['pdf_page']<=7 for e in x['evidence']) for x in rows))
check('all training gates disabled',all(not x['eligible_training'] for x in rows+figures))
byid={x['id']:x for x in rows}
check('lognormal spread has no invented unit',byid['char-a-surface-hist-sd']['quantity']['unit'] is None)
check('potential unit conflict preserved',byid['char-donnan-swelling']['quantity']['unit']=='meV')
check('effective diffusion remains calculated',all(byid[f'char-{s}-effective-HS-diffusion']['basis']=='author_calculated' for s in ['sample-a','sample-b']))
check('no phantom XRD figure',len(figures)==9 and not any('X-ray' in f['title'] for f in figures))
check('figure 2 marker reversal explicit','filled circles' in figures[1]['panels'][0]['identity'] and figures[7]['panels'][0]['marker']=='Filled circle')
check('all numeric ranges ordered',all(x['quantity'].get('lower_bound',0)<=x['quantity'].get('upper_bound',float('inf')) for x in rows if 'quantity' in x))
check('sample-a and sample-b XRD means retained',[byid[f'char-{s}-xrd-mean']['quantity']['value'] for s in ['sample-a','sample-b']]==[3.8,3.1])
check('source model values not product measurement scope',all(byid[f'char-donnan-{s}']['scope_type']=='model_context' for s in ['no-salt','salt','swelling']))

(BASE/'characterization-draft.json').write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
lines=['# Yao et al. 1998 — characterization extraction','','Private source-scoped draft. All seven main pages were read and visually reviewed. SI, canonical integration, reader rendering, and publication are not promoted by this report.','',f"Source DOI: {payload['source']['doi']}  ",f'Source SHA256: `{actual_sha}`','',f"Inventory: {len(rows)} typed measurement/context rows; 9 figures; no tables; 3 numbered equations plus the unnumbered diffusion-length relation.",'','## Evidence and sample scope','','CdS remains embedded in Chelex 100. Sample a is the no-salt cohort; sample b is NaCl-pretreated. Surface and depth regions are not independent batches. Cross-instrument specimen identity is not established.','', '## Main quantitative evidence','', '| Row | Sample/context | Property | Value | Basis / locator |','|---|---|---|---|---|']
for r in rows:
    value=json.dumps(r.get('quantity',r.get('fact')),ensure_ascii=False)
    value=value.replace('|','\\|')
    lines.append(f"| {r['id']} | {r['sample_id']} | {r['property']} | {value} | {r['basis']}; PDF p. {r['evidence'][0]['pdf_page']}, {r['evidence'][0]['locator']} |")
lines += ['', '## Methods','']
for m in methods:
    lines += [f"### {m['name']}",'', '; '.join(m['apparatus'])+'.', '',m.get('preparation',m.get('observable','')),m.get('settings',''),'','Unreported: '+ '; '.join(m['unreported'])+'.','']
lines += ['## Figure coverage','']
for f in figures:
    lines += [f"- **Figure {f['id'].split('-')[1]}**, PDF p. {f['pdf_page']}: {f['title']}. {f['quantitative_context']}"]
lines += ['','## Equations and models','']
for e in equations: lines += [f"- {e['id']}: `{e['expression']}`. {e['kind']}."]
lines += ['']+['- '+x for x in model['limitations']]+['','## Conflicts and safeguards','']
for c in conflicts: lines += [f"- **{c['id']}**: {c['text']} {c['resolution']}"]
lines += ['', '## Missing source data','']+['- '+x for x in payload['not_reported']]+['','## Integration','', 'Use the JSON measurement rows and evidence locators. Keep `model_context` and `cited_context` rows separate from product measurements. The full figure inventory carries panel-specific labels and scale bars. No figure values have been digitized. A source-audit crosswalk can be added after independent unit IDs are available.','']
(BASE/'characterization-draft.md').write_text('\n'.join(lines),encoding='utf-8')
validation={'status':'passed','checks':checks,'counts':payload['counts'],'artifact_sha256':{'characterization-draft.json':sha(BASE/'characterization-draft.json'),'characterization-draft.md':sha(BASE/'characterization-draft.md')},'scope':'Private extraction consistency only; no canonical, UI or publication verification.'}
(BASE/'characterization-validation.json').write_text(json.dumps(validation,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'status':'passed','checks':len(checks),'counts':payload['counts'],'sha256':validation['artifact_sha256']['characterization-draft.json']}))
