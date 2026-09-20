from pathlib import Path
import sys,json,hashlib,html,collections,math,re
sys.dont_write_bytecode=True
sys.path.insert(0,'[local path redacted]')
sys.path.insert(0,'[local path redacted]')
from rdkit import Chem,__version__ as RV
from rdkit.Chem import rdDepictor,rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D
import pymupdf
from PIL import Image,ImageDraw
B=Path(__file__).resolve().parent.parent; O=B/'visuals';REG=Path('[local path redacted]')
DOI='10.1021/ja9805425';SH='9ab487d6125bd30631b0acf02803e59b0a5bfc4524ae1b3f25d4e40e5e8ff98d'
for n in ['svg','models','review']:(O/n).mkdir(exist_ok=True)
def load(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(v,s):checks.append({'check':s,'passed':bool(v)})
def base(id,name,formula,kind,caption):return {'id':id,'name':name,'aliases':[name],'formula':formula,'displayFormula':formula,'depictionKind':kind,'pubchemCid':None,'sourceUrls':['https://doi.org/'+DOI],'svgPath':None,'model2dPath':None,'model3dPath':None,'functionalGroups':[],'caption':caption,'limitations':[],'provenance':{'sourceDoi':DOI,'sourceSha256':SH,'identitySource':'Named reagent/formula in inspected main p.5343 footnotes 21–22; no unverified database identifier','measuredCoordinates':False,'eligible_training':False,'sourceRecords':[]}}
entries=[]
name='Tris(trimethylsilyl)arsine';id='tms3as';formula='C9H27AsSi3';smi='C[Si](C)(C)[As]([Si](C)(C)C)[Si](C)(C)C'
caption='Illustrative 2D connectivity for the source TMS₃As reagent, with the three trimethylsilyl groups highlighted. Coordinates are a computed drawing, not a measured molecular geometry, In–As intermediate or solution speciation model.'
e=base(id,name,formula,'molecule',caption);m=Chem.MolFromSmiles(smi)
check(m is not None,'TMS3As parses');check(rdMolDescriptors.CalcMolFormula(m)==formula,'TMS3As elemental formula C9H27AsSi3');check(Chem.GetFormalCharge(m)==0,'TMS3As charge neutral');check(len(Chem.GetMolFrags(m))==1,'TMS3As one connected reference')
rdDepictor.Compute2DCoords(m);c=m.GetConformer();As=[a.GetIdx() for a in m.GetAtoms() if a.GetSymbol()=='As'][0];Sis=[a.GetIdx() for a in m.GetAtoms() if a.GetSymbol()=='Si'];groups=[]
check(len(Sis)==3 and m.GetAtomWithIdx(As).GetDegree()==3,'TMS3As arsenic bonded to three silicon centers')
colors=[(.84,.65,.25),(.55,.42,.69),(.23,.66,.63)];atomColors={};bondColors={}
for i,si in enumerate(Sis):
 inds=[si]+[a.GetIdx() for a in m.GetAtomWithIdx(si).GetNeighbors() if a.GetSymbol()=='C'];bonds=[b.GetIdx() for b in m.GetBonds() if b.GetBeginAtomIdx() in inds and b.GetEndAtomIdx() in inds];groups.append({'label':f'Trimethylsilyl group {i+1}','atomIndices':inds,'bondIndices':bonds});check(len(inds)==4 and len(bonds)==3,f'TMS group {i+1} has Si with three methyl carbons')
 for a in inds:atomColors[a]=colors[i]
 for b in bonds:bondColors[b]=colors[i]
dr=rdMolDraw2D.MolDraw2DSVG(840,400);op=dr.drawOptions();op.clearBackground=False;op.padding=.2;op.minFontSize=23;op.maxFontSize=30;op.bondLineWidth=2
dr.DrawMolecule(m,highlightAtoms=list(atomColors),highlightBonds=list(bondColors),highlightAtomColors=atomColors,highlightBondColors=bondColors);dr.FinishDrawing();svg=dr.GetDrawingText().replace('<!-- END OF HEADER -->','<title>'+html.escape(name)+'</title><desc>'+html.escape(caption)+'</desc>')
e['svgPath']='svg/'+id+'.svg';(O/e['svgPath']).write_text(svg,encoding='utf8');e['functionalGroups']=groups;e['model2dPath']='models/'+id+'-2d.json';model={'id':id,'name':name,'formula':formula,'representation':'2d','has3D':False,'allowRotation':False,'coordinateUnits':'drawing units','indexConvention':'zero-based','modelType':'Source-identity connectivity schematic','caption':caption,'atoms':[{'index':a.GetIdx(),'element':a.GetSymbol(),'x':round(c.GetAtomPosition(a.GetIdx()).x,6),'y':round(c.GetAtomPosition(a.GetIdx()).y,6),'z':0,'formalCharge':a.GetFormalCharge(),'implicitHydrogenCount':a.GetTotalNumHs()} for a in m.GetAtoms()],'bonds':[{'a':b.GetBeginAtomIdx(),'b':b.GetEndAtomIdx(),'order':b.GetBondTypeAsDouble()} for b in m.GetBonds()],'functionalGroups':groups,'computedBy':'RDKit '+RV,'source':'https://doi.org/'+DOI,'eligible_training':False}
save(O/e['model2dPath'],model);e['provenance'].update(smiles=smi,software='RDKit '+RV,coordinates='rdDepictor.Compute2DCoords; planar drawing only',energyOptimization='Not applicable to 2D schematic; no optimized conformer claimed');e['assetHashes']={k:sha(O/e[k]) for k in ['svgPath','model2dPath']};entries.append(e)
def txt(x,y,s,size=22):return f'<text x="{x}" y="{y}" text-anchor="middle" font-family="Arial,sans-serif" font-size="{size}" fill="#254a5c">{html.escape(s)}</text>'
cards=[('identity-peng-incl3-top','Indium chloride in trioctylphosphine',None,'mixture',['InCl₃ + TOP','Prepared stock solution','Coordination/speciation unresolved'],'The source names a concentrated InCl₃·TOP solution prepared from 0.33 g InCl₃ per mL of distilled TOP. The dot is not evidence for a solved 1:1 molecular adduct or a measured In–P coordination geometry. Components remain separately inspectable.'),('identity-peng-cdse','CdSe nanocrystals','CdSe','solid',['CdSe nanocrystals','Source sample identity','Atomic structure not measured here'],'Nanocrystal product identity, not a molecule or refined unit cell. Main Figure 3 shows a separate 8.5 nm CdSe TEM context. No phase-resolved lattice, surface-ligand coordinates or exact atomic reconstruction is supplied for the focusing series.'),('identity-peng-inas','InAs nanocrystals','InAs','solid',['InAs nanocrystals','Source sample identity','Atomic structure not measured here'],'Nanocrystal product identity, not a molecule or refined unit cell. Main and SI report optical measurements and size calibration. No InAs micrograph, diffraction pattern or measured atomic lattice is supplied in this source bundle.'),('identity-peng-pl-data','CdSe or InAs photoluminescence data',None,'analytical-data',['Photoluminescence data','CdSe OR InAs spectral input','Analytical data, not a chemical species'],'Separate material-specific measured spectra feed the analysis procedure. This identity card is not a chemical, mixed CdSe–InAs sample or generated spectrum. The original measured traces remain in their own paper/SI assets.')]
for id,name,formula,kind,rows,caption in cards:
 e=base(id,name,formula,kind,caption);svg='<svg xmlns="http://www.w3.org/2000/svg" width="840" height="360" viewBox="0 0 840 360" role="img"><title>'+html.escape(name)+'</title><desc>'+html.escape(caption)+'</desc><rect x="20" y="22" width="800" height="316" rx="18" fill="#f1f6f9" stroke="#cbdce6"/>'
 if 'incl3' in id:svg+=txt(220,165,'InCl₃',37)+txt(420,165,'+',30)+txt(620,165,'TOP',37)+txt(420,224,rows[1],23)+txt(420,270,rows[2],18)
 else:svg+=txt(420,138,rows[0],37)+txt(420,207,rows[1],23)+txt(420,270,rows[2],18)
 svg+='</svg>';e['svgPath']='svg/'+id+'.svg';(O/e['svgPath']).write_text(svg,encoding='utf8');e['assetHashes']={'svgPath':sha(O/e['svgPath'])};entries.append(e)
old={e['id']:e for e in load(REG/'registry.json')['entries']};new={e['id']:e for e in entries};combined={**old,**new}
# Exact canonical material IDs are bound only after the root has written drafts.
mapping={'se':'selenium-element','selenium':'selenium-element','cdme2':'dimethylcadmium','dimethylcadmium':'dimethylcadmium','tbp':'tbp','top':'top','topo':'topo','ar':'argon','argon':'argon','methanol':'methanol','toluene':'toluene','incl3':'indium-chloride','tms3as':'tms3as','incl3-top':'identity-peng-incl3-top','stock':'identity-peng-incl3-top','cdse':'identity-peng-cdse','inas':'identity-peng-inas','spectra':'identity-peng-pl-data'}
bindings={};notes={};sourceHashes={};unresolved=[];reuse=set()
for p in sorted((B/'canonical-drafts').glob('*.json')):
 r=load(p);rid=r['record_id'];bindings[rid]={};notes[rid]={};sourceHashes[rid]=sha(p)
 for material in r.get('materials',[]):
  mid=material['id'];cid=mapping.get(mid)
  if not cid:unresolved.append({'record':rid,'material':mid,'name':material.get('name')});continue
  e=combined[cid];bindings[rid][mid]=cid;notes[rid][mid]='Chemical identity reference only. Source quantities and handling belong to this Peng1998 record, not an earlier recipe.'
  # Elemental formulas here contain no parentheses or mixtures; preserve source order independently of this check.
  if material.get('formula') and e.get('formula'):
   counts=lambda f:collections.Counter({el:int(n or 1) for el,n in re.findall(r'([A-Z][a-z]?)(\d*)',f)})
   check(counts(material['formula'])==counts(e['formula']),rid+'/'+mid+' reference formula elemental identity')
  else:check(material.get('formula')==e.get('formula'),rid+'/'+mid+' nonmolecular identity retains null formula')
  if cid in new:e['provenance']['sourceRecords'].append({'recordId':rid,'materialId':mid,'evidence':material.get('evidence',[])})
  else:reuse.add(cid)
for a in model['atoms']:check(all(math.isfinite(a[k]) for k in ['x','y','z']),f'TMS3As atom {a["index"]} finite drawing coordinates')
for b in model['bonds']:
 check(0<=b['a']<len(model['atoms']) and 0<=b['b']<len(model['atoms']) and b['a']!=b['b'],'TMS3As bond endpoints valid '+str(b['a'])+'-'+str(b['b']))
 a1=model['atoms'][b['a']];a2=model['atoms'][b['b']];dist=math.hypot(a1['x']-a2['x'],a1['y']-a2['y']);check(.5<dist<3,'TMS3As drawing bond length plausible in drawing units '+str(b['a'])+'-'+str(b['b']))
for cid in sorted(reuse):
 for k,h in old[cid]['assetHashes'].items():check(sha(REG/old[cid][k])==h,cid+' reused '+k+' hash verified')
for e in entries:
 for k,h in e['assetHashes'].items():check(sha(O/e[k])==h,e['id']+' '+k+' hash verified')
check(not unresolved,'Every canonical material has an explicit reference binding')
summary={'newEntryCount':len(entries),'new2dModels':1,'new3dModels':0,'referenceCards':len(cards),'reusedEntryCount':len(reuse),'recordCount':len(bindings),'materialBindingCount':sum(map(len,bindings.values())),'unresolvedBindings':len(unresolved),'draftsPresent':bool(bindings)}
save(O/'registry-additions.json',{'schemaVersion':'1.0.0','entries':entries,'summary':summary})
save(O/'bindings-additions.json',{'schemaVersion':'1.0.0','recordBindings':bindings,'bindingNotes':notes,'sourceRecordSha256':sourceHashes,'unresolved':unresolved})
save(O/'reused-references.json',{'registrySha256':sha(REG/'registry.json'),'entries':[old[x] for x in sorted(reuse)]})
save(O/'molecular-validation.json',{'status':'passed' if all(c['passed'] for c in checks) and bindings else 'pending_drafts' if not bindings else 'failed','checks':checks,'summary':summary})
save(O/'asset-manifest.json',{'sourceDoi':DOI,'sourceSha256':SH,'illustrative_only':True,'eligible_training':False,'files':[{'path':p.relative_to(O).as_posix(),'sha256':sha(p)} for folder in ['svg','models'] for p in sorted((O/folder).glob('*'))]})
ims=[]
for e in entries:
 d=pymupdf.open(stream=(O/e['svgPath']).read_bytes(),filetype='svg');pdf=pymupdf.open('pdf',d.convert_to_pdf());px=pdf[0].get_pixmap(matrix=pymupdf.Matrix(.7,.7),alpha=False);im=Image.frombytes('RGB',(px.width,px.height),px.samples);can=Image.new('RGB',(620,330),'white');can.paste(im,(10,28));ImageDraw.Draw(can).text((10,3),e['id'],fill='black');ims.append(can)
sheet=Image.new('RGB',(1240,990),'#dce7ec')
for i,im in enumerate(ims):sheet.paste(im,(i%2*620,i//2*330))
sheet.save(O/'review'/'molecular-contact.png');print(json.dumps(summary))
