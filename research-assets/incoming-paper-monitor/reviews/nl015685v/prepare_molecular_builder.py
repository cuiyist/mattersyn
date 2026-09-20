from pathlib import Path
B=Path(__file__).resolve().parent;P=B.parent/'jp010002l'
s=(P/'build_molecular_assets.py').read_text(encoding='utf-8')
s=s[:s.index('cards=[')]
s=s.replace("DOI='10.1021/jp010002l';SH='00ac817e60651f0e7f9faabe85ba18372ac37fea1f0f5d174779c982064b4184'","DOI='10.1021/nl015685v';SH='9f1b5b781e7a36f1ec109eb14ee724bb6c99a8156b4bc6899cfffe8ab613c357'")
start=s.index('definitions=[');end=s.index('\nfor id,name,smi',start)
s=s[:start]+'''definitions=[
 ('tetraethyl-orthosilicate','Tetraethyl orthosilicate (TEOS)','CCO[Si](OCC)(OCC)OCC','C8H20O4Si','Si(OC2H5)4',True,'Free TEOS molecule; acid-catalyzed hydrolyzed and condensed silica species have no unique molecular geometry here.'),
 ('cetyltrimethylammonium-bromide','Cetyltrimethylammonium bromide (CTAB)','CCCCCCCCCCCCCCCC[N+](C)(C)C.[Br-]','C19H42BrN','C19H42NBr',False,'Conventional CTAB cation and bromide connectivity. Ion placement is a 2D layout, not an ion-pair distance, micelle shape or crystal packing.'),
 ('cadmium-nitrate-hydration-unspecified','Cadmium nitrate (hydration unspecified)','[Cd+2].[O-][N+](=O)[O-].[O-][N+](=O)[O-]','CdN2O6','Cd(NO3)2',False,'Cadmium and nitrate formula-unit connectivity. The source does not identify a hydrate; hydration, coordination and solution complexation are not assigned.')]
'''+s[end:]
s=s.replace("('Thiol','[S;H1]',(.87,.67,.18)),", "('Quaternary ammonium','[N+](C)(C)(C)C',(.45,.55,.86)),('Nitrate ion','[O-][N+](=O)[O-]',(.87,.67,.18)),")
s+='''
cards=[
 ('identity-besson-acid','Unspecified acid for the water at pH 1.25',None,'unresolved-identity',['Acid identity unreported','Water adjusted to pH 1.25','No HCl or other acid assumed'],'Water pH is reported; the acid identity, dose and final mixed-sol pH are not supplied.'),
 ('identity-besson-citrate','Sodium citrate (form unspecified)',None,'unresolved-identity',['Sodium citrate','Citrate complexing reagent','Protonation / hydration unspecified'],'The source names sodium citrate without identifying protonation or hydrate. No sodium stoichiometry, unique formula or coordination geometry is imposed.'),
 ('identity-besson-pyrex','Pyrex glass slide',None,'support',['Pyrex slide','Film substrate','Glass formulation unspecified'],'Solid glass support, not a molecular compound. No measured glass structure or precise formulation is provided.'),
 ('identity-besson-silicon','Silicon wafer','Si','support',['Silicon wafer','PL specimen substrate','Orientation / doping unreported'],'Silicon support used to avoid Pyrex luminescence. The source does not specify orientation, doping or measured atomic coordinates.'),
 ('identity-besson-copolymer','Unspecified triblock copolymer',None,'unresolved-identity',['Triblock copolymer','Larger-pore template','Block chemistry / mass unreported'],'The preliminary larger-pore film uses an unnamed triblock copolymer. P123, block lengths, molar mass and templating dose are not inferred.'),
 ('identity-besson-silica-sol','Polymeric silica sol',None,'mixture',['TEOS-derived silica sol','Water + ethanol','Hydrolysis / condensation mixture'],'The source describes a polymeric silica sol; no unique oligomer or molecular structure is assigned. TEOS, water and ethanol have separate reference structures.'),
 ('identity-besson-ctab-sol','CTAB-containing silica coating sol',None,'mixture',['CTAB + polymeric silica sol','Ethanol dilution','Templating mixture'],'Coating solution contains surfactant and hydrolyzed/condensed silica species. No micelle structure or condensed oligomer formula is measured.'),
 ('identity-besson-loading-solution','Cadmium nitrate / citrate / ammonia solution',None,'mixture',['Cd nitrate + citrate + NH₃','Aqueous loading solution','pH 9.5; complexes unresolved'],'The source specifies starting solution and additives but no exact Cd complex stoichiometry, equilibrium speciation or final Cd concentration after additions.'),
 ('identity-besson-film-specimens','Separate porous-film specimens',None,'specimen',['Separate silica-film specimens','Blank / Cd-loaded / CdS-loaded','Comparison set; not a mixture'],'Comparison context only. Empty, ion-impregnated and CdS-loaded films remain separate specimen states; method assignment does not establish batch identity.'),
 ('identity-besson-cds-colloid','CdS colloidal optical comparator','CdS','specimen',['CdS colloidal comparator','Optical loading reference','Cited reverse-micelle preparation'],'The source uses a CdS colloid as an optical loading comparator. Its cited reverse-micelle recipe is not supplied in the inspected article; no invented reagent inventory or new complete route.'),
]
for id,name,formula,kind,rows,caption in cards:
 e=base(id,name,formula,kind,caption)
 svg='<svg xmlns="http://www.w3.org/2000/svg" width="900" height="360" viewBox="0 0 900 360"><title>'+html.escape(name)+'</title><desc>'+html.escape(caption)+'</desc><rect x="18" y="20" width="864" height="320" rx="20" fill="#f1f6f9" stroke="#cbdce6"/>'
 for y,row,size in zip([120,199,263],rows,[29,22,19]):svg+=f'<text x="450" y="{y}" text-anchor="middle" font-family="Arial,sans-serif" font-size="{size}" fill="#294451">{html.escape(row)}</text>'
 svg+='</svg>'; (O/e['svgPath']).write_text(svg,encoding='utf-8');e['assetHashes']={'svgPath':sha(O/e['svgPath'])};entries.append(e)
for suffix,name,formula,filled,rows in [
 ('empty-film','Calcined mesoporous silica film','SiO2',False,['Open mesopores in silica','Mesoscopic periodic arrangement','Atomic silica structure unreported']),
 ('cd-loaded-film','Cadmium-ion-loaded mesoporous silica film',None,False,['Adsorbed cadmium species','CdS not yet precipitated','Cd coordination unresolved']),
 ('ctab-cds-film','CdS in CTAB-templated silica film','CdS/SiO2',True,['CdS inside silica mesopores','Ordered nanoparticle arrangement','CdS atomic fringes: blende-type 111']),
 ('copolymer-cds-film','CdS in copolymer-templated silica film','CdS/SiO2',True,['CdS inside larger silica pores','Template chemistry unreported','Not an independently refined lattice'])]:
 id='identity-besson-'+suffix;caption='Mesoscopic arrangement schematic, not to scale and not measured atomic coordinates. Host-pore symmetry and dimensions are distinct from CdS atomic phase; the paper supplies no atomic CIF or unique particle reconstruction.'
 e=base(id,name,formula,'specimen',caption)
 svg='<svg xmlns="http://www.w3.org/2000/svg" width="900" height="420" viewBox="0 0 900 420"><title>'+html.escape(name)+'</title><desc>'+html.escape(caption)+'</desc><rect x="10" y="12" width="880" height="396" rx="24" fill="#f5f9fb"/><rect x="55" y="76" width="293" height="217" rx="9" fill="#d8e8ee" stroke="#6d93a5"/>'
 for j in range(4):
  for i in range(5):
   x=82+i*52+(j%2)*16;y=108+j*50
   svg+=f'<circle cx="{x}" cy="{y}" r="18" fill="#fff" stroke="#80a5b1"/>'
   if filled:svg+=f'<circle cx="{x}" cy="{y}" r="13" fill="#d4b344"/>'
   elif suffix=='cd-loaded-film':svg+=f'<circle cx="{x+13}" cy="{y}" r="3" fill="#557cbb"/><circle cx="{x-13}" cy="{y}" r="3" fill="#557cbb"/>'
 for y,row in zip([118,180,242],rows):svg+=f'<text x="389" y="{y}" font-family="Arial,sans-serif" font-size="21" fill="#294451">{html.escape(row)}</text>'
 svg+='<text x="450" y="349" text-anchor="middle" font-family="Arial,sans-serif" font-size="18" fill="#617580">Pore / particle schematic · not an atomic crystal model</text></svg>'
 (O/e['svgPath']).write_text(svg,encoding='utf-8');e['assetHashes']={'svgPath':sha(O/e['svgPath'])};entries.append(e)
write(O/'registry-additions.json',{'schemaVersion':'1.0.0','entries':entries})
write(O/'molecular-generation-check.json',{'status':'passed' if all(c['passed'] for c in checks) else 'failed','checks':checks,'entries':len(entries),'sourceSha256':SH})
write(O/'asset-manifest.json',{'files':[{'path':p.relative_to(O).as_posix(),'sha256':sha(p)} for folder in ['svg','models'] for p in sorted((O/folder).glob('*'))]})
for offset in range(0,len(entries),6):
 sheet=Image.new('RGB',(1200,960),'#dce7ec')
 for j,e in enumerate(entries[offset:offset+6]):
  d=pymupdf.open(stream=(O/e['svgPath']).read_bytes(),filetype='svg');pdf=pymupdf.open('pdf',d.convert_to_pdf());px=pdf[0].get_pixmap(matrix=pymupdf.Matrix(.62,.62),alpha=False);im=Image.frombytes('RGB',(px.width,px.height),px.samples);can=Image.new('RGB',(600,320),'white');can.paste(im,(15,30));ImageDraw.Draw(can).text((10,4),e['id'],fill='black');sheet.paste(can,(j%2*600,j//2*320))
 sheet.save(O/'review'/f'molecular-contact-{offset//6+1}.png')
print('Created',len(entries),'private references;',sum(c['passed'] for c in checks),'/',len(checks),'checks passed.')
'''
(B/'build_molecular_assets.py').write_text(s,encoding='utf-8')
print('Molecular authoring helper prepared.')
