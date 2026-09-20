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
DOI='10.1021/jp0105488';SH='98a21f9489eda29e1e1f5f40b336661ceb1b27d9468095a9b44ad342a780400b'
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
entries=[];checks=[]
def check(ok,text):checks.append({'check':text,'passed':bool(ok)})
def base(id,name,formula,kind,caption):
 return dict(id=id,name=name,aliases=[name],formula=formula,displayFormula=formula,depictionKind=kind,pubchemCid=None,sourceUrls=['https://doi.org/'+DOI],svgPath='svg/'+id+'.svg',model2dPath=None,model3dPath=None,functionalGroups=[],caption=caption,limitations=[],provenance={'sourceDoi':DOI,'sourceSha256':SH,'identitySource':'Named compound and/or connectivity diagram in inspected local main article; no external database lookup claimed.','measuredCoordinates':False,'eligible_training':False},assetHashes={})
# The expected formulas use RDKit Hill order; display formulas retain chemical convention.
definitions=[
 ('mps-trimethoxy','(3-Mercaptopropyl)trimethoxysilane','CO[Si](CCCS)(OC)OC','C6H16O3SSi','C6H16O3SSi',True,'Free MPS reagent, not the hydrolyzed silanol drawn schematically in Figure 1.'),
 ('aps-trimethoxy','(3-Aminopropyl)trimethoxysilane','CO[Si](CCCN)(OC)OC','C6H17NO3Si','C6H17NO3Si',True,'Free APS reagent; successful later amine functionalization is distinct from unsuccessful APS priming.'),
 ('mercaptopropionic-acid','3-Mercaptopropionic acid','O=C(O)CCS','C3H6O2S','C3H6O2S',True,'Neutral free MPA reference. Surface-bound form and solution protonation depend on conditions.'),
 ('dimethylaminopyridine','4-(Dimethylamino)pyridine','CN(C)c1ccncc1','C7H10N2','C7H10N2',True,'DMAP reference identity; the supplier-list misspelling is retained separately in source evidence.'),
 ('dtnb','5,5\u2032-Dithiobis(2-nitrobenzoic acid)','O=C(O)c1c([N+](=O)[O-])ccc(SSc2ccc([N+](=O)[O-])c(C(=O)O)c2)c1','C14H8N2O8S2','C14H8N2O8S2',True,'Ellman reagent connectivity in the free-acid reference form. Nitro groups are ortho to carboxyl and disulfide groups are at each ring position 5. This is not the colored assay product or measured buffer speciation.'),
 ('mes-buffer-acid','2-(N-Morpholino)ethanesulfonic acid','O=S(=O)(O)CCN1CCOCC1','C6H13NO4S','C6H13NO4S',True,'Neutral MES reference connectivity. The buffer has pH-dependent protonation; no unique aqueous species is asserted.'),
 ('glycerol','Glycerol','OCC(O)CO','C3H8O3','C3H8O3',True,'Glycerol component reference, not a complete model of the gel-loading solution.'),
 ('tetramethylammonium-hydroxide','Tetramethylammonium hydroxide','C[N+](C)(C)C.[OH-]','C4H13NO','C4H13NO',False,'Separated tetramethylammonium and hydroxide ionic identities. No ion-pair geometry or methanolic stock concentration is assigned.'),
 ('tetramethylammonium-hydroxide-pentahydrate','Tetramethylammonium hydroxide pentahydrate','C[N+](C)(C)C.[OH-].O.O.O.O.O','C4H23NO6','C4H13NO·5H2O',False,'Formula components of the stated pentahydrate; water positions and ion arrangement are a 2D identity diagram, not a crystal structure.'),
 ('dipotassium-hydrogen-phosphate','Dipotassium hydrogen phosphate','O=P([O-])([O-])O.[K+].[K+]','HK2O4P','K2HPO4',False,'One phosphate-buffer component as separated ions. The mixed buffer has pH-dependent speciation and no reported component ratio.'),
 ('potassium-dihydrogen-phosphate','Potassium dihydrogen phosphate','O=P([O-])(O)O.[K+]','H2KO4P','KH2PO4',False,'One phosphate-buffer component as separated ions. No ion geometry or buffer component ratio is inferred.')]
for id,name,smi,formula,display,conformer,specific in definitions:
 m=Chem.MolFromSmiles(smi);assert m is not None
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
 dr=rdMolDraw2D.MolDraw2DSVG(900,440);op=dr.drawOptions();op.padding=.16;op.clearBackground=False;op.minFontSize=18;op.maxFontSize=27;op.bondLineWidth=2
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
 ('identity-gerion-phosphonate','(Trihydroxysilyl)propyl methylphosphonate solution',None,'mixture',['Silane–propyl–phosphonate','42 wt% in water','Counterion / exact stock formula unverified'],'Printed reagent identity retained. Figure 1 depicts a negatively charged phosphonate functionality. No complete stock formula, counterion or molecular geometry is invented.'),
 ('identity-gerion-pb','Phosphate buffer',None,'mixture',['K2HPO4 + KH2PO4','Aqueous phosphate buffer','Component ratio not reported'],'Both named phosphate salts and water are separate molecular references. Source-specific concentration and pH belong to the current operation.'),
 ('identity-gerion-tbe','Tris–borate–EDTA buffer',None,'mixture',['Tris · borate · EDTA','TBE buffer','Composition / speciation unresolved'],'Commercially supplied TBE buffer. No unreported component concentrations, salt forms or mixture geometry are assigned.'),
 ('identity-gerion-agarose','Agarose gel',None,'polymer',['Agarose network','Electrophoresis matrix','Not a nanoparticle shell'],'Cross-linked or entangled gel structure is not characterized atomically in the supplied source. Source-specific gel percentage and buffer remain operation data.'),
 ('identity-gerion-sephadex','Sephadex G25 medium',None,'polymer',['Sephadex G25','Size-exclusion medium','Cross-linked dextran matrix'],'Commercial chromatographic medium, not the product composition. No exact polymer sequence or pore geometry is assigned.'),
 ('identity-gerion-carbon-grid','Carbon-coated electron-microscopy grid',None,'support',['Carbon-coated grid','TEM / EELS specimen support','Mesh applies only where reported'],'Ultrathin carbon grid for TEM or 400 mesh carbon-coated grid for EELS. A particular metal backing is not reported. Grid properties are not nanocrystal dimensions.'),
 ('identity-gerion-mica','Freshly cleaved mica',None,'support',['Mica substrate','AFM specimen support','Exact mineral composition unreported'],'Freshly cleaved mica is the stated substrate. Do not infer a particular mica mineral formula or confuse substrate height with particle height.'),
 ('identity-gerion-zns-precursors','Unspecified ZnS shell precursors',None,'unresolved-identity',['ZnS shell precursors','Control described in Note 28','Identities and charges unreported'],'The no-CdSe control and room-temperature stock aging use unspecified shell precursors. Cited historical preparations do not supply missing identities in this experiment.'),
 ('identity-gerion-specimens','CdSe/ZnS specimen families',None,'specimen',['CdSe/ZnS specimen families','Siloxane or MPA surface contexts','Separate specimens; no shared batch assumed'],'Shared analytical procedure input. Coating, optical color, medium and lineage retain their explicit source scope; no mixed product or exact batch equivalence implied.'),
 ('identity-gerion-hplc-phase','TSK-gel silica-based stationary phase',None,'support',['TSK-gel G4000-SWxl','Silica-based size-exclusion beads','Chromatography hardware context'],'Stationary-phase material in the analytical HPLC column. Pore and bead dimensions characterize the separation medium, not the nanocrystal product.'),
 ('identity-gerion-siloxane-complexes','Unassigned silica/siloxane complexes',None,'unresolved-identity',['Silica / siloxane complexes','Unassigned solution byproducts','No exact molecular structure supplied'],'Source interpretation of small species in the dispersion. No pure-silica stoichiometry, unique oligomer, exact molecular formula or nanocrystal core is inferred.'),
 ('identity-gerion-mps-primed','MPS-primed CdSe/ZnS intermediate',None,'specimen',['CdSe/ZnS + MPS primer','Intermediate before later functionalization','Shell completeness unresolved'],'MPS-primed intermediate for the optional APS addition. This depiction does not show a final mature siloxane shell or imply that APS replaces the initial MPS primer.')]
for id,name,formula,kind,rows,caption in cards:
 e=base(id,name,formula,kind,caption)
 svg='<svg xmlns="http://www.w3.org/2000/svg" width="900" height="360" viewBox="0 0 900 360"><title>'+html.escape(name)+'</title><desc>'+html.escape(caption)+'</desc><rect x="18" y="20" width="864" height="320" rx="20" fill="#f1f6f9" stroke="#cbdce6"/>'
 for y,row,size in zip([120,199,263],rows,[30,22,19]):svg+=f'<text x="450" y="{y}" text-anchor="middle" font-family="Arial,sans-serif" font-size="{size}" fill="#254a5c">{html.escape(row)}</text>'
 (O/e['svgPath']).write_text(svg+'</svg>',encoding='utf-8');e['assetHashes']={'svgPath':sha(O/e['svgPath'])};entries.append(e)

# Layer diagrams describe architecture only: no atomistic shell or unique core count.
for id,name,formula,coating in [
 ('identity-gerion-cdse-zns','TOPO-capped CdSe/ZnS starting nanocrystals','CdSe/ZnS','TOPO'),
 ('identity-gerion-siloxane','Siloxane-coated CdSe/ZnS nanocrystals','CdSe/ZnS/siloxane','siloxane'),
 ('identity-gerion-mpa','MPA-coated CdSe/ZnS nanocrystals','CdSe/ZnS','MPA')]:
 cap='Layer architecture schematic, not atomic coordinates or a measured particle reconstruction. Source does not establish a unique crystal phase, shell uniformity or number of CdSe/ZnS cores in each siloxane entity.'
 e=base(id,name,formula,'specimen',cap)
 svg='<svg xmlns="http://www.w3.org/2000/svg" width="900" height="420" viewBox="0 0 900 420"><title>'+html.escape(name)+'</title><desc>'+html.escape(cap)+'</desc><rect x="10" y="12" width="880" height="396" rx="24" fill="#f5f9fb"/>'
 if coating=='siloxane':svg+='<circle cx="248" cy="200" r="129" fill="#ddeeee" stroke="#64a4aa" stroke-width="4" stroke-dasharray="5 4"/>'
 svg+='<circle cx="248" cy="200" r="91" fill="#d6b875" stroke="#987542" stroke-width="3"/><circle cx="248" cy="200" r="61" fill="#c66452" stroke="#98483f" stroke-width="3"/>'
 if coating!='siloxane':
  for i in range(12):
   a=i*math.pi/6;x=248+93*math.cos(a);y=200+93*math.sin(a);x2=248+118*math.cos(a);y2=200+118*math.sin(a)
   svg+=f'<path d="M{x:.1f} {y:.1f} L{x2:.1f} {y2:.1f}" stroke="#3c858b" stroke-width="3"/>'
 rows=['CdSe core','ZnS shell', 'Organic-functional siloxane' if coating=='siloxane' else coating+' surface ligands']
 for y,row,col in zip([139,198,257],rows,['#ad5142','#a78142','#3c858b']):svg+=f'<circle cx="453" cy="{y-7}" r="7" fill="{col}"/><text x="476" y="{y}" font-family="Arial,sans-serif" font-size="23" fill="#294451">{row}</text>'
 svg+='<text x="450" y="357" text-anchor="middle" font-family="Arial,sans-serif" font-size="18" fill="#617580">Architecture illustration · not to scale · no measured atomic model</text></svg>'
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
