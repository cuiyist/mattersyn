"""Freeze independent source reading before opening the author's extraction."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib
O=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,data):
 p=O/name
 if p.exists(): raise RuntimeError('Refuse to replace independent baseline: '+str(p))
 p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 return p
table={
 'reviewer':'/root/backlog_eta','author_extraction_opened':False,
 'basis':'Independent manual transcription from original page images; raw precision and source inconsistencies retained.',
 'main_table_1':{'source':'main PDF5 / printed807','unit':'delta absorbance at500nm / s','columns':['In(MA)3 equivalents','150 C','200 C','250 C'],'rows':[['0','3.50e-6','6.07e-5','1.80e-4'],['10','3.83e-6','9.38e-5','6.37e-4'],['20','6.17e-6','1.34e-4','8.03e-4'],['50','1.13e-5','1.31e-4','1.80e-3']]},
 'si_s22':{'source':'SI15 FigureS22','columns':['time (min)','eV gaussian max'],'rows':[['0','0.2965'],['4','0.2378'],['8','0.2265'],['12','0.2158'],['16','0.2108'],['20','0.2102']],'conditions':'0.182mM,250 C','note':'eV is the printed unit. Do not rescale or assert these are independently validated optical transition energies.'},
 'scherrer_printed_prose':{'columns':['figure','nominal peak deg 2theta','a','x0','dx','D nm'],'rows':[
 ['S38','26','38.2411','26.4049','1.4908','5.5'],['S38','44','46.6309','44.0878','2.01632','4.3'],['S38','51','46.3851','51.5602','1.99453','4.4'],
 ['S39','26','73.0539','26.0581','2.8174','2.9'],['S39','44','30.2403','43.8450','2.7325','3.2'],['S39','49','20.9793','51.2843','2.6645','3.3']]},
 'scherrer_fit_boxes':{'columns':['figure','box','a (Area)','x0 (X Position)','dx (HWHM)','ampl','s'],'rows':[
 ['S38','top','60.7828','26.5841','1.67','17.0968','1.4183'],['S38','middle','46.6309','44.0878','2.0163','10.863','1.7125'],['S38','bottom','46.3851','51.5602','1.9945','10.9239','1.694'],
 ['S39','top','73.0539','26.0581','2.8174','12.1794','2.3929'],['S39','middle','30.2403','43.845','2.7324','5.1984','2.3207'],['S39','bottom','20.9793','51.2843','2.6645','3.6984','2.263']],
 'formula':'sqrt(ln(2)/pi)*(a/dx)*exp(-ln(2)*(x-x0)^2/dx^2)',
 'note':'S38 top fit box materially differs from its prose. S39 middle dx last digit differs. HWHM label is retained, without reinterpreting as FWHM. Units of a/ampl/s not explicitly supplied.'},
 'printed_linear_fits':{'columns':['source','context','slope','intercept','R2','x basis'],'rows':[
 ['S6','150 C','0.00021','0.02940','0.99777','min'],['S6','200 C','0.00734','0.02148','0.99588','min'],['S6','250 C','0.01082','0.02907','0.99755','min'],['S6','300 C','0.03815','0.06248','0.98321','min'],
 ['S8','150 C 500nm','0.000211','0.029991','0.997036','min'],['S20','lograte-logMSC','1.2986','1.7957','0.987','logMSC'],
 ['S21','300 C .182mM','0.23142','0.12695','0.9962','min'],['S21','300 C .061mM','0.04096','0.05968','0.9919','min'],['S21','300 C .030mM','0.02660','0.03518','0.9778','min'],['S21 inset','300 C rate vs MSC','1.4112','-0.02876','0.9828','mM'],
 ['S30','250 C InMA3','5.17e-4','2.25e-4','0.990','additive mM'],['S31','250 C InMA3','5.17e-4','2.26e-4','0.990','additive mM'],['S31','250 C MAH','2.92e-4','1.98e-4','0.998','additive mM'],
 ['S32','zero order .030mM','0.00009','0.02348','0.98296','s'],['S32','zero order .061mM','0.00018','0.02905','0.99776','s'],['S32','zero order .182mM','0.00091','0.06246','0.99271','s'],['S33','rate vs MSC','0.00564','-0.00012','0.99041','mM'],
 ['S34','first order .03mM','0.0029','-3.8076','0.9892','s'],['S34','first order .061mM','0.0026','-3.3089','0.9847','s'],['S34','first order .18mM','0.0029','-2.0386','0.9946','s'],
 ['S36','second order .03mM','-3.64052','39.88464','0.92347','s'],['S36','second order .061mM','-0.0495','26.592','0.943','s'],['S36','second order .18mM','-0.0154','7.5358','0.9819','s']],
 'note':'These are printed fit annotations, not independently fitted raw data; distinct graph scopes and printed precision remain. S36 first slope has a scale tension with its drawn line.'}
}
tablepath=save('independent-table-reading.json',table)
main_notes=[
 'Title/byline/DOI verified; abstract claims mechanism and ligand exchange; prior In37P20 cluster structure is cited context, not new coordinate data.',
 'Scheme1 monomer/reaction pathways; phenylacetate vs myristate scope; Fig1 variable-temperature NMR and room-temperature dynamic absence. Prose -35C versus plot -30C.',
 'Fig2 acid and indium-carboxylate exchange; 1/10/30eq acid and1/5/10/20eq In carboxylate; precipitate/solubility caveat, CDCl3 follow-up.',
 'Fig3 thermolysis150/200/250/300C, TEM150 agglomerates versus250 spherical particles;2.6+/-0.5nm315particles;0.30nm(200) fringe. Fig4 130C30h NMR; 31P caption202Hz retained.',
 '130C72h pretreatment before250C conversion; DSC/TGA interpretations; Fig5 concentration .030/.061/.182mM; Table1 all12 rates plus4 equivalents manually transcribed. Scheme2 and additive interpretation.',
 'Conclusions separate proposed monomer mechanism from measurements. Materials, drying, general N2, analytical instruments. Representative19mL hot medium+1mL cluster stock,20.0mg/1.21e-3mmol; spectra every30s, not a30s delay.',
 '13C phenylacetic acid synthesis:50mL1M Grignard+50mLTHF;13CO2 1.90L40.9mmol;LN2/static vacuum then-76C1h/RT8h;MeOH quench,HCl pH2,Et2O3x20mL/brine/Na2SO4,DCM/pentane0C12h;5.15g92%; all NMR shifts/multiplicities/couplings read. References1 onward and SI declaration.',
 'Remaining references through56 read. Literature syntheses and computations not reclassified as current measured source data.'
]
si_notes=[
 'SI title/byline match main despite initial On the;contents first page read.',
 'Contents duplicate figure numbers; actual supplied figures extend toS39 whereas main declaration endsS28.',
 'S1 absorbance natural/labeled clusters;S2 full13C spectrum and solvent upfield assignment.',
 'S3 heating20-110C and reversibility;S4 MAH0/1/5/10/50/100eq and smallshift.',
 'S5 CDCl3 20eq labeled indium phenylacetate and controls; full spectrum/zoom.',
 'S6 four temperature fits .061mM and time inminutes;S7 150C spectra.',
 'S8 wavelength-specific growth traces and500nm linearfit;S9 300C aging described as Ostwald ripening.',
 'S10 two300C extended-time TEM images20nm bars;S11 XRD150/250 InP/In2O3 references and InMA3 scattering assignment.',
 'S12 150C HRTEM0.3nm fringe and FFT, not SAED;S13 130C spectra0/2/4/6/8/10/30h.',
 'S14 legend oleate MSC vs broader myristate context,130C72h;S15 pretreated250C spectra.',
 'S16 130C72h then250C traces,0-60min.',
 'S17 solid TGA above300C and348C label;S18 DSC10C/min35-160C,66/105/121C marks.',
 'S19 DSC35-75C three cycles10C/min then180C malformed printed rate1800C;68/124C marks.',
 'S20 logfit slope1.2986;S21 300C concentration fits allread/transcribed.',
 'S22 six time/value rows with eV heading, .2965-.2102 preserved raw.',
 'S23 150C0/10/20/50eq MAH;S24 corresponding InMA3; normalized/final absorbance not measured isolated yield.',
 'S25 200C InMA3;S26 250C MAH.',
 'S27 250C InMA3;S28 acid/indium comparison with solid/dotted lines.',
 'S29 250C rate vsintensity, yieldproxy only;S30 150/200/250C additive-rate fit.',
 'S31 separate acid andindium linearfit intercepts differ slightly fromS30.',
 'S32/S33 zero-order presentation; all3 fit annotations andrate-vsconcfit transcribed.',
 'S34/S35 first-order presentation; all3 fit annotations, .03/.061/.18mM labels retained.',
 'S36/S37 second-order presentation; all3 fits raw including -3.64052 slope; no repair.',
 'S38 150C XRD/Scherrer fit screenshot and prose each independently transcribed; materially inconsistent26deg fit;HWHM formula/labels retained.',
 'S39 250C XRD/Scherrer;44deg dx lastdigit differs screenshot/prose,49deg heading vs51.2843fit center. All three screenshot+prose sets read.'
]
conflicts=[
 {'id':'IR01','sources':['main2 Fig1A','main2 prose'],'scope':'low-temperature NMR','issue':'Plot -30C versus prose -35C; retain distinct printed versions.'},
 {'id':'IR02','sources':['main3 prose','SI4 S3'],'scope':'absorption temperature sweep','issue':'Prose starts25C; S3 legend starts20C.'},
 {'id':'IR03','sources':['main4 Fig4A','main5','SI10-11 S14-S16'],'scope':'130C pretreatment','issue':'NMR30h and later72h conversion contexts must not be merged; Fig4B these two samples language is ambiguous.'},
 {'id':'IR04','sources':['main4 Fig4A'],'scope':'31P acquisition','issue':'Printed202Hz; no silentMHz correction.'},
 {'id':'IR05','sources':['main7 SI declaration','SI1-2 contents','SI25 S39'],'scope':'document coverage','issue':'Main saysS1-S28; supplied SI extendsS39; contents repeat S21/S30 labels.'},
 {'id':'IR06','sources':['SI10 S14','main4-5'],'scope':'precursor ligand identity','issue':'S14 bluelegend oleate MSC despite main myristate discussion; do not silently relabel.'},
 {'id':'IR07','sources':['SI13 S19'],'scope':'thermal ramp','issue':'Rate of1800C lacks time denominator and conflicts with sensible rate syntax; actual ramp unknown.'},
 {'id':'IR08','sources':['SI15 S22'],'scope':'optical fitted values','issue':'eV printed for0.2965-0.2102; unit/meaning not independently validated and no rescaling.'},
 {'id':'IR09','sources':['SI24 S38'],'scope':'150C Scherrer','issue':'26deg fitted box60.7828/26.5841/1.67 versus prose38.2411/26.4049/1.4908; keepboth.'},
 {'id':'IR10','sources':['SI25 S39'],'scope':'250C Scherrer','issue':'44deg dx2.7324 box versus2.7325 prose;49deg heading versusx0=51.2843.'},
 {'id':'IR11','sources':['SI23 S36-S37'],'scope':'second-order slope','issue':'Printed-3.64052 versus slope scale drawn overhundredsseconds; retain printed value without deriving replacement.'},
 {'id':'IR12','sources':['main6 materials','main7 isotope acid preparation'],'scope':'13CO2 charge','issue':'Purchased1Lbreakseal versus procedure1.90L/40.9mmol bulb; source reports both.'},
 {'id':'IR13','sources':['main5 Table1','SI6 S6'],'scope':'200C noadditive rate','issue':'Table1 6.07e-5/s differs fromS6 .00734/min after unitconversion; independentfit contexts not silently harmonized.'},
 {'id':'IR14','sources':['main4 Scherrer discussion','SI24 S38'],'scope':'reported size summary','issue':'Main says3-4nm from44deg peak; S38 gives4.3nm at150C; preserve scopes/precision.'}
]
prep=json.loads((O/'reading-preparation.json').read_text())
for d in prep['documents']:
 assert sha(d['source_path'])==d['sha256']
 notes=main_notes if d['role']=='main' else si_notes
 for p,note in zip(d['pages'],notes):
  assert sha(p['text_path'])==p['text_sha256'] and sha(p['image_path'])==p['image_sha256']
  p.update(text_read=True,visual_review=True,independent_reading_note=note)
prep.update(completed_at=datetime.now(timezone.utc).isoformat(),reading_status='all_supplied_pages_independently_read_and_visually_reviewed_before_author_comparison',
 source_id='friedfeld2019',title='Conversion of InP Clusters to Quantum Dots',authors=['Max R. Friedfeld','Dane A. Johnson','Brandi M. Cossairt'],
 pairing={'result':'content_verified','main_pages':8,'si_pages':25,'evidence':['Matching author trio and title except SI On the prefix','Main DOI/title/2019 volume58 pp803-810','Main SI declaration and direct S-figure continuity in supplied SI']},
 synthesis_relevance='Relevant: explicit cluster-to-QD conversion and isotope-labeled phenylacetic acid preparation; several upstream cluster syntheses remain cited-only.',
 table_reading_path=str(tablepath),table_reading_sha256=sha(tablepath),source_tensions=conflicts,
 boundaries=['No author source-facts opened before this checkpoint.','No atomic coordinates are supplied for current InP products; prior cluster structure is cited context.','FFT is not SAED. Scherrer sizes are author analysis, not measured atomic structures.','Abs500 intensity is a yield proxy, not isolated mass yield.','Figure dose/temperature/ligand contexts do not establish one universal sample join.','No full extraction audit pass, canonical approval, training admission or publication approval is claimed.'])
prep['bound_files']={str(p):sha(p) for p in [O/'prepare_reading.py',O/'reading-preparation.json',Path(__file__),tablepath]+list((O/'source-render').glob('*'))}
checkpoint=save('independent-reading-checkpoint.json',prep)
(O/'independent-reading-notes.md').write_text('# Independent Friedfeld source reading\n\nAll 8 main and 25 SI pages were read as text and actually viewed as native images before opening author extraction. Both source hashes match intake. Pairing is supported by title/byline and figure continuity.\n\n'+ '\n'.join('- '+c['id']+': '+c['issue']+' ['+'; '.join(c['sources'])+']' for c in conflicts)+'\n\nThe independent table baseline contains Table1, S22, both printed-prose and screenshot Scherrer fields, and 23 linear-fit annotations. Exact source scopes, raw precision and unresolved inconsistencies are preserved. This is a source-reading checkpoint, not approval of an unseen extraction.\n',encoding='utf8')
print(json.dumps({'checkpoint':str(checkpoint),'sha256':sha(checkpoint),'table_sha256':sha(tablepath),'pages':33,'conflicts':len(conflicts)}))
