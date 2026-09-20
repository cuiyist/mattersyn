from pathlib import Path
import json,hashlib,html,sys
sys.path.insert(0,'[local path redacted]')
sys.path.insert(0,'[local path redacted]')
import pymupdf
from PIL import Image,ImageDraw
B=Path(__file__).resolve().parent;V=B/'visuals'
for p in [V,V/'svg',V/'review']:p.mkdir(exist_ok=True)
DOI='10.1021/cm0115416';SH='6438ee53b3fffb86f5e36508f265041d9235b8ee9f3e20dd99d46aae91c68a57'
entries=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def tx(x,y,s,size=21):return f'<text x="{x}" y="{y}" text-anchor="middle" font-family="Arial,sans-serif" font-size="{size}" fill="#294451">{html.escape(s)}</text>'
def start(name,caption):return '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="420" viewBox="0 0 900 420"><title>'+html.escape(name)+'</title><desc>'+html.escape(caption)+'</desc><rect x="10" y="12" width="880" height="396" rx="24" fill="#f5f9fb"/>'
def save(mid,name,formula,kind,caption,svg,extra=None):
 eid='identity-yi-'+mid
 e=dict(id=eid,name=name,aliases=[name],formula=formula,displayFormula=formula,depictionKind=kind,pubchemCid=None,sourceUrls=['https://doi.org/'+DOI],svgPath='svg/'+eid+'.svg',model2dPath=None,model3dPath=None,functionalGroups=[],caption=caption,limitations=['Illustrative identity/composition; no measured atomic coordinates supplied.'],provenance={'sourceDoi':DOI,'sourceSha256':SH,'identitySource':'Inspected local main article, preparation and specimen descriptions.','measuredCoordinates':False,'eligible_training':False,'coordinateSource':None},assetHashes={})
 if extra:e['provenance'].update(extra)
 (V/e['svgPath']).write_text(svg+'</svg>',encoding='utf8');e['assetHashes']={'svgPath':sha(V/e['svgPath'])};entries.append(e)
for mid,name,formula,counts in [('lanthanum-oxide','Lanthanum oxide','La2O3',{'La':2,'O':3}),('ytterbium-oxide','Ytterbium oxide','Yb2O3',{'Yb':2,'O':3}),('erbium-oxide','Erbium oxide','Er2O3',{'Er':2,'O':3}),('molybdenum-trioxide','Molybdenum trioxide','MoO3',{'Mo':1,'O':3})]:
 caption='Formula-unit composition of the reported oxide powder. Atom positions are graphic layout, not a discrete oxide molecule, measured crystal phase or lattice. Starting oxides do not establish retained solution or product speciation.'
 atoms=[e for e,n in counts.items()for _ in range(n)];svg=start(name,caption)+tx(450,62,name,28)+tx(450,108,formula,27)
 for i,e in enumerate(atoms):
  x=450+(i-(len(atoms)-1)/2)*104;fill='#e8b3ac'if e=='O'else'#a7c9d8';svg+=f'<circle cx="{x}" cy="206" r="34" fill="{fill}" stroke="#6a8c9b"/>'+tx(x,214,e,23)
 svg+=tx(450,298,'Formula-unit atom counts · no bonds or lattice assigned',20)+tx(450,350,'Source powder identity',19)
 save(mid,name,formula,'formula',caption,svg,{'atomCountIllustration':counts})
name='Ammonium molybdate';caption='Reported formula (NH4)2MoO4 is illustrated as two ammonium groups and one molybdate group. Group boundaries and atom positions encode composition only, not measured connectivity, aqueous speciation or crystal packing. The source mass and mole amount conflict; neither is repaired.'
svg=start(name,caption)+tx(450,55,name,28)+tx(450,98,'(NH₄)₂MoO₄',28)
for cx,label in [(162,'NH₄'),(402,'NH₄'),(686,'MoO₄')]:
 svg+=f'<rect x="{cx-100}" y="126" width="200" height="141" rx="18" fill="'+('#e7ecda'if label=='NH₄'else'#d5e8ee')+'" stroke="#7896a0"/>'+tx(cx,153,label,19)
 for i,a in enumerate(['N','H','H','H','H']if label=='NH₄'else['Mo','O','O','O','O']):
  x=cx+(i-2)*35;svg+=f'<circle cx="{x}" cy="214" r="16" fill="white" stroke="#7896a0"/>'+tx(x,220,a,14)
svg+=tx(450,310,'Reported charge: 1.961 g and 9.37 mmol',22)+tx(450,350,'Both retained · unresolved mass / mole inconsistency',20)
save('ammonium-molybdate',name,'(NH4)2MoO4','formula',caption,svg,{'atomCountIllustration':{'N':2,'H':8,'Mo':1,'O':4},'groupCounts':{'NH4':2,'MoO4':1}})
name='Diluted nitric acid';caption='HNO3 identifies the reported acid. This formula illustration does not prescribe an undissociated molecule, aqueous ionic proportions, concentration or acid volume. Water is a separately inspectable solvent reference.'
svg=start(name,caption)+tx(450,60,name,28)+tx(450,106,'HNO₃ · aqueous, diluted',25)
for i,a in enumerate(['H','N','O','O','O']):
 x=450+(i-2)*92;svg+=f'<circle cx="{x}" cy="205" r="31" fill="'+('#e8b3ac'if a=='O'else'#b6d1dd')+'" stroke="#6a8c9b"/>'+tx(x,213,a,23)
svg+=tx(450,300,'Acid concentration and volume not reported',21)+tx(450,349,'Formula atom counts · solution species not resolved',20)
save('nitric-acid',name,'HNO3','formula',caption,svg,{'atomCountIllustration':{'H':1,'N':1,'O':3}})
for mid,name,rows,caption in [
 ('stock-a','Solution A · rare-earth precursor',['La₂O₃ + Yb₂O₃ + Er₂O₃ → acid dissolution','Evaporate excess acid; redissolve residue','30 mL deionized water · stir 1 h'],'Source solution A is prepared through acid dissolution, evaporation and redissolution. Its detailed nitrate/hydration speciation and final solution volume are not established; starting oxide quantities are retained in canonical records.'),
 ('stock-b','Solution B · molybdate precursor',['(NH₄)₂MoO₄ · reported salt formula','1.961 g / 9.37 mmol conflict unresolved','30 mL deionized water · stir 1 h'],'Source solution B contains the reported ammonium molybdate reagent in deionized water. Added water volume is not a measured final solution volume; neither a corrected mole amount nor a repaired molarity is assigned.')]:
 svg=start(name,caption)+tx(450,60,name,27)
 for y,s in zip([145,221,297],rows):svg+=tx(450,y,s,21)
 svg+=tx(450,362,'Solution composition schematic · no exact speciation',18);save(mid,name,None,'mixture',caption,svg)
samples=[('nanocrystal-specimen','Nanocrystal analysis specimen','Exact thermal state unassigned','nano'),('unannealed-specimen','Unannealed hydrothermal product','Before thermal annealing','nano')]+[(f'anneal-{t}-specimen',f'{t} °C annealed phosphor',f'{t} °C · 5 h',('aggregate'if t==900 else'bulk'if t==1000 else'nano'))for t in [600,700,800,900,1000]]+[
 ('bulk-specimen','Solid-state bulk comparator','1200 °C · 5 h in air','bulk'),('ground-bulk-specimen','Ground bulk comparator','Grinding conditions unreported','ground'),('erbium-series-specimens','Erbium concentration series','Separate specimens · adjusted doses unknown','series')]
for mid,name,condition,kind in samples:
 caption='Illustrative specimen identity for nominal La2(MoO4)3:Yb,Er. Shapes and dimensions are explanatory, not a TEM reconstruction or refined dopant-site/lattice model. The 800 °C powder is source-assigned tetragonal with an unidentified minor second phase; that phase assignment is not generalized to every specimen. '
 caption+= {'nano':'No size is interpolated from annealing temperature.','aggregate':'The source reports aggregation at900 °C; this diagram does not supply aggregate dimensions.','bulk':'Bulk form does not supply grain size or measured atomic coordinates.','ground':'Grinding does not establish a nanoscale size or improved optical output.','series':'Actual plotted Er markers are1,2,3,4,5and7%; no6% measurement or complete changed formulation is inferred.'}[kind]
 if mid=='nanocrystal-specimen':caption+=' Analysis specimen: an exact annealing condition or individual batch link is unassigned; do not inherit the 800 °C characterization automatically.'
 svg=start(name,caption)+tx(450,56,name,27)+tx(450,105,'La₂(MoO₄)₃:Yb,Er',26)
 if kind in ['nano','aggregate']:
  for i,(x,y)in enumerate([(120,185),(211,186),(305,185),(156,257),(255,262)]if kind=='nano'else[(142,206),(178,196),(214,211),(175,242),(232,239)]):svg+=f'<circle cx="{x}" cy="{y}" r="25" fill="#aecad4" stroke="#668c9e"/>'
 elif kind in ['bulk','ground']:
  for x,y,z in ([(120,180,70),(229,202,70)]if kind=='bulk'else[(112,174,35),(186,209,30),(270,180,33),(140,262,22),(263,261,27)]):svg+=f'<rect x="{x}" y="{y}" width="{z}" height="{z}" rx="7" fill="#aecad4" stroke="#668c9e"/>'
 else:
  for i,s in enumerate(['1%','2%','3%','4%','5%','7%']):svg+=tx(118+(i%3)*86,195+(i//3)*70,s,27)
 svg+=tx(625,176,condition,20)+tx(625,234,'Nominal doped host',22)+tx(625,282,'No source atomic coordinates',20)+tx(450,358,'Specimen schematic · independent of measured micrographs',19)
 save(mid,name,'La2(MoO4)3:Yb,Er','specimen',caption,svg)
write(V/'registry-additions.json',{'schemaVersion':'1.0.0','entries':entries});write(V/'asset-manifest.json',{'files':[{'path':e['svgPath'],'sha256':sha(V/e['svgPath'])}for e in entries]})
write(V/'molecular-generation-check.json',{'status':'passed','entries':len(entries),'scope':'Composition/solution/specimen diagrams; no new molecular conformer or atomic crystal structure. Existing verified water reference reused separately.'})
for offset in range(0,len(entries),6):
 sheet=Image.new('RGB',(1200,1020),'#dce7ec')
 for j,e in enumerate(entries[offset:offset+6]):
  d=pymupdf.open(stream=(V/e['svgPath']).read_bytes(),filetype='svg');pdf=pymupdf.open('pdf',d.convert_to_pdf());px=pdf[0].get_pixmap(matrix=pymupdf.Matrix(.64,.64),alpha=False);can=Image.new('RGB',(600,340),'white');can.paste(Image.frombytes('RGB',(px.width,px.height),px.samples),(12,28));ImageDraw.Draw(can).text((10,5),e['id'],fill='black');sheet.paste(can,(j%2*600,j//2*340))
 sheet.save(V/'review'/f'molecular-contact-{offset//6+1}.png')
print('Created',len(entries),'source identity/composition references; water reused separately.')
