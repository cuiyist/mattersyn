from pathlib import Path
import sys,json,hashlib
from datetime import datetime,timezone

A=Path(__file__).resolve().parent
G=A.parent
M=G.parents[4]
sys.path.insert(0,str(M/'research-assets/corpus-20260917/runtime'))
import pymupdf
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

identity=json.loads((G/'intake-identity.json').read_text(encoding='utf-8'))
docs=[]
for item in identity['documents']:
 p=Path(item['source_path']);assert sha(p)==item['sha256'];doc=pymupdf.open(p);assert len(doc)==item['page_count']
 docs.append({'role':item['role'],'path':str(p),'sha256':sha(p),'page_count':len(doc)})
 if item['role']=='si':
  crop=A/'si05-caption-native-300dpi.png'
  doc[4].get_pixmap(matrix=pymupdf.Matrix(300/72,300/72),clip=pymupdf.Rect(65,440,558,535),alpha=False).save(crop)
  write(A/'si05-caption-native-300dpi.json',{'source_path':str(p),'source_sha256':sha(p),'pdf_page':5,'crop_box_pdf_points':[65,440,558,535],'renderer':'PyMuPDF 300 dpi; source pixels only','path':str(crop),'sha256':sha(crop),'viewed':False})

s1='''2.2 4.80 84.29 0.26 51.32 0.62 21.44 0.11 4.06 35.83
2.2 7.40 195.03 0.38 59.07 0.54 21.50 0.09 7.07 45.54
2.2 13.00 692.17 0.13 121.25 0.61 37.94 0.26 9.59 67.93
2.2 14.50 901.95 0.27 99.73 0.60 27.59 0.13 12.37 69.85
3.0 8.70 365.71 0.61 38.04 0.37 12.98 0.02 6.10 33.63
3.0 12.45 776.50 0.04 175.48 0.54 46.55 0.42 21.26 64.81
3.0 14.90 1165.68 0.17 103.85 0.56 35.19 0.28 25.14 60.79
3.0 17.20 1632.86 0.10 209.35 0.33 59.77 0.56 46.56 102.62
3.0 19.00 2075.06 0.11 240.58 0.19 86.98 0.70 51.90 122.85
3.0 21.70 2877.72 0.11 293.08 0.52 78.72 0.37 38.64 151.87
4.0 6.60 316.48 0.19 65.56 0.67 23.46 0.14 5.45 40.90
4.0 8.70 503.83 0.27 56.79 0.65 22.10 0.08 4.94 39.67
4.0 9.00 535.47 0.14 88.75 0.66 30.75 0.19 8.64 50.97
4.0 17.70 2123.62 0.26 90.19 0.74 28.08 0.01 4.93 61.01
5.5 4.70 341.53 0.12 106.83 0.64 30.77 0.24 8.99 57.04
5.5 8.00 678.08 0.09 110.90 0.62 31.22 0.29 10.47 54.03
5.5 10.47 1038.86 0.12 113.55 0.69 33.63 0.19 9.44 61.06
5.5 15.57 2147.23 0.10 133.55 0.65 34.11 0.25 10.50 66.80'''
table1=[['10 min','10 min','~20','~10','~5'],['10 min','3 h','>45','~40','~15'],['3 h','10 min','~35','~10','~6'],['1 h','3 h','~70','~25','~20'],['3 h','1 h','~25','~10','~5']]
table2=[
 ['Octadecene / Primary Amine','Early','Rounded at thin shells, but polydisperse at thick shells','80:20','Low'],
 ['Octadecane / Primary Amine','Middle','Improved structural dispersity','74:26','Low'],
 ['Octadecane / Primary Amine (longer anneal times)','Middle to late','Rounded to faceted hexagonal (>15 MLs)','~85:15','Mod-High'],
 ['Octadecane / Primary Amine (extreme dilution)','None','Half-moons','60:40','Low'],
 ['Octadecane / Secondary Amine','None','Octahedral','~70:30','None'],
 ['Octadecane / No Added Amine','Early','Faceted hexagonal (>6 MLs)','~80:20','Mod-High']]
table3=[
 ['Excess Precursor (10%)','~None','Mis-shapen','Low'],
 ['Excess Precursor (1%)','Late','Rods','Mod.'],
 ['Excess Precursor (1%) + Excess Oleic Acid','Middle','Spherical / hexagonal','High'],
 ['Constant Sulfur','Middle (minimal & persistent)','Rods','Low']]
tables={
 'author':'/root/norberg2004_extract',
 'status':'independent_source_reading_before_author_extraction_comparison',
 'table1':{'locator':'MAIN3, Table1','columns':['post_S_anneal','post_Cd_anneal','QY5ML_percent','QY11ML_percent','QY15ML_percent'],'raw_rows':table1},
 'table2':{'locator':'MAIN4, Table2','columns':['variant','precipitation','shape','WZ_ZB_ratio','QY_thickest_gt15ML'],'raw_rows':table2,'TEM_panels':6,'scale_nm':10},
 'table3':{'locator':'MAIN7, Table3','columns':['variant','precipitation','shape','QY_thickest_gt15ML'],'raw_rows':table3,'TEM_panels':4,'scale_nm':10,'scope':'Main6 says images show moderately thick shells; do not join automatically to the thickest-shell QY specimen.'},
 'table_s1':{'locator':'SI6, TableS1','columns':['core_nm','shell_ML_TEM','volume_nm3_TEM','A1','T1_ns','A2','T2_ns','A3','T3_ns','Tavg_ns'],'raw_rows':[r.split() for r in s1.splitlines()],'cell_count':180,'scope':'Printed rounded fit coefficients and reported average lifetimes retained; no numeric repair by recalculation.'},
 'figure_s2_table':{'locator':'SI2 FigS2 inset','raw_rows':[['n(O-H)','3300-2500'],['n(CH) of -CH=CH-','3000'],['nas(CH3)','2954'],['nas(CH2)','2920'],['ns(CH3)','2866'],['ns(CH2)','2850'],['n(C=O)','1705'],['n(C=C)','1650 (v. weak)'],['d(CH2)','1456'],['d(C-O-H)','1427'],['n(C-OH)','1283']],'wavenumber_unit_from_plot':'cm^-1'}
}
write(A/'independent-table-reading.json',tables)
notes={
 'author':'/root/norberg2004_extract','created_at':datetime.now(timezone.utc).isoformat(),
 'status':'all_supplied_pages_independently_read_pending_extraction_comparison',
 'pairing':{'title':'New Insights into the Complexities of Shell Growth and the Strong Influence of Particle Volume in Nonblinking Giant Core/Shell Nanocrystal Quantum Dots','authors':['Yagnaseni Ghosh','Benjamin D. Mangum','Joanna L. Casson','Darrick J. Williams','Han Htoon','Jennifer A. Hollingsworth'],'journal':'JACS 2012, 134, 9634-9643','doi':'10.1021/ja212032q','content_match':'SI title/byline and Figures S1-S8/Table S1/discussion match main citations and supplied content. SI title uses Non-Blinking; no role mismatch.'},
 'documents':docs,
 'coverage':[{'role':d['role'],'pdf_page':i,'text_read':True,'page_visually_viewed':True,'text_path':str(G/'private/text'/f"{d['role']}-{i:02}.txt"),'text_sha256':sha(G/'private/text'/f"{d['role']}-{i:02}.txt"),'render_path':str(G/'source-render'/f"{d['role']}-{i:02}.png"),'render_sha256':sha(G/'source-render'/f"{d['role']}-{i:02}.png")} for d in docs for i in range(1,d['page_count']+1)],
 'source_scopes_to_check':[
  {'locator':'MAIN2','scope':'Reagents have source-specific purity and no further purification; main prints 1-octadecane. FTIR six wash cycles differ from routine 2-3 workup. Pure OA/oleylamine/dioctylamine/TOP/TOPO comparator spectra prepared separately. XRD 1.5406 angstrom,10-90deg,0.005deg steps,0.100deg/min.'},
  {'locator':'MAIN2;SI8-9','scope':'Blinking 405nm CW,~15mW,~75um,20000frames,100ms+~90ms readout; SI says91ms. Threshold Ipix>BG+2sqrt(BG), no BG subtraction in main; SI trace subtracts threshold. Nonblinking criterion MAIN4 >99% versus MAIN8 figure >=99%; preserve definition variants.'},
  {'locator':'MAIN2;SI6-7','scope':'Lifetime rough film separate acquisition: ~70ps405nm,400kHz-2.5MHz,~100um,100x1.3NA,severalnW-hundredspW,~1e-5 exciton/dot/pulse. Triexponential and weighted Tavg; TableS1 fit parameters initial-guess sensitive; average less sensitive.'},
  {'locator':'MAIN3','scope':'Core preparation100mL round-bottom,reflux condenser,thermocouple;1gTOPO8mLODE0.38mmolCdoleate;vacuum30minRT+30min80C;Ar300C;quick4mmolTOPSe3mLOAm1mLODE;270Cgrowthseveralmin;2-3ethanolcentrifugewashhexane. 2.2nm branch coldtolueneafterseveralseconds,amountunreported. 5.5nm branch~10mingrowth +0.8mmolCdoleate8mmolTOPSe dropwise270C +10min300C; do not silently reassign additional precursor quantities as total.'},
  {'locator':'MAIN3','scope':'Shell250mLround-bottom,~2e-7molwashedcores,5mLOAm5mLOD;0.2MS/OD and0.2MCdoleate/OD;prepassivateoneCdML;geometricMLdosesnotabsolutealiquots;first5-8layersCd/OA1:4then1:10;240C,postS1hpostCd2.5h;withdraw1%aftereachcyclewithoutdoseadjustment,2-3ethanolprecipitationshexane;relativeQY R6G99%.'},
  {'locator':'MAIN3-4 Table1','scope':'5 anneal controls; postCd3h in comparison differs from optimized2.5h. Text calls~3h overall despite3h+10min specified; preserve without fabricated reconciliation. Text5MLQY21+/-0.2 versus41+/-6 ensemble summary not new discrete recipe replicates.'},
  {'locator':'MAIN4-6 Table2','scope':'Six solvent/ligand controls. OD delays7MLto>=11ML;starting10MLdilution9e-6to7e-6M;extreme1.5e-6M suppressesprecipitationbutQY<15%. OAm15mmol vsOA6.5mmolafter14ML contextualamounts, no direct5mLconversion. Noaddedamine stillpermitsboundcoreamine. Phase fractions semi-quantitative not atomic coordinate data.'},
  {'locator':'MAIN6-7 Table3','scope':'Four stoichiometry controls;1%/10%labels mean reaction-volume aliquot removed eachcycle withunchangedprecursordoses,notexactaddedprecursorexcess. 1%+2.5foldOAfifth-eighthshell yields~50%;10%<10%,1%35-40%. ConstantS13MLinventoryupfrontthenCd4hperaddition;precipitationstarting7MLweakpersistent,WZ:ZB40:60.'},
  {'locator':'MAIN5 Fig1;SI2-5','scope':'Oleate and acid FTIR distinguished. Main1635/1555/1408,acid~1710 versusSI2table1705,SI6caption~1653/1542/1469thin and1542/1429thick preserved separately. SI5 secondary-ligand identity wording contradictory; no silent repair.'},
  {'locator':'MAIN6-8;SI4 FigS5','scope':'Dipoles,facets,surface reconstruction/stericblocking are author interpretations. TEMattachment image is observational with5nmscale; causal dipole statement not directly measured dipole model. No atomic structure or ligand coordinates.'},
  {'locator':'MAIN8-9 Fig3/4;SI6-8','scope':'2.2/3.0/4.0/5.5nmcores;~750nm3threshold;~65nslifetimeplateau except3.0nmseries. Nonblinking fraction measuredpopulation not absoluteexperimentalsuccess. SI5.5nm+16.9ML FigS7/S8 is not silently same asTableS1last15.57ML.'},
  {'locator':'SI9','scope':'~11.2nmcore-only thresholdestimate/weakconfinementcontext theoretical. 7nmcoreunwashed~15%680nm;washed~noluminescence;unwasheddiluted single-dotundetectable. Full7nmrouteunreported; do not inherit5.5nmroute.'},
  {'locator':'MAIN10','scope':'23numberedreferences including8a/b; sourcecitation8a printed2009,12,331 retainedraw. Prior citedmethods not retrieved. No provenance projection should include full-page or full-textsourceequivalents.'}
 ],
 'manual_table_reading_file':str(A/'independent-table-reading.json'),
 'numeric_source_comparison_to_author_complete':False,
 'scientific_extraction_approved':False,'canonical_approved':False,'published':False
}
write(A/'independent-reading-checkpoint.json',notes)
print(json.dumps({'pages_read':len(notes['coverage']),'main_pages':10,'si_pages':9,'table_s1_cells':180,'author_extraction_compared':False,'checkpoint_sha256':sha(A/'independent-reading-checkpoint.json'),'table_reading_sha256':sha(A/'independent-table-reading.json')}))
