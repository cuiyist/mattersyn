"""Executed in build_records authoring namespace; all values linked to source compound classes."""
r=records[-1]
NMR={
 '1':[('6.0-7.3','m,4H,aromatic'),('8.6-9.1','m,1H,OH')],
 '2a':[('6.0-7.7','m,4H,aromatic'),('2.2','s,3H,CH3')],
 '2b':[('6.0-7.7','m,4H,aromatic'),('2.5','br,2H,alpha-CH2'),('1.6','br,2H,beta-CH2'),('0.95','br,3H,CH3')],
 '2c':[('6.4-9.5','m,aromatic; integral not tabulated')],
 '2d':[('6.4-8.2','m,aromatic; integral not tabulated')],
 '2e':[('6.4-7.3','m,4H,aromatic'),('2.5','br,2H,alpha-CH2'),('1.7','br,2H,beta-CH2'),('1.2-1.5','br,12H,aliphatic'),('0.91','br,3H,CH3')],
 '3a':[('8.4','s,1H,ImC2'),('7.7','s,1H,ImC4'),('7.1','s,1H,ImC5'),('2.2','s,3H,CH3')],
 '3b':[('8.4','s,1H,ImC2'),('7.7','s,1H,ImC4'),('7.1','s,1H,ImC5'),('3.1','t,2H,alpha-CH2'),('1.8','m,2H,beta-CH2'),('1.0','t,3H,CH3')],
 '3c':[('8.2-8.5','m,10H,ImC2+pyrene'),('7.8','s,1H,ImC4'),('7.2','s,1H,ImC5')],
 '3d':[('8.2','s,1H,ImC2'),('7.7','s,1H,ImC4'),('7.2','s,1H,ImC5'),('7.8','d,2H,phenyl2,6'),('7.6','m,2H,phenyl3,5'),('7.7','s,1H,phenyl4'),('2.6','s,3H,CH3; anomalous printed entry for benzoyl compound, unresolved')],
 '3e':[('8.4','s,1H,ImC2'),('7.7','s,1H,ImC4'),('7.0','s,1H,ImC5'),('3.0','t,2H,alpha-CH2'),('1.7','m,2H,beta-CH2'),('1.2-1.4','br,12H,aliphatic'),('0.9','t,3H,CH3')]
}
IR={
 '1':[('3301','s,vbr,O-H stretch'),('1870','w,1,4-disubstituted phenyl overtone'),('1730','w,1,4-disubstituted phenyl overtone'),('1636','m'),('1598','s'),('1488','s,ring C=C'),('1429','s'),('1359','m'),('1170','s,br,phenyl-O'),('1088','m'),('1009','m,phenyl-S'),('819','s,phenyl C-H out-of-plane'),('634','m'),('510','m')],
 '2a':[('3400','w,vbr,residual OH'),('3060','w,aromatic C-H stretch'),('2931','w,aliphatic C-H stretch'),('1486','s,ring C=C'),('1758','vs,C=O stretch'),('1582','w'),('1427','w'),('1369','s'),('1223','s,br,phenyl-O'),('1085','m'),('1013','s,phenyl-S'),('911','w'),('840','m'),('820','m,phenyl C-H out-of-plane'),('797','w'),('510','m')],
 '2b':[('3375','vw,vbr,residual OH'),('3090','w,aromatic C-H stretch'),('2965','m,br,aliphatic C-H stretch'),('2934','w,shoulder,aliphatic C-H stretch'),('2875','w,aliphatic C-H stretch'),('1751','vs,C=O stretch'),('1580','vw'),('1539','vw'),('1485','vs,ring C=C'),('1245-1203','vs,br,phenyl-O'),('1167','vs'),('1080','m'),('1013','m,phenyl-S'),('836','w,phenyl C-H out-of-plane'),('749','vw'),('653','vw'),('510','w')],
 '2c':[('3129','w,aromatic C-H stretch'),('3047','w,aromatic C-H stretch'),('2973','w,aromatic C-H stretch'),('1720','s,C=O stretch'),('1583','m'),('1490','vs,ring C=C'),('1364','m'),('1234','s,br,phenyl-O'),('1205','shoulder'),('1167','shoulder'),('1066','m'),('842','s'),('818','s,phenyl C-H out-of-plane'),('748','w'),('712','w'),('645','w'),('511','w')],
 '2d':[('3400','vw,vbr,residual OH'),('3060','w,aromatic C-H stretch'),('3033','w,aromatic C-H stretch'),('1736','vs,C=O stretch'),('1673','m'),('1600','w'),('1485','s,ring C=C'),('1451','m'),('1269','vs,br,phenyl-O'),('1201','vs'),('1166','s,shoulder'),('1061','s'),('1013','m,phenyl-S'),('902','w'),('876','w'),('822','w,phenyl C-H out-of-plane'),('705','vs,sharp,monosubstituted phenyl C-H out-of-plane'),('686','vs,sharp,monosubstituted phenyl C-H out-of-plane'),('634','vw'),('511','m')],
 '2e':[('3060','vw,aromatic C-H stretch'),('2925','s,aliphatic C-H stretch'),('2852','s,br,aliphatic C-H stretch'),('1754','s,C=O stretch'),('1579','w'),('1537','w'),('1486','s,ring C=C'),('1458','m'),('1377','w'),('1170-1081','s,br,many bands'),('1012','m,phenyl-S'),('915','w'),('840-802','w,br'),('736','vw'),('510','m')]
}
def position(v,u,e,basis=''):
 if '-'in v:
  a,b=map(float,v.split('-'));return Q(u=u,e=e,minimum=min(a,b),maximum=max(a,b),raw_text=v,basis=basis)
 return Q(float(v),u,e=e,raw_text=v,basis=basis)
for c,peaks in NMR.items():
 solvent='CDCl3'if c=='2e'else'DMSO-d6'if c=='1'or c.startswith('2')or c=='3e'else'NMR solvent not independently specified for this molecular precursor'
 for j,(pos,assignment)in enumerate(peaks,1):
  V(r,c+'-nmr-'+str(j),'compound-'+c,'proton_nmr_chemical_shift',position(pos,'ppm',T1,'Reported assignment: '+assignment),'400 MHz proton NMR',T1+SPEC+ (E(4,'Figure2')if c=='3e'else[]),solvent+'; '+assignment+'. Table1 assignments retained even where Results prose reverses ImC4/C5. No fabricated raw spectrum.')
for c,peaks in IR.items():
 for j,(pos,assignment)in enumerate(peaks,1):
  V(r,c+'-ir-'+str(j),'compound-'+c,'infrared_band_wavenumber',position(pos,'cm^-1',T2,'Source intensity/assignment: '+assignment),'FTIR, KBr pellet',T2+SPEC,'Mattson3000; '+assignment+'. Legend:vs very strong;s strong;m medium;w weak;vw very weak;br broad;vbr very broad. Unassigned peaks remain unassigned.')
for c,conv in zip(['2a','2b','2c','2d','2e'],[95,97,95,100,100]):
 V(r,c+'-conversion','compound-'+c,'surface_phenol_esterification_conversion',Q(conv,'%',e=T1+E(5,'NMR integration'),status='author_derived',basis='Estimated from residual OH to aromatic proton integration; not isolated yield'),'Proton NMR integration',T1+E(5,'Conversion determination'),'Compound-class value; no precise replicate or isolated batch mapping. Table reports100% without a detection limit.')
 V(r,c+'-reaction-time','compound-'+c,'source_reported_reaction_duration',Q(30,'min',e=T1),'Table1 preparation condition',T1,'Source table reaction duration; same information as route, not an independent repeated experiment.')
for c,yieldpc,mins in [('3a',100,30),('3b',50,15),('3c',65,30),('3d',100,15),('3e',100,30)]:
 V(r,c+'-yield','compound-'+c,'reported_molecular_precursor_yield',Q(yieldpc,'%',e=T1,basis='Molecular precursor yield; basis not fully defined in Table1'),'Source Table1 yield',T1,'Not surface esterification conversion; isolated mass unreported.')
 V(r,c+'-reaction-time','compound-'+c,'source_reported_reaction_duration',Q(mins,'min',e=T1),'Table1 preparation condition',T1,'Overall tabulated reaction duration; stage-specific heating allocation unknown.3b conflicts with common30min prose.')
for c,lam,cal,tem in [('1',390,24,30.4),('2a',400,25,27.3),('2b',420,27,24.7),('2c',None,None,26.3),('2d',350,19,28.2),('2e',420,27,28.2)]:
 if lam is not None:V(r,c+'-absorption','compound-'+c,'absorption_onset_wavelength',Q(lam,'nm',e=T3,basis='CdS band-to-band absorption as Table3 footnote'),'UV–visible absorption',T3+SPEC,'QDOH in methanol; esters in CHCl3.2c is masked by pyrene bands and has no assigned CdS onset.')
 else:V(r,c+'-pyrene-absorption','compound-'+c,'pyrene_absorption_range',Q(u='nm',e=T3,minimum=356,maximum=420,basis='Pyrene pi–pi* transitions; not CdS band-to-band onset'),'UV–visible absorption',T3+SPEC,'CHCl3; strong ligand absorption prevents optical core-size assignment.')
 V(r,c+'-model-diameter','compound-'+c,'tight_binding_derived_cluster_diameter',Q(cal,'angstrom',e=T3,status='author_derived'if cal is not None else'not_reported',basis='Author tight-binding interpretation, ref13; Table3 refers to Eq1 but no numbered equation is supplied'),'Author optical/tight-binding estimate',T3+E(6,'Optical-derived diameter discussion'),'Model-derived; not measured atomic structure or TEM size. Table blank for2c stays missing.')
 V(r,c+'-tem-diameter','compound-'+c,'tem_mean_cluster_diameter',Q(tem,'angstrom',e=T3),'Transmission electron microscopy',T3+TEM,'Compound-class tabulation; no measurement count or per-variant uncertainty supplied in table.')
e=E(2,'QDOH product spectroscopy')
V(r,'1-methods-edge','compound-1','source_reported_absorption_edge',Q(295,'nm',e=e,basis='Methods value conflicts with Table3/body390nm'),'UV–visible, Methods report',e,'Solvent not explicitly repeated in this product listing. Retained without replacing Table3 value.')
V(r,'1-methods-shoulder','compound-1','source_reported_absorption_shoulder',Q(305,'nm',e=e),'UV–visible, Methods report',e,'Separate reported feature; no digitization ofFigure5.')
for pos,assignment in [(3302,'strong broad OH'),(1870,'weak ring overtone'),(1734,'weak ring overtone'),(819,'strong ring CH')]:V(r,'1-methods-ir-'+str(pos),'compound-1','source_reported_ir_wavenumber',Q(pos,'cm^-1',e=e,basis=assignment),'IR, KBr pellet; Methods listing',e,'Source repetition retained with source-specific values; not an independent replicate.3302versusTable23301;1734versusTable21730.')
e=E(4,'QDOH NMR/IR discussion')
V(r,'1-oh-exchange','compound-1','hydroxyl_resonance_after_d2o',F('8.6–9.1ppm resonance vanishes after one dropD2O',e),'Proton NMR exchange comparison',e,'Figure1a/b: sameQDOHspecimen before/after exchange; all esters are not claimed to undergo this test.')
V(r,'1-nmr-integration','compound-1','aromatic_to_hydroxyl_integration_ratio',Q(4,'',e=e,basis='4:1 aromatic-to-OH integral ratio'),'Proton NMR integration',e)
V(r,'1-sh-absence','compound-1','thiol_stretch_observation',F('No characteristic S–H stretch near2580cm^-1',e),'FTIR',e,'Supports sulfur-bound thiolate interpretation; no numerical zero concentration or detection limit.')
V(r,'1-phenol-ir-body','compound-1','source_assigned_phenolic_deformation_band',Q(1013,'cm^-1',e=e,basis='p4 calls phenolic O–H deformation; Table2assigns1009/1013phenyl-S andp5discussesS-coupled mode'),'FTIR, author assignment',e,'Assignment conflict preserved; not independently corrected.')
for loc,value in [(E(2,'QDOH yield interpretation'),20),(E(3,'Gravimetric cap estimate'),34)]:V(r,'1-thiol-sulfur-'+str(value),'compound-1','author_estimated_thiol_contribution_to_sulfur',Q(value,'mol%',e=loc,status='author_derived',basis='Assuming quantitative yield based on sulfide; conflicting source estimates20and34%'),'Author gravimetric model',loc,'Neither value is direct elemental-analysis measurement in this paper.')
e=E(4,'Gravimetric surface coverage calculation')
for i,prop,v,u in [('density','assumed_core_specific_gravity',4.8,''),('caps','estimated_caps_per_cluster',130,'caps'),('coverage','estimated_surface_area_per_cap',22,'angstrom^2/cap'),('sphere-area','model_sphere_surface_area',2827,'angstrom^2'),('model-d','model_cluster_diameter',30,'angstrom')]:
 V(r,'1-'+i,'compound-1',prop,Q(v,u,e=e,status='author_derived',approximate=i=='caps',basis='Author gravimetric spherical-cluster model; not measured atom count'),'Author surface-coverage model',e)
e=E(5,'Figure5 and optical band-edge discussion')
for i,prop,v,u in [('molarity','figure5_reported_molarity',1e-4,'M'),('gap','optically_estimated_band_gap',3.19,'eV'),('bulk-gap','bulk_cds_reference_band_gap',2.53,'eV'),('shift','quantum_confinement_energy_shift',.66,'eV')]:
 V(r,'1-'+i,'compound-1',prop,Q(v,u,e=e,status='reported'if i=='molarity'else'author_derived',basis='Molarity basis unspecified; do not infer particle concentration'if i=='molarity'else'Author band-edge analysis; bulk reference is not a measured sample value'),'UV–visible caption'if i=='molarity'else'Author optical interpretation',e,'QDOHmethanol1cm; originalFigure5preserved.')
e=E(6,'TEM discussion, Figure6 and Note15')
V(r,'1-tem-uncertainty','compound-1','reported_tem_diameter_uncertainty',Q(7,'angstrom',e=e,raw_text='30.4 ± 7 Å (reference15)',basis='Type of ±7 uncertainty not defined; Note15says precision limited by microscope resolution'),'TEM, author histogram summary',e,'Not assigned as SD/SE; no histogram arrays supplied.')
V(r,'1-aggregate-body','compound-1','source_described_aggregate_dimension',Q(1100,'angstrom',e=e,basis='Body calls the Figure6aggregate1100angstrom; preserve discrepancy with illustrated6nm scale'),'Source TEM discussion',e,'Aggregate dimension, not nanocluster mean. No independent image-size recalibration.')
V(r,'1-figure6-scale','compound-1','figure6_scale_bar',Q(6,'nm',e=E(6,'Figure6 image')),'Original TEM image scale annotation',E(6,'Figure6 image'),'Image annotation; not a new particle diameter.')
V(r,'1-tyndall','compound-1','colloidal_dispersion_observation',F('Transparent nonopalescent DMSO suspension under ambient light; pronounced Tyndall effect in a He–Ne laser beam',E(2,'QDOH redispersion')),'Qualitative optical observation',E(2,'QDOH redispersion')+E(3,'Note10'),'No scattering intensity, turbidity coefficient or laser power supplied.')
solub={'1':{'dmso':True,'dmf':True,'methanol':True,'ethanol':True,'water':False,'ether':False,'hexane':False,'chloroform':False},'2a':{'chloroform':True,'lower-alcohols':False,'acetone':False,'ether':False},'2b':{'chloroform':True,'lower-alcohols':False,'acetone':True},'2c':{'chloroform':True,'lower-alcohols':False},'2d':{'chloroform':True,'lower-alcohols':False,'acetone':False,'ether':False},'2e':{'chloroform':True,'lower-alcohols':False,'acetone':True,'ether':True,'dmso':False}}
for c,solvents in solub.items():
 for solv,yes in solvents.items():
  e=(E(3,'Solubility and Note10')if c=='1'and solv!='chloroform'else E(6,'Solubility discussion'))
  V(r,c+'-solubility-'+solv,'compound-'+c,'qualitative_colloidal_solubility_in_'+solv,F('Reported soluble'if yes else'Reported insoluble / solubility absent',e),'Qualitative colloidal dispersion behavior',e+E(3,'Note10'),'Soluble means stable clear transparent colloidal suspension: no settling, not separated by conventional centrifugation, Tyndall effect. No equilibrium solubility concentration or quantitative detection threshold. Ether explicitly called diethyl ether in p6 discussion; generic workup ether separately retained.')
for key,label in [('qdoh','QDOH preparation')]+[('ester-2'+x,'Ester2'+x+' preparation')for x in'abcde']+[(x,x+' analytical preparation')for x in['nmr','ftir','uv-visible','tem']]:link(r,key,label,'Compound-class or methodological source linkage, not evidence of a uniquely identified physical batch.')
r['quality']['conflicts']=[
 'QDOHMethods lists295nm edge/305nm shoulder;Table3andbody assign390nm band-to-band onset.',
 'Thiol contribution to sulfur20mol% inMethods versus34mol% inResults under the same gravimetric assumption.',
 'QDOHOH3302cm^-1 Methods versus3301Table2; ring overtone1734Methods/prose versus1730Table2.',
 'Table1ImC4/C5assignments7.7/7.1ppm differ fromp5general discussion7.0/7.7ppm.',
 'Table13dbenzoylimidazole includes2.6ppm3HCH3; no impurity or correction inferred.',
 'Table32d optical-derived diameter19Å and other19–27Å values are not identical to24ÅQDOH despite general prose saying unchanged.',
 'Table3referencesEq1 but none is printed in the supplied six pages.',
 'Figure6body aggregate1100Å appears inconsistent with the6nm scale annotation; neither is silently repaired.',
 'QDOH1013cm^-1 phenolic deformation assignment in p4 differs from Table2phenyl-S / p5S-coupled band discussion.',
 'Source molecular precursor3breaction duration15min inTable1 differs from common30min preparation.'
]
r['quality']['missing_fields']+=['Original figures retained but no raw digital spectra, peak-fitting uncertainty, TEM counting statistics or measured crystal coordinates supplied.','Compound identity does not prove same physical optical, IR, NMR and TEM aliquot.','QDOHCHCl3TEMsuspension is not the stable colloidal solubility defined inNote10.','No SAED, XRD, Raman or quantified photoluminescence data supplied in this article.']
