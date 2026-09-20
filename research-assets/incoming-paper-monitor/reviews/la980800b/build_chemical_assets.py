from pathlib import Path
import sys,json,hashlib,html,re,collections
sys.dont_write_bytecode=True
sys.path.insert(0,'[local path redacted]');sys.path.insert(0,'[local path redacted]')
from rdkit import Chem,__version__ as RV
from rdkit.Chem import rdDepictor,rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D
import pymupdf
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent;O=R/'molecular-assets';O.mkdir(exist_ok=True)
for name in ['svg','models','review']:(O/name).mkdir(exist_ok=True)
REG=Path('[local path redacted]');DOI='10.1021/la980800b';SH='e581449713ddca5e0cb68d05593df476d0e5150b88bc7c6dcbdb269ac70881fb'
def load(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(v,label):checks.append({'check':label,'passed':bool(v)})
def flat(s):return collections.Counter({e:int(n or 1) for e,n in re.findall(r'([A-Z][a-z]?)(\d*)',s)})
old={e['id']:e for e in load(REG/'registry.json')['entries']};checks=[];entries=[];mapping={'h2so4':'sulfuric-acid','hf':'hydrogen-fluoride','water':'water','ethanol':'ethanol','mecn':'acetonitrile','nitrogen':'nitrogen'}
def base(id,name,formula,kind,caption):return {'id':id,'name':name,'aliases':[name],'formula':formula,'displayFormula':formula,'depictionKind':kind,'pubchemCid':None,'sourceUrls':['https://doi.org/'+DOI],'svgPath':None,'model2dPath':None,'model3dPath':None,'functionalGroups':[],'caption':caption,'limitations':[caption],'provenance':{'sourceDoi':DOI,'sourceSha256':SH,'identitySource':'Explicit identity in inspected local paper; no guessed database identifier','sourceRecords':[],'measuredCoordinates':False,'eligible_training':False}}
ions=[('agclo4','silver-perchlorate-monohydrate','Silver perchlorate monohydrate','AgClO4·H2O','AgClH2O5','[Ag+].[O-]Cl(=O)(=O)=O.O',3),('liclo4','lithium-perchlorate','Lithium perchlorate','LiClO4','ClLiO4','[Li+].[O-]Cl(=O)(=O)=O',2)]
for mid,id,name,formula,expect,smi,components in ions:
 caption='Illustrative 2D ionic component connectivity only. Fragment positions are arbitrary; no dissolved complex, solvation shell, cation–perchlorate geometry or crystal lattice is asserted. RDKit uses a charge-separated perchlorate representation; displayed formal charges are bonding bookkeeping, not oxidation states.'
 if mid=='agclo4':caption+=' The water component preserves the source-named monohydrate reagent; it does not establish a coordinated water or an aqueous plating solution.'
 e=base(id,name,formula,'ionic',caption);m=Chem.MolFromSmiles(smi);check(m is not None,id+' parses');check(flat(rdMolDescriptors.CalcMolFormula(m))==flat(expect),id+' formula');check(Chem.GetFormalCharge(m)==0,id+' net charge');check(len(Chem.GetMolFrags(m))==components,id+' disconnected component count');rdDepictor.Compute2DCoords(m);c=m.GetConformer()
 dr=rdMolDraw2D.MolDraw2DSVG(840,360);op=dr.drawOptions();op.clearBackground=False;op.padding=.16;op.minFontSize=23;op.maxFontSize=30;op.bondLineWidth=2;dr.DrawMolecule(m);dr.FinishDrawing();svg=dr.GetDrawingText().replace('<!-- END OF HEADER -->','<title>'+html.escape(name)+'</title><desc>'+html.escape(caption)+'</desc>');e['svgPath']='svg/'+id+'.svg';(O/e['svgPath']).write_text(svg,encoding='utf8')
 model={'id':id,'name':name,'formula':formula,'representation':'2d','has3D':False,'allowRotation':False,'coordinateUnits':'drawing units','indexConvention':'zero-based','modelType':'Disconnected ionic/hydrate component reference','caption':caption,'atoms':[{'index':a.GetIdx(),'element':a.GetSymbol(),'x':round(c.GetAtomPosition(a.GetIdx()).x,6),'y':round(c.GetAtomPosition(a.GetIdx()).y,6),'z':0,'formalCharge':a.GetFormalCharge(),'isotope':a.GetIsotope(),'implicitHydrogenCount':a.GetTotalNumHs()} for a in m.GetAtoms()],'bonds':[{'a':b.GetBeginAtomIdx(),'b':b.GetEndAtomIdx(),'order':b.GetBondTypeAsDouble(),'stereo':str(b.GetStereo())} for b in m.GetBonds()],'computedBy':'RDKit '+RV,'source':'https://doi.org/'+DOI,'eligible_training':False}
 e['model2dPath']='models/'+id+'-2d.json';save(O/e['model2dPath'],model);e['assetHashes']={k:sha(O/e[k]) for k in ['svgPath','model2dPath']};e['provenance'].update(smiles=smi,software='RDKit '+RV,modelDimensionPolicy='2D component reference; no invented ion-pair geometry');entries.append(e);mapping[mid]=id
def text(x,y,t,size=20):return f'<text x="{x}" y="{y}" text-anchor="middle" font-family="Arial,sans-serif" font-size="{size}" fill="#254b5e">{html.escape(t)}</text>'
cards=[
 ('si-npp','Antimony-doped n++ silicon (100)','Si','solid','Degenerately Sb-doped silicon substrate. Source doping, face orientation and treatment state belong to the canonical record; no measured dopant coordinates, molecular Si species or reconstructed surface is supplied.'),
 ('si-n','Antimony-doped n-silicon (100)','Si','solid','Nondegenerate Sb-doped comparison substrate. This is distinct from the n++ preparative series; no atomic dopant map or measured surface structure is supplied.'),
 ('h-si','Hydrogen-terminated silicon (100)','Si','surface','H-terminated substrate identity. Hydrogen coverage, oxide residue, surface reconstruction and atom-by-atom coordinates are unreported. Si identifies the substrate; it is not a stoichiometric Si–H molecule.'),
 ('ga-in','Gallium–indium eutectic contact',None,'mixture','Electrical-contact alloy. Ga/In composition, microscopic phase distribution and geometry are unreported; not a discrete Ga–In molecule.'),
 ('silver-paint','Colloidal silver contact paint',None,'mixture','Back-contact formulation with unspecified binder, solvent and silver fraction. Paint silver is separate from the front-face electrodeposited nanoparticle product.'),
 ('ag-wire','Silver reference-electrode wire','Ag','solid','Solid silver reference electrode used with silver-containing solutions. This is an electrode component, not the deposited nanocrystal specimen or a refined crystal model.'),
 ('pt-wire','Platinum counter-electrode wire','Pt','solid','Solid counter electrode. No platinum synthesis, dissolved platinum speciation or Pt nanoparticle product is reported in this procedure.'),
 ('sce','Saturated calomel reference electrode',None,'equipment','Electrode assembly used for silver-free electrolyte. Component fill recipe and numerical reference-potential conversion are not supplied; no complete electrode molecular formula is asserted.'),
 ('ag-si','Silver nanocrystals on hydrogen-terminated Si(100)',None,'composite','Separate Ag nanoparticles and semiconductor substrate. No solved composite unit cell, epitaxial registry, measured Ag–Si bonds, surface hydrogen stoichiometry or exact particle layout is supplied.'),
 ('carbon-grid','Carbon-coated gold TEM grid',None,'support','Composite microscopy support. The source names gold grid and carbon coating; thickness, mesh, transfer yield and exact carbon structure are unreported.'),
 ('hopg','Highly oriented pyrolytic graphite flakes','C','solid','Graphitic calibration flakes used to correct electron-microscope astigmatism. Not a synthesized material in this paper or an atom-by-atom sample reconstruction.'),
 ('transferred-ag','Silver nanoparticles transferred to the TEM grid','Ag','supported-particles','Silver nanoparticles mechanically transferred from Si to a carbon-coated gold TEM grid. Source Figure 6 reports the TEM/SAED evidence, but exact preparative pulse duration is unassigned. The cartoon is not a measured particle layout, support structure or reconstructed Ag unit cell.')]
for mid,name,formula,kind,caption in cards:
 id='identity-stiger-'+mid;e=base(id,name,formula,kind,caption);s='<svg xmlns="http://www.w3.org/2000/svg" width="840" height="360" viewBox="0 0 840 360" role="img"><title>'+html.escape(name)+'</title><desc>'+html.escape(caption)+'</desc><rect x="20" y="22" width="800" height="316" rx="18" fill="#f1f6f9" stroke="#cbdce6"/>'
 if mid in ['si-npp','si-n','h-si','ag-si']:
  s+='<path d="M82 153H367L405 192H120Z" fill="#c4d6df" stroke="#7897a8" stroke-width="2"/><path d="M120 192H405V221H120Z" fill="#a8c0ce" stroke="#7897a8" stroke-width="2"/>'
  if mid in ['h-si','ag-si']:s+='<path d="M84 149H365L403 188" fill="none" stroke="#518a87" stroke-width="3"/>'+text(160,136,'H-terminated surface',16)
  if mid=='ag-si':
   for x,y in [(146,167),(209,155),(275,175),(330,163)]:s+=f'<ellipse cx="{x}" cy="{y}" rx="12" ry="8" fill="#8197a5" stroke="#637b89"/>'
  s+=text(596,137,'Ag particles / Si substrate' if mid=='ag-si' else 'Si(100) substrate',22)+text(596,184,'Illustrative surface only',19)+text(596,232,'No measured atomic coordinates',17)
 elif mid in ['carbon-grid','transferred-ag']:
  s+='<ellipse cx="221" cy="177" rx="139" ry="58" fill="#d6c691" stroke="#8c855f" stroke-width="2"/>'
  for dy in [-20,0,20]:s+=f'<path d="M97 {177+dy}H345" stroke="#7c898e" stroke-width="2"/>'
  if mid=='transferred-ag':
   for x,y in [(151,172),(218,159),(270,189),(314,172)]:s+=f'<ellipse cx="{x}" cy="{y}" rx="10" ry="7" fill="#8197a5" stroke="#637b89"/>'
  s+=text(600,137,'Ag on carbon / Au grid' if mid=='transferred-ag' else 'Carbon-coated Au grid',24)+text(600,184,'Transferred TEM specimen' if mid=='transferred-ag' else 'Microscopy support',20)+text(600,232,'No measured particle layout' if mid=='transferred-ag' else 'No source mesh or coating thickness',16)
 elif mid=='hopg':
  for k in [0,1,2]:s+=f'<path d="M91 {145+18*k}H330L374 {174+18*k}H135Z" fill="#abbcc6" stroke="#7897a8" stroke-width="2"/>'
  s+=text(602,144,'HOPG calibration flakes',24)+text(602,190,'Astigmatism correction',20)+text(602,236,'Reference specimen only',18)
 else:
  title={'ga-in':'Ga–In','silver-paint':'Ag-containing paint','ag-wire':'Ag','pt-wire':'Pt','sce':'SCE'}[mid]
  s+=text(216,183,title,32)+text(575,136,'Contact formulation' if mid in ['ga-in','silver-paint'] else 'Electrode component',23)+text(575,183,'Source identity card',20)+text(575,231,'No invented molecular or crystal model',16)
 s+=text(420,297,'Illustrative reference • not measured sample geometry',17)+'</svg>';e['svgPath']='svg/'+id+'.svg';(O/e['svgPath']).write_text(s,encoding='utf8');e['assetHashes']={'svgPath':sha(O/e['svgPath'])};entries.append(e);mapping[mid]=id
new={e['id']:e for e in entries};allentries={**old,**new};bindings={};notes={};hashes={};unresolved=[];reuse=set();drafts=sorted((R/'canonical-drafts').glob('*.json'))
if drafts:records=[(load(p),sha(p)) for p in drafts];record_basis='Current canonical-draft file bytes'
else:
 sys.path.insert(0,str(R));import build_records as br
 records=[(r,hashlib.sha256((json.dumps(r,ensure_ascii=False,indent=2)+'\n').encode()).hexdigest()) for r in br.records];record_basis='Provisional serialized build_records objects; refresh after root writes the complete canonical drafts'
for r,hs in records:
 rid=r['record_id'];bindings[rid]={};notes[rid]={};hashes[rid]=hs
 for m in r['materials']:
  mid=m['id'];id=mapping.get(mid)
  if not id:unresolved.append({'record':rid,'material':mid});continue
  e=allentries[id];check(e['formula']==m.get('formula'),rid+'/'+mid+' formula identity');bindings[rid][mid]=id
  notes[rid][mid]=(e['caption'] if id in new else 'Chemical identity reference only. Stiger1999 concentrations, mixtures, temperature and handling are supplied in this record; no earlier-paper process conditions are inherited.')
  if id in new:e['provenance']['sourceRecords'].append({'recordId':rid,'materialId':mid,'evidence':m.get('evidence',[])})
  else:reuse.add(id)
check(not unresolved,'Every current material bound')
for id in reuse:
 for k,h in old[id].get('assetHashes',{}).items():check(sha(REG/old[id][k])==h,id+' actual reused '+k+' hash')
for e in entries:
 for k,h in e['assetHashes'].items():check(sha(O/e[k])==h,e['id']+' actual '+k+' hash')
 check(e['model3dPath'] is None,e['id']+' no fabricated 3D salt/surface geometry')
summary={'newEntryCount':len(entries),'new2dModels':len(ions),'new3dModels':0,'referenceCards':len(cards),'reusedEntryCount':len(reuse),'recordCount':len(bindings),'materialBindingCount':sum(map(len,bindings.values())),'unresolvedBindings':len(unresolved)}
save(O/'registry-additions.json',{'schemaVersion':'1.0.0','entries':entries,'summary':summary})
save(O/'bindings-additions.json',{'schemaVersion':'1.0.0','recordBindings':bindings,'bindingNotes':notes,'sourceRecordSha256':hashes,'sourceRecordHashBasis':record_basis,'unresolved':unresolved})
save(O/'reused-references.json',{'existingRegistrySha256':sha(REG/'registry.json'),'entries':[{'id':id,'assetPaths':{k:old[id][k] for k in ['svgPath','model2dPath','model3dPath'] if old[id].get(k)},'assetHashes':old[id]['assetHashes'],'sourceUrls':old[id]['sourceUrls']} for id in sorted(reuse)]})
save(O/'asset-manifest.json',{'source_doi':DOI,'source_sha256':SH,'illustrative_only':True,'eligible_training':False,'files':[{'path':p.relative_to(O).as_posix(),'sha256':sha(p)} for folder in ['svg','models'] for p in sorted((O/folder).glob('*'))]})
save(O/'model-provenance.json',{'sourceDoi':DOI,'sourceSha256':SH,'entries':[{'id':e['id'],'provenance':e['provenance'],'assetHashes':e['assetHashes']} for e in entries],'limits':['Two ionic references are 2D disconnected components; no measured solvation or coordination geometry.','No new Ag CIF or solved Ag/Si composite model.','HF and sulfuric-acid shared captions require the supplied neutralizations to remove prior-paper conditions.']})
save(O/'validation.json',{'status':'passed' if all(c['passed'] for c in checks) else 'failed','passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'checks':checks,'summary':summary})
ims=[]
for e in entries:
 d=pymupdf.open(stream=(O/e['svgPath']).read_bytes(),filetype='svg');pdf=pymupdf.open('pdf',d.convert_to_pdf());px=pdf[0].get_pixmap(matrix=pymupdf.Matrix(.7,.7),alpha=False);im=Image.frombytes('RGB',(px.width,px.height),px.samples);can=Image.new('RGB',(620,300),'white');can.paste(im,(10,22));ImageDraw.Draw(can).text((10,3),e['id'],fill='black');ims.append(can)
for i in range(0,len(ims),6):
 sheet=Image.new('RGB',(1240,900),'#dee6eb')
 for n,im in enumerate(ims[i:i+6]):sheet.paste(im,(n%2*620,n//2*300))
 sheet.save(O/'review'/f'contact-{i//6+1:02d}.png')
print(json.dumps(summary))
