import json,hashlib,datetime
from pathlib import Path
O=Path(__file__).parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=json.loads((O/'reading-preparation.json').read_text(encoding='utf-8-sig'))
assert len(p['pages'])==20
for x in p['pages']:
    assert sha(x['png'])==x['png_sha256'] and sha(x['text_path'])==x['text_sha256']
    x['actual_text_read']=True;x['actual_visual_inspection']=True
for f in p['paper']['file_copies']:assert sha(f['source_path'])==f['sha256']
p.update(completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Independent complete source reading before opening author scientific extraction. All nine main and eleven SI text pages and native page images actually read/viewed; not yet an extraction comparison or approval.',pairing={'status':'content_verified','basis':['Matching complete title and byline','Main Associated Content names experimental details, Raman data, phase-transition comparison and 350 K stability, all present in SI','Consistent FA/Pb precursor chemistry, three ligand ratios, three wash ratios and three growth temperatures']},note='Preparation checkpoint remains immutable. Completion is recorded here after actual reading and visual inspection.')
p['page_notes']={
'main1':'Title, abstract, background; 10.4±1.1 nm and ~150 ns are optimized QD claims; graphical abstract is illustrative, not atomic data.',
'main2':'Figure 1 ligand ratio 1:2/1:3/1:4, growth 100 °C, wash 1:20; ligand/facet arguments are author interpretations, not measured coverage.',
'main3':'Figure 2 wash comparison; growth-temperature discussion; beyond-1:20 dissolution is warning, not demonstrated condition.',
'main4':'Figure 3 25/50/100 °C TEM/size/PL/XRD comparison; reported 6.38 Å (002) label retained without reindexing. Figure-specific samples, no full factorial inferred.',
'main5':'Figures 4–5 temperature-dependent PL, 140/250 K source-assigned transitions, intensity maximum 350 K. Lorentzian spectral fitting.',
'main6':'Scheme 1 phase/facet model; unit cells explicitly taken from ref15, not current coordinate refinement. Author explanation distinguished from measurement.',
'main7':'Affiliations, acknowledgments, abbreviations and refs1–24.',
'main8':'Refs25–58; preserve duplicate titles rather than collapse numbering.',
'main9':'Refs59–74 and publisher advertisement; advertisement non-scientific.',
'si1':'Matching full title and authors/affiliations.',
'si2':'Contents includes incorrect later page locators for Table S1 and Figure S3; actual pages govern.',
'si3':'All chemicals, FA-oleate stock and complete Pb/QD/purification procedure read. Stock final volume unspecified; amounts not silently converted to concentration. Hexane supernatant retained after second spin.',
'si4':'Characterization and triple-exponential/average lifetime equations; no component-fit table. 404 nm excitation, 4 ns IRF.',
'si5':'Figure S1 washing-waste photos; Figure S2 Raman actual 80–190 K caption/plots.',
'si6':'Raman prose says 80–200 K; 633 nm pump, 50–300 cm−1, PL overlap above190 K; Raman figure called S1 in prose although actual S2.',
'si7':'Raman FWHM/discontinuity discussion continues; source assignment ~140 K, no invented fitted point values.',
'si8':'All 11 Table S1 rows independently transcribed; blank beta→alpha cells remain null; literature rows not current samples; row9/ref14 identity conflict.',
'si9':'Figure S3 350 K PL series0–210 min and I(t)=−0.026t+1 with t in hours. 300 K reference separate; finite measured stability only. Refs1–3.',
'si10':'SI refs4–9.',
'si11':'SI refs10–15; ref14 title is methylammonium, contradicting Table S1 FAPbI3 label.'}
p['boundary_notes']=[
'FA-oleate charge: 0.1042 g formamidine acetate, 0.8 mL OA, 3.2 mL ODE; 60 °C/30 min/vacuum then135 °C/2 h/N2. Sum of liquid charges is not verified final volume.',
'Pb precursor:0.075 mmol PbI2 +2.5 mL ODE;60 °C30 min degassing,135 °C30 min,0.4/0.6/0.8 mL OA then0.2 mL OAm. Source says cooled to25/50/100 °C for30 min; do not turn into post-injection growth duration.',
'FA stock aliquot0.51 mL then promptly cool room temperature, unquantified. AllQD synthesis N2; do not silently assign vacuum to Pb degassing.',
'Wash1:1/1:10/1:20 MeCN:toluene v/v, absolute volumes unreported.12000 rpm5 min retain precipitate; redissolve hexane;6000 rpm5 min retain supernatant. Unknown final concentration/storage duration and conditions.',
'Main uses literature cells gamma P4/mbm a=b8.88,c6.28 Å; beta P4/mbm a=b8.92,c6.33 Å; alpha Pm-3m a=b=c6.36 Å. They cannot be relabeled current measured coordinates/CIF.',
'Printed d(002)=6.38 Å is retained as reported; it does not agree with cubic a6.36 Å under ordinary indexing, and no external resolution is attempted.',
'Source size ± terms are not assigned a standard-deviation statistic unless explicitly defined. Triple-exponential average is sum(A*tau^2)/sum(A*tau).',
'Source Raman range and numbering conflicts, row9/ref14 material identity conflict, and contents page-number errors stay explicit. No inferred exact per-point plot data or sample joins.'
]
baseline={
'author':'/root/backlog_eta','basis':'Independent actual native-page visual/text reading before opening extraction values',
'table_s1_columns':['row','sample','gamma_beta_K','beta_alpha_K','reference','instruments'],
'table_s1_rows':[
[1,'FAPbI3 bulk',140,285,6,'synchrotron XRD; steady-state PL'],[2,'FAPbI3 bulk',130,270,7,'synchrotron XRD; neutron diffraction; steady-state PL'],[3,'FAPbI3 bulk',140,285,8,'neutron diffraction'],[4,'FAPbI3 single crystals',150,'260–280',9,'XRD'],[5,'FAPbI3 single crystals',140,280,10,'differential scanning calorimetry'],[6,'FAPbI3 powder',140,285,11,'neutron diffraction'],[7,'(FAPbI3)0.85(MAPbBr3)0.15 thin film',90,260,12,'XRD; steady-state and time-resolved PL'],[8,'FAPbI3 nanocrystals (13.3 nm)',140,None,13,'steady-state and time-resolved PL'],[9,'FAPbI3 nanocrystals (15.6 nm)',140,None,14,'UV–visible; steady-state and time-resolved PL'],[10,'FAPbI3 nanocrystals (40 nm)',110,250,15,'XRD; steady-state and time-resolved PL'],[11,'This study quantum dots (10 nm)',140,250,None,'Raman; steady-state PL']],
'figure1_columns':['OAm:OA','FWHM001_deg','FWHM002_deg','lifetime_ns'],
'figure1_rows':[['1:2',0.56,0.60,95],['1:3',0.37,0.44,150],['1:4',0.71,0.78,70]],
'figure2_columns':['MeCN:toluene','FWHM001_deg','FWHM002_deg','lifetime_ns'],
'figure2_rows':[['1:1',0.48,0.53,80],['1:10',0.42,0.48,135],['1:20',0.37,0.44,150]],
'figure3_columns':['growth_C','mean_size_nm','printed_plusminus_nm','size_FWHM_nm','lifetime_ns'],
'figure3_rows':[[25,7.6,2.4,5.7,60],[50,9.5,1.6,3.7,70],[100,10.4,1.1,2.7,150]],
'temperature_slopes_columns':['T_range_K','peak_eV_per_K','FWHM_eV_per_K'],
'temperature_slopes_rows':[['80–140',-7.9e-5,4.01e-4],['140–250',4.32e-4,2.29e-4],['250–350',3.97e-4,1.69e-4],['>350',7.26e-4,3.35e-4]],
'stability':{'T_K':350,'minutes':[0,30,60,90,120,150,180,210],'reference_T_K':300,'linear_fit':'I(t) = -0.026t + 1','t_unit':'h'},
'uncertainty_policy':'Approximate lifetime/prose quantities retained as approximate; listed numerical centers do not override printed approximate/bounded meaning. Native figure cells retain literal digits.'}
for name,data in [('independent-numeric-reading.json',baseline),('independent-reading-checkpoint.json',p)]:
    dest=O/name;assert not dest.exists();dest.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(name,sha(dest))
