import json, hashlib
from pathlib import Path
from datetime import datetime, timezone
A=Path(__file__).parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def out(n,d):
 p=A/n;p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return sha(p)
tables=[]
def tab(id,pages,columns,rows,notes=[]):tables.append(dict(id=id,pages=pages,columns=columns,rows=rows,notes=notes))
tab('main-table1',[8],['sample','A1 %','tau1 ps','A2 %','tau2 ps','A3 %','tau3 ps'],[
 ['150','95.8','0.4','4.2','47.1','',''],['180//0.7','70.9','1.5','10.6','152.7','18.5','8026.8'],['180//0.5','71.8','1.1','11.2','161.7','17.0','8525.1']],['Two empty printed cells are missing, not zero. TA fitted components; author assignments are not independently established mechanisms.'])
tab('si-tableS1',[6],['sample','space group','a A','b A','c A','V A^3','Rwp %','chi^2'],[
 ['150','Pm-3m','10.23','10.23','10.23','1072.03','2.06','2.90'],['180//0.7','R-3m','7.27','7.27','27.23','1245.89','1.54','2.23'],['180//0.5','R-3m','7.30','7.30','27.19','1255.17','1.27','1.78'],['180//0.35','R-3m','7.30','7.30','27.22','1254.61','1.57','2.22'],['200','R-3m','7.29','7.29','28.03','1289.91','2.31','3.57']],['a and b superscript footnote markers appear before Rwp/chi-squared; definitions not supplied on this page. These are author refinement parameters, not an independently verified coordinate model.'])
tab('si-tableS2',[6,7],['sample','atom','Wyckoff','s.o.f.','x','y','z','B / 10^4 pm^2'],[
 ['150','Cs1','1b','1','0.5','0.5','0.5','0.5'],['150','Mn1','1a','0','0','0','0','0.5'],['150','Cl1','3d','0','0.5','0','0','0'],
 ['180//0.7','Cs1','4b','1','0','0.25','0.625','2.97'],['180//0.7','Mn1','16f','1','0.105','0.0426','0.1323','1.6'],['180//0.7','Cl1','16f','1','0.1041','0.0521','0.369','1.64'],['180//0.7','Cl2','16f','1','0.2903','0.1539','0.1307','1.35'],['180//0.7','Cl3','4a','1','0','0.25','0.125','1.71'],
 ['180//0.5','Cs1','3a','1','0','0','0','2.01077'],['180//0.5','Cs2','6c','1','0','0','0.2185','2.00025'],['180//0.5','Mn1','3b','1','0','0','0.5','1.16154'],['180//0.5','Mn2','6c','1','0','0','0.3836','1.31244'],['180//0.5','Cl2','9e','1','0.5','0','0','2.4775'],['180//0.5','Cl1','18h','1','0.49093','0.50907','0.22447','1.61072'],
 ['180//0.35','Cs1','3a','1','0','0','0','2.01077'],['180//0.35','Cs2','6c','1','0','0','0.2185','2.00025'],['180//0.35','Mn1','3b','1','0','0','0.5','1.16154'],['180//0.35','Mn2','6c','1','0','0','0.3836','1.31244'],['180//0.35','Cl1','9e','1','0.5','0','0','2.4775'],['180//0.35','Cl2','18h','1','0.49093','0.50907','0.22447','1.61072']],['20 printed atom rows, no NCs@200 row supplied. Zero occupancies for Mn/Cl at150 are printed and must not be silently repaired. The 180//0.7 Wyckoff/coordinate block does not establish a verified R-3m model. 180//0.5 and0.35 share numbers while Cl1/Cl2 row labels exchange.'])
tab('si-tableS3',[7],['sample','Mn:Cs'],[['150','0.98 ± 0.11'],['180//0.7','1.02 ± 0.13'],['200','1.02 ± 0.11'],['180//0.5','1.04 ± 0.14'],['180//0.35','0.99 ± 0.12']],['These are measured product ICP-MS ratios, separate from nominal precursor ratios.'])
tab('si-tableS4',[9],['row group','sample setting','absorption peak nm','Eg eV','PL peak nm','FWHM nm'],[
 ['injection temperature degC','150','275','4.8','-','-'],['injection temperature degC','180','280','5.0','670','97'],['injection temperature degC','200','280','5.0','670','97'],['Mn:Cs ratio','0.7','280','5.0','670','97'],['Mn:Cs ratio','0.5','280','5.0','670','97'],['Mn:Cs ratio','0.35','282','5.0','670','97']],['Setting labels are contexts, not six independent certified batches. Dashes mean no reported emission value, not zero wavelength.'])
tab('si-tableS5',[10],['transition or parameter','printed value'],[['6A1 -> 4T1(G)','18868'],['6A1 -> 4T2(G)','22371'],['6A1 -> 4A1,4E(G)','23810'],['6A1 -> 4T2g(D)','26882'],['6A1 -> 4E(D)','28011'],['6A1 -> 4T1(P)','29940'],['Delta/B','11.18'],['B','770'],['Delta','8601']],['Printed common heading is Wavenumber cm^-1; Delta/B is semantically a dimensionless ratio. Transition assignment and calculated parameters are author interpretation.'])
tab('si-tableS6',[10],['excitation nm','A1 %','tau1 us','A2 %','tau2 us','tauavg us'],[
 ['280','85.63','182.7','14.37','397.4','240.12'],['330','86.48','185.6','13.52','415.3','245.13'],['355','89.14','195.3','10.86','405.4','237.71'],['370','88.85','194.1','11.15','414.1','240.56'],['420','87.56','189.0','12.44','417.2','243.50'],['445','83.83','184.1','16.17','388.5','243.23'],['530','86.14','181.8','13.86','407.3','241.55']],['Printed equation tauavg=sum(A_i*tau_i) does not reproduce the printed mean values using A fractions; preserve both. Source assigns component1 non-radiative/component2 radiative; do not promote as independent mechanism. Table330 conflicts with FigureS5 legend335.'])
out('independent-table-transcription.json',{'reviewer':'/root/norberg2004_extract','basis':'Manual source-page reading and visual comparison before author extraction opened; strings preserve displayed precision and blanks.','tables':tables})
page_notes={
 'main-01':'Title/byline/DOI pair. Abstract claims cubic nonemissive vs rhombohedral670nm40%QY; DFT/STE interpretation and LSC proof. Introduction literature efficiencies belong to cited work, not current samples.',
 'main-02':'All materials and complete reported stock/synthesis/purification methods read. Cs2CO3407mg+ODE18mL50mLthree-neck;120C1h,OA1.74mL and extra15min ambiguous wording,150C dissolve;vacuumstorage. Preheatstock≥30min120C then150CAr. MnCl2156mg+ODE10/OA2/OlAm2mL25mLthree-neck,120C1.5h vacuum,150/180/200CAr;2/3/4mLstock correspond source Mn/Cs.7/.5/.35;5s growth then icewater.8550rpm5min without antisolvent;discard supernatant,vacuumovernight retained solids,hexane. Failed washing controls separate from MeOAc1:1 successful precipitation. XRD/TEM/optical/stability acquisition read.',
 'main-03':'TA300nm/~150fs;ICP-MS acid digestion2%HNO3/0.001–1000ugL standards;LTPL30–293K20K steps380nm;DFTHSE06ZORA and grids6^3/3^3;LSC geometry2x.15cm edge/2x2cm photodiode/1.6cm spot/~9.5mW/-5to+.5V. Figure1 process sketch/equation and photos;below150 noNC but unspecified test values.',
 'main-04':'Figure2 all XRD fits/reference sticks and source structure illustrations. Caption swaps actual reference phases a/h, mistypes reference code and iodide; plots show chloride. Figure3 distinct180//.5 TEM50/10nm,SAED10nm^-1,13.4±.9nm. Octahedra and ICP claims qualified.',
 'main-05':'Morphology/size interpretation and Figure4 absorbance/PL/PLE/QY/TRPL read. Main3.9nm called rod length versus SI diameter;Figure3uncertainty.9 vs prose1.0. Highest420nmQY40%;PL670/97nm,exciton280nm;c275. Figure4c saysCs/Mn unlike sourceMn/Cs. Distortion formula7.8%;DFT model scopes.',
 'main-06':'Figure5 DFT bands/PDOS/selected wavefunctions, not measured spectra/coordinates. Cubicindirect5.18,direct5.37,unoccupied3d5.95eV. Rhombohedraldirect5.35/5.37eV plot labels. Spin-up/spin-down and Cs/Cl/Mn density scopes.',
 'main-07':'Source considers defects/STE and admits mechanism remains unclarified. B770cm^-1/.095eV,Delta8601cm^-1/1.06eV. r size10.8–15.5nm prose differs measured histogramvalues. QY40/12/24% versusMnMn3.52/3.13/3.17A. Figure6 TA distinct150/.7/.5 specimens,300nm80uW,445/550nm traces.',
 'main-08':'MainTable1 transcribed. TA lifetime components<2ps/<200ps/>8ns author assignments. LTPLfilm655RT->~680110K->673below100K;Arrhenius100–300K100±18meV;FWHM69to52meV stated293to50K. Stability filmXRD vs hexanePL distinct.',
 'main-09':'Figure7 temperature traces and fitI026.8/A96.7/Rsquare.96/Eb100meV;warming acquisition sequence distinct narrativecooling. Figure8r XRD0/1/3/5/8/10/12weeks,source PL >70%1week/50%20d/5%55d versus plotted ~.15 at55d;no exact digitized dataset. Ligand loss/agglomeration proposed.',
 'main-10':'Figure9LSC bareglass/fresh/11weeks/dark curves;~order abovebareglass/~4orders abovedark and3foldage drop are author descriptions. NC surfacefilm no stated encapsulating matrix. SI declaration matches supplied PDF;no attached CIF declared.',
 'main-11':'Author affiliations/correspondence/acknowledgments and first references; no new own protocol. References are citations, their full texts not read.',
 'main-12':'References continued through55, complete bibliographic text reviewed. No additional own synthesis recipe.',
 'main-13':'Publisher footer/advertisement, not scientific experiment or material data.',
 'si-01':'SI title has The prefix but exact DOI-topic/byline pairing;allauthors matchmain.',
 'si-02':'Affiliations and contents S3synthesis,S4TEM,S6refinement,S8optical,S13stability.',
 'si-03':'FigureS1 source photos precursor/quench/isolatedNCs/unisolatedNCs degraded after1h inair.',
 'si-04':'FigureS2 all12TEM/SAED panels;50nm/10nm/10nm^-1 bars. Rowc center is labelledc3/rightc2 despite captiongeneric x2/x3. Lastrowd captioncalls(e). Separate150/200/180//.7/180//.35.',
 'si-05':'S2captioncontinuation and S3fourhistograms:1503.9±.9;180//.7 11.0±1.0;20010.8±.8;180//.35 13.4±.8nm. Caption150rod diameter vs mainlength.',
 'si-06':'TablesS1/S2 firstpart allcells transcribed. Zero occupancies150Mn/Cl and inconsistent180//.7 Wyckoff block retained; no unitcell generation qualification.',
 'si-07':'S2continuation complete .5/.35 coordinateblocks and ICPTableS3. No200coordinates supplied. Identicalvalues for .5/.35 do not prove identical measured specimen.',
 'si-08':'FigureS4absorption/Tauc/TRPL/PL. a/c/d use1:3/1:4 legends versusb.5/.35;preserve uncertainty. RightTauc axis unit exponent1/2 versus displayed quantity^2, leftunitexponent2; no silently corrected trace assignment.',
 'si-09':'FigureS5all7excitation spectra/TRPL,monitor670nm;335nmlegend vsTableS6 330. TableS4all6rows,150dashes and.35abs282nm.',
 'si-10':'TablesS5/S6allcells/equations reviewed. Delta/B dimensionless despite sharedcm^-1header. Average-lifetimeformula inconsistent withvalues;fitcomponentphysicalassignment author-only.',
 'si-11':'FigureS6NC180//.7 TA300/370/420nm,600nm monitor,ps time. No invented numeric series;absenceclaimscoped.',
 'si-12':'FigureS7FWHM plot explicitly meV,380nmexcitation. Lowestplottedpoint~70K althoughmain prose mentions50K;no invented exact table.',
 'si-13':'FigureS8fresh/agedcubic fit,aged88.1%CsCl4.5%Cs3MnCl5 7.4%CsMn4Cl9,initial100%cubicauthorrefinement. S9agedrTEM50nm/20nm,25C/RH~40/dark;no explicitage nor .5link inS9caption.'
}
notes={
 'title':'Role of CsMnCl3 Nanocrystal Structure on Its Luminescence Properties', 'doi':'10.1021/acsanm.2c04342','author':'Matuhina et al.','year':2023,
 'reviewer':'/root/norberg2004_extract','status':'independent_complete_source_reading_before_author_comparison','created_at':datetime.now(timezone.utc).isoformat(),
 'scope':'All13main+13SI pages actually visually inspected and text read; separate extraction package not opened. This is reading evidence, not final extraction approval.',
 'page_notes':page_notes,
 'critical_boundaries':[
 'Only five demonstrated primary sample labels; do not invent a complete3x3temperature/ratio factorial or independent replicate IDs.',
 'Reported loading ratios are source labels; no reported final stock volume/concentration permits silently replacing them from nominal charges.',
 'Five synthesis sample families do not prove that every measurement uses the same physical batch; XRDfilm,TEMgrid,hexanesolution,LTPLsilicafilm,LSCglassfilm,DFTmodel remain contexts.',
 'All recipes/control purifications share only explicitly inherited stages. Failed antisolvent tests cannot be mixed into successful workup.',
 'Source refinement coordinates have defects; no CIF verified or exactstructure-recipe training pair approved.',
 'Author theoretical/kinetic/STEmodel assignments and cited-literature values remain separate from measurements.',
 'S2zero occupancies and unusualWyckoff,missing200coordinates,caption/ratio/size/lifetimeformula conflicts retained.',
 'No source-derived numeric values altered from physical expectations or conventional formulas.'
 ], 'table_transcription_sha256':sha(A/'independent-table-transcription.json')
}
inputs=json.loads((A/'reading-inputs.json').read_text())
bound=[]
for x in inputs['original_copies']:
 assert sha(x['path'])==x['sha256'];bound.append(x)
for d in inputs['documents']:
 for p in d['pages']:
  assert sha(p['render'])==p['render_sha256']
  for path in [Path(p['render']),A/'audit-text-normal'/f"{d['role_candidate']}-{p['page']:02}.txt"]:
   bound.append({'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size})
notes['bound_files']=bound
out('independent-reading-notes.json',notes)
md=['# Independent source reading — Matuhina2023','',notes['scope'],'','All four source-copy hashes verified before and after reading.','']
md += [f'- **{k}:** {v}' for k,v in page_notes.items()]
md += ['','## Boundaries','']+[f'- {v}' for v in notes['critical_boundaries']]
(A/'independent-reading-notes.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
print(json.dumps({'reading_notes_sha256':sha(A/'independent-reading-notes.json'),'tables_sha256':sha(A/'independent-table-transcription.json'),'pages':26,'tables':len(tables),'table_rows':sum(len(t['rows']) for t in tables)},indent=2))
