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
DOI='10.1021/jp011815c';SH='2e6310ab5f5c6102ffa46e91dc3ccc2a180e6a6d17fd6a82ef448867edd79967'
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
entries=[];checks=[]
def check(ok,text):checks.append({'check':text,'passed':bool(ok)})
def base(id,name,formula,kind,caption):
 return dict(id=id,name=name,aliases=[name],formula=formula,displayFormula=formula,depictionKind=kind,pubchemCid=None,sourceUrls=['https://doi.org/'+DOI],svgPath='svg/'+id+'.svg',model2dPath=None,model3dPath=None,functionalGroups=[],caption=caption,limitations=[],provenance={'sourceDoi':DOI,'sourceSha256':SH,'identitySource':'Named compound or explicit condensed formula in inspected local main article; no external database lookup claimed.','measuredCoordinates':False,'eligible_training':False},assetHashes={})
molecules=[
 ('carbon-dioxide','Carbon dioxide','O=C=O','CO2'),
 ('perfluorooctanethiol','1H,1H,2H,2H-Perfluorooctanethiol','SCC'+'C(F)(F)'*5+'C(F)(F)F','C8H5F13S'),
 ('perfluorodecanethiol','1H,1H,2H,2H-Perfluorodecanethiol','SCC'+'C(F)(F)'*7+'C(F)(F)F','C10H5F17S'),
 ('heptane','n-Heptane','CCCCCCC','C7H16'),
 ('dodecanethiol','1-Dodecanethiol','CCCCCCCCCCCCS','C12H26S'),
 ('octanethiol','1-Octanethiol','CCCCCCCCS','C8H18S'),
 ('hexanethiol','1-Hexanethiol','CCCCCCS','C6H14S'),
 ('trichlorotrifluoroethane','1,1,2-Trichlorotrifluoroethane','ClC(Cl)(F)C(F)(F)Cl','C2Cl3F3')]
for id,name,smi,formula in molecules:
 m=Chem.MolFromSmiles(smi);assert m is not None
 check(rdMolDescriptors.CalcMolFormula(m)==formula,id+' elemental formula')
 caption='Reference molecular connectivity with a computed conformer. Neither drawing nor conformer is a measured solution species, surface-bound geometry or experimental structural label.'
 e=base(id,name,formula,'molecule',caption);rdDepictor.Compute2DCoords(m)
 groups=[];ac={};bc={}
 if any(a.GetSymbol()=='S'for a in m.GetAtoms()):
  inds=[a.GetIdx()for a in m.GetAtoms()if a.GetSymbol()=='S'];groups.append({'label':'Thiol group','atomIndices':inds,'bondIndices':[]})
  for i in inds:ac[i]=(.88,.71,.23)
 if any(a.GetSymbol()=='F'for a in m.GetAtoms()):
  inds=[a.GetIdx()for a in m.GetAtoms()if a.GetSymbol()=='F' or any(n.GetSymbol()=='F'for n in a.GetNeighbors())];bs=[b.GetIdx()for b in m.GetBonds()if b.GetBeginAtomIdx()in inds and b.GetEndAtomIdx()in inds]
  groups.append({'label':'Fluorinated segment','atomIndices':inds,'bondIndices':bs})
  ac.update({i:(.36,.70,.70)for i in inds});bc.update({i:(.36,.70,.70)for i in bs})
 dr=rdMolDraw2D.MolDraw2DSVG(900,440);op=dr.drawOptions();op.padding=.16;op.clearBackground=False;op.minFontSize=18;op.maxFontSize=27;op.bondLineWidth=2
 dr.DrawMolecule(m,highlightAtoms=list(ac),highlightBonds=list(bc),highlightAtomColors=ac,highlightBondColors=bc);dr.FinishDrawing()
 (O/e['svgPath']).write_text(dr.GetDrawingText().replace('<!-- END OF HEADER -->','<title>'+html.escape(name)+'</title><desc>'+html.escape(caption)+'</desc>'),encoding='utf-8')
 def model(mol,dim):
  c=mol.GetConformer();return {'id':id,'name':name,'formula':formula,'representation':dim,'has3D':dim=='3d','allowRotation':dim=='3d','coordinateUnits':'angstrom'if dim=='3d'else'drawing units','indexConvention':'zero-based','modelType':'Computed free-molecule reference, not measured coordinates','caption':caption,'atoms':[{'index':a.GetIdx(),'element':a.GetSymbol(),'x':round(c.GetAtomPosition(a.GetIdx()).x,6),'y':round(c.GetAtomPosition(a.GetIdx()).y,6),'z':round(c.GetAtomPosition(a.GetIdx()).z,6),'formalCharge':a.GetFormalCharge(),'implicitHydrogenCount':a.GetTotalNumHs()}for a in mol.GetAtoms()],'bonds':[{'a':b.GetBeginAtomIdx(),'b':b.GetEndAtomIdx(),'order':b.GetBondTypeAsDouble()}for b in mol.GetBonds()],'functionalGroups':groups,'computedBy':'RDKit '+RV,'source':'https://doi.org/'+DOI,'eligible_training':False}
 e['model2dPath']='models/'+id+'-2d.json';write(O/e['model2dPath'],model(m,'2d'));e['functionalGroups']=groups
 h=Chem.AddHs(m);params=AllChem.ETKDGv3();params.randomSeed=20260919;emb=AllChem.EmbedMolecule(h,params)
 conv=AllChem.UFFOptimizeMolecule(h,maxIters=3000)if emb==0 else None
 check(emb==0 and conv==0,id+' ETKDG/UFF conformer converged')
 if emb==0 and conv==0:
  e['model3dPath']='models/'+id+'-3d.json';model3=model(h,'3d');write(O/e['model3dPath'],model3)
  check(all(math.isfinite(a[v])for a in model3['atoms']for v in ['x','y','z']),id+' finite conformer coordinates')
  check(rdMolDescriptors.CalcMolFormula(h)==formula,id+' explicit-H conformer formula')
 e['provenance'].update(smiles=smi,software='RDKit '+RV,coordinates='2D depiction and ETKDGv3/UFF computed free-molecule conformer',conformerConverged=conv==0)
 e['assetHashes']={k:sha(O/e[k])for k in ['svgPath','model2dPath','model3dPath']if e[k]};entries.append(e)
cards=[
 ('identity-shah-agno3','Silver nitrate','AgNO3','formula',['AgNO3','Silver nitrate — cited comparator','No coordination geometry assigned'],'Chemical identity for the prior aqueous silver-nitrate optical comparator discussed in Figure 7; this is not a precursor in the current supercritical CO2 synthesis. Formula reference only; no measured coordination geometry is assigned.'),
 ('identity-shah-ag-acac','Silver acetylacetonate','C5H7AgO2','formula',['Ag(acac)','Silver acetylacetonate','Coordination geometry unresolved'],'Source chemical identity Ag(acac). Formula reference only; no discrete monomer, polymeric coordination or measured Ag–O geometry is inferred.'),
 ('identity-shah-pt-precursor','Platinum precursor as printed',None,'unresolved-identity',['Dimethyl Pt(II) precursor','Printed cyclopentadiene identity unresolved','See source note before interpreting structure'],'The paper prints dimethyl(1,5-cyclopentadiene)platinum(II) twice. This ambiguous name is retained without silently substituting cyclooctadiene or assigning a guessed molecular formula or geometry.'),
 ('identity-shah-fluorinert','Fluorinert electronic liquid',None,'mixture',['Fluorinert','Fluorinated dispersion medium','Grade / exact composition not reported'],'Commercial fluorinated liquid named in the paper. Grade and molecular composition are not specified; no single molecular formula or conformer is assigned.'),
 ('identity-shah-ag','Fluorothiol-coated silver nanocrystals','Ag','solid',['Ag nanocrystals','Fluorothiol surface coating','Original TEM retains specimen scope'],'Product composition and surface context. The source reports crystalline cores, {111} fringes and some polycrystalline specimens; this card is not measured atomic coordinates or a solved ligand shell.'),
 ('identity-shah-ir','Fluorothiol-coated iridium nanocrystals','Ir','solid',['Ir nanocrystals','Fluorothiol surface coating','No refined atomic coordinates supplied'],'Product identity. Original Figure 8a supplies microscopy with its own scale bars; no exact mean diameter, refined phase or ligand coordinates are inferred.'),
 ('identity-shah-pt','Fluorothiol-coated platinum nanocrystals','Pt','solid',['Pt nanocrystals','Fluorothiol surface coating','No refined atomic coordinates supplied'],'Product identity. Original Figure 8b supplies microscopy; no exact mean diameter, refined phase or ligand coordinates are inferred.'),
 ('identity-shah-tem-grid','Carbon-coated copper TEM grid',None,'support',['Carbon film / Cu grid','200 mesh microscopy support','Support geometry is illustrative'],'Microscopy support, distinct from the metal nanocrystal composition. Mesh count is a source acquisition detail, not a particle dimension.'),
 ('identity-shah-metal-dispersion','Metal nanocrystal dispersion',None,'mixture',['Ag, Ir OR Pt dispersion','Separate source-specific specimens','No mixed-metal product implied'],'A generic operation input shared by separate elemental-metal specimens. It does not assert an Ag–Ir–Pt alloy, mixed batch or unreported concentration.'),
 ('identity-shah-size-data','TEM particle-size observations',None,'analytical-data',['TEM diameter observations','Statistical analysis input','Not a molecular species'],'Sample-specific TEM diameter observations are analytical data; normalized distributions and moments are derived under stated spherical-particle assumptions, not additional synthesis batches.')]
for id,name,formula,kind,rows,caption in cards:
 e=base(id,name,formula,kind,caption)
 svg='<svg xmlns="http://www.w3.org/2000/svg" width="900" height="360" viewBox="0 0 900 360"><title>'+html.escape(name)+'</title><desc>'+html.escape(caption)+'</desc><rect x="18" y="20" width="864" height="320" rx="20" fill="#f1f6f9" stroke="#cbdce6"/>'
 for y,row,size in zip([120,199,263],rows,[32,22,19]):svg+=f'<text x="450" y="{y}" text-anchor="middle" font-family="Arial,sans-serif" font-size="{size}" fill="#254a5c">{html.escape(row)}</text>'
 (O/e['svgPath']).write_text(svg+'</svg>',encoding='utf-8');e['assetHashes']={'svgPath':sha(O/e['svgPath'])};entries.append(e)
write(O/'registry-additions.json',{'schemaVersion':'1.0.0','entries':entries})
write(O/'molecular-generation-check.json',{'status':'passed'if all(c['passed']for c in checks)else'failed','checks':checks,'entries':len(entries),'sourceSha256':SH})
write(O/'asset-manifest.json',{'files':[{'path':p.relative_to(O).as_posix(),'sha256':sha(p)}for folder in ['svg','models']for p in sorted((O/folder).glob('*'))]})
for offset in range(0,len(entries),6):
 sheet=Image.new('RGB',(1200,900),'#dce7ec')
 for j,e in enumerate(entries[offset:offset+6]):
  d=pymupdf.open(stream=(O/e['svgPath']).read_bytes(),filetype='svg');pdf=pymupdf.open('pdf',d.convert_to_pdf());px=pdf[0].get_pixmap(matrix=pymupdf.Matrix(.62,.62),alpha=False);im=Image.frombytes('RGB',(px.width,px.height),px.samples);can=Image.new('RGB',(600,300),'white');can.paste(im,(15,25));ImageDraw.Draw(can).text((10,4),e['id'],fill='black');sheet.paste(can,(j%2*600,j//2*300))
 sheet.save(O/'review'/f'molecular-contact-{offset//6+1}.png')
print('Created',len(entries),'private chemical/product references;',sum(c['passed']for c in checks),'/',len(checks),'checks passed.')
