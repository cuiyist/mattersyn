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
DOI='10.1021/nl0345116';SH='72684e3bf22a2ef173ea1d6d6e31648a1222b2b15bc069bb8fe6cef8d1876a33'
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
entries=[];checks=[]
def check(ok,text):checks.append({'check':text,'passed':bool(ok)})
def base(id,name,formula,kind,caption):
 return dict(id=id,name=name,aliases=[name],formula=formula,displayFormula=formula,depictionKind=kind,pubchemCid=None,sourceUrls=['https://doi.org/'+DOI],svgPath='svg/'+id+'.svg',model2dPath=None,model3dPath=None,functionalGroups=[],caption=caption,limitations=[],provenance={'sourceDoi':DOI,'sourceSha256':SH,'identitySource':'Named compound and/or connectivity diagram in inspected local main article; no external database lookup claimed.','measuredCoordinates':False,'eligible_training':False},assetHashes={})
# The expected formulas use RDKit Hill order; display formulas retain chemical convention.
definitions=[('trimethylsilane','Trimethylsilane, literal source name','C[SiH](C)C','C3H10Si','C3H10Si',True,'Connectivity of the compound literally named trimethylsilane in the source. The surface diagram shows a bound trimethylsilyl motif but does not identify a different chlorosilane reagent. This free-molecule reference does not verify the reported surface treatment or its reaction mechanism.')]


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
 patterns=[('Si–H bond','[Si]-[H]',(.87,.67,.18)),('Thiol','[S;H1]',(.87,.67,.18)),('Silane anchor','[Si](O)(O)O',(.29,.66,.69)),('Primary amine','[N;H2]',(.45,.55,.86)),('Carboxylate group','C(=O)[O-]',(.88,.47,.43)),('Disulfide bridge','SS',(.87,.67,.18)),('Nitro group','[N+](=O)[O-]',(.5,.57,.84)),('Phosphate group','P(=O)(O)(O)O',(.29,.66,.69)),('Sulfonic acid','S(=O)(=O)O',(.29,.66,.69)),('Hydroxyl','[O;H1]',(.6,.72,.36))]
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

cards=[('identity-sashchiuk-lead-chxbu', 'Lead-cyclohexanebutirate, as printed', None, 'unresolved-identity', ['Pb-cHxBu precursor', 'Source spelling retained', 'Formula and exact connectivity unresolved'], 'The local article supplies a precursor name and abbreviation but no structural drawing, formula, CAS or preparation. Exact carboxylate identity and coordination are unresolved; no guessed molecule is drawn.'), ('identity-sashchiuk-topo-reagent', 'TOPO reagent: 90% or 99% purity', None, 'mixture', ['TOPO mother solution', 'Aldrich 90% or 99% purity', 'Impurity composition not quantified'], 'The source lists 90% or 99% TOPO and discusses phosphonic-acid impurities in the 90% material. A pure TOPO molecule is separately shown as a named component; no complete mixture composition or exact purity assignment for every sample is known.'), ('identity-sashchiuk-pbse-individual', 'Individual PbSe nanocrystals', 'PbSe', 'specimen', ['Individual PbSe nanocrystals', 'Rock-salt phase reported', 'Dimensions remain specimen-specific'], 'PbSe composition and rock-salt phase are source assignments. Cubic individual particles are described and imaged; spherical wording also appears in the source. This schematic is not a measured particle geometry or surface-ligand reconstruction.'), ('identity-sashchiuk-pbse-spheres', 'Spherical PbSe nanocrystal assemblies', 'PbSe', 'specimen', ['Spherical polycrystalline assemblies', 'Randomly oriented PbSe building blocks', 'Assembly size is not crystallite size'], 'The spheres comprise multiple PbSe nanocrystals. Their assembly dimensions, constituent particle sizes and diffraction evidence have separate source scopes. Relative packing and ligand positions are illustrative.'), ('identity-sashchiuk-pbse-wires', 'Wire-like PbSe nanocrystal assemblies', 'PbSe', 'specimen', ['Ordered wire-like assemblies', 'PbSe nanocrystal building blocks', 'Junctions and gradual orientation changes'], 'Source microscopy and SAED support ordered assemblies of PbSe nanocrystals. A straight chain sketch does not establish atomic fusion, measured interface coordinates or a continuous bulk single-crystal wire.'), ('identity-sashchiuk-formvar-grid', 'Formvar/carbon-coated copper TEM grid', None, 'support', ['Copper grid · 300 mesh', 'Amorphous Formvar + evaporated carbon', 'Microscopy preparation support'], 'Source-specific microscopy support. Formvar composition, film thickness and support geometry are not fully specified; no unique molecular formula or measured grid structure is assigned.'), ('identity-sashchiuk-silicon-substrate', 'p-Doped silicon substrate', 'Si', 'support', ['p-Doped silicon substrate', 'Device support and back gate', 'Dopant identity and concentration unknown'], 'Silicon electrical-device support with unspecified p-type dopant and orientation. This is not a PbSe synthesis precursor or an independently synthesized silicon material.'), ('identity-sashchiuk-silica-layer', 'Silicon oxide layer', 'SiO2', 'support', ['200 nm oxide layer on silicon', 'Source labels the stack Si/SiO2', 'Growth method unreported'], 'The paper reports a 200 nm oxide layer and depicts SiO2 on silicon. Its growth process, defect chemistry and atomic coordinates are not supplied.'), ('identity-sashchiuk-pmma', 'Poly(methyl methacrylate) resist', None, 'polymer', ['PMMA lithography resist', 'Spin coating followed by annealing', 'Molecular weight and formulation unknown'], 'Named PMMA resist used in device fabrication. Molecular weight, tacticity, solvent and film thickness are not reported; no unique molecule or chain conformer is claimed.'), ('identity-sashchiuk-titanium', 'Titanium contact component', 'Ti', 'element', ['Ti contact component', 'Evaporated with Au contact leads', 'Layer thickness and sequence unknown'], 'Elemental component of the Ti/Au electrical contacts, not a molecular titanium reagent or PbSe synthesis ingredient. Evaporation thicknesses and detailed layer sequence are unreported.'), ('identity-sashchiuk-gold', 'Gold contact component', 'Au', 'element', ['Au contact component', 'Ti/Au leads shown in device', 'Contact dimensions unreported'], 'Elemental component of the electrical leads. A metal identity illustration is not a molecular gas, exact contact structure or separate gold synthesis.')]

for id,name,formula,kind,rows,caption in cards:
 e=base(id,name,formula,kind,caption)
 svg='<svg xmlns="http://www.w3.org/2000/svg" width="900" height="360" viewBox="0 0 900 360"><title>'+html.escape(name)+'</title><desc>'+html.escape(caption)+'</desc><rect x="18" y="20" width="864" height="320" rx="20" fill="#f1f6f9" stroke="#cbdce6"/>'
 if 'pbse-' in id:
  if id.endswith('individual'):
   svg+='<rect x="406" y="53" width="88" height="88" rx="5" fill="#739caf" stroke="#2c5268" stroke-width="3"/><path d="M406 53l20-14h88l-20 14M494 53l20-14v88l-20 14" fill="none" stroke="#2c5268" stroke-width="3"/>'
  elif id.endswith('spheres'):
   svg+='<circle cx="450" cy="97" r="66" fill="#dce9ed" stroke="#739caf"/>'
   for x,y,a in [(415,68,16),(449,54,-24),(475,74,12),(398,99,28),(433,96,-17),(469,108,31),(427,132,9),(461,141,-20),(489,131,6)]:svg+=f'<rect x="{x}" y="{y}" width="20" height="20" fill="#739caf" stroke="#2c5268" transform="rotate({a},{x+10},{y+10})"/>'
  else:
   for k in range(9):
    x=278+k*39;y=76+5*math.sin(k/2);svg+=f'<rect x="{x}" y="{y:.2f}" width="34" height="34" fill="#739caf" stroke="#2c5268" stroke-width="2" transform="rotate({k-4},{x+17},{y+17})"/>'
  ys=[199,245,290];sizes=[27,20,18]
 else:ys=[115,193,257];sizes=[28,21,18]
 for y,row,size in zip(ys,rows,sizes):svg+=f'<text x="450" y="{y}" text-anchor="middle" font-family="Arial,sans-serif" font-size="{size}" fill="#294451">{html.escape(row)}</text>'

 svg+='</svg>'; (O/e['svgPath']).write_text(svg,encoding='utf-8');e['assetHashes']={'svgPath':sha(O/e['svgPath'])};entries.append(e)
write(O/'registry-additions.json',{'schemaVersion':'1.0.0','entries':entries})
write(O/'molecular-generation-check.json',{'status':'passed' if all(c['passed'] for c in checks) else 'failed','checks':checks,'entries':len(entries),'sourceSha256':SH})
write(O/'asset-manifest.json',{'files':[{'path':p.relative_to(O).as_posix(),'sha256':sha(p)} for folder in ['svg','models'] for p in sorted((O/folder).glob('*'))]})
for offset in range(0,len(entries),6):
 sheet=Image.new('RGB',(1200,960),'#dce7ec')
 for j,e in enumerate(entries[offset:offset+6]):
  d=pymupdf.open(stream=(O/e['svgPath']).read_bytes(),filetype='svg');pdf=pymupdf.open('pdf',d.convert_to_pdf());px=pdf[0].get_pixmap(matrix=pymupdf.Matrix(.62,.62),alpha=False);im=Image.frombytes('RGB',(px.width,px.height),px.samples);can=Image.new('RGB',(600,320),'white');can.paste(im,(15,30));ImageDraw.Draw(can).text((10,4),e['id'],fill='black');sheet.paste(can,(j%2*600,j//2*320))
 sheet.save(O/'review'/f'molecular-contact-{offset//6+1}.png')
print('Created',len(entries),'private references;',sum(c['passed'] for c in checks),'/',len(checks),'checks passed.')
