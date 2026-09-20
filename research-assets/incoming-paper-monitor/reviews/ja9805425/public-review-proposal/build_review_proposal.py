"""Private source-reader proposal; only the owning root may integrate it."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import json, hashlib

O=Path(__file__).resolve().parent
B=O.parent
SID='peng1998'; P='peng-1998-'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read(B/'reader-assets/crop-manifest.json')
sources=read(B/'source-render-manifest.json')
sections=[{'id':k,'title':v,'items':[]} for k,v in [('precursors','Precursors'),('protocol','Synthesis protocol'),('structures','Final structures'),('properties','Properties'),('intuition','Chemical intuition'),('sources','Sources and limitations')]]
items={}
def ev(role,page,loc):
 e={'source_id':SID,'document_role':role,'pdf_page':page,'printed_page':5342+page if role=='main' else (page-1 if page>1 else None),'locator':f'{"Main" if role=="main" else "SI"} PDF p. {page}, '+loc}
 return e
N21=('main',1,'printed p. 5343, Note 21')
N22=('main',1,'printed p. 5343, Note 22')
M1=('main',1,'printed p. 5343, growth and optical-analysis discussion')
M2=('main',2,'printed p. 5344, growth model and concentration comparisons')
SCOPE={
 'source_cohort':'Paper-level method, aliquot series or figure cohort. Curator labels are not author batch IDs; distinct TEM, calibration and optical series are not silently joined.',
 'method_context':'Preparation or acquisition setting. This context does not establish an independently measured specimen or material property.',
 'calibration_context':'Source calibration row relating optical peaks to TEM size; not a newly synthesized batch or a time-point assignment in this paper.',
 'model_context':'Author theoretical interpretation or model relation, separate from measured specimen data.',
 'cited_context':'Earlier research cited by the inspected source. The cited work was not independently reviewed for this proposal and does not fill unreported recipe fields.',
 'source_metadata':'Source identity, reference or review limitation; no additional experiment is introduced.',
 'author_outlook':'Authors’ proposed future control strategy; not an implemented apparatus or experimental demonstration.',
 'curator_interpretation':'Explicit curator interpretation or data-handling decision, separate from the reported experiment.'}
def item(sec,key,title,text,evidence,records=(),samples=(),kind='reported_source_fact',scope='source_cohort',notes=(),facts=()):
 assert key not in items
 ee=[ev(*e) for e in evidence]
 d={'id':key,'title':title,'text':text,'claim_type':kind,
 'sample_scope':{'formulations':list(samples),'physical_batch_id':None,'scope_kind':scope,'state':title,'link_limit':SCOPE[scope]},
 'evidence':ee,'source_locators':[e['locator'] for e in ee],
 'canonical_links':[{'record_id':P+r,'json_pointer':'','relation':SCOPE[scope]} for r in records],
 'notes':list(notes),'facts':list(facts),'training_eligible':False}
 items[key]=d
 next(s for s in sections if s['id']==sec)['items'].append(d)
 return d
def fact(key,label,value,unit=None,basis='reported',qualifier='',approximate=False,evidence=()):
 return {'id':key,'label':label,'value':value,'unit':unit,'basis':basis,'approximate':approximate,'qualifier':qualifier,'evidence':[ev(*e) for e in evidence]}

# Complete precursor and stock distinctions.
item('precursors','cdse-medium','CdSe growth medium: trioctylphosphine oxide',
 'The CdSe preparation starts with 4 g of trioctylphosphine oxide (TOPO), heated under flowing argon. This oxide is distinct from the tributylphosphine used in the injection stock and the trioctylphosphine used in the InAs method. TOPO grade, purity, supplier, pre-degassing treatment and vessel geometry are not specified.',[N21],['cdse-focusing'])
item('precursors','cdse-stock','CdSe injection stock: selenium, dimethylcadmium and tributylphosphine',
 'Note 21 describes the cold stock as Se : Cd(CH₃)₂ : tributylphosphine = 2 : 5 : 100 by mass. The first injection uses 2.4 mL and the later feed uses 0.8 mL of that stock. The source supplies relative masses, not the total stock mass or a measured molarity. It does not give the sequence or temperature of stock dissolution or independently identify the solution’s selenium species.',[N21],['cdse-focusing'],notes=['Retain Se as the reported stock constituent; do not silently replace it with TOPSe, TBPSe or bis(trimethylsilyl)selenium.','Do not convert the mass ratio and injected volume into absolute precursor moles without unreported density or stock mass.'])
item('precursors','cdse-workup-solvents','CdSe analytical solvents',
 'Methanol is the precipitant for sampled CdSe aliquots: 0.2 mL of reaction mixture is added to 2 mL of methanol. Purified particles are redissolved in toluene for UV–visible absorption and PL. No solvent grades, final dispersion volumes or complete washing sequence are specified.',[N21],['cdse-aliquot-analysis'])
item('precursors','inas-indium-stock','Indium chloride in distilled trioctylphosphine',
 'A concentrated InCl₃·TOP solution is prepared using 0.33 g of InCl₃ per mL of distilled trioctylphosphine, heated to 260 °C under argon. The reported denominator is the TOP volume, not a measured final solution volume. The dot notation is retained as the source’s solution/adduct label; it does not supply a crystallographically established coordination structure.',[N22],['incl3-top-stock','inas-focusing'],scope='method_context',notes=['No hydrate, reagent purity, supplier, preparation time or total stock scale is specified.'])
item('precursors','inas-cold-stock','InAs cold injection stock',
 'The InAs injection solution is reported as TMS₃As : InCl₃ : TOP = 1 : 1.1 : 2.8 by mass. TMS₃As denotes tris(trimethylsilyl)arsine in this context. The initial injected volume is 1 mL. The actual stock temperature, complete mixing sequence and absolute molar concentrations are not supplied.',[N22],['inas-focusing'],notes=['The concentrated InCl₃·TOP preparation and the final ternary injection ratio are separately stated. The exact mass or volume of the concentrated solution used to assemble the final stock is not given.'])
item('precursors','inas-bath-and-solvent','InAs growth medium and optical solvent',
 'The InAs reactor is charged with 2 g of TOP before the first injection. Aliquots are subsequently diluted in toluene for UV–visible absorption and PL. The article does not report an InAs precipitation or powder-isolation procedure, and the CdSe methanol workup is not transferred to this route.',[N22],['inas-focusing','inas-aliquot-analysis'])
item('precursors','stock-storage','Cooling and drybox storage of InCl₃·TOP',
 'After its 260 °C preparation, the InCl₃·TOP solution is cooled and transferred to a drybox for storage. Neither the storage temperature nor storage duration is stated. This explicit storage instruction belongs to the indium solution; it is not evidence for −35 °C storage of the final InAs injection stock.',[N22],['incl3-top-stock'],scope='method_context')

# Actual synthesis and separate analytical procedures.
item('protocol','cdse-heat','CdSe: heat TOPO under argon',
 'Heat 4 g of TOPO to 360 °C with argon flowing. Note 21 describes rapid stirring at injection but does not specify an rpm, argon flow, pressure, heating rate, dwell time or thermometer placement.',[N21],['cdse-focusing'],scope='method_context')
item('protocol','cdse-injection','CdSe: rapid first injection',
 'Inject 2.4 mL of the cold Se / Cd(CH₃)₂ / tributylphosphine stock into the rapidly stirred TOPO in less than 0.1 s. The source reports that the injection lowers the temperature from 360 to 300 °C. These are the reactor conditions around injection, not two interchangeable temperatures or a stated external-bath program.',[N21],['cdse-focusing'],scope='method_context')
item('protocol','cdse-growth','CdSe: growth and time-series sampling',
 'Growth is followed over time after the first injection, with 300 °C reported as the post-injection temperature. At selected times, withdraw 0.2 mL aliquots. The plotted CdSe spectra are labeled 0.2, 1.0, 12, 35, 55, 190, 210 and 240 min; the figure is a sampled trajectory, not a continuous kinetic calibration.',[N21,('main',2,'printed p. 5344, Figure 1')],['cdse-focusing','cdse-aliquot-analysis','cdse-kinetics'])
item('protocol','cdse-precipitate','CdSe aliquots: methanol precipitation and purification',
 'Precipitate each 0.2 mL reaction aliquot in 2 mL methanol. The authors determine mass and particle yield after removing excess TOPO, byproducts and solvent. Separation equipment, centrifugation settings, wash count, drying conditions and yield-calculation details are not supplied.',[N21],['cdse-aliquot-analysis'],scope='method_context')
item('protocol','cdse-optical-preparation','CdSe aliquots: optical measurement preparation',
 'Redissolve the purified CdSe nanocrystals in toluene for absorption and PL. For PL, the optical density is kept at 0.09 ± 0.02. The wavelength at which that optical density was set, excitation wavelength, path length, instrument and final dispersion concentration are not given.',[N21],['cdse-aliquot-analysis','pl-size-analysis'],scope='method_context',facts=[fact('cdse-pl-od','Optical density for PL','0.09 ± 0.02',None,'method_setting','The source gives no OD reference wavelength.',evidence=[N21])])
item('protocol','cdse-refeed','CdSe: second precursor feed at 190 min',
 'At 190 min after the first injection, slowly inject 0.8 mL of stock into the reaction mixture. No numerical addition rate or feed duration is reported. This additional feed belongs to the same growth sequence; it is not a separate batch or another rapid nucleation injection.',[N21],['cdse-focusing','cdse-kinetics'],scope='method_context')
item('protocol','cdse-reduced-injection','CdSe comparison: approximately 15% smaller first injection',
 'With the first injected volume reduced by about 15% and other conditions stated to be unchanged, the focusing time falls from 22 to 11 min and the focused diameter from 3.3 to 2.7 nm. The reduced volume itself is not printed as an absolute value. This is a source-described comparison, not an independently complete recipe or a continuous volume–size rule.',[M2],['cdse-kinetics'])
item('protocol','cdse-cd-rich-comparison','CdSe comparison: Cd:Se ratio of 1.9:1',
 'The authors state that the main reaction uses a Cd:Se molar ratio of approximately 1.4:1. At 1.9:1, focused nanocrystals can remain at the growth temperature for hours before defocusing. The duration, full stock formulation and separately measured product size are not quantified for this comparison.',[M2],['cdse-kinetics'])
item('protocol','cdse-cd-poor-comparison','CdSe comparison: Cd:Se ratio of 1.1:1',
 'At Cd:Se = 1.1:1, defocusing is described as rapid. Nearly doubling the concentrations of both Cd and Se is reported as necessary to recover a narrow distribution in that comparison. Absolute concentrations, an exact multiplier, focusing time and achieved width are not given.',[M2],['cdse-kinetics'])
item('protocol','inas-stock-preparation','InAs: prepare and store the indium solution',
 'Heat InCl₃ in distilled TOP at 0.33 g per mL TOP and 260 °C under argon; cool, then store in a drybox. The source does not quantify the heating interval, cooling endpoint, storage conditions or subsequent stock-assembly amounts.',[N22],['incl3-top-stock'],scope='method_context')
item('protocol','inas-first-injection','InAs: rapid injection into TOP',
 'Heat 2 g TOP to 300 °C, then inject 1 mL of cold ternary stock in less than 0.1 s. The injection initially lowers the temperature to 250 °C. The source’s explicit argon condition accompanies the indium-stock preparation; a separate reactor gas-flow value is not supplied.',[N22],['inas-focusing'],scope='method_context')
item('protocol','inas-growth-temperature','InAs: growth at 260 °C',
 'After the initial drop to 250 °C, continue growth at 260 °C. The ramp duration and reheating rate are not specified. Keeping 300 °C before injection, 250 °C immediately after injection and 260 °C during growth as separate stages preserves the reported sequence.',[N22],['inas-focusing'],scope='method_context')
item('protocol','inas-sampling','InAs: aliquot dilution and optical measurement',
 'Remove aliquots at selected times and dilute them in toluene for UV–visible and PL spectra. Aliquot volume, dilution factor, cuvette path length, excitation wavelength and instrument are unreported. The supplementary PL panel is explicitly at room temperature.',[N22,('si',3,'supplemental p. 2, InAs optical spectra')],['inas-aliquot-analysis','pl-size-analysis'],scope='method_context')
item('protocol','inas-feeds','InAs: additional injections at 23 and 158 min',
 'The stated additional injections are 0.5 mL at 23 min and 0.8 mL at 158 min. Their numerical rates, durations and temperatures are not separately reported. Note 22 introduces them after the cold-stock recipe but does not independently repeat their composition; the source wording is retained without inventing additional feed formulations.',[N22],['inas-focusing','inas-kinetics'],scope='method_context')

# Structural evidence and explicit sample boundaries.
item('structures','cdse-tem','CdSe morphology and diameter in Figure 3',
 'The original TEM image shows faceted CdSe nanocrystals and carries a 25 nm scale bar. Its caption reports an 8.5 nm diameter and preparation by distribution focusing. No injection history, reaction time, batch identifier, numerical size distribution or TEM acquisition conditions are assigned to this image.',[('main',2,'printed p. 5344, Figure 3 and caption'),M1],['cdse-tem'],samples=['cdse-tem-figure3'],notes=['The 8.5 nm TEM sample is not identified as the endpoint of the smaller-diameter Figure 1/2 kinetics experiment.'])
item('structures','structural-scope','Atomic structure and diffraction evidence',
 'This main article and matched SI provide a CdSe TEM morphology image and TEM-linked optical calibration tables. They do not provide a sample-specific refined crystal structure, unit cell, atomic coordinates, XRD pattern, SAED image or Raman spectrum. Any separately sourced atomic model must remain labeled as a reference model and cannot establish these particles’ phase or surface structure.',[('main',2,'printed p. 5344, Figure 3'),('si',2,'supplemental p. 1, CdSe calibration'),('si',4,'supplemental p. 3, InAs calibration')],['cdse-tem'],kind='reviewed_source_limitation',scope='curator_interpretation')
item('structures','tem-calibration-scope','TEM calibration is separate from growth trajectories',
 'The supplementary tables relate optical peak positions to TEM sizes for CdSe and InAs. The main text attributes prior calibration to references 5, 7 and 9. Table rows are calibration reference points; no row is assigned an injection time, reaction batch, core/shell interface or independently reviewed synthesis in the tables.',[M1,('si',2,'supplemental p. 1, CdSe calibration'),('si',4,'supplemental p. 3, InAs calibration')],['cdse-calibration','inas-calibration','pl-size-analysis'],scope='calibration_context')

# Optical observations and analysis limitations.
item('properties','cdse-spectra','CdSe absorption and PL time series',
 'Figure 1 pairs room-temperature normalized PL with absorption spectra. The horizontal axes are photon energy in eV; absorption is in arbitrary units and PL intensity is normalized. Spectra are labeled 0.2, 1.0, 12, 35, 55, 190, 210 and 240 min. The secondary feed occurs at 190 min. No numerical peak list, absolute quantum yield or digitally sampled spectrum accompanies these curves.',[('main',2,'printed p. 5344, Figure 1')],['cdse-kinetics','cdse-focusing'],samples=['cdse-kinetics-series'])
item('properties','cdse-focusing-results','CdSe: first focusing interval',
 'During the first 22 min, the reported average diameter increases from 2.1 to 3.3 nm and relative standard deviation narrows from 20% to 7.7%. These diameters and widths come from the PL-based analysis, rather than individual TEM images at every time point.',[M1,('main',2,'printed p. 5344, Figure 2 left')],['cdse-kinetics'],samples=['cdse-kinetics-series'])
item('properties','cdse-defocusing-results','CdSe: depletion and defocusing',
 'After the initial focused state and before the 190 min feed, growth slows as the mean diameter reaches 3.9 nm and the relative width broadens to 10.6%. The article describes this interval as defocusing. It does not report that the subsequent 8.5 nm TEM specimen belongs to this trajectory.',[M1],['cdse-kinetics'],samples=['cdse-kinetics-series'])
item('properties','cdse-refocusing-results','CdSe: refocusing after additional precursor',
 'The second precursor feed raises the growth rate and narrows the reported relative standard deviation to 8.7%. The prose does not pair that 8.7% value with an exact post-feed time or mean diameter. Figure 2 retains the original plotted trajectory without an invented interpolated endpoint.',[M1,('main',2,'printed p. 5344, Figure 2 left')],['cdse-kinetics'],samples=['cdse-kinetics-series'])
item('properties','particle-number','Particle number during focusing and defocusing',
 'Particle-yield measurements are reported to show approximately constant particle number during focusing and refocusing, with a decrease during defocusing. The text does not supply numerical counts, yields, concentration calibrations, uncertainty or a tabulated particle-number trace.',[M1,N21],['cdse-kinetics'],samples=['cdse-kinetics-series'])
item('properties','monomer-concentration','Monomer concentration inferred from particle yield',
 'The authors determine monomer concentration through particle-yield analysis. They report a pronounced decline during focusing and refocusing and approximately constant concentration during defocusing. No independent in situ chemical assay or numerical monomer-concentration series is supplied.',[M1,N21],['cdse-kinetics'],samples=['cdse-kinetics-series'],kind='reported_derived_observation')
item('properties','qualitative-yield','Qualitative particle yield',
 'The nanocrystal yield is described as high, and the resulting particles as faceted. No numerical percentage is supplied for this claim. Figure 3 specifically depicts CdSe; the general statement does not create an independently imaged InAs specimen.',[M1,('main',2,'printed p. 5344, Figure 3')],['cdse-kinetics','inas-kinetics','cdse-tem'],notes=['The broad yield statement is retained as qualitative source context.'])
item('properties','inas-kinetics','InAs growth and distribution kinetics',
 'Figure 2 right presents PL-derived mean diameter in nm and relative standard deviation in percent as functions of time in minutes. The authors report focusing and refocusing behavior analogous to CdSe. The main text does not give a numerical list of InAs means or widths; exact values are not reverse-engineered from the small plot for training.',[M1,('main',2,'printed p. 5344, Figure 2 right')],['inas-kinetics'],samples=['inas-kinetics-series'])
item('properties','inas-absorption-series','InAs supplementary absorption series',
 'The supplementary absorption panel labels traces t = 18, 28, 43, 158, 176 and 245. Its energy axis is in eV and absorption is in arbitrary units with vertical offsets. The SI does not print a time unit next to the t labels; minutes follow the linked main-article growth experiment. No numerical absorption peak positions are assigned to these traces in this panel.',[('si',3,'supplemental p. 2, left absorption panel'),N22,('main',2,'printed p. 5344, Figure 2 right')],['inas-kinetics','inas-aliquot-analysis'],samples=['inas-optical-series'])
item('properties','inas-pl-series','InAs supplementary PL series',
 'The room-temperature PL panel labels t = 23, 28, 80, 158 and 176. Its horizontal axis is energy in eV and intensity is in arbitrary units. The absorption and PL panels show different selected sampling times; neither missing time points nor one-to-one specimen identity are filled in from the neighboring panel.',[('si',3,'supplemental p. 2, right room-temperature PL panel')],['inas-kinetics','inas-aliquot-analysis'],samples=['inas-optical-series'])
item('properties','inas-reabsorption','InAs: use only the high-energy PL half',
 'The SI states that reabsorption affects the lower-energy half of the InAs PL spectrum around 1 eV. Only the higher-energy half is used to estimate the size distribution and standard deviation. A fit to the full asymmetric PL line would therefore differ from the source’s stated analysis.',[('si',3,'supplemental p. 2, note below spectra')],['pl-size-analysis','inas-kinetics'],scope='method_context')
item('properties','pl-size-assumptions','PL-to-size conversion assumptions',
 'PL spectra are converted to size distributions using a delta-function emission for each single size and equal emission efficiency for different sizes. The authors state that both assumptions make the reported distributions systematically broader than the true size distributions. These assumptions are retained with the results and do not justify interpreting the widths as direct TEM dispersities.',[M1],['pl-size-analysis','cdse-kinetics','inas-kinetics'],scope='method_context')
item('properties','distribution-moments','Reported distribution moments',
 'The paper reports the mean size, described as the first moment, and variance, described as the second moment. It does not determine the third moment or distribution asymmetry; the authors say a more accurate sizing method would be needed. Figure 2 expresses the plotted width as relative standard deviation in percent.',[M1,('main',2,'printed p. 5344, Figure 2')],['pl-size-analysis'],scope='method_context')

CDSE=[(484,2.47,2.1),(488,2.46,2.1),(516,2.34,2.4),(526,2.3,2.6),(534,2.27,2.7),(542,2.24,2.9),(550,2.21,3.1),(560,2.17,3.3),(566,2.16,3.4),(570,2.14,3.5),(576,2.09,3.6),(596,2.04,4.3),(600,2.03,4.4),(606,2.02,4.6),(608,2.01,4.7),(610,2,4.8)]
INAS=[(838,1.41,2.3),(861,1.38,2.4),(886,1.34,2.6),(905,1.31,2.8),(929,1.28,3),(954,1.24,3.2),(976,1.22,3.4),(1004,1.19,3.6),(1029,1.16,3.8),(1051,1.13,4),(1078,1.1,4.2),(1107,1.08,4.4),(1132,1.05,4.6),(1159,1.03,4.8),(1187,1.01,5),(1216,0.98,5.2),(1246,0.96,5.4),(1272,0.94,5.6),(1305,0.92,5.8),(1333,0.9,6)]
for material,data,page in [('CdSe',CDSE,2),('InAs',INAS,4)]:
 key=material.lower()
 item('properties',key+'-calibration-overview',material+' optical-peak / TEM-size calibration',
  f'The matched SI supplies {len(data)} calibration rows linking the UV–visible exciton peak wavelength, PL peak energy and TEM size of {material}. Each printed row is preserved separately with its original units. The table contains no synthesis times or sample identifiers and is not treated as {len(data)} new synthesis experiments.',[('si',page,f'supplemental p. {page-1}, {material} table')],[key+'-calibration','pl-size-analysis'],scope='calibration_context')
 for n,(uv,pl,size) in enumerate(data,1):
  loc=('si',page,f'supplemental p. {page-1}, {material} calibration row {n}')
  item('properties',f'{key}-calibration-row{n:02}',f'{material} calibration {n:02}: {size:g} nm',
   f'The printed row pairs an absorption exciton peak at {uv:g} nm with a PL peak at {pl:g} eV and a TEM size of {size:g} nm.',[loc],[key+'-calibration'],samples=[f'{key}-calibration-row{n:02}'],scope='calibration_context',
   facts=[fact(f'{key}-cal-{n:02}-abs','Absorption exciton peak',uv,'nm','source_calibration',evidence=[loc]),fact(f'{key}-cal-{n:02}-pl','PL peak',pl,'eV','source_calibration',evidence=[loc]),fact(f'{key}-cal-{n:02}-size','TEM size',size,'nm','source_calibration',evidence=[loc])])

# Chemical interpretation, theory and explicit outlook.
item('intuition','historical-strategies','Earlier strategies for narrow size distributions',
 'The introduction cites molecular-precursor syntheses of II–VI CdS/CdSe and III–V InP/InAs (references 1–16). It contrasts extended nucleation and growth at 180–300 °C, followed by sorting, with rapid injection at 350 °C to separate nucleation and growth. These numbers summarize earlier references, not the specific 360 °C CdSe and 300 °C InAs reactor settings in Notes 21 and 22. The authors note that the latter strategy depends strongly on early kinetics and had not been achieved for III–V systems in that form.',[('main',1,'printed p. 5343, introductory synthesis strategies')],kind='source_cited_context',scope='cited_context')
item('intuition','growth-background','Diffusion and size-dependent surface energy',
 'The paper builds on Reiss’s treatment of diffusion-limited narrowing in micron-sized colloids and on size-dependent surface-energy effects described by the Gibbs–Thomson relation. References 17–20 supply the theoretical background. Those works are cited context, rather than newly verified experimental evidence in this contribution.',[('main',1,'printed p. 5343, Reiss and Gibbs–Thomson discussion')],['growth-model'],kind='source_cited_context',scope='cited_context')
item('intuition','nucleation-limits','Rapid nucleation and the start of growth analysis',
 'The authors describe nucleation as beginning rapidly after injection and continuing until temperature and monomer concentration fall below a threshold. They emphasize that nucleation kinetics are difficult to study, whereas the later growth stage is more accessible. No measured threshold concentration, critical temperature or complete nucleation-rate history is supplied.',[M1],['growth-model'],kind='author_interpretation',scope='model_context')
item('intuition','gibbs-thomson','Gibbs–Thomson solubility relation',
 'The source uses Sᵣ = Sᵦ exp(2σVₘ/rRT): Sᵣ and Sᵦ are nanocrystal and bulk solubilities, σ is specific surface energy, r is nanocrystal radius, Vₘ is molar volume, R is the gas constant and T is temperature. The relation connects curvature to equilibrium solubility; no numeric surface energy or fitted monomer solubility is reported.',[('main',1,'printed p. 5343, unnumbered Gibbs–Thomson equation and symbol definitions')],['growth-model'],kind='author_theoretical_model',scope='model_context')
item('intuition','growth-equation','Diffusion-controlled growth-rate relation',
 'For 2σVₘ/rRT ≪ 1, the source writes dr/dt = K(1/r + 1/δ)(1/r* − 1/r). K is proportional to the monomer diffusion constant and δ is the diffusion-layer thickness. At fixed monomer concentration, r* is the radius at which nanocrystal solubility equals the solution concentration, giving zero growth rate. The expression assumes diffusion-limited growth; it is not a fitted rate law with supplied parameter values.',[('main',1,'printed p. 5343, fixed-concentration diffusion assumption'),('main',2,'printed p. 5344, unnumbered growth-rate equation and definitions')],['growth-model'],kind='author_theoretical_model',scope='model_context')
item('intuition','model-figure4','Figure 4 is a model, not a measured size–rate curve',
 'Figure 4 plots the source growth relation for an infinite diffusion-layer thickness. The horizontal coordinate is r/r* and the vertical coordinate is growth rate in arbitrary units. Negative rates below the critical size indicate dissolution; positive rates describe growth. The source supplies no absolute rate calibration for converting the curve into a reactor-time prediction.',[('main',2,'printed p. 5344, Figure 4 and associated theory')],['growth-model'],kind='author_theoretical_model',scope='model_context')
item('intuition','why-focusing','Why a distribution can narrow during growth',
 'In the authors’ model, focusing occurs when all particles are slightly larger than the critical size. Smaller particles within that population then grow faster than the larger ones, narrowing the distribution. This statement is conditional on the growth regime and should not be generalized to every size or concentration.',[M2],['growth-model'],kind='author_interpretation',scope='model_context')
item('intuition','why-defocusing','Monomer depletion and Ostwald ripening',
 'As growth depletes monomer, the critical size increases. When it exceeds the population’s average size, smaller particles shrink and disappear while larger particles continue to grow. The authors call this broadening Ostwald ripening or defocusing, consistent with their reported decrease in particle number.',[M2,M1],['growth-model','cdse-kinetics'],kind='author_interpretation',scope='model_context')
item('intuition','why-refeeding','Why a later precursor feed can refocus the distribution',
 'Adding precursor at the growth temperature is interpreted to increase monomer availability and move the critical size downward. This can restore a focusing regime without requiring a wholly new nucleation event. The reported particle number remains approximately constant during refocusing; no independent nucleation-rate measurement proves a universal absence of secondary nucleation.',[M1,M2],['growth-model','cdse-kinetics','inas-kinetics'],kind='author_interpretation',scope='model_context')
item('intuition','concentration-control','Initial concentration changes focusing time and size',
 'The authors interpret the smaller initial CdSe injection as faster monomer depletion, explaining a shorter focusing interval and smaller focused diameter. Their Cd:Se comparisons also show that precursor stoichiometry changes the interval before defocusing. These discrete comparisons motivate concentration control but do not establish a quantitative continuous predictor.',[M2],['growth-model','cdse-kinetics'],kind='author_interpretation',scope='model_context')
item('intuition','generality-limits','Reported scope beyond CdSe and InAs',
 'The authors state that the effects also occur for CdS and InP and suggest relevance across II–VI and III–V semiconductors. This short article and its SI do not provide CdS or InP synthesis procedures, spectra or sample-level results, so the claim is retained as a scope statement rather than creating new synthesis records for those materials.',[M2],['growth-model'],kind='author_scope_statement',scope='model_context')
item('intuition','automation-outlook','Continuous concentration monitoring as an outlook',
 'Because monomer concentration and critical size evolve continuously, the authors propose monitoring and adjusting concentration to keep the mean particle size slightly above the critical size. They suggest this could improve reproducibility and uniformity at larger preparation scales. The paper does not demonstrate an automated feedback apparatus or provide a deployable control algorithm.',[('main',2,'printed p. 5344, concluding paragraph')],['growth-model'],kind='author_outlook',scope='author_outlook')

# Source identity and all reference / note dispositions.
item('sources','article-identity','Article identity and supplied documents',
 'Xiaogang Peng, J. Wickham and A. P. Alivisatos published this communication in Journal of the American Chemical Society 1998, 120(21), 5343–5344, DOI 10.1021/ja9805425. It was received February 18, 1998 and published online May 14, 1998. The supplied main PDF has two pages. The matched SI PDF has a publisher cover plus three scientific pages, agreeing with the main article’s three-page SI declaration.',[('main',1,'printed p. 5343, title, authors, received date and publication footer'),('main',2,'printed p. 5344, SI declaration'),('si',1,'publisher cover with matching DOI, volume and pages')],kind='reviewed_source_identity',scope='source_metadata')
item('sources','si-identity','Supporting Information identity',
 'The SI cover prints the exact DOI, journal, volume, issue and page range. Its three scientific pages carry Peng / supplemental-page headers and contain the CdSe calibration, InAs optical spectra and InAs calibration specifically described in the main paper. These links establish main–SI identity despite the four-page file including an administrative cover.',[('si',1,'publisher cover'),('si',2,'supplemental p. 1 header and CdSe table'),('si',3,'supplemental p. 2 header and InAs spectra'),('si',4,'supplemental p. 3 header and InAs table'),('main',2,'printed p. 5344, SI declaration')],kind='reviewed_source_identity',scope='source_metadata')
item('sources','si-cover-disposition','Publisher cover disposition',
 'The first SI PDF page contains bibliographic identity and publisher terms, with no synthesis method, material measurement or scientific figure. It is retained in the source audit as administrative metadata, not counted as an additional scientific page or experiment.',[('si',1,'publisher cover and terms')],kind='reviewed_source_disposition',scope='source_metadata')
item('sources','funding','Acknowledgment',
 'The authors acknowledge the U.S. Department of Energy, Office of Basic Energy Sciences, Division of Materials Sciences, under contract DE-AC03-76SF00098. This funding context does not add experimental data.',[('main',2,'printed p. 5344, acknowledgment')],scope='source_metadata')
item('sources','method-gaps','Unreported recipe and measurement details',
 'No total injection-stock mass, density, absolute molarity, complete stock-mixing sequence, final whole-batch isolation or termination, exact purification sequence, instrument model, excitation wavelength or individual batch identity is supplied. Precursor purities, pressure, numerical gas flow, stirring speed, injection hardware, cold-stock temperature and numerical slow-feed rate also remain unspecified. The indium solution’s drybox storage is stated, but its temperature and duration are not. Missing fields are not inherited from another paper.',[N21,N22,M1,('main',2,'printed p. 5344, Figures 1–3'),('si',3,'supplemental p. 2, optical spectra')],kind='reviewed_source_limitation',scope='curator_interpretation')
item('sources','printed-ratios','Printed stock ratios and interpretation limits',
 'Note 21’s 2:5:100 constituent mass ratio and the body’s approximate 1.4:1 Cd:Se molar ratio are retained in their own reported bases. The reader does not silently recompute or reconcile the author’s approximate molar statement, infer a stock density, or convert the InCl₃-per-TOP-volume preparation into a final-solution molarity.',[N21,N22,M2],kind='reviewed_source_limitation',scope='curator_interpretation')
item('sources','injection-arrows','Injection markers and written schedules',
 'Figure 2’s arrows indicate injections but do not visibly enumerate all of Note 22’s stated InAs additions. The written schedule retains 0.5 mL at 23 min and 0.8 mL at 158 min. A plot arrow alone is not used to erase or add an injection.',[('main',2,'printed p. 5344, Figure 2'),N22],kind='reviewed_source_limitation',scope='curator_interpretation')
item('sources','model-training-scope','Dataset interpretation',
 'Synthesis routes, analytical procedures, optical trajectories, the unassigned 8.5 nm TEM cohort, calibration references and theoretical context are separate records. Calibration rows and repeated spectra are not independent recipes. No exact atomic structure or unreported recipe parameter is generated from the growth model.',[N21,N22,M1,M2,('si',2,'CdSe table'),('si',4,'InAs table')],kind='curator_data_interpretation',scope='curator_interpretation')
item('properties','main-axis-metadata','Main-figure axes and scale metadata',
 'Figure 1 labels PL energy ticks at 1.8, 2.2 and 2.6 eV and absorption ticks at 2, 2.5 and 3 eV. In Figure 2, visible CdSe labels include mean size 4 and 6 nm, width 6 and 14%, and times 0, 80 and 180 min. InAs labels include mean size 3 and 4 nm, width 20 and 25%, and times 0, 100 and 200 min. These are plotting scales, not a list of measured peak positions or particle sizes.',[('main',2,'printed p. 5344, Figures 1 and 2, axes')],['cdse-kinetics','inas-kinetics'],scope='method_context')
item('properties','si-axis-metadata','InAs supplementary plotting scales',
 'The absorption panel has energy ticks at 0.9, 1.3 and 1.7 eV, and a vertically offset arbitrary-unit scale from 0 to 7. The PL energy ticks are 0.75, 1.25 and 1.75 eV; its intensity is also in arbitrary units. Vertical offsets and energy ticks do not provide absolute yields or digitally measured peak positions.',[('si',3,'supplemental p. 2, absorption and PL axes')],['inas-kinetics'],scope='method_context')
REFS=[
 ('Brennan, J. G.; Siegrist, T.; Carroll, P. J.; Stuczynski, S. M.; Reynders, P.; Brus, L. E.; Steigerwald, M. L. Chem. Mater. 1990, 2, 403–409.','Molecular-precursor nanocrystal growth background.'),
 ('Steigerwald, M. L. Polyhedron 1994, 13, 1245–1252.','Molecular-precursor synthesis background.'),
 ('Steigerwald, M. L.; Stuczynski, S. M.; Kwon, Y. U.; Vennos, D. A.; Brennan, J. G. Inorg. Chim. Acta 1993, 212, 219–224.','Molecular-precursor synthesis background.'),
 ('Stuczynski, S. M.; Brennan, J. G.; Steigerwald, M. L. Inorg. Chem. 1989, 28, 4431–4432.','Molecular-precursor synthesis background.'),
 ('Murray, C. B.; Norris, D. J.; Bawendi, M. G. J. Am. Chem. Soc. 1993, 115, 8706–8715.','II–VI synthesis background and prior optical/TEM size calibration.'),
 ('Vossmeyer, T.; Katsikas, L.; Giersig, M.; Popovic, I. G.; Diesner, K.; Chemseddine, A.; Eychmuller, A.; Weller, H. J. Phys. Chem. 1994, 98, 7665–7673.','Size-distribution sorting context.'),
 ('Katari, J. E. B.; Colvin, V. L.; Alivisatos, A. P. J. Phys. Chem. 1994, 98, 4109–4117.','Separated nucleation/growth strategy and optical/TEM calibration context.'),
 ('Guzelian, A. A.; Katari, J. E. B.; Kadavanich, A. V.; Banin, U.; Hamad, K.; Juban, E.; Alivisatos, A. P.; Wolters, R. H.; Arnold, C. C.; Heath, J. R. J. Phys. Chem. 1996, 100, 7212–7219.','Prior III–V nanocrystal synthesis.'),
 ('Guzelian, A. A.; Banin, U.; Kadavanich, A. V.; Peng, X.; Alivisatos, A. P. Appl. Phys. Lett. 1996, 69, 1432–1434.','Prior III–V synthesis and optical/TEM calibration.'),
 ('Olshavsky, M. A.; Goldstein, A. N.; Alivisatos, A. P. J. Am. Chem. Soc. 1990, 112, 9438–9439.','Prior III–V nanocrystal synthesis.'),
 ('Micic, O. I.; Curtis, C. J.; Jones, K. M.; Sprague, J. R.; Nozik, A. J. J. Phys. Chem. 1994, 98, 4966–4969.','Prior III–V nanocrystal synthesis.'),
 ('Micic, O. I.; Sprague, J. R.; Curtis, C. J.; Jones, K. M.; Machol, J. L.; Nozik, A. J.; Giessen, H.; Fluegel, B.; Mohs, G.; Peyghambarian, N. J. Phys. Chem. 1995, 99, 7754–7759.','Prior III–V nanocrystal synthesis.'),
 ('Micic, O. I.; Nozik, A. J. J. Luminescence 1996, 70, 95–107.','Prior III–V nanocrystal context.'),
 ('Micic, O. I.; Sprague, J.; Lu, Z. H.; Nozik, A. J. Appl. Phys. Lett. 1996, 68, 3150–3152.','Prior III–V nanocrystal synthesis.'),
 ('Douglas, T.; Theopold, K. H. Inorg. Chem. 1991, 30, 594–596.','Prior III–V nanocrystal synthesis.'),
 ('Kher, S. S.; Wells, R. L. Nanostructured Mater. 1996, 7, 591–603.','Prior III–V nanocrystal synthesis.'),
 ('Reiss, H. J. Chem. Phys. 1951, 19, 482–487.','Diffusion-limited size-distribution narrowing theory.'),
 ('Lifshitz, I. M.; Slyozov, V. V. J. Phys. Chem. Solids 1961, 19, 35–50.','Size-dependent growth and ripening theory.'),
 ('Wagner, C. Z. Zeit. Electrochemie 1961, 65, 581–591.','Size-dependent growth and ripening theory; journal abbreviation retained as printed.'),
 ('Sugimoto, T. Adv. Colloid Interfac. Sci. 1987, 28, 65–108.','Gibbs–Thomson / diffusion-controlled growth framework used for Figure 4.'),
 ('Note 21 in this article: synthesis of CdSe nanocrystal samples.','Directly inspected CdSe synthesis, aliquot workup, optical-density setting and second feed.'),
 ('Note 22 in this article: synthesis of InAs nanocrystal samples.','Directly inspected indium stock, InAs injection and growth temperatures, dilution and additional feeds.')]
referenced=[]
for n,(bib,context) in enumerate(REFS,1):
 records=(['cdse-focusing','cdse-aliquot-analysis'] if n==21 else ['inas-focusing','incl3-top-stock','inas-aliquot-analysis'] if n==22 else [])
 item('sources',f'reference-{n:02}',f'{"Note" if n>20 else "Reference"} {n}',bib+' '+context,
  [('main',1,f'printed p. 5343, reference/note {n}')],records,kind='source_reference' if n<=20 else 'direct_source_method_note',scope='cited_context' if n<=20 else 'method_context',notes=['Bibliographic citation checked in this source; cited full text was not read for this proposal.'] if n<=20 else [])
 referenced.append({'id':f'reference-{n}','reference_number':n,'bibliography':[bib],'context':context,'direct_source_note_reviewed':n>20,'cited_work_independently_reviewed_in_this_task':False,'import_experimental_evidence':n>20,'source_locators':[ev('main',1,f'printed p. 5343, reference/note {n}')['locator']]})

# Original assets, panel associations and scientific provenance.
assets={a['id']:a for a in manifest['assets']}
groups={'figures':[],'tables':[],'schemes':[],'equations':[],'source_notes':[]}
def asset(key,group,caption,scope,records,classification,notes=(),panels=(),rows=None,expression=None,axes=()):
 a=assets[key];role=a['source_role'];page=a['source_pdf_page']
 e=ev(role,page,a['label'])
 d={'id':key,'label':a['label'],'document_role':role,'page':page,'printed_page':e['printed_page'],'source_locators':[e['locator']],
 'caption_paraphrase':caption,'sample_scope':scope,'sample_links':[P+r for r in records],
 'sample_linkage':'Explicit source-series association only; no independent batch identity or cross-cohort join is inferred.',
 'evidence_class':classification,'public_asset':a['public_asset'],'public_asset_sha256':a['sha256'],
 'asset_provenance':{'source_file':a['source_filename'],'source_sha256':a['source_sha256'],'source_pdf_page':page,'crop_bbox_pdf_points_top_left':a['crop_bbox_pdf_points_top_left'],'crop_normalized':a['crop_normalized'],'render_dpi':a['render_dpi'],'pixel_dimensions':a['pixel_dimensions'],'renderer':'PDFium 300 dpi original-source crop','transformation':a['transformation']},
 'quantitative_context':list(notes),'panels':list(panels),'notes':list(notes),'text_reviewed':True,'visual_reviewed':True,'reviewed':False,'reader_render_verified':False,'training_eligible':False,'source_asset_type':a['source_asset_type'],'axes':list(axes)}
 if rows is not None:d['structured_rows']=rows
 if expression:d['expression']=expression
 groups[group].append(d)
asset('figure-1','figures','Room-temperature CdSe normalized PL and absorption spectra at selected times, with a second feed at 190 min.',
 'One CdSe optical growth trajectory; source aliquots, not eight independent synthesis experiments.',['cdse-focusing','cdse-kinetics'],'experimental',
 ['Times: 0.2, 1.0, 12, 35, 55, 190, 210 and 240 min.','PL normalized; absorption arbitrary units. No absolute quantum yield.','Original traces and captions retained; no digitization or fabricated intermediate spectra.'],['left: normalized PL','right: absorption'],axes=['Photon energy (eV)','Normalized PL intensity','Absorbance (a.u.)'])
asset('figure-2','figures','PL-derived mean diameter and relative width for CdSe and InAs growth; arrows mark injections.',
 'Left CdSe series and right InAs series are separate material-specific trajectories.',['cdse-focusing','cdse-kinetics','inas-focusing','inas-kinetics'],'experimental_derived',
 ['Diameter and distribution width are inferred from PL with stated calibration assumptions.','Time in minutes; diameter in nm; width is relative standard deviation (%).','Written InAs schedule in Note 22 includes additional feeds at 23 and 158 min; visible arrows are not the complete textual schedule.'],['left top: CdSe mean diameter','left bottom: CdSe relative standard deviation','right top: InAs mean diameter','right bottom: InAs relative standard deviation'])
asset('figure-3','figures','TEM image of faceted CdSe nanocrystals, captioned 8.5 nm diameter, with a 25 nm scale bar.',
 'Unassigned 8.5 nm CdSe TEM cohort produced by distribution focusing. Not proven to be the Figure 1/2 kinetics endpoint.',['cdse-tem'],'experimental',
 ['Caption diameter 8.5 nm; original scale bar 25 nm.','Exact batch, time, distribution and imaging settings unreported.','No SAED, lattice-resolved atomic image or refined phase is supplied here.'])
asset('figure-4','figures','Theoretical growth rate versus normalized radius from the Sugimoto-based growth relation.',
 'Source model with infinite diffusion-layer thickness; not a measured nanoparticle data series.',['growth-model'],'source_theoretical_model',
 ['x: r/r*, dimensionless. y: growth rate in arbitrary units.','Source assumes fixed concentration and diffusion-limited growth with 2σVₘ/rRT ≪ 1.','Do not turn this curve into an absolute recipe-time prediction.'])
asset('si-inas-spectra','figures','InAs absorption and room-temperature PL traces with the source’s high-energy-half analysis note.',
 'Selected InAs optical sampling times; absorption and PL panels have different time sets.',['inas-focusing','inas-kinetics','inas-aliquot-analysis'],'experimental',
 ['Absorption t = 18, 28, 43, 158, 176, 245. PL t = 23, 28, 80, 158, 176.','SI labels t without a unit; minutes follow the associated main growth experiment.','Only the high-energy PL half is used for size analysis because of low-energy reabsorption around 1 eV.','Intensity is in arbitrary units with vertically separated traces; no absolute quantum yield.'],['left: absorption','right: PL (Room T)','bottom note: reabsorption limitation'])
for material,data in [('CdSe',CDSE),('InAs',INAS)]:
 key=material.lower()
 rows=[{'row':n,'absorption_exciton_peak_nm':uv,'pl_peak_eV':pl,'tem_size_nm':size,'sample_relation':'calibration_reference_not_new_batch'} for n,(uv,pl,size) in enumerate(data,1)]
 asset('si-'+key+'-calibration','tables',f'TEM-linked optical calibration table for {material}, containing {len(rows)} printed rows.',
  'Source calibration references, not newly synthesized batches or uniquely mapped kinetic aliquots.',[key+'-calibration','pl-size-analysis'],'source_calibration',
  [f'{len(rows)} rows retain UV–visible peak (nm), PL peak (eV), size (nm).','No row-specific synthesis time, source batch, uncertainty or assignment to a current kinetics sample.','Repeated rounded sizes remain distinct printed calibration rows.'],rows=rows)
asset('equation-gibbs-thomson','equations','Curvature-dependent nanocrystal solubility relative to the bulk solid.',
 'Author theory, not experimentally fitted solubility data.',['growth-model'],'source_theoretical_model',
 ['The equation is unnumbered in the source.','Sᵣ and Sᵦ are nanocrystal and bulk solubility; σ surface energy; Vₘ molar volume; r radius; R gas constant; T temperature.'],expression='S_r = S_b exp(2σV_m / rRT)')
asset('equation-growth-rate','equations','Diffusion-controlled radius growth under the stated small-curvature-energy approximation.',
 'Author model at fixed monomer concentration; K and diffusion-layer thickness are not numerically calibrated.',['growth-model'],'source_theoretical_model',
 ['The equation is unnumbered in the source.','Validity statement: 2σVₘ/rRT ≪ 1. K proportional to monomer diffusivity; δ diffusion-layer thickness; r* critical radius.'],expression='dr/dt = K(1/r + 1/δ)(1/r* − 1/r)')
asset('note-21','source_notes','Original CdSe method note, including stock ratio, reactor temperatures, aliquot workup, optical density and second feed.',
 'Direct source method; aliquot analysis remains separate from the complete reactor batch.',['cdse-focusing','cdse-aliquot-analysis'],'direct_source_method',
 ['4 g TOPO; 360 °C pre-injection; 2.4 mL stock, <0.1 s; post-injection 300 °C.','Se:Cd(CH₃)₂:tributylphosphine = 2:5:100 by mass; 0.8 mL slow feed at 190 min.','0.2 mL aliquot into 2 mL methanol; purified particles in toluene; PL OD 0.09 ± 0.02.'])
asset('note-22','source_notes','Original InAs method note, including indium stock preparation, storage, injection, growth and additional feeds.',
 'Direct source method; InCl₃·TOP preparation is distinct from the ternary injection stock.',['inas-focusing','incl3-top-stock','inas-aliquot-analysis'],'direct_source_method',
 ['0.33 g InCl₃ per mL distilled TOP; 260 °C under argon; cool and drybox store.','2 g TOP at 300 °C; 1 mL cold stock at TMS₃As:InCl₃:TOP = 1:1.1:2.8 by mass; inject <0.1 s.','Initial temperature drop to 250 °C, then growth at 260 °C; additional 0.5 mL at 23 min and 0.8 mL at 158 min.','Aliquots diluted in toluene; no stated methanol precipitation for InAs.'])

ROUTES=['cdse-focusing','inas-focusing'];PROCEDURES=['incl3-top-stock','cdse-aliquot-analysis','inas-aliquot-analysis','pl-size-analysis'];OBS=['cdse-kinetics','inas-kinetics','cdse-tem','cdse-calibration','inas-calibration','growth-model']
labels={'cdse-focusing':'CdSe · Hot injection and size-distribution focusing','inas-focusing':'InAs · Hot injection and size-distribution focusing','incl3-top-stock':'InCl₃ in TOP · Stock preparation','cdse-aliquot-analysis':'CdSe · Aliquot workup and optical analysis','inas-aliquot-analysis':'InAs · Aliquot dilution and optical analysis','pl-size-analysis':'CdSe / InAs · PL-based size-distribution analysis','cdse-kinetics':'CdSe · Growth and concentration comparisons','inas-kinetics':'InAs · Growth and optical trajectories','cdse-tem':'CdSe · Unassigned 8.5 nm TEM cohort','cdse-calibration':'CdSe · Optical-peak / TEM-size calibration','inas-calibration':'InAs · Optical-peak / TEM-size calibration','growth-model':'Diffusion-controlled focusing · Theory and interpretation'}
docs=[]
for d in sources['documents']:
 docs.append({'role':d['role'],'filename':Path(d['source']).name,'sha256':d['sha256'],'page_count':d['page_count'],'pages':[{'page':p['page'],'printed_page':5342+p['page'] if d['role']=='main' else (p['page']-1 if p['page']>1 else None),'text_read':True,'visual_review':True,'sections':['Complete supplied page: text, graphics, captions, notes and metadata inspected by reader/assets preparer.']} for p in d['pages']]})
out={'schema_version':'1.0','paper_id':SID,'doi':'10.1021/ja9805425',
 'title':'Kinetics of II–VI and III–V Colloidal Semiconductor Nanocrystal Growth: “Focusing” of Size Distributions',
 'paper':{'authors':['Xiaogang Peng','J. Wickham','A. P. Alivisatos'],'journal':'Journal of the American Chemical Society','year':1998,'volume':120,'issue':21,'pages':'5343–5344'},
 'source_group':SID,'corpus_paper_id':None,'corpus_document_id':None,'review_scope':'supplied_main_and_matched_si',
 'supporting_information':{'status':'matched_local_si','matched_local_si_count':1,'scientific_pages':3,'administrative_cover_pages':1,'scope':'Two main pages and matched four-page SI file (one cover plus three scientific pages) inspected. Exact DOI/journal/pages on cover; Peng headers and declared scientific contents corroborate identity.'},
 'documents':docs,'document_identity_verification':{'method':'Main title/byline/journal/footer, exact DOI on SI cover, matching journal volume/pages and Peng supplemental headers, and exact main SI declaration content.','full_doi_printed_on_si_cover':True},
 'coverage_status':'private_reader_proposal_pending_independent_audit','independent_audit':'Pending independent source-to-reader, crop and canonical-link audit.','publication_status':'Private proposal only; not integrated or published.','source_review_promoted':False,'training_eligible':False,
 'training_note':'The two synthesis routes, their aliquot analyses, source optical series, isolated TEM cohort, calibration tables and author theory are distinct. Calibration rows and image traces are not additional recipes or exact-structure labels.',
 'recipe_inventory':[{'id':P+k,'label':labels[k],'record_ids':[P+k],'record_type':'literature_protocol' if k in ROUTES else 'procedure' if k in PROCEDURES else 'observation','status':'pending_independent_audit','scope':'A reported synthesis route.' if k in ROUTES else 'Supporting procedure or scoped observation; not an additional synthesis route.','gaps':['No author batch identifiers or exact cross-cohort sample mapping.'],'canonical_draft_present':(B/'canonical-drafts'/f'{P+k}.json').exists()} for k in ROUTES+PROCEDURES+OBS],
 'characterization_inventory':{'reader_item_ids':[i['id'] for s in sections if s['id'] in ['structures','properties'] for i in s['items']]},
 'chemical_intuition':{'reader_item_ids':[i['id'] for s in sections if s['id']=='intuition' for i in s['items']],'scope':'Original author explanations, cited theory and proposed outlook retain separate claim types.'},
 'reader_contract':{'version':'1.0','section_ids':[s['id'] for s in sections],'item_fields':['id','title','text','claim_type','sample_scope','evidence','source_locators','canonical_links','notes','facts','training_eligible']},
 'reader_sections':sections,**groups,'referenced_methods':referenced,
 'remaining_gaps':['Independent canonical-link and source-to-reader audits remain pending for this private proposal.','Detailed stock mixing, concentrations, purification, instrument conditions and exact batch identities remain unreported.','Figure 3’s 8.5 nm TEM specimen is not joined to the smaller-size optical trajectory.','Calibration references are not current recipe outcome labels.'],
 'material_evidence_records':{'CdSe':[P+k for k in ['cdse-focusing','cdse-aliquot-analysis','pl-size-analysis','cdse-kinetics','cdse-tem','cdse-calibration','growth-model']],'InAs':[P+k for k in ['inas-focusing','incl3-top-stock','inas-aliquot-analysis','pl-size-analysis','inas-kinetics','inas-calibration','growth-model']]},
 'material_evidence_scope_notes':['CdS and InP are scope claims without local experiment details in this paper; no new material synthesis page is proposed from the mention alone.','The indium stock is an upstream procedure, not an independently synthesized InAs product.'],
 'evidence_conflicts':[{'id':k,'text':items[k]['text'],'source_locators':items[k]['source_locators']} for k in ['printed-ratios','injection-arrows','cdse-tem','inas-pl-series','inas-reabsorption']],
 'counts':{'reader_items':len(items),'figures':5,'main_figures':4,'si_figures':1,'tables':2,'table_rows':36,'schemes':0,'numbered_equations':0,'unnumbered_equations':2,'original_assets':11,'references_and_notes':22,'records':12,'record_types':{'literature_protocol':2,'procedure':4,'observation':6},'supplied_main_pages':2,'matched_si_pages':4,'si_scientific_pages':3}}

# Optional source audit mapping is deliberately separate from the authored prose.
drafts={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')}
if drafts:
 measurement_targets={
 'cdse-kinetics':{'initial-size':'cdse-focusing-results','initial-spread':'cdse-focusing-results','focused-time':'cdse-focusing-results','focused-size':'cdse-focusing-results','focused-spread':'cdse-focusing-results','defocused-size':'cdse-defocusing-results','defocused-spread':'cdse-defocusing-results','refocused-spread':'cdse-refocusing-results','particle-number':'particle-number','monomer-trend':'monomer-concentration','reduced-focusing-time':'cdse-reduced-injection','reduced-focused-size':'cdse-reduced-injection','baseline-ratio':'cdse-cd-rich-comparison','rich-ratio':'cdse-cd-rich-comparison','rich-stability':'cdse-cd-rich-comparison','lean-ratio':'cdse-cd-poor-comparison','lean-defocusing':'cdse-cd-poor-comparison','lean-concentrated':'cdse-cd-poor-comparison'},
 'cdse-tem':{'tem-diameter':'cdse-tem','tem-scale':'cdse-tem'},
 'inas-kinetics':{'focusing-trend':'inas-kinetics','reabsorption-energy':'inas-reabsorption','high-half-only':'inas-reabsorption'},
 'growth-model':{'gibbs-thomson':'gibbs-thomson','growth-rate':'growth-equation','figure4-limit':'model-figure4','focusing':'why-focusing','defocusing':'why-defocusing','refocusing':'why-refeeding','automation':'automation-outlook','generality':'generality-limits','nucleation':'nucleation-limits'}}
 rowlinks={}
 for rid,draft in drafts.items():
  for index,m in enumerate(draft.get('measurements',[])):
   short=rid.removeprefix(P);mid=m['id']
   if short.endswith('-calibration'):target=short+'-row'+m['sample_id'].split('-')[-1]
   elif mid.startswith('figure1-time-'):target='cdse-spectra'
   elif mid.startswith('absorption-time-'):target='inas-absorption-series'
   elif mid.startswith('pl-time-'):target='inas-pl-series'
   else:target=measurement_targets[short][mid]
   q=m['value']; ii=items[target]
   # Replace separately transcribed calibration facts only after exact comparison.
   if short.endswith('-calibration'):
    match={'uv':'abs','pl':'pl','size':'size'}[mid.split('-')[0]]
    original=next(f for f in ii['facts'] if f['id'].endswith('-'+match))
    assert original['value']==q['value'] and original['unit']==q.get('unit'),(rid,mid)
    ii['facts'].remove(original)
   ee=[]
   for e in m['evidence']:
    loc=e['locator'];role='si' if loc.startswith('SI') else 'main';page=int(loc.split('PDF p. ')[1].split(',')[0])
    ee.append({'source_id':SID,'document_role':role,'pdf_page':page,'printed_page':5342+page if role=='main' else page-1,'locator':loc})
   qvalue=q.get('value')
   if qvalue is None and q.get('minimum') is not None:qvalue=f"{q['minimum']}–{q['maximum']}"
   f={'id':rid+'::'+mid,'label':m['property'].replace('_',' ').capitalize(),'value':qvalue,'unit':q.get('unit'),'approximate':q.get('approximate',False),
    'basis':'source_calibration' if short.endswith('-calibration') else 'author_theoretical_model' if short=='growth-model' else 'reported_derived' if m['property'].startswith('optically_') else q.get('status','reported'),
    'qualifier':' '.join(x for x in [q.get('qualifier'),q.get('note'),m.get('conditions')] if x),'evidence':ee,
    'canonical_record_id':rid,'canonical_measurement_id':mid,'sample_id':m['sample_id'],'json_pointer':f'/measurements/{index}'}
   ii['facts'].append(f)
   ii['canonical_links'].append({'record_id':rid,'json_pointer':f'/measurements/{index}','relation':SCOPE[ii['sample_scope']['scope_kind']]})
   rowlinks[rid+'::'+mid]=target
   for e in ee:
    if e not in ii['evidence']:ii['evidence'].append(e)
    if e['locator'] not in ii['source_locators']:ii['source_locators'].append(e['locator'])
 # Replace provisional cohort labels with precise canonical product links. These remain source-context joins.
 for ii in items.values():
  joins=[]
  for f in ii['facts']:
   if not f.get('canonical_record_id'):continue
   rid=f['canonical_record_id'];samp=f['sample_id']
   n=next(n for n,p in enumerate(drafts[rid]['products']) if p['sample_id']==samp)
   join={'record_id':rid,'sample_id':samp,'json_pointer':f'/products/{n}','relation':SCOPE[ii['sample_scope']['scope_kind']]}
   if join not in joins:joins.append(join)
  ii['sample_scope']['formulations']=list(dict.fromkeys(j['sample_id'] for j in joins))
  if joins:ii['sample_scope']['canonical_sample_links']=joins
  ii['canonical_links']=list({json.dumps(x,sort_keys=True):x for x in ii['canonical_links']}.values())
 out['record_formulation_labels']={rid:[p['sample_id'] for p in d.get('products',[])] for rid,d in drafts.items()}
 out['record_formulation_scope_note']='Sample/context IDs are curator labels within each record. Calibration row IDs require their material-specific record ID; no global row-only join or new batch is asserted.'
 out['counts']['typed_characterization_rows']=len(rowlinks)
 (O/'canonical-measurement-coverage.json').write_text(json.dumps({'measurement_count':len(rowlinks),'measurement_to_reader_item':rowlinks,'draft_sha256':{k:sha(B/'canonical-drafts'/f'{k}.json') for k in drafts}},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
mapping_path=O/'source-item-mapping.json'
if mapping_path.exists():
 mapping=read(mapping_path)
 units=read(B/'source-audit.json')['units']
 unitids={u['id'] for u in units}
 assert set(mapping)==unitids,(sorted(unitids-set(mapping)),sorted(set(mapping)-unitids))
 for uid,targets in mapping.items():
  assert targets and all(t in items for t in targets),(uid,targets)
 for uid,targets in mapping.items():
  for target in targets:items[target].setdefault('source_audit_unit_ids',[]).append(uid)
 out['counts']['source_audit_units']=len(units)
 (O/'source-item-coverage.json').write_text(json.dumps({'source_id':SID,'source_audit_sha256':sha(B/'source-audit.json'),'mapped_unit_count':len(mapping),'unit_to_reader_items':mapping,'unmapped_units':[]},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 for k,v in items.items():
  # Independent source mapping may cover a source unit in more than one reader item.
  if not v.get('source_audit_unit_ids'):v['source_audit_mapping_note']='Supplementary reader explanation with direct source locator; no independent audit unit asserted.'

(O/'peng1998.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(O/'reader-items-summary.json').write_text(json.dumps([{'id':i['id'],'title':i['title'],'section':s['id'],'source_locators':i['source_locators']} for s in sections for i in s['items']],ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'reader_items':len(items),'counts':out['counts'],'path':str(O/'peng1998.json')},ensure_ascii=False))
