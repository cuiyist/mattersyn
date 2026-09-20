"""Heo2003 source-native extraction. No canonical, CIF or publication promotion."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import re
import pypdfium2 as pdfium

P=Path(__file__).resolve().parent
SID='heo2003'
manifest=json.loads((P/'intake-manifest.json').read_bytes())
docs={d['role_candidate']:d for d in manifest['documents']}
for d in manifest['documents']:
 assert hashlib.sha256(Path(d['path']).read_bytes()).hexdigest()==d['sha256']
now=dt.datetime.now(dt.timezone.utc).isoformat()
def save(name,data): (P/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def ev(page,locator,role='main'):
 return {'source_id':SID+'-'+role,'source_sha256':docs[role]['sha256'],'pdf_page':page,'printed_page':1119+page if role=='main' else 40+page,'locator':locator}
facts=[]
def f(key,page,locator,scope,prop,value,unit=None,status='reported',qualifier='',approximate=False):
 facts.append({'id':SID+'-'+key,'sample_scope':scope,'property':prop,'value':value,'unit':unit,'status':status,'approximate':approximate,'qualifier':qualifier,'evidence':[ev(page,locator)],'eligible_training':False,'independent_review_status':'pending'})

f('parent-host',2,'Experimental opening','supplied sodium zeolite X','nominal unit-cell composition','Na92Si100Al92O384',qualifier='Host crystals were prepared in St. Petersburg and attributed to ref28. The host synthesis was not supplied in full here.')
f('host-shape',2,'Experimental opening','supplied sodium zeolite X','morphology','colorless single-crystal octahedra')
f('host-size',2,'Experimental opening','host crystals before exchange','cross-section',.15,'mm',approximate=True,qualifier='Macroscopic zeolite-host dimension, not indium-dot diameter.')
f('capillary',2,'Experimental','host handling and redox preparation','container','fine Pyrex capillary',qualifier='Bore, wall thickness and crystal count per treatment are not stated.')
f('exchange-reagent',2,'Experimental','dynamic ion exchange','reagent','aqueous thallous acetate; Aldrich Chemical Co.; 99.99%')
f('exchange-stock',2,'Experimental','aqueous thallous acetate feed','concentration',.1,'mol/L')
f('exchange-ph',2,'Experimental','aqueous thallous acetate feed','pH',6.4)
f('exchange-method',2,'Experimental','Na-X to Tl-X','operation','flow method; dynamic ion exchange',qualifier='Flow rate and whether the Table1 10mL is total passed or reservoir volume are not resolved.')
f('exchange-duration',4,'Table1 experimental rows','Na-X to Tl-X','duration',4,'days',qualifier='Table1 adds this detail; prose does not state the duration.')
f('exchange-volume',4,'Table1 experimental rows','Na-X to Tl-X','reported volume',10,'mL',qualifier='Do not invent flow rate or circulation arrangement from total time and volume.')
f('exchange-temperature',4,'Table1 experimental rows','Na-X to Tl-X','temperature',298,'K')
f('tl-product',2,'Experimental','after ion exchange','nominal composition','Tl92Si100Al92O384',qualifier='Stoichiometric exchange suitability supported by cited earlier work, not a new per-crystal chemical-analysis table.')
f('initial-dehydration-prose-t',2,'Experimental second paragraph','Tl-X initial dehydration; prose version','temperature',623,'K',qualifier='Conflicts with Table1 673K; no single resolved setting admitted.')
f('initial-dehydration-prose-time',2,'Experimental second paragraph','Tl-X initial dehydration; prose version','duration',48,'h',qualifier='Conflicts with Table1 3days.')
f('dehydration-vacuum',2,'Experimental','both prose dehydration steps','pressure',1e-6,'Torr',qualifier='Explicit dehydration pressure; not automatically the subsequent indium-contact reactor pressure.')
f('initial-dehydration-table-t',4,'Table1 experimental rows','Tl-X initial dehydration; table version','temperature',673,'K',qualifier='Unresolved disagreement with prose623K.')
f('initial-dehydration-table-time',4,'Table1 experimental rows','Tl-X initial dehydration; table version','duration',3,'days',qualifier='Unresolved disagreement with prose48h.')
f('indium-metal',2,'Experimental second paragraph','redox ion exchange','reagent','In metal; Aldrich Chemical Co.;99.999%',qualifier='Mass and metal-to-zeolite ratio are not stated.')
f('redox-t',2,'Experimental second paragraph; Table1','Tl-X contact with indium','reported temperature',623,'K',qualifier='Crystal described as somewhat cooler than metal in coaxial ovens; separate setpoints not supplied.')
f('redox-prose-time',2,'Experimental second paragraph','indium contact; prose version','duration',96,'h',qualifier='Conflicts with Table1 5days; not silently treated as a second successful route.')
f('redox-table-time',4,'Table1 experimental rows','indium contact; table version','duration',5,'days',qualifier='Conflicts with prose96h.')
f('redox-pressure',2,'Experimental second paragraph','indium-contact stage','pressure','under vacuum; numerical value unspecified',status='reported_qualitative',qualifier='Dehydration vacuum and literature metal vapor pressures are separate quantities.')
f('redox-ovens',2,'Experimental second paragraph','indium-contact stage','apparatus and transport','coaxially connected cylindrical ovens; condensation of In around crystals somewhat cooler than metal; droplets observed near crystals',qualifier='Geometry, temperature gradient, metal mass and actual vacuum pressure are absent.')
f('in-vapor-pressure',2,'Experimental citing42','reference In(l) at623K','vapor pressure',2.19e-12,'Torr',status='cited_reference',approximate=True,qualifier='Source also prints2.92e-10N/m2. Not measured reactor pressure; ref42 full text not read.')
f('tl-vapor-pressure',2,'Experimental citing42','reference Tl(s) at623K','vapor pressure',1.22e-6,'Torr',status='cited_reference',qualifier='Source also prints1.63e-4N/m2; used to explain thallium distillation, not a process pressure.')
f('black-reactant',2,'Experimental wash paragraph','after indium redox contact','appearance','black crystal',qualifier='One crystal selected, exposed to atmosphere and washed; no particle-dispersion optical color inference.')
f('wash',2,'Experimental wash paragraph','black crystal surface cleaning','operation','expose to atmosphere and wash with deionized water',qualifier='Authors hope to remove surface Tl/In residues; no quantified removal yield.')
f('wash-time',4,'Table1 experimental rows','DI-water wash','duration',1,'day')
f('wash-volume',4,'Table1 experimental rows','DI-water wash','volume',10,'mL')
f('redehydrate-prose-t',2,'Experimental wash paragraph','redehydration; prose version','temperature',623,'K',qualifier='Conflicts with Table1 673K.')
f('redehydrate-prose-time',2,'Experimental wash paragraph','redehydration; prose version','duration',48,'h',qualifier='Conflicts with Table1 3days.')
f('redehydrate-table-t',4,'Table1 experimental rows','redehydration; table version','temperature',673,'K',qualifier='Conflicts with prose623K.')
f('redehydrate-table-time',4,'Table1 experimental rows','redehydration; table version','duration',3,'days',qualifier='Conflicts with prose48h.')
f('washed-parent',2,'End of Introduction and Experimental','washed/redehydrated parent In-X','nominal formula','In87Si100Al92O384',qualifier='In87-X identity relates to previous ref34; current product is In66-X, not this parent.')
f('h2s-reagent',2,'Experimental final treatment','H2S exposure','reagent','zeolitically dried H2S; Aldrich Chemical Co.;99.999%',qualifier='Drying apparatus/zeolite type and drying procedure are not supplied.')
f('h2s-pressure',2,'Experimental final treatment; Table1','H2S exposure','pressure',.5,'atm')
f('h2s-t',2,'Experimental final treatment; Table1','H2S exposure','temperature',673,'K')
f('h2s-time',2,'Experimental final treatment; Table1','H2S exposure','duration',12,'h')
f('evacuate-final',4,'Table1 experimental rows','post-H2S evacuation','duration',10,'min',qualifier='At673K from table and prose evacuated at temperature; numerical vacuum pressure not restated.')
f('seal',2,'Experimental final treatment','after post-H2S evacuation','handling','seal off from vacuum line at room temperature for X-ray experiments, followed by EPXMA and XPS',qualifier='No numeric cooling rate, sealing temperature or long-term storage instruction.')
f('surface-powder',2,'Experimental final paragraph','treated crystal surface','observation','metallic gray powder',qualifier='In2O,In2S,InS or finely dividedIn suggested by appearance; In2S/InS considered most likely. Not confirmed phase identification or a separate sulfide recipe.')

f('product-formula',1,'Abstract','final In66-X crystal','nominal composition','In66Si100Al92O384',approximate=True,qualifier='Distinct from Table2 equal Si/Al average-scatterer representation; exact oxygen/hydrogen balance is unresolved.')
f('epxma-instrument',2,'Experimental final paragraph','product exposed to atmosphere','instrument','EDAX9100 EDS attached to Phillips515 SEM')
f('epxma-parent-control',4,'Results EPXMA','parent In87-X','additional control','fresh surface of intentionally broken reactant crystal confirms In as the only nonframework element',qualifier='Control is not the final H2S-treated crystal.')
f('xps-instrument',2,'Experimental final paragraph','XPS analysis','instrument','VG ESCALAB250')
f('xps-excitation',2,'Experimental final paragraph','XPS acquisition','Al K-alpha energy',1486.7,'eV')
f('xps-power-voltage',2,'Experimental final paragraph','XPS acquisition','source voltage',15,'kV')
f('xps-current',2,'Experimental final paragraph','XPS acquisition','source current',10,'mA')
f('sputter-voltage',2,'Experimental final paragraph','XPS depth profiling','ion-gun voltage',3,'kV')
f('sputter-rate',2,'Experimental; Figure3 caption','XPS depth profiling','sputtering rate',.6,'angstrom/s')
f('sputter-step',4,'Figure3 caption','successive XPS measurements','sputter interval after each measurement',10,'s',approximate=True,qualifier='Not a statement of total sputtering time or depth; figure shows a displayed series.')
f('depth-prose',5,'XPS Analyses last paragraph','XPS depth profile','depth described in prose',4300,'angstrom',approximate=True,qualifier='Does not follow from~20displayed cycles at~10s and0.6angstrom/s. Preserve unreported total-history mismatch; do not fabricate schedule.')
f('in-metal-xps',4,'XPS Analyses','In metal reference Figure2A','3d3/2 and3d5/2 energies',[451.8,444.3],'eV',approximate=True)
f('xps-splitting',4,'XPS Analyses','In3d doublet','energy splitting',7.5,'eV',approximate=True)
f('atomic-like-xps',5,'XPS Analyses','In66-X B and In87-X C','lower-binding-energy doublet',[452.5,445.0],'eV',approximate=True,qualifier='Atomic-like In assignment and~0.7eV shift attributed to cation interaction; not separate pure-metal phase proof.')
f('xps-cation-pair',5,'XPS Analyses','In66-X B and In87-X C','higher-binding-energy doublet',[454.7,447.2],'eV',approximate=True,qualifier='Cation oxidation states inferred between1+ and3+ using cited reference ranges, not uniquely measured per-site oxidation numbers.')
f('xps-reference-ranges',5,'XPS Analyses citing53','cited comparison compounds','In3d5/2 binding energy ranges',{'InCl':[444.6,445.2],'InCl3':[446.0,446.9],'other_InIII':[444.1,446.3]},'eV',status='cited_reference',approximate=True,qualifier='These are literature ranges, not experimental products of this protocol.')
f('xps-parent-difference',5,'XPS Analyses','product versus parent XPS','relative atomic-like intensity','lower-energy doublet stronger in product although total In per cell lower',status='reported_qualitative',qualifier='No fitted per-specimen fraction table is supplied.')
f('epxma-lines',4,'Results EPXMA','Figure1 spectra','reported line energies',{'O':[.53,.53,.52],'Al':[1.49],'Si':[1.74],'In_Lalpha':[3.28,3.29],'In_Lbeta':[3.49,3.71,3.57],'S':[2.31]},'keV',qualifier='Element/line assignments in source prose; overlapping lines and specimen comparisons are not quantitative stoichiometry.')
f('epxma-tl',4,'Results EPXMA','product Figure1A','thallium exclusion argument','absence of additional Tl L lines at10.26/12.21keV supports S assignment at2.31keV rather than overlapping Tl2.27keV',status='author_interpretation')
f('epxma-surface',4,'Results EPXMA','product Figure1A','sulfur scope','sulfur likely at crystal surface; no sulfur position found in crystallographic model',status='author_interpretation',qualifier='Do not insert sulfur into the refined In66-X unit cell.')
f('epxma-background',4,'Results EPXMA','spectral backgrounds/controls','assignment caveats','parent spectrum lack of oxygen attributed to earlier Be window; near0.3keV C contamination (C0.28); near0.1keV frequent instrumental ghost may contain S lines at0.15keV',status='author_interpretation')

f('xrd-instrument',3,'X-ray Data Collection','single-crystal diffraction','instrument','CAD4/Turbo rotating-anode generator with graphite monochromator; Mo radiation')
f('xrd-t',3,'X-ray Data Collection','diffraction specimen','temperature',294,'K')
f('unit-cell',3,'X-ray Data Collection','final average structure','cubic lattice constant',24.942,'angstrom',qualifier='Reported24.942(4)angstrom; estimated standard deviation0.004angstrom. Not a finite-dot dimension.')
f('cell-reflections',3,'X-ray Data Collection','unit-cell determination','intense reflections',25,qualifier='Diverse reciprocal-space regions; not the full reflection dataset.')
f('background-count',3,'X-ray Data Collection','diffraction acquisition','background counting','at each scan endpoint for half the scan time')
f('xrd-monitor',3,'X-ray Data Collection','instrument/crystal monitoring','check schedule','three reflections in diverse regions every3h; small random fluctuations only')
f('absorption-correction',3,'X-ray Data Collection','refinement data treatment','absorption correction','semiempirical psi-scan evaluated with mu2.20mm^-1; not used because corrected data yielded nearly identical final R values',qualifier='Do not state absorption correction was applied to the adopted final result.')
f('space-group',3,'X-ray Data Collection','adopted average structure','space group','Fd-3m (No.227)',qualifier='Fd-3(No.203) was considered; reflection equality, near-equal average Si/Al–O distances and lower residuals favor227. Origin/setting for downloadable coordinates still needs independent validation.')
f('reflection-conditions',3,'X-ray Data Collection','observed diffraction symmetry','reflection conditions','hkl:h+k,k+l,l+h=2n; 0kl:k+l=4n; hkl and khl intensity equality',qualifier='As printed. Not a substitution for validating a chosen space-group origin/setting.')
f('si-al-order',6,'Space Group Considerations','final In66-X compared with parent zeolites','framework order','loss of long-range Si/Al ordering',status='author_interpretation',qualifier='Average diffraction refinement is disordered; an ordered DFT supercell would be a derived hypothesis, not uniquely experimental.')
f('alternative-si-al-distance',6,'Space Group Considerations','refinement in rejectedFd-3','average assigned Si–O and Al–O distances',[1.66,1.68],'angstrom',qualifier='Compared with cited typical1.62/1.72angstrom; not two separately characterized product phases.')
f('refinement-method',3,'Structure Determination','adopted structure','refinement','SHELXL97 full-matrix least squares on F² using all reflections with no n-sigma cutoff; framework starting coordinates fromref34')
f('refinement-stages',3,'Structure Determination','model development; not experiments','successive models',[
 {'sites':['InII'],'occupancies':['24.3(2)'],'R1':.48},
 {'sites':['InII','InU'],'occupancies':['22.8(2)','4.6(5)'],'R1':.46},
 {'sites':['InII','InU','InIprime'],'occupancies':['25.9(4)','8.0(1)','32.4(4)'],'R1':.063},
 {'sites':['InII','InU','InIprime','InIIa'],'occupancies':['25.0(4)','7.9(1)','31.7(3)','0.8(2)'],'R1':.062},
 {'sites':['InII','InU','InIprime','InIIa'],'fixed_occupancies':[25,8,32,1],'R1':.058}],status='reported_refinement',qualifier='Occupancies are atoms per conventional unit cell. Final tabulated R1 is0.0583. These are refinement iterations, not five synthesis variants.')
f('unrefined-peaks',3,'Structure Determination','final difference-Fourier map','unassigned sites','some peaks opposite a four-ring supercage failed stable refinement as In or S',qualifier='Do not add these peaks as atoms in a structure download.')
f('weight-model',3,'Structure Determination last paragraph','diffraction refinement','weight equation','w=1/[sigma²(Fo²)+(aP)²+bP]; P=[max(Fo²,0)+2Fc²]/3; a=.0789,b=296.55',status='author_model',qualifier='The max() term is in the weight model; measured negative Fo² observations in SI must not be clamped away.')
f('scattering-model',3,'Structure Determination last paragraph','diffraction refinement','scattering factors','InII=(2*InIII+In0)/3; InI=(InIII+2*In0)/3; (Si,Al) average of SiIV,Si0,AlIII,Al0; anomalous dispersion included',status='author_model',qualifier='Source also says atomic factors for O− and (Si,Al)^1.75+; this refinement convention is not a formal-charge measurement.')
f('table2-scales',5,'Table2 and footnotes','refined coordinates and displacement parameters','printed scales','positions times10^5; thermal Uij times10^4; parentheses estimated standard deviations in final significant digits; occupancy atoms/unitcell',qualifier='Coordinate table retained separately in main-tables.json. Never interpret25or1 as site-fraction occupancies.')
f('table2-si-al',5,'Table2 footnote c','framework average-scatterer model','Si/Al atom-count representation',[96,96],'atoms/unitcell',qualifier='Nominal bulk formula isSi100Al92. Preserve both; do not silently substitute one for the other.')
f('table2-fixed-sites',5,'Table2','final indium model','site counts and multiplicities',{'InU':[8,8],'InIprime':[32,32],'InII':[25,32],'InIIa':[1,32]},status='reported_refinement',qualifier='Pairs are fixed atom count and Wyckoff multiplicity. InII/InIIa partial occupancies and possible local correlations are not an ordered atomistic configuration.')
f('data-ratio-mismatch',4,'Table1 and footnotes','refinement summary','data/parameter ratio caveat','printed17.1/18.3 match754/44 and1207/66 observed-reflection counts; headingm/s definesm as unique1209/2032',status='source_conflict',qualifier='Retain original table and identify this definition mismatch instead of rewriting reported ratios.')

f('zeolite-description',5,'General Description of Zeolite X','host framework','topology','Al-rich synthetic analogue of faujasite; sodalite beta-cages, six-ring connections giving D6R prisms, supercages accessible through12-ring windows',qualifier='Background framework description; Figure4 is stylized, not microscopy of the product.')
f('site-definitions',5,'General Description of Zeolite X','zeolite site convention','site mapping','I center of D6R; Iprime sodalite-facing D6R; IIprime sodalite-facing single6-ring; II supercage-facing single6-ring; III supercage2fold opposite4-ring; IIIprime offaxis/near12-ring; U sodalite center')
f('oxidation-assignment',6,'Crystal Structure: assignment of tentative oxidation states','final In66-X','tentative oxidation states','8In0 atU,32ca.In2+ atIprime,25In+ atII,1In2+ atIIa; Iprime subsequently approximated1.75+ to giveIn5^7+',status='author_interpretation',qualifier='Crystallography cannot distinguish1.75+ from2+ solely by these bond lengths. No site oxidation state is independently measured exactly.')
f('cluster-count',6,'Crystal Structure; Figure6','final average In66-X','centered tetrahedral In5 clusters',8,'clusters/conventional unitcell',qualifier='One per sodalite cavity from final occupancy model; not eight independently synthesized particles.')
f('supercage-filling',7,'Figure5 caption','supercage model','common local configuration','about87.5% have three In+ atInII with an In atInIIa in one of them; drawing shows four tetrahedrally arrangedIn+ possibilities',status='author_model',qualifier='Average partially occupied crystallographic sites do not uniquely specify a local DFT supercell.')
f('ellipsoid-probability',7,'Figure5 caption','structure stereoviews','displacement ellipsoid probability',50,'%',qualifier='Display convention, not chemical yield or site occupancy.')
f('cluster-bond',5,'Table3; mainp8discussion','InU toInIprime','distance','2.6831(13)','angstrom',status='reported_refinement')
f('cluster-oxygen',5,'Table3; mainp7discussion','InIprime toO3','distance','2.170(7)','angstrom',status='reported_refinement')
f('inIIa-radius',7,'Dipositive Indium Ions','author estimate forInIIa','ionic radius',.93,'angstrom',status='author_derived',approximate=True,qualifier='Computed fromrounded2.25angstromIn–O minus1.32angstromoxygen radius; not the In5-dot radius.')
f('extra-ligand',7,'Dipositive Indium Ions','low-occupancy InIIa','possible extra ligand','near-tetrahedral112degree O2–InIIa–O2 angle suggests another supercage ligand; not confirmed crystallographically',status='author_interpretation')
f('inU-density',8,'Indium Atoms at Site U continuation','InU assignment','Fourier electron-density argument','ca387e/angstrom^3 divided by8 gives48e/angstrom^3 at special position',status='author_interpretation',qualifier='Preserve source explanation; not an integrated electron count measured per isolated dot.')
f('prior-parent-sites',8,'Indium Atoms at Site U','cited parent In88-X to washedIn87-X','prior occupancy comparison',{'InU':[2.0,2.5],'InIprime':[8.0,10.0]},'atoms/unitcell',status='cited_reference',qualifier='Earlierref34 results, not new protocols characterized in this source.')
f('h2s-site-increase',8,'Indium Atoms at Site U','current product versus In87-X parent','additional sites attributed to H2S',{'InU':5.5,'InIprime':22},'atoms/unitcell',status='author_derived',qualifier='Difference from cited parent occupancies; mechanism proposed as further disproportionation.')
f('cluster-stability',8,'The In5 cation in sodalite cavity','authors chemical interpretation','stabilization','In0 preferentially coordinates more-polarizing Inca2+ rather than framework oxygen or In+; Iprime ligands complete tetrahedron; electron delocalization makes integer site charges approximate',status='author_interpretation')
f('cluster-charge',6,'Assignment of Tentative Oxidation States; mainp8','In5 cluster model','proposed cluster charge',7,'elementary positive charges',status='author_interpretation',qualifier='In5^8+ would be odd-electron under author counting;7+ satisfies Lewis octet. Formal charge not independently resolved experimentally.')
f('charge-deficit',8,'Charge balance discussion','proposed8In5^7+ +25In+ +1In2+ model','charge count',[83,92],'positive model charge versus negative nominal framework',status='author_derived',qualifier='Not a charge-neutral experimentally complete atomistic model.')
f('oxygen-loss-hypothesis',8,'Charge balance discussion','proposed charge compensation','possible oxygen loss',4.5,'O/unitcell',status='author_hypothesis',qualifier='No refined oxygen-vacancy positions or measured oxygen loss. Do not delete atoms from measured coordinate model.')
f('proton-hypothesis',8,'Charge balance discussion','alternative compensation without oxygen loss','possible protons',9,'H+/unitcell',status='author_hypothesis',qualifier='Hydrogen not detected or located; do not add these as measured atoms. H2S source and site possibilities are proposed.')
f('cluster-size',8,'An Array of In5 quantum dots','structure-based In5 cluster estimate','radius',3.5,'angstrom',status='author_derived',approximate=True,qualifier='Estimated2.68angstrombond+0.85angstromionic radius; not TEM measurement. Diameter~7angstrom is derived, not a separate reported TEM outcome.')
f('cluster-spacing',9,'Array discussion continuation','diamond-like array of cluster centers','intercluster distance',10.8,'angstrom',status='author_derived',approximate=True)
f('dot-count',9,'Array discussion continuation','~0.15mm octahedral host single crystal','estimated ordered-dot count',300e12,'dots',status='author_derived',approximate=True,qualifier='Author estimate; not individually counted or independently reproduced here.')
f('outlook',9,'Array discussion conclusion','future applications','proposed storage','if individual clusters could be tagged electronically or magnetically, crystal might store information at a capacity of orderTeras',status='author_outlook',qualifier='No individual addressing, transport, device storage, optical absorption/PL, Raman or magnetic switching result is demonstrated.')
f('motivation',2,'Introduction final paragraphs','current study motivation','chemical rationale','H2S treatment hoped to promote disproportionation and raise partially occupied In5 populations to a complete three-dimensional cluster array',status='author_interpretation',qualifier='Earlier In-A/S/H2S and In-X filling fractions are cited comparison systems, not variants of this single protocol.')
f('prior-exchange-failure',2,'Introduction','cited earlier preparation attempts','limitations','aqueous InIII exchange and some melts destroy high-Al zeolite crystallinity at required low pH; cited high-pressure20kbar inclusion and low-loading high-Si systems motivate solvent-free redox',status='cited_reference',qualifier='Not current failed synthesis trials; do not copy20kbar to the present recipe.')

equations=[
 ('redox',2,'Introduction','Tl+ + In0 -> In+ + Tl0','prior/current redox interpretation'),
 ('disproportionation-II',2,'Introduction','2In+ -> In2+ + In0','author disproportionation pathway'),
 ('disproportionation-III',2,'Introduction','3In+ -> In3+ + 2In0','author disproportionation pathway'),
 ('cluster-formation',6,'Crystal Structure','7In+ -> (In5)7+ + 2In0','hypothetical cluster stabilization'),
 ('oxygen-loss-1',8,'Charge balance','O2- + H2S + In2+ -> InS + H2O','hypothesized charge compensation'),
 ('oxygen-loss-2',8,'Charge balance','3O2- + 3H2S + 3In2+ -> In2S3 + 3H2O + In0','hypothesized charge compensation'),
 ('proton-1',8,'Charge balance','H2S + In2+ -> InS + 2H+','alternative hypothesized charge compensation'),
 ('proton-2',8,'Charge balance','3H2S + 3In2+ -> In2S3 + 6H+ + In0','alternative hypothesized charge compensation')]
for key,page,loc,value,scope in equations:
 f('equation-'+key,page,loc,scope,'chemical equation',value,status='author_hypothesis',qualifier='Proposed mechanism, not an independently demonstrated preparation or confirmed side-product phase.')

materials=[
 ('na-x','Sodium zeolite X','Na92Si100Al92O384','host crystals','Upstream synthesisref28 not inspected here.'),
 ('tl-acetate','Thallous acetate','TlC2H3O2','ion-exchange solute','Source calls it thallous acetate; expanded formula is a chemical normalization, not an atomic structure from this paper.'),
 ('water','Deionized water','H2O','wash; water medium for thallous stock','Feed solvent aqueous; only wash explicitly deionized.'),
 ('tl-x','Thallium-exchanged zeolite X','Tl92Si100Al92O384','redox substrate/intermediate','Nominal stoichiometry.'),
 ('in-metal','Indium metal','In','redox reagent','99.999%; mass unspecified.'),
 ('h2s','Hydrogen sulfide','H2S','treatment gas','Zeolitically dried99.999%; drying method not supplied.'),
 ('ar','Argon','Ar','XPS sputtering gas','Mentioned in p5 analysis; not synthesis atmosphere.'),
 ('in87-x','Washed and redehydrated In-X','In87Si100Al92O384','parent substrate/comparison','Previousref34 defines parent; keep controls separate.'),
 ('in66-x','H2S-treated indium zeolite X','In66Si100Al92O384','current final material','Approximate nominal formula; average structure and charge-compensation uncertainty retained.'),
 ('surface-powder','Unidentified surface gray powder',None,'observed surface residue','In2O/In2S/InS/In proposed; no confirmed new material hub or recipe.'),
 ('pyrex','Pyrex',None,'capillary apparatus','Not a molecular precursor or product dopant.')]
material_records=[{'id':SID+'-'+k,'name':n,'formula':formula,'role':role,'note':note,'evidence':[ev(5,'XPS analysis') if k=='ar' else ev(2,'Experimental and parent identity')],'molecular_coordinates':None} for k,n,formula,role,note in materials]

operations=[
 ('host','prepare host for treatment','Lodge colorless~0.15mm sodium-zeolite-X octahedra in fine Pyrex capillary.',['na-x','pyrex'],'host-mounted',[2],'Host synthesis cited, not provided; crystal count/bore absent.'),
 ('exchange','dynamic ion exchange','Use0.1M aqueous thallous acetate,pH6.4; Table1 adds4days,10mL,298K.',['host-mounted','tl-acetate','water'],'tl-x',[2,4],'Flow rate and stock-volume interpretation not explicit.'),
 ('dehydrate','vacuum dehydration','Prose623K,48h,1e-6Torr; Table1 instead673K,3days.',['tl-x'],'dehydrated-tl-x',[2,4],'Unresolved temperature/time source conflict.'),
 ('redox','indium vapor contact','Contact In metal under vacuum in coaxial cylindrical ovens at reported623K; prose96h versus Table1 5days.',['dehydrated-tl-x','in-metal'],'black-in-x',[2,4],'Crystal somewhat cooler than metal; numeric reactor vacuum/mass/gradient unreported.'),
 ('wash','expose and wash','Expose one black crystal to atmosphere; wash with DI water; Table1 adds1day,10mL.',['black-in-x','water'],'washed-in-x',[2,4],'No quantitative residue-removal endpoint.'),
 ('redehydrate','vacuum dehydration','Relodge black crystal in Pyrex; prose623K,48h,1e-6Torr versus Table1 673K,3days.',['washed-in-x','pyrex'],'in87-x',[2,4],'Unresolved temperature/time source conflict.'),
 ('h2s','gas treatment','Expose redehydrated crystal to0.5atm zeolitically driedH2S for12h at673K.',['in87-x','h2s'],'treated-crystal',[2,4],'Gas quantity/flow, dryer details absent.'),
 ('evacuate','evacuate','Evacuate at treatment temperature; Table1 adds10min at673K.',['treated-crystal'],'evacuated-product',[2,4],'Final vacuum pressure not explicitly restated.'),
 ('seal','cool and seal','Seal from vacuum line at room temperature for X-ray measurements.',['evacuated-product'],'sealed-in66-x',[2],'No numerical cooling rate or long-term storage procedure.'),
 ('surface-analysis','characterization specimen handling','After X-ray measurement, expose product for EPXMA/XPS; Ar sputtering for XPS depth profile.',['sealed-in66-x','ar'],'analyzed-in66-x',[2,5],'Not part of synthesis of a colloidal dispersion; sputter history incomplete.')]
protocol={'id':SID+'-in66-x','kind':'single_reported_route_with_unresolved_prose_table_conditions','method':'Dynamic ion exchange, solvent-free redox and H2S treatment','input_host_scope':'Na-X preparationref28 remains uninspected','steps':[{'id':SID+'-'+k,'operation':a,'description':desc,'inputs':inputs,'output':out,'evidence':[ev(pg,'Experimental' if pg==2 else 'Table1' if pg==4 else 'XPS Analyses') for pg in pages],'missingness_or_conflict':note} for k,a,desc,inputs,out,pages,note in operations],'training_eligible':False}

figure_rows=[
 (1,3,'EPXMA spectra','A finalIn66-X;B parentIn87-X copiedfromref34. EDS elemental spectra, not powderXRD.','properties'),
 (2,3,'Indium3d XPS','A Inmetal reference;B In66-X;C In87-X; caption says metal spectrum intensities reducedby1/20.','properties'),
 (3,4,'XPS depth profile','Current product;~10s sputtering after each measurement at0.6angstrom/s; total4300angstrom prose gap retained.','properties'),
 (4,5,'Zeolite-X framework and site convention','Stylized background topology; depicted Si/Al alternation is not evidence of ordered finalIn66-X.','final_structures'),
 (5,7,'Supercage stereoview','Refined-model illustration with50% probability ellipsoids and partial site context; not TEM.','final_structures'),
 (6,7,'In5 in sodalite stereoview','Centered tetrahedral cluster with proposedn=7charge and final full-cavity occupancy model; not microscope image.','final_structures'),
 (7,8,'Adjacent sodalite cages','Two neighboring cluster centers in the refined model; not measured real-space microscopy.','final_structures')]
figures=[{'id':SID+'-figure-'+str(n),'number':n,'pdf_page':p,'title':title,'scope':scope,'reader_section':section,'evidence':[ev(p,'Figure'+str(n))],'asset_id':SID+'-figure-'+str(n)} for n,p,title,scope,section in figure_rows]

# Use the source PDFs directly, never regenerate a scientific plot.
boxes={
 'figure-1':(3,(87,75,520,597)), 'figure-2':(3,(87,601,520,994)),
 'figure-3':(4,(87,76,975,575)), 'figure-4':(5,(545,383,975,830)),
 'figure-5':(7,(87,78,978,388)), 'figure-6':(7,(87,399,978,708)),
 'figure-7':(8,(87,77,975,373)), 'experimental-procedure':(2,(546,269,978,1144)),
 'charge-balance-models':(8,(546,387,976,1142)),
 'references-left':(9,(86,540,523,1323)), 'references-right':(9,(546,75,978,1323))}
(P/'reader-assets').mkdir(exist_ok=True)
assets=[]
pdf=pdfium.PdfDocument(docs['main']['path'])
for name,(pg,box) in boxes.items():
 page=pdf[pg-1];im=page.render(scale=3).to_pil()
 bbox=tuple(round(v*(im.width/1063 if i%2==0 else im.height/1375)) for i,v in enumerate(box))
 out=P/'reader-assets'/(name+'.png');im.crop(bbox).save(out);page.close()
 assets.append({'id':SID+'-'+name,'path':str(out.relative_to(P)),'source_sha256':docs['main']['sha256'],'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'evidence':[ev(pg,name)],'reference_bbox':[1063,1375,*box],'original_source_render':True,'independent_visual_audit':'pending'})
pdf.close()
for role in ['main','si']:
 for n in range(1,docs[role]['page_count']+1):
  path=P/f'{role}-{n:02d}.png'
  assets.append({'id':SID+f'-{role}-page-{n:02d}','path':str(path.relative_to(P)),'source_sha256':docs[role]['sha256'],'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'evidence':[ev(n,'complete original page',role)],'original_source_render':True,'independent_visual_audit':'pending'})

refs_text=(P/'main-09.txt').read_text(encoding='utf-8').split('References and Notes',1)[1]
refs_text=re.split(r'(?m)^1128\s+J\. Phys\. Chem\. B',refs_text,maxsplit=1)[0]
references=[]
for n,raw in re.findall(r'\((\d+)\)\s*(.*?)(?=\(\d+\)|\Z)',refs_text,re.S):
 # Parenthesized journal issue numbers are not reference delimiters; patched below if extracted as duplicates.
 references.append({'number':int(n),'raw_bibliographic_text':' '.join(raw.split()),'evidence':[ev(9,'References and Notes')],'external_full_text_inspected':False})
if len(references)!=71 or len({x['number'] for x in references})!=71:
 # Actual source references start at a line boundary; journal issue numbers do not.
 references=[]
 for n,raw in re.findall(r'(?m)^\((\d+)\)[ \t]+(.*?)(?=^\(\d+\)[ \t]+|\Z)',refs_text,re.S):
  references.append({'number':int(n),'raw_bibliographic_text':' '.join(raw.split()),'evidence':[ev(9,'References and Notes')],'external_full_text_inspected':False})
assert len(references)==71 and {x['number'] for x in references}==set(range(1,72))

checkpoint=json.loads((P/'root-reading-checkpoint.json').read_bytes())
conflicts=[{'id':SID+'-source-limitation-'+str(i+1),'description':x,'disposition':'preserve original evidence and withhold dependent training labels'} for i,x in enumerate(checkpoint['major_findings']) if any(t in x.lower() for t in ['conflict','vs','versus','mismatch','not derivable','cannot','unverified','footnote','heading','623k','data/parameter'])]
gaps=[
 'Full main reading and visual SI inspection do not constitute numerical transcription/audit of every SI reflection cell. All14 original SI pages are preserved; typed reflection export remains pending.',
 'MainTable1 conflicts with prose for both dehydration temperature/duration and indium contact time. No unique resolved executable route or condition-target training pair admitted.',
 'MainTable2 represents an average structure with partial occupancies and disordered Si/Al; nominal formula, scattering representation and charge-compensation hypotheses are distinct.',
 'No CIF was supplied or generated in this pass. Space-group setting, occupancy conversion, symmetry expansion, cell composition and distances require independent validation before a derived CIF download.',
 'In66-X is an extended zeolite containing cluster array, not a free colloidal indium QD. Host crystal0.15mm and cluster radius3.5angstrom must remain separate.',
 'Upstream host synthesis and cited parent/refinement comparison sources not read; no external downloads.',
 'Source images preserve all plots, but no raw XPS/EDS numerical traces or fitted-component integrals were digitized.',
 'Final gray surface phase and charge-compensation H/O species unverified; no new sulfide material entry or defect recipe invented.',
 'No supplied TEM/SAED, Raman, optical absorption/PL, device transport or functioning storage experiment. Potential applications remain outlook.',
 'Complete reader sections, molecular/apparatus illustrations, canonical records, independent audit, integration and publication remain pending.'
]
table_path=P/'main-tables.json'
table_dependency={'path':'main-tables.json','status':'available_for_integration' if table_path.exists() else 'being_transcribed_by_separate_agent','independent_audit':'pending'}
inventory={'schema':'mattersyn-source-inventory/1','source_id':SID,'doi':'10.1021/jp0219348','title':'Spatially Ordered Quantum Dot Array of Indium Nanoclusters in Fully Indium-Exchanged Zeolite X','authors':['Nam Ho Heo','Jong Sam Park','Young Joo Kim','Woo Taik Lim','Sung Wook Jung','Karl Seff'],'journal':'Journal of Physical Chemistry B','year':2003,'volume':107,'issue':5,'pages':'1120–1128','published_online':'2003-01-08','source_documents':docs,'author':'/root','at':now,'extraction_status':'main narrative extracted; table integration and SI numerical transcription pending','materials':material_records,'protocols':[protocol],'figures':figures,'main_tables':{'count':5,'dependency':table_dependency},'supporting_tables':[{'number':1,'pdf_pages':list(range(1,15)),'printed_pages':list(range(41,55)),'title':'Observed and calculated structure factors squared with esds forIn66-X','columns':['h','k','l','Fcal^2','Fobs^2','sigma(Fobs^2)','trailing marker as printed'],'scope':'single continuous reflection table','row_count':None,'numerical_transcription_status':'pending','negative_observations_preserved':True,'all_original_pages_retained':True,'identity_note':'Header says2002J.Phys.Chem.A andHeojp0219348; manuscript code, material and main SI declaration match despite journal/year header discrepancy.'}],'chemical_equations':[{'id':SID+'-equation-'+x[0],'evidence':[ev(x[1],x[2])],'formula':x[3],'status':'author_hypothesis'} for x in equations],'mathematical_models':['weight-model','Table1 residual/goodness-of-fit formulas','Table2 anisotropic-displacement exponent'],'references':references,'assets':assets,'evidence_conflicts':conflicts,'remaining_gaps':gaps,'training_eligible':False,'published':False}
coverage={'source_id':SID,'author':'/root','at':now,'documents':[{'role':'main','sha256':docs['main']['sha256'],'pages':[{'pdf_page':n,'text_read':True,'visually_inspected':True} for n in range(1,10)]},{'role':'si','sha256':docs['si']['sha256'],'pages':[{'pdf_page':n,'visually_inspected':True,'identity_continuity_and_table_scope_checked':True,'all_numeric_cells_read_or_transcribed':False} for n in range(1,15)]}],'independent_scientific_audit':'pending','all_supplied_numerical_content_fully_extracted':False}
save('source-facts.json',{'schema':'mattersyn-source-facts/1','source_id':SID,'source_sha256':docs['main']['sha256'],'si_sha256':docs['si']['sha256'],'scope':'main narrative extraction; dedicated tables and SI reflection data remain separately tracked; no training admission','facts':facts})
save('source-inventory.json',inventory);save('page-coverage.json',coverage)
save('root-asset-manifest.json',{'source_id':SID,'assets':assets})
save('source-extraction-summary.json',{'at':now,'main_pages_read':9,'si_pages_visually_inspected':14,'si_numeric_transcription':'pending','typed_main_facts':len(facts),'materials':len(material_records),'protocol_groups':1,'operations':len(operations),'figures':7,'main_tables':5,'si_tables':1,'chemical_equations':8,'references':71,'root_assets':len(assets),'independent_audit':'pending','published':False})
(P/'extraction-notes.md').write_text('# Heo2003 source extraction in progress\n\nAll9mainpages were read and visually inspected. All14scannedSIpages were visually inspected for identity, continuity and table scope; every reflection numerical cell has NOT yet been transcribed or audited. All original pages are retained. The main narrative now has source-located typed facts, complete treatment sequence, materials, all7figures,8proposed chemical equations and71references. A separate author is transcribing all5main tables with coordinates, displacement parameters, occupancies, distances and refinement comparisons.\n\nThe source disagrees internally on dehydration temperature/time and indium-contact duration. NominalSi100Al92 is distinct from Table2Si96Al96 average-scatterer representation; partial In occupancies, proposed7+cluster charge and unobserved charge compensation prevent treating the average refinement as a unique ordered DFT structure. Metal vapor pressures are cited reference data, not reactor pressure. Surface sulfide phases are tentative.\n\nComplete numerical SI extraction, independent scientific audit, canonical records, five-section reader visuals, structure validation, integration and publication remain pending. No new exact structure-recipe pair or training admission is claimed.\n',encoding='utf-8')
print(json.dumps(json.loads((P/'source-extraction-summary.json').read_bytes())))
