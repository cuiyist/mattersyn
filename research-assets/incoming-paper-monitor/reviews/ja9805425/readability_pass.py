"""Format the audit prose without changing its scientific content or stable IDs."""
import json,re,hashlib
from pathlib import Path
B=Path(__file__).parent
p=B/'source-audit.json'; a=json.loads(p.read_text(encoding='utf-8'))
claims={
'identity':'Kinetics of II-VI and III-V Colloidal Semiconductor Nanocrystal Growth: “Focusing” of Size Distributions. Xiaogang Peng, J. Wickham and A. P. Alivisatos. JACS 1998, 120, 5343–5344; received February 18, 1998; online May 14, 1998. Issue 21 is printed on page 2. Terminal code JA9805425 and the SI DOI bind this article to 10.1021/ja9805425.',
'm1-cdse-to-po-charge':'Trioctylphosphine oxide (TOPO), 4 g, is the growth medium; supplier and purity are not specified.',
'm1-cdse-heat':'Heat 4 g TOPO to 360 °C with Ar flowing. The hot solution is rapidly stirred at injection. Heating duration and pressure are not given.',
'm1-cdse-stock':'Cold stock comprises Se:Cd(CH3)2:tributylphosphine = 2:5:100 by mass. Exact stock preparation, speciation, total stock mass, temperature and component molarity are not reported. Tributylphosphine is distinct from TOP.',
'm1-cdse-initial-injection':'Quickly inject 2.4 mL cold stock into hot TOPO, with an injection duration <0.1 s. Preserve the strict upper bound rather than an exact duration of 0.1 s.',
'm1-cdse-temperature-drop':'Injection lowers the temperature to 300 °C, distinct from the 360 °C preinjection condition. No cooling curve, ramp or bath is specified.',
'm1-cdse-aliquot':'At various intervals withdraw 0.2 mL aliquots of the reaction mixture. Each aliquot is distinct from the full reaction batch.',
'm1-cdse-precipitate':'Precipitate each 0.2 mL aliquot in 2 mL methanol. This solvent amount is not a whole-batch workup charge.',
'm1-cdse-purification':'Mass and particle yield are measured after purification from excess TOPO, byproducts and solvent. No purification steps or cycle counts are supplied; do not invent centrifugation or washes.',
'm1-cdse-redissolve':'Redissolve the nanocrystals in toluene for UV–vis and PL spectra; the toluene volume is not given.',
'm1-cdse-optical-density':'Keep optical density at 0.09 ± 0.02 for the CdSe PL samples described in footnote 21. Do not transfer this setting to InAs without supporting evidence.',
'm1-cdse-reinjection':'At 190 min after the first injection, slowly inject 0.8 mL stock into the same reaction mixture. Duration and numerical rate are not specified. This is a sequential dose, not a new independent batch.',
'm1-cdse-missing':'No numerical Ar flow, pressure, vessel geometry, stirring rate, precursor purity, heating time, exact cold-stock temperature, final batch isolation, storage or termination is specified in the supplied main article or SI.',
'm1-inas-indium-stock':'Prepare concentrated InCl3·TOP solution by heating 0.33 g InCl3 per mL of distilled TOP to 260 °C under argon. This is an amount per solvent volume, not a verified concentration per final solution volume.',
'm1-inas-indium-storage':'Cool the prepared InCl3·TOP solution and take it into a drybox for storage. Storage temperature and duration are unreported; do not inherit −35 °C from the Murray paper.',
'm1-inas-top-charge':'Use 2 g TOP as the separate growth medium. TOP means trioctylphosphine; it is distinct from CdSe tributylphosphine and TOPO.',
'm1-inas-heat':'Heat 2 g TOP to 300 °C. Argon is explicit for the InCl3·TOP preparation, but a separate numerical gas flow or atmosphere measurement is not supplied for this growth vessel.',
'm1-inas-stock':'Cold injection stock has TMS3As:InCl3:TOP = 1:1.1:2.8 by mass. TMS3As denotes tris(trimethylsilyl)arsine. Mixing time, preparation details and the exact amount of prepared InCl3·TOP solution consumed are unreported.',
'm1-inas-initial-injection':'Rapidly inject 1 mL cold stock into hot TOP at 300 °C in <0.1 s. Preserve the strict upper bound.',
'm1-inas-drop':'Injection initially lowers the temperature to 250 °C; this is distinct from the subsequent growth temperature.',
'm1-inas-growth':'Growth continues at 260 °C after the initial drop to 250 °C. No measured ramp is specified.',
'm1-inas-aliquots':'Withdraw aliquots at various intervals and dilute in toluene. The InAs aliquot volume is unreported. Do not inherit the CdSe 0.2 mL aliquot or methanol procedure.',
'm1-inas-spectra':'Record UV–vis and PL spectra in toluene. Dilution volume and optical density are not reported for InAs.',
'm1-inas-reinjection1':'An additional injection of 0.5 mL occurs after 23 min in the same InAs growth sequence. Association with the same stock is contextual; injection duration and rate are not stated.',
'm1-inas-reinjection2':'An additional injection of 0.8 mL occurs after 158 min in the same sequence. Time is interpreted as elapsed from the first injection, rather than 158 min after the second injection.',
'm1-inas-missing':'The InAs procedure lacks final isolation, washing, purification, vessel geometry, stirring rate, pressure, numerical gas flow, precursor purities, storage temperature and duration, later injection rates and exact sample-to-time joins.',
'm1-growth-01':'One CdSe growth experiment supplies Figures 1 and 2, left. Initial PL-inferred diameter is 2.1 nm and relative standard deviation is 20%.',
'm1-growth-02':'During the first 22 min, PL-inferred mean diameter increases from 2.1 to 3.3 nm while relative standard deviation decreases from 20% to 7.7%, within the same kinetic trajectory.',
'm1-growth-03':'During the subsequent period up to 190 min, mean diameter increases from 3.3 to 3.9 nm, width broadens to 10.6%, and growth slows.',
'm1-growth-04':'A second injection increases the growth rate and refocuses the distribution to 8.7%. The body does not assign an exact time to this refocused endpoint.',
'm1-growth-05':'Particle-yield data indicate constant particle number during focusing and refocusing, and decreasing number during defocusing. No numerical counts or yields are tabulated.',
'm1-growth-06':'Monomer concentration, determined from particle yield, falls during focusing and refocusing and remains approximately constant during defocusing. No numerical concentration series is supplied.',
'm1-growth-07':'Similar kinetics are reported for InAs in Figure 2, right. The following high-yield/faceted-particle statement is qualitative; the actual TEM Figure 3 is CdSe. Do not fabricate a numerical yield or assign this TEM image to InAs.',
'm1-growth-08':'The authors interpret nucleation as rapid after injection and continuing until temperature and monomer concentration fall below a critical threshold. No numerical nucleation time or threshold concentration is supplied.',
'm1-eq1-expression':'Sr = Sb exp(2σVm/rRT). The equation is unnumbered in the original. Preserve its original rendering and symbols.',
'm1-eq1-symbols':'Sr and Sb are nanocrystal and bulk-solid solubility; σ is specific surface energy; r is nanocrystal radius; Vm is molar material volume; R is the gas constant; T is temperature. The argument assumes fixed monomer concentration and diffusion as the rate-limiting step. No fitted constants are supplied.',
'm2-fig1-overview':'Room-temperature CdSe PL and absorption spectra from the example growth trajectory, with a second monomer injection at 190 min. PL is normalized and absorption is in arbitrary units; this does not measure quantum yield.',
'm2-fig1-axes':'Both horizontal axes are energy (eV): labeled PL ticks 1.8, 2.2 and 2.6, and absorption ticks 2, 2.5 and 3. Preserve the offset traces without asserting digitized curve values.',
'm2-fig2-cdse':'The CdSe panels show mean size (nm) and standard deviation (%) versus time (minutes), extracted from Figure 1 PL. Arrows denote injections. These are neither direct TEM data nor independent batches per point.',
'm2-fig2-inas':'The InAs panels show PL-derived mean size (nm) and standard deviation (%) versus time (minutes); arrows mark injections. Numerical curve values are not tabulated. Do not assert precise values read from pixels.',
'm2-fig2-visible-axes':'Visible CdSe axis ticks include mean size 4/6 nm, width 6/14%, and time 0/80/180 min. InAs ticks include mean size 3/4 nm, width 20/25%, and time 0/100/200 min. These are axis metadata, not individual measured outcomes.',
'm2-fig3-tem':'Figure 3 is a TEM image of CdSe nanocrystals reported as 8.5 nm in diameter, prepared by distribution focusing, with a 25 nm scale bar. Facets are visible. The specimen is not assigned to the smaller 2.1–4.x nm kinetic trajectory, and no exact preparation conditions or time are supplied for it.',
'm2-fig3-characterization-scope':'The supplied sources do not provide the TEM instrument, accelerating voltage, grid preparation, crystal phase, lattice parameters, SAED, XRD or elemental analysis. A geometric atomic illustration would not establish a measured crystal structure.',
'm2-eq2-condition':'The approximation 2σVm/rRT ≪ 1 precedes the diffusion-controlled growth expression. Preserve “much less than”, not merely “less than”.',
'm2-eq2-expression':'dr/dt = K(1/r + 1/δ)(1/r* − 1/r). This unnumbered expression is a model, not a measured kinetic fit.',
'm2-eq2-symbols':'K is proportional to the monomer diffusion constant; δ is diffusion-layer thickness; r* is the critical radius where nanocrystal solubility equals monomer concentration and growth is zero. No numerical K, δ or r* is fitted.',
'm2-fig4':'Figure 4 shows the Sugimoto-model growth rate (arbitrary units) versus r/r*, for infinite diffusion-layer thickness. It is a theoretical curve, not a measured CdSe or InAs rate series.',
'm2-intuition-01':'At fixed monomer concentration, the critical size is at equilibrium. Smaller particles dissolve; larger particles grow at size-dependent rates.',
'm2-intuition-02':'The authors explain focusing when all particles are slightly larger than the critical size, with smaller particles growing faster.',
'm2-intuition-03':'As monomer is depleted the critical size increases; smaller particles shrink and disappear while larger particles grow. The authors identify this as Ostwald ripening or defocusing.',
'm2-intuition-04':'Additional monomer injected at growth temperature lowers the critical size and refocuses the distribution.',
'm2-intuition-05':'Changing the initial monomer concentration changes depletion time, focusing time and focused size.',
'm2-intuition-06':'The authors state that these effects also apply to CdS and InP, and presumably to the broader II-VI/III-V classes. No CdS or InP synthesis procedure or dataset is supplied here.',
'm2-intuition-07':'Continuous monitoring and adjustment of monomer concentration is proposed to keep average size slightly above the critical size. This is an automation outlook, not a demonstrated closed-loop synthesis system.',
'm2-variant-lower-volume':'Reducing the first CdSe injection volume by about 15%, with other conditions unchanged, shortens focusing time from 22 to 11 min and decreases focused diameter from 3.3 to 2.7 nm. An injection volume of 2.04 mL would be a calculation, not a directly reported amount.',
'm2-variant-baseline-ratio':'The authors report a Cd:Se molar ratio of about 1.4:1 in the stock for the described reaction. This is distinct from the reported three-component stock mass ratio.',
'm2-variant-cd-rich':'At Cd:Se = 1.9:1 by mole, focused nanocrystals can remain at growth temperature for hours before defocusing. Exact duration, stock charges and focused size are unreported.',
'm2-variant-lower-cd':'At Cd:Se = 1.1:1 by mole, defocusing is rapid; the authors say almost doubling both Cd and Se concentrations is needed for a tight distribution. No exact concentrations, size, width, time or volume are given. Preserve the low-ratio condition and concentration-rescue comparison as qualitative contexts.',
'm2-ack':'The work was supported by the DOE Office of Basic Energy Sciences, Division of Materials Sciences, under contract DE-AC03-76SF00098. This is administrative information, not experimental evidence.',
'm2-si-announcement':'The main article announces three scientific SI pages containing CdSe/InAs size-calibration tables and InAs absorption/PL spectra. The local four-page PDF includes an added ACS cover; no fourth scientific page is implied.',
'ref21':'Footnote 21 is this paper’s CdSe experimental procedure, not a separate cited paper. Its details are inventoried in the CdSe source units.',
'ref22':'Footnote 22 is this paper’s InAs experimental procedure, not a separate cited paper. Its details are inventoried in the InAs source units.',
'si-cover':'The ACS cover identifies DOI 10.1021/ja9805425 and JACS 1998, 120(21), 5343–5344, matching the main article. Publisher terms and copyright are administrative information, not a recipe or scientific page.',
'si-inas-spectra-overview':'The InAs panels show absorption on the left and room-temperature PL on the right, both versus energy (eV). They have different selected time grids; do not create one-to-one absorption/PL pairs for every trace.',
'si-inas-spectra-reabsorption':'The note states that reabsorption affects the lower-energy half of the PL spectrum around 1 eV. Only the higher-energy half was used to determine size distribution and standard deviation. Do not assume the full PL profile was used for InAs.',
'si-inas-spectra-axes':'Absorption ticks are 0.9, 1.3 and 1.7 eV; its vertical axis is Absorption (a.u.), with stacked offsets from 0 to 7. PL ticks are 0.75, 1.25 and 1.75 eV; its vertical axis is Intensity (a.u.). These offsets do not measure absolute yield.',
'audit-gap-01':'Stock mass ratios plus injection volumes do not establish component masses or moles without density or a stock-batch recipe.',
'audit-gap-02':'Neither main article nor SI reports crystal phase, XRD, SAED, lattice constants or a unit cell. The TEM image alone does not verify a phase assignment.',
'audit-gap-03':'The PL optical density of 0.09 ± 0.02 belongs to the CdSe procedure in footnote 21 and must not silently propagate to InAs footnote 22.',
'audit-gap-04':'SI table rows are TEM calibration points. No row can be assigned to a kinetic sampling time solely because sizes are similar.',
'audit-gap-05':'Initial injection durations are <0.1 s; the second CdSe dose is slow, and InAs reinjection durations are unspecified. Preserve these differences.',
'audit-gap-06':'The 8.5 nm TEM product is described as prepared by distribution focusing but is not joined to the exact recipe parameters of the smaller kinetic trajectory.',
'audit-gap-07':'The CdSe dose at 190 min and InAs doses at 23 and 158 min are sequential additions within their respective trajectories, not independent starting recipes.',
'audit-gap-08':'Preserve InAs 300 °C preheat → 250 °C initial drop → 260 °C continued growth, and CdSe 360 → 300 °C. The 350 °C prior-literature example cannot replace the current 360 °C condition.'}
text=(B/'main-01.txt').read_text(encoding='utf-8')
for u in a['units']:
    i=u['id']
    if i in claims:u['claim']=claims[i]
    if re.fullmatch(r'ref\d\d',i) and int(i[-2:])<=20:
        n=int(i[-2:]); match=re.search(r'\('+str(n)+r'\)\s+(.*?)(?=\('+str(n+1)+r'\)\s)',text,re.S)
        if match:u['claim']=re.sub(r'\s+',' ',match.group(1)).strip().replace('\ufffe','')
    if i.startswith('si-') and '-row' in i:
        v=u['values'];u['claim']=f"{u['material']}: UV–vis exciton peak {v['uv_vis_peak_nm']} nm; PL peak {v['pl_peak_eV']:g} eV; TEM size {v['tem_size_nm']:g} nm. Calibration evidence with no assigned recipe or reaction time."
    if i in ['si-cdse-table','si-inas-table']:
        count=16 if 'cdse' in i else 20;u['claim']=f'Unnumbered calibration table with {count} data rows: UV–vis exciton peak (nm), PL peak (eV), and TEM size (nm). Values were read from the image because embedded OCR is severely corrupted. No individual row is assigned to a current recipe, reaction time, or independent batch.'
    if i.startswith('m2-fig1-time-'):u['claim']=f"Paired normalized PL and absorption traces labeled t = {u['time_min']:g} min in the same CdSe trajectory. Exact peaks are not tabulated; each trace is not an independent batch."
    if i.startswith('si-inas-spectra-abs') or i.startswith('si-inas-spectra-pl'):
        technique='absorption' if '-abs' in i else 'room-temperature PL';u['claim']=f"InAs {technique} trace labeled t = {u['time_label']}. The SI plot does not print the time unit; minutes follow the linked main Figure 2 context. No exact digitized peak is asserted."
    replacements={'Footnote21':'Footnote 21','Footnote22':'Footnote 22','Figure1':'Figure 1','Figure2':'Figure 2','Figure3':'Figure 3','Figure4':'Figure 4','Leftcolumn':'Left column','Rightcolumn':'Right column','rightcolumn':'right column','Fullsuppliedmain/SI':'Full supplied main/SI','cross-check':'cross-check','ACScover':'ACS cover','Calibrationtable,datarow':'Calibration table, data row ','Unnumberedcalibrationtable,printedS':'Unnumbered calibration table, printed S','PrintedS2,twoopticalpanels':'Printed S2, two optical panels','Noteunderplots':'Note under plots','Panelaxes':'Panel axes','PLpanel,trace':'PL panel, trace','Absorptionpanel,trace':'Absorption panel, trace','growthrateequation':'growth-rate equation','equationdefinitions':'equation definitions','SupportingInformationAvailable':'Supporting Information Available'}
    for old,new in replacements.items():u['locator']=u['locator'].replace(old,new)
p.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# Independent source audit: Peng, Wickham and Alivisatos (1998)','',f"DOI 10.1021/ja9805425. All 2 main pages and 4 SI PDF pages (one ACS cover plus 3 scientific pages) were read and visually inspected. {len(a['units'])} stable source units are inventoried. The SI is verified by exact DOI, page headers and matching contents.",'','This is a source inventory. Canonical and public-reader coverage require their separate audits.','']
for u in a['units']:lines+=['## '+u['id'],f"{u['source_role']} PDF page {u['pdf_page']}; {u['locator']}. [{u['kind']}; {u['disposition']}]",u['claim'],'']
(B/'source-audit.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'unit_count':len(a['units']),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))
