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
DOI='10.1021/ja036811v';SH='48bb96493905290ae44c58f2346c6313677041e68ec5a9d50bdc428011c2be9f'
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
entries=[];checks=[]
def check(ok,text):checks.append({'check':text,'passed':bool(ok)})
def base(id,name,formula,kind,caption):
 return dict(id=id,name=name,aliases=[name],formula=formula,displayFormula=formula,depictionKind=kind,pubchemCid=None,sourceUrls=['https://doi.org/'+DOI],svgPath='svg/'+id+'.svg',model2dPath=None,model3dPath=None,functionalGroups=[],caption=caption,limitations=[],provenance={'sourceDoi':DOI,'sourceSha256':SH,'identitySource':'Named compound and/or connectivity diagram in inspected local main article; no external database lookup claimed.','measuredCoordinates':False,'eligible_training':False},assetHashes={})
# The expected formulas use RDKit Hill order; display formulas retain chemical convention.
definitions=[
('zinc-acetate-dihydrate','Zinc acetate dihydrate','[Zn+2].CC(=O)[O-].CC(=O)[O-].O.O','C4H10O6Zn','Zn(OAc)2·2H2O',False,'Reported hydrate represented as disconnected formula components. No Zn–acetate coordination, crystal packing or DMSO solution complex is assigned.'),
('cobalt-acetate-tetrahydrate','Cobalt(II) acetate tetrahydrate','[Co+2].CC(=O)[O-].CC(=O)[O-].O.O.O.O','C4H14CoO8','Co(OAc)2·4H2O',False,'Reported hydrate represented as disconnected formula components. No cobalt coordination, hydration shell or DMSO speciation is assigned.'),
('nickel-perchlorate-hexahydrate','Nickel(II) perchlorate hexahydrate','[Ni+2].[O-]Cl(=O)(=O)=O.[O-]Cl(=O)(=O)=O.O.O.O.O.O.O','H12Cl2NiO14','Ni(ClO4)2·6H2O',False,'Reported hydrate formula components. Perchlorate connectivity is a resonance representation, not a measured nickel complex or hydrated crystal.'),
('dodecylamine','Dodecylamine','CCCCCCCCCCCCN','C12H27N','C12H27N',True,'Free dodecylamine connectivity and computed conformer. Surface binding, protonation and ligand density on ZnO are not reconstructed.')]

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
 patterns=[('Thiol','[S;H1]',(.87,.67,.18)),('Silane anchor','[Si](O)(O)O',(.29,.66,.69)),('Primary amine','[N;H2]',(.45,.55,.86)),('Carboxylate group','C(=O)[O-]',(.88,.47,.43)),('Disulfide bridge','SS',(.87,.67,.18)),('Nitro group','[N+](=O)[O-]',(.5,.57,.84)),('Phosphate group','P(=O)(O)(O)O',(.29,.66,.69)),('Sulfonic acid','S(=O)(=O)O',(.29,.66,.69)),('Hydroxyl','[O;H1]',(.6,.72,.36))]
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
('identity-schwartz-zinc-acetate-additive','Zinc acetate clarity additive',None,'unresolved-identity',['Zn(OAc)2 · hydration unspecified','Approximately 10 mg','Only for a cloudy suspension'],'The source writes approximately10mg Zn(OAc)2 for optical-clarity restoration without specifying hydration. The separate main starting salt is dihydrate; that hydration is not silently transferred here.'),
('identity-schwartz-topo-technical','Technical-grade TOPO',None,'mixture',['TOPO-containing technical reagent','Phosphonic-acid impurities reported','Mixture composition unspecified'],'Footnote16 specifies technical-grade TOPO and unidentified phosphonic-acid impurities. The linked pure TOPO structure describes only the named component, not the full reagent or actual surface ligand distribution.'),
('identity-schwartz-zno-specimen','ZnO nanocrystals','ZnO','specimen',['Wurtzite ZnO nanocrystals','Pure-host route','Particle dimensions remain sample-specific'],'Source reports ZnO phase and TEM/electron-diffraction evidence. This identity card is not a measured particle lattice; the separate independent bulk CIF does not reconstruct the synthesized sample.'),
('identity-schwartz-co-specimen','Co-doped ZnO nanocrystals','ZnO:Co','specimen',['Co2+-doped wurtzite ZnO','Dopant loading varies by sample','Feed and incorporated content kept separate'],'Source-assigned substituted Co2+ in ZnO. No exact universal stoichiometry, site occupancy, radial dopant profile or measured atomic coordinates are supplied.'),
('identity-schwartz-ni-specimen','Ni-doped ZnO nanocrystals','ZnO:Ni','specimen',['Ni2+-doped wurtzite ZnO','Dopant loading varies by sample','Feed and incorporated content kept separate'],'Source-assigned substituted Ni2+ in ZnO. No exact universal stoichiometry, site occupancy, radial dopant profile or measured atomic coordinates are supplied.'),
('identity-schwartz-surface-co-specimen','Surface-bound Co on ZnO control',None,'specimen',['Co intentionally bound to ZnO surface','SI Figure S2 cleaning control','Surface-loading preparation incomplete'],'This control has intentionally surface-bound Co and is separate from substitutionally doped ZnO. No exact loading, binding geometry or missing preparation recipe is inferred.'),
('identity-schwartz-co-aggregate-specimen','Co-doped ZnO aggregate powder','ZnO:Co','specimen',['3.6% Co:ZnO aggregate specimen','Slow evaporation from ethanol','Magnetic measurement population'],'Macroscopic aggregates of doped nanocrystals are distinct from isolated colloids. The source prints4.9 and5.0nm precursor sizes in different places. No measured interparticle atomic reconstruction is supplied.'),
('identity-schwartz-quartz','Quartz optical support','SiO2','support',['Quartz disk','Spin-coated optical film support','Thickness and spin settings unreported'],'Source-named optical support, not a synthesis ingredient or a refined quartz crystal. SiO2 identifies the material; no measured substrate structure or thickness is assigned.')]

for id,name,formula,kind,rows,caption in cards:
 e=base(id,name,formula,kind,caption)
 svg='<svg xmlns="http://www.w3.org/2000/svg" width="900" height="360" viewBox="0 0 900 360"><title>'+html.escape(name)+'</title><desc>'+html.escape(caption)+'</desc><rect x="18" y="20" width="864" height="320" rx="20" fill="#f1f6f9" stroke="#cbdce6"/>'
 for y,row,size in zip([120,199,263],rows,[30,22,19]):svg+=f'<text x="450" y="{y}" text-anchor="middle" font-family="Arial,sans-serif" font-size="{size}" fill="#294451">{html.escape(row)}</text>'
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
