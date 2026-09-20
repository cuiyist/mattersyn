from pathlib import Path
import sys,json,hashlib,html,math
sys.dont_write_bytecode=True
sys.path.insert(0,'[local path redacted]')
sys.path.insert(0,'[local path redacted]')
from rdkit import Chem,__version__ as RV
from rdkit.Chem import rdDepictor,rdMolDescriptors,AllChem
from rdkit.Chem.Draw import rdMolDraw2D
import pymupdf
from PIL import Image,ImageDraw
B=Path(__file__).resolve().parent;O=B/'visuals'
for d in [O,O/'svg',O/'models',O/'review']:d.mkdir(exist_ok=True)
DOI='10.1021/jp010002l';SH='00ac817e60651f0e7f9faabe85ba18372ac37fea1f0f5d174779c982064b4184'
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
entries=[];checks=[]
def check(ok,text):checks.append({'check':text,'passed':bool(ok)})
def base(id,name,formula,kind,caption):
 return dict(id=id,name=name,aliases=[name],formula=formula,displayFormula=formula,depictionKind=kind,pubchemCid=None,sourceUrls=['https://doi.org/'+DOI],svgPath='svg/'+id+'.svg',model2dPath=None,model3dPath=None,functionalGroups=[],caption=caption,limitations=[],provenance={'sourceDoi':DOI,'sourceSha256':SH,'identitySource':'Named compound and/or connectivity diagram in inspected local main article; no external database lookup claimed.','measuredCoordinates':False,'eligible_training':False},assetHashes={})
# The expected formulas use RDKit Hill order; display formulas retain chemical convention.
definitions=[('hydrogen-sulfide','Hydrogen sulfide','S','H2S','H2S',True,'Free H2S molecular reference. Gas injection and aqueous delivery are distinct recipe states; solution ionization is not represented by a unique hydrated structure.')]
for id,name,smi,formula,display,conformer,specific in definitions:
 m=Chem.AddHs(Chem.MolFromSmiles(smi));assert m is not None
 check(rdMolDescriptors.CalcMolFormula(m)==formula,id+' elemental formula')
 caption=specific+' Reference connectivity; any computed conformer is illustrative and is not measured solution or surface geometry.'
 e=base(id,name,formula,'molecule' if conformer else 'ionic_components',caption);e['displayFormula']=display
 rdDepictor.Compute2DCoords(m)
 if id=='tetramethylammonium-hydroxide-pentahydrate':
  from rdkit.Geometry import Point3D
  conf=m.GetConformer();frags=Chem.GetMolFrags(m)
  centers=[(-2,1),(3,1),(-4,-3),(-2,-3),(0,-3),(2,-3),(4,-3)]
  for frag,(cx,cy) in zip(frags,centers):
   mx=sum(conf.GetAtomPosition(i).x for i in frag)/len(frag);my=sum(conf.GetAtomPosition(i).y for i in frag)/len(frag)
   for i in frag:
    pos=conf.GetAtomPosition(i);conf.SetAtomPosition(i,Point3D(pos.x-mx+cx,pos.y-my+cy,0))
 groups=[];ac={};bc={}
 patterns=[('Thiol','[S;H1]',(.87,.67,.18)),('Silane anchor','[Si](O)(O)O',(.29,.66,.69)),('Primary amine','[N;H2]',(.45,.55,.86)),('Carboxyl group','C(=O)[O;H1]',(.88,.47,.43)),('Disulfide bridge','SS',(.87,.67,.18)),('Nitro group','[N+](=O)[O-]',(.5,.57,.84)),('Phosphate group','P(=O)(O)(O)O',(.29,.66,.69)),('Sulfonic acid','S(=O)(=O)O',(.29,.66,.69)),('Hydroxyl','[O;H1]',(.6,.72,.36))]
 for label,smarts,color in patterns:
  hits=m.GetSubstructMatches(Chem.MolFromSmarts(smarts));inds=sorted({i for hit in hits for i in hit})
  if inds:
   bonds=[b.GetIdx() for b in m.GetBonds() if b.GetBeginAtomIdx() in inds and b.GetEndAtomIdx() in inds]
   groups.append({'label':label,'atomIndices':inds,'bondIndices':bonds});ac.update({i:color for i in inds});bc.update({i:color for i in bonds})
 dr=rdMolDraw2D.MolDraw2DSVG(900,440);op=dr.drawOptions();op.padding=.16;op.clearBackground=False;op.minFontSize=18;op.maxFontSize=27;op.bondLineWidth=2;op.updateAtomPalette({16:(.61,.45,.08)})
 dr.DrawMolecule(m,highlightAtoms=list(ac),highlightBonds=list(bc),highlightAtomColors=ac,highlightBondColors=bc);dr.FinishDrawing()
 (O/e['svgPath']).write_text(dr.GetDrawingText().replace('<!-- END OF HEADER -->','<title>'+html.escape(name)+'</title><desc>'+html.escape(caption)+'</desc>'),encoding='utf-8')
 def model(mol,dim):
  c=mol.GetConformer();return {'id':id,'name':name,'formula':formula,'representation':dim,'has3D':dim=='3d','allowRotation':dim=='3d','coordinateUnits':'angstrom' if dim=='3d' else 'drawing units','indexConvention':'zero-based','modelType':'Computed free-molecule reference' if dim=='3d' else 'Identity connectivity diagram','caption':caption,'atoms':[{'index':a.GetIdx(),'element':a.GetSymbol(),'x':round(c.GetAtomPosition(a.GetIdx()).x,6),'y':round(c.GetAtomPosition(a.GetIdx()).y,6),'z':round(c.GetAtomPosition(a.GetIdx()).z,6),'formalCharge':a.GetFormalCharge(),'implicitHydrogenCount':a.GetTotalNumHs()} for a in mol.GetAtoms()],'bonds':[{'a':b.GetBeginAtomIdx(),'b':b.GetEndAtomIdx(),'order':b.GetBondTypeAsDouble()} for b in mol.GetBonds()],'functionalGroups':groups,'computedBy':'RDKit '+RV,'source':'https://doi.org/'+DOI,'eligible_training':False}
 e['model2dPath']='models/'+id+'-2d.json';write(O/e['model2dPath'],model(m,'2d'));e['functionalGroups']=groups
 if conformer:
  h=Chem.AddHs(m);params=AllChem.ETKDGv3();params.randomSeed=20260919;emb=AllChem.EmbedMolecule(h,params);conv=AllChem.UFFOptimizeMolecule(h,maxIters=3000) if emb==0 else None
  check(emb==0 and conv==0,id+' ETKDG/UFF conformer converged')
  if emb==0 and conv==0:
   e['model3dPath']='models/'+id+'-3d.json';md=model(h,'3d');write(O/e['model3dPath'],md)
   check(all(math.isfinite(a[v]) for a in md['atoms'] for v in ['x','y','z']),id+' finite coordinates')
   check(rdMolDescriptors.CalcMolFormula(h)==formula,id+' explicit-H conformer formula')
  e['provenance'].update(conformerConverged=conv==0,embeddingSeed=20260919,minimization='UFF, maximum 3000 iterations')
 e['provenance'].update(smiles=smi,software='RDKit '+RV,coordinates='2D depiction'+(' and ETKDGv3/UFF computed conformer' if conformer else '; no ion-pair or crystalline geometry'))
 e['assetHashes']={k:sha(O/e[k]) for k in ['svgPath','model2dPath','model3dPath'] if e[k]};entries.append(e)

cards=[
 ('identity-cadmium-ii-aqueous','Cadmium(II) ions in water','Cd2+','ionic_components',['Cd²⁺ (aq)','Aqueous cadmium source','Counterion / hydration unspecified'],'Source names aqueous Cd²⁺, not a specific salt. The displayed ion identity does not establish coordination number, counterion, hydrate or solution complex.'),
 ('identity-mercury-ii-aqueous','Mercury(II) ions in water','Hg2+','ionic_components',['Hg²⁺ (aq)','Aqueous mercury source','Counterion / hydration unspecified'],'Source names aqueous Hg²⁺, not a specific salt. The displayed ion identity does not establish coordination number, counterion, hydrate or solution complex.'),
 ('identity-hexametaphosphate-unresolved','Hexametaphosphate stabilizer',None,'unresolved-identity',['Hexametaphosphate','Colloid stabilizer','Salt form / dose unspecified'],'The paper names hexametaphosphate but gives no counterion, concentration, chain-length characterization or confirmed discrete ring structure. No formula or unique molecular geometry is assigned.'),
 ('identity-braun-h2s-water','Hydrogen sulfide in water',None,'mixture',['H₂S + water','Dropwise sulfide feed','Concentration / total volume unreported'],'Source-named aqueous H2S feed. Molecular H2S and water are separate references; no exact solution speciation, concentration or delivered dose is assigned.'),
 ('identity-braun-sapphire','Sapphire continuum-generation plate','Al2O3','support',['Sapphire plate','White-light continuum generation','Optical hardware; not product'],'Source-named sapphire plate. Al2O3 is a chemical identity reference, not a measured nanocrystal phase, unit cell or a synthesis ingredient.'),
 ('identity-braun-glass-cell','Glass optical cell',None,'support',['Glass sample cell','Rotated optical specimen','Glass composition unreported'],'Reported glass cell is optical hardware. Do not infer its glass formulation or transfer its dimensions to the synthesized particles.'),
 ('identity-braun-qdqw-specimens','CdS/HgS quantum-dot quantum-well specimens',None,'specimen',['CdS / HgS / CdS','Systems I, II and III','Separate architectures / specimens'],'Shared acquisition context for separately measured quantum-dot quantum-well systems. This is not a physical mixture or a uniquely identified experimental batch.'),
 ('identity-braun-cds-core','CdS core dispersion','CdS','specimen',['CdS nanocrystal cores','Aqueous colloid','Source core-size discrepancy retained'],'Composition reference for the CdS core dispersion. The general preparation states 3.5 nm while the system description and Figure1 state 3.2 nm; no measured atomic coordinates, phase or exact particle geometry are assigned.')]
for id,name,formula,kind,rows,caption in cards:
 e=base(id,name,formula,kind,caption)
 svg='<svg xmlns="http://www.w3.org/2000/svg" width="900" height="360" viewBox="0 0 900 360"><title>'+html.escape(name)+'</title><desc>'+html.escape(caption)+'</desc><rect x="18" y="20" width="864" height="320" rx="20" fill="#f1f6f9" stroke="#cbdce6"/>'
 for y,row,size in zip([120,199,263],rows,[30,22,19]):svg+=f'<text x="450" y="{y}" text-anchor="middle" font-family="Arial,sans-serif" font-size="{size}" fill="#294451">{html.escape(row)}</text>'
 svg+='</svg>'; (O/e['svgPath']).write_text(svg,encoding='utf-8');e['assetHashes']={'svgPath':sha(O/e['svgPath'])};entries.append(e)
for system,layers,rows in [
 ('i',['CdS','HgS','CdS'],['CdS core: 3.2 nm as assigned','One HgS well: 0.4 nm','CdS cap: 0.4 nm']),
 ('ii',['CdS','HgS','HgS','CdS'],['CdS core: 3.2 nm as assigned','Double-layer HgS well: 0.8 nm','CdS cap: 0.4 nm']),
 ('iii',['CdS','HgS','CdS','CdS','HgS','CdS'],['CdS core: 3.2 nm as assigned','Two HgS wells: 0.4 nm each','CdS barrier: 0.8 nm; cap: 0.4 nm'])]:
 id='identity-braun-system-'+system;name='System '+system.upper()+' quantum-dot quantum-well architecture';cap='Composition-layer schematic following the paper. Rings communicate sequence only, not particle shape, scale or measured geometry. The source cites tetrahedral CdS; its core-size 3.5 nm/3.2 nm discrepancy remains unresolved. No atomistic interface, phase or exact crystal structure is assigned.'
 e=base(id,name,'CdS/HgS/CdS','specimen',cap)
 svg='<svg xmlns="http://www.w3.org/2000/svg" width="900" height="420" viewBox="0 0 900 420"><title>'+html.escape(name)+'</title><desc>'+html.escape(cap)+'</desc><rect x="10" y="12" width="880" height="396" rx="24" fill="#f5f9fb"/>'
 for i in reversed(range(len(layers))):
  col='#c65b55' if layers[i]=='HgS' else '#56a397';radius=59+i*14
  svg+=f'<circle cx="212" cy="191" r="{radius}" fill="{col}" stroke="#ffffff" stroke-width="2"/>'
 for y,row in zip([120,181,242],rows):svg+=f'<text x="394" y="{y}" font-family="Arial,sans-serif" font-size="22" fill="#294451">{html.escape(row)}</text>'
 svg+='<text x="450" y="342" text-anchor="middle" font-family="Arial,sans-serif" font-size="18" fill="#617580">Layer-sequence illustration · not to scale · no measured atomic model</text></svg>'
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
