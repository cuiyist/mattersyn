from pathlib import Path
import json,hashlib,html,sys
sys.path.insert(0,'[local path redacted]');sys.path.insert(0,'[local path redacted]')
import pymupdf
from PIL import Image,ImageDraw
B=Path(__file__).resolve().parent;V=B/'visuals'
for p in [V,V/'svg',V/'review']:p.mkdir(exist_ok=True)
entries=[];DOI='10.1021/ja035980c';SH='24faaec54cea1293bc7951b7d363587e2ec80edaa68d6e90049b5525bc312837'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def tx(x,y,s,size=22):return f'<text x="{x}" y="{y}" text-anchor="middle" font-family="Arial,sans-serif" font-size="{size}" fill="#294451">{html.escape(s)}</text>'
def base(name):return '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="420" viewBox="0 0 900 420"><title>'+html.escape(name)+'</title><rect x="10" y="12" width="880" height="396" rx="24" fill="#f4f8fa"/>'+tx(450,58,name,27)
def save(mid,name,formula,kind,caption,art,extra=None):
 eid='identity-banerjee-'+mid;p=V/'svg'/(eid+'.svg');p.write_text(art+'<desc>'+html.escape(caption)+'</desc></svg>',encoding='utf8')
 e={'id':eid,'name':name,'aliases':[name],'formula':formula,'displayFormula':formula,'depictionKind':kind,'pubchemCid':None,'sourceUrls':['https://doi.org/'+DOI],'svgPath':'svg/'+eid+'.svg','model2dPath':None,'model3dPath':None,'functionalGroups':[],'caption':caption,'limitations':['Source-scoped identity or specimen schematic; no measured atomic coordinates.'],'provenance':{'sourceDoi':DOI,'sourceSha256':SH,'identitySource':'Inspected supplied main and matched IR supplement.','measuredCoordinates':False,'eligible_training':False,'coordinateSource':None},'assetHashes':{'svgPath':sha(p)}}
 if extra:e['provenance'].update(extra)
 entries.append(e)
def tube(x,y,w=270,h=74,oxidized=False):
 s=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}" fill="#aabfc8" stroke="#526f7f" stroke-width="2"/>'
 for dy in [14,27,40,53,64]:s+=f'<path d="M{x+30} {y+dy}H{x+w-30}" stroke="#7894a1" fill="none"/>'
 s+=f'<ellipse cx="{x+35}" cy="{y+h/2}" rx="25" ry="{h/2-8}" fill="#e7eff2" stroke="#526f7f"/><ellipse cx="{x+35}" cy="{y+h/2}" rx="13" ry="{h/2-19}" fill="#fafcfd" stroke="#7894a1"/>'
 if oxidized:
  for a,b in [(32,-2),(63,5),(w-26,10),(w-18,h-14),(113,h),(196,-1)]:s+=f'<circle cx="{x+a}" cy="{y+b}" r="7" fill="#bd5b53"/>'
 return s
for mid,name,formula,ox,sub in [('mwnt-pristine','Pristine multiwalled carbon nanotubes','C',False,'Purchased MWNT starting material'),('mwnt-oxidized','Oxidized multiwalled carbon nanotubes',None,True,'Variable oxygenated surface; no exact formula'),('mwnt-mild','Mildly oxidized nanotube comparison',None,True,'Comparison context; oxidation recipe unreported')]:
 cap='Multiple-wall tube geometry is illustrative, not a measured chirality, wall count, diameter or atomic lattice. '
 if ox:cap+='Red marks denote expected oxygenated sites (carboxylic acid, alcohol and ketone motifs), not a measured site map or a specified surface formula. '
 cap+='Mild oxidation settings remain unreported.'if mid=='mwnt-mild'else'Source composition and sample state remain separate from cartoon geometry.'
 art=base(name)+tube(90,153,330,90,ox)+tx(648,174,'C-based tubular framework',20)+tx(648,221,'O sites shown in red'if ox else'No oxygen sites assigned',20)+tx(450,310,sub,22)+tx(450,365,'Illustrative morphology · no atomic coordinates',18)
 save(mid,name,formula,'specimen',cap,art)
name='Potassium permanganate';cap='Reported KMnO4 reagent identity. K and MnO4 group atom counts are shown without a measured crystal lattice, solvation shell or imposed acid-phase speciation; quantities and concentration remain unreported.'
art=base(name)+tx(450,105,'KMnO₄',28)+tx(181,205,'K⁺',38)+tx(619,147,'MnO₄⁻ formula group',21)
for i,a in enumerate(['Mn','O','O','O','O']):
 x=490+i*62;art+=f'<circle cx="{x}" cy="215" r="25" fill="'+('#b6ced8'if a=='Mn'else'#e4b1aa')+'" stroke="#6b8c9b"/>'+tx(x,223,a,18)
art+=tx(450,305,'Oxidation with sulfuric acid',22)+tx(450,356,'Formula-group counts · no solution species assigned',18)
save('potassium-permanganate',name,'KMnO4','formula',cap,art,{'atomCountIllustration':{'K':1,'Mn':1,'O':4}})
name='Hydrofluoric acid solution';cap='HF identifies the source acid treatment. The H and F symbols encode formula composition only; this is not a claim of undissociated HF, a measured species ratio or hydration structure. The source gives10%, without a percentage basis or delivered volume.'
art=base(name)+tx(450,113,'HF · aqueous acid identity',27)
for x,a,c in [(374,'H','#c8dce4'),(526,'F','#bbd7b1')]:art+=f'<circle cx="{x}" cy="206" r="37" fill="{c}" stroke="#698999"/>'+tx(x,217,a,28)
art+=tx(450,301,'Reported treatment: 10% HF',23)+tx(450,353,'Percentage basis and dose unreported',20)
save('hydrofluoric-acid',name,'HF','formula',cap,art,{'atomCountIllustration':{'H':1,'F':1}})
name='Tellurium source in TOP';cap='The article reports a Te solution in trioctylphosphine. The upstream tellurium chemical form, stock-making procedure, dose and speciation are not supplied. This identity card does not invent a bottle of elemental Te, a tellurium salt or a TOPTe molecular structure.'
art=base(name)+tx(450,146,'Reported as “Te solution in TOP”',29)+tx(450,221,'Tellurium chemical form unresolved',23)+tx(450,291,'No discrete structure assigned',22)+tx(450,355,'TOP solvent has a separate verified molecular reference',18)
save('tellurium-source',name,None,'unresolved-identity',cap,art)
name='Te / TOP injection stock';cap='Source-named tellurium solution in trioctylphosphine, injected at300°C. The stock concentration, component amounts, preparation conditions and delivered volume are not given. TOP reference connectivity does not establish the dissolved tellurium species.'
art=base(name)+tx(260,165,'Te species',29)+tx(260,211,'Unresolved identity',20)+tx(450,185,'+',32)+tx(653,165,'TOP solvent',29)+tx(653,211,'C₂₄H₅₁P',23)+tx(450,302,'Injection stock · concentration and dose unreported',21)+tx(450,357,'Mixture composition schematic',18)
save('te-top-stock',name,None,'mixture',cap,art)
name='PTFE filtration membrane';cap='A0.2µm PTFE membrane is reported as separation equipment. The illustration is not a measured pore map, polymer-chain model or reaction ingredient. The retained fraction is the nanotube composite; free nanocrystals are removed by toluene washing.'
art=base(name)+tx(450,105,'Polytetrafluoroethylene · separation equipment',21)+'<rect x="178" y="145" width="544" height="116" rx="17" fill="#dbe7ec" stroke="#7894a1"/>'
for x in range(209,701,48):
 for y in [174,226]:art+=f'<circle cx="{x}" cy="{y}" r="11" fill="white" stroke="#7894a1"/>'
art+=tx(450,312,'Reported pore size: 0.2 µm',25)+tx(450,364,'Diagram pores are not drawn to scale',18)
save('ptfe-membrane',name,None,'equipment',cap,art)
name='CdTe / MWNT heterostructure';cap='Illustrative CdTe nanocrystal attachment and junction architecture on oxygenated multiwalled nanotubes. Positions, colors, particle number and geometry are explanatory, not a measured interface or atomic model. Source predominantly assigns wurtzite CdTe with possible zinc blende and stacking faults; no refined interfacial coordinates are supplied.'
art=base(name)+tx(450,103,'CdTe nanocrystals + oxygenated carbon nanotubes',22)+tube(86,174,295,70,True)+tube(429,200,330,70,True)
for x,y in [(115,155),(240,247),(405,213),(603,188),(748,239)]:art+=f'<path d="M{x-19} {y-21}L{x+21} {y-13}L{x+24} {y+19}L{x-16} {y+25}L{x-27} {y}Z" fill="#cfaa6c" stroke="#9f783e" stroke-width="2"/>'
art+=tx(450,315,'Attached particles and possible nanotube junctions',21)+tx(450,366,'Specimen architecture · no measured atomic reconstruction',18)
save('composite-specimen',name,'CdTe/MWNT','specimen',cap,art)
for mid,name,note in [('washings-specimen','CdTe in the toluene washings','Removed fraction · size/shape spread remains source-scoped'),('no-tube-specimen','CdTe comparison without nanotube ligands','No-tube reference · complete recipe not supplied here')]:
 cap='Illustrative free CdTe specimen identity, not a reconstruction of measured particle geometry. The source discussion distinguishes washed-away particles from the approximately5nm quasi-spherical no-tube comparison; its monodispersity wording does not establish that these are the same sample. No missing comparator recipe or exact polymorph is supplied.'
 art=base(name)+tx(450,109,'CdTe',28)
 for i,(x,y)in enumerate([(170,180),(329,227),(477,173),(636,226),(734,171)]):art+=f'<ellipse cx="{x}" cy="{y}" rx="{26+(i%2)*7 if mid=="washings-specimen" else 28}" ry="27" fill="#cfaa6c" stroke="#9f783e" stroke-width="2"/>'
 art+=tx(450,310,note,21)+tx(450,365,'Illustrative particles · not a measured size distribution',18)
 save(mid,name,'CdTe','specimen',cap,art)
write(V/'registry-additions.json',{'schemaVersion':'1.0.0','entries':entries});write(V/'asset-manifest.json',{'files':[{'path':e['svgPath'],'sha256':sha(V/e['svgPath'])}for e in entries]});write(V/'molecular-generation-check.json',{'status':'passed','entries':len(entries),'scope':'Source identity, variable nanotube surface and composite architecture only; existing verified molecular references reused separately.'})
for offset in range(0,len(entries),6):
 sheet=Image.new('RGB',(1200,1020),'#dce7ec')
 for j,e in enumerate(entries[offset:offset+6]):
  d=pymupdf.open(stream=(V/e['svgPath']).read_bytes(),filetype='svg');pdf=pymupdf.open('pdf',d.convert_to_pdf());px=pdf[0].get_pixmap(matrix=pymupdf.Matrix(.64,.64),alpha=False);can=Image.new('RGB',(600,340),'white');can.paste(Image.frombytes('RGB',(px.width,px.height),px.samples),(12,28));ImageDraw.Draw(can).text((10,5),e['id'],fill='black');sheet.paste(can,(j%2*600,j//2*340))
 sheet.save(V/'review'/f'molecular-contact-{offset//6+1}.png')
print('Created',len(entries),'new source-scoped chemical and specimen cards.')
