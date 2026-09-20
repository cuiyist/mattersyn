"""Private Yao1998 ionic-connectivity and polymer-motif reference package."""
from pathlib import Path
import sys,json,hashlib,html,math,re,collections
sys.dont_write_bytecode=True
sys.path.insert(0,'[local path redacted]')
sys.path.insert(0,'[local path redacted]')
from rdkit import Chem,__version__ as RV
from rdkit.Chem import rdDepictor,rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D
import pymupdf
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent;O=R/'molecular-assets';O.mkdir(exist_ok=True)
for f in ['svg','models','review']:(O/f).mkdir(exist_ok=True)
OLD=Path('[local path redacted]');DOI='10.1021/la970480g';SH='6a7fb66fb56f6daa4aa677c91ddf0d78aa733b165b7537bbac4c4e1327defb06'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old={e['id']:e for e in read(OLD/'registry.json')['entries']};entries=[];mapping={'water':'water','methanol':'methanol','ethanol':'ethanol','na2s':'identity-veinot-na2s'};checks=[]
def check(v,s):checks.append({'check':s,'passed':bool(v)})
def base(id,name,formula,kind,caption):return {'id':id,'name':name,'aliases':[name],'formula':formula,'displayFormula':formula,'depictionKind':kind,'pubchemCid':None,'sourceUrls':['https://doi.org/'+DOI],'svgPath':None,'model2dPath':None,'model3dPath':None,'functionalGroups':[],'caption':caption,'limitations':[caption],'provenance':{'sourceDoi':DOI,'sourceSha256':SH,'identitySource':'Explicit compound identity in the local source; no guessed external identifier','sourceRecords':[],'measuredCoordinates':False,'eligible_training':False}}
ions=[
('cd-acetate','cadmium-acetate-dihydrate','Cadmium acetate dihydrate','Cd(C2H3O2)2·2H2O','C4H10CdO6','[Cd+2].CC(=O)[O-].CC(=O)[O-].O.O'),
('nacl','sodium-chloride','Sodium chloride','NaCl','ClNa','[Na+].[Cl-]'),
('hcl','hydrochloric-acid-aqueous','Hydrochloric acid, aqueous identity','HCl','HCl','[H+].[Cl-]'),
('naoh','sodium-hydroxide','Sodium hydroxide','NaOH','HNaO','[Na+].[OH-]'),
('licl','lithium-chloride','Lithium chloride','LiCl','ClLi','[Li+].[Cl-]'),
('kcl','potassium-chloride','Potassium chloride','KCl','ClK','[K+].[Cl-]'),
('tmacl','tetramethylammonium-chloride','Tetramethylammonium chloride','C4H12NCl','C4H12ClN','C[N+](C)(C)C.[Cl-]')]
def counts(s):return collections.Counter({e:int(n or 1) for e,n in re.findall(r'([A-Z][a-z]?)(\d*)',s)})
for mid,id,name,formula,flat,smiles in ions:
 caption='Illustrative 2D component connectivity and charge only. Disconnected ions or waters have arbitrary drawing positions; no 3D ion-pair, solvation shell, coordination geometry or crystal lattice is asserted.'
 if mid=='cd-acetate':caption+=' The two water components preserve the explicitly named dihydrate; they do not establish Cd–water coordination bonds.'
 if mid=='hcl':caption+=' H+ is conventional aqueous acid notation, not an isolated unsolvated proton or a specified hydronium cluster.'
 e=base(id,name,formula,'ionic',caption);m=Chem.MolFromSmiles(smiles);check(m is not None,id+' parse');check(counts(rdMolDescriptors.CalcMolFormula(m))==counts(flat),id+' atom stoichiometry');check(Chem.GetFormalCharge(m)==0,id+' total electroneutrality');rdDepictor.Compute2DCoords(m)
 drawer=rdMolDraw2D.MolDraw2DSVG(840,360);opt=drawer.drawOptions();opt.clearBackground=False;opt.padding=.14;opt.minFontSize=21;opt.maxFontSize=29;opt.bondLineWidth=2;drawer.DrawMolecule(m);drawer.FinishDrawing();svg=drawer.GetDrawingText();svg=svg.replace('<!-- END OF HEADER -->','<title>'+html.escape(name)+'</title><desc>'+html.escape(caption)+'</desc>');e['svgPath']='svg/'+id+'.svg';(O/e['svgPath']).write_text(svg,encoding='utf8')
 c=m.GetConformer();model={'id':id,'name':name,'formula':formula,'representation':'2d','has3D':False,'allowRotation':False,'source':'https://doi.org/'+DOI,'coordinateUnits':'drawing units','indexConvention':'zero-based','modelType':'Disconnected ionic and hydrate component reference','caption':caption,'atoms':[{'index':a.GetIdx(),'element':a.GetSymbol(),'x':round(c.GetAtomPosition(a.GetIdx()).x,6),'y':round(c.GetAtomPosition(a.GetIdx()).y,6),'z':0,'formalCharge':a.GetFormalCharge(),'isotope':a.GetIsotope(),'implicitHydrogenCount':a.GetTotalNumHs()} for a in m.GetAtoms()],'bonds':[{'a':b.GetBeginAtomIdx(),'b':b.GetEndAtomIdx(),'order':b.GetBondTypeAsDouble(),'stereo':str(b.GetStereo())} for b in m.GetBonds()],'functionalGroups':[],'computedBy':'RDKit '+RV,'eligible_training':False}
 if mid=='tmacl':model['functionalGroups']=[{'label':'Tetramethylammonium cation','atomIndices':list(Chem.GetMolFrags(m)[0]),'bondIndices':[b.GetIdx() for b in m.GetBonds()]}]
 e['model2dPath']='models/'+id+'-2d.json';save(O/e['model2dPath'],model);e['functionalGroups']=model['functionalGroups'];e['assetHashes']={k:sha(O/e[k]) for k in ['svgPath','model2dPath']};e['provenance'].update({'smiles':smiles,'software':'RDKit '+RV,'modelDimensionPolicy':'2D only because source does not establish ion pair, hydration or coordination geometry'});entries.append(e);mapping[mid]=id
def text(x,y,t,size=20):return f'<text x="{x}" y="{y}" text-anchor="middle" font-family="Arial,sans-serif" font-size="{size}" fill="#254b5e">{html.escape(t)}</text>'
cards=[('resin','Chelex 100 chelate polymer',None,'polymer','Local iminodiacetate motif on a styrene-divinylbenzene network. Crosslink fraction, chain length, stereochemistry, counterion population and exact geometry are unreported.'),('cd-loaded-resin','Cadmium-loaded Chelex 100',None,'polymer','Cd2+ incorporation in chelate resin, not a refined coordination structure. Loading and qualitative supernatant test remain in the source procedure; no one-Cd-per-site stoichiometry is assumed.'),('hybrid','CdS nanocrystals embedded in Chelex 100',None,'composite','Polymer-hosted nanocrystals. Spatial distributions differ by formulation, time and radial position; the cartoon is not a measured layer map, particle count, size distribution or atomic interface.'),('diagnostic-hs','Hydrosulfide test solution','HS−','formula','HS− is the source-named diagnostic species, not a complete test-solution formula. Counterion, stock source, dose and detection limit are unreported; it is not a verified Na2S feed.')]
for mid,name,formula,kind,caption in cards:
 id='identity-yao-'+mid;e=base(id,name,formula,kind,caption)
 s='<svg xmlns="http://www.w3.org/2000/svg" width="840" height="360" viewBox="0 0 840 360" role="img"><title>'+html.escape(name)+'</title><desc>'+html.escape(caption)+'</desc><rect x="20" y="22" width="800" height="316" rx="18" fill="#f1f6f9" stroke="#cbdce6"/>'
 if kind=='polymer':
  s+='<rect x="57" y="116" width="216" height="96" rx="12" fill="#d8e9ee" stroke="#7797a7"/>'+text(165,156,'Polymer network',20)+text(165,187,'Styrene / divinylbenzene',15)+'<path d="M273 164H323M444 164L507 117M444 164L507 211" stroke="#517888" stroke-width="2" fill="none"/>'+text(382,172,'CH₂–N',23)+text(589,122,'CH₂–COO⁻',22)+text(589,221,'CH₂–COO⁻',22)
  if mid=='cd-loaded-resin':s+=text(422,288,'Cd²⁺ incorporated · coordination not refined',20)
  else:s+=text(422,288,'Local functional motif · not a finite polymer molecule',18)
 elif kind=='composite':
  s+='<circle cx="206" cy="173" r="99" fill="#e3edf0" stroke="#7797a7" stroke-width="2"/>'
  for x,y in [(145,141),(156,203),(206,104),(257,128),(276,181),(239,232),(200,254)]:s+=f'<circle cx="{x}" cy="{y}" r="8" fill="#bdad5b"/>'
  s+=text(206,179,'Polymer',19)+text(554,137,'Embedded CdS nanocrystals',24)+text(554,181,'Illustrative spatial arrangement',19)+text(554,225,'No exact layer width or atom positions',17)
 else:s+=text(420,145,'HS⁻ · diagnostic species',31)+text(420,202,'Test solution identity incomplete',21)+text(420,253,'Counterion, dose and stock source unspecified',17)
 s+='</svg>';e['svgPath']='svg/'+id+'.svg';(O/e['svgPath']).write_text(s,encoding='utf8');e['assetHashes']={'svgPath':sha(O/e['svgPath'])};entries.append(e);mapping[mid]=id
new={e['id']:e for e in entries};allentries={**old,**new};bindings={};notes={};hashes={};reused=set();unresolved=[]
for p in sorted((R/'canonical-drafts').glob('*.json')):
 r=read(p);rid=r['record_id'];bindings[rid]={};notes[rid]={};hashes[rid]=sha(p)
 for m in r['materials']:
  mid=m['id'];id=mapping.get(mid)
  if not id:unresolved.append({'record':rid,'material':mid});continue
  e=allentries[id];check(e['formula']==m.get('formula'),rid+'/'+mid+' exact formula match');bindings[rid][mid]=id
  notes[rid][mid]=e['caption'] if id in new else 'Reference chemical identity only; source-specific amounts, aqueous conditions and treatment sequence belong to this Yao1998 record. No earlier-paper procedure is inherited.'
  if id in new:e['provenance']['sourceRecords'].append({'recordId':rid,'materialId':mid,'evidence':m.get('evidence',[])})
  else:reused.add(id)
check(not unresolved,'Every current canonical material bound')
for id in reused:
 for k,h in old[id]['assetHashes'].items():check(sha(OLD/old[id][k])==h,id+' reused '+k+' hash')
for e in entries:
 for k,h in e['assetHashes'].items():check(sha(O/e[k])==h,e['id']+' '+k+' hash')
 check(e['model3dPath'] is None,e['id']+' no fabricated 3D ionic/polymer geometry')
summary={'newEntryCount':len(entries),'new2dModels':len(ions),'new3dModels':0,'referenceCards':len(cards),'reusedEntryCount':len(reused),'recordCount':len(bindings),'materialBindingCount':sum(map(len,bindings.values())),'unresolvedBindings':len(unresolved)}
save(O/'registry-additions.json',{'schemaVersion':'1.0.0','assetPurpose':'Yao1998 source identities; ionic components and polymer motifs, no measured geometry','entries':entries,'summary':summary})
save(O/'bindings-additions.json',{'schemaVersion':'1.0.0','recordBindings':bindings,'bindingNotes':notes,'sourceRecordSha256':hashes,'unresolved':unresolved})
save(O/'reused-references.json',{'existingRegistrySha256':sha(OLD/'registry.json'),'entries':[{'id':id,'assetPaths':{k:old[id][k] for k in ['svgPath','model2dPath','model3dPath'] if old[id].get(k)},'assetHashes':old[id]['assetHashes'],'sourceUrls':old[id]['sourceUrls']} for id in sorted(reused)]})
save(O/'validation.json',{'status':'passed' if all(x['passed'] for x in checks) else 'failed','passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'checks':checks,'summary':summary})
save(O/'asset-manifest.json',{'source_doi':DOI,'source_sha256':SH,'illustrative_only':True,'eligible_training':False,'files':[{'path':str(p.relative_to(O)).replace('\\','/'),'sha256':sha(p)} for f in ['svg','models'] for p in sorted((O/f).glob('*'))]})
save(O/'model-provenance.json',{'sourceDoi':DOI,'sourceSha256':SH,'entries':[{'id':e['id'],'provenance':e['provenance'],'assetHashes':e['assetHashes']} for e in entries],'limits':['All seven new ionic depictions are 2D disconnected components, not ion-pair or coordination models.','Chelex and Cd-loaded resin have local motifs/cards without a finite polymer graph.','CdS phase assignment is in source XRD text; no measured CIF or existing verified cubic CdS asset is available.']})
ims=[]
for e in entries:
 d=pymupdf.open(stream=(O/e['svgPath']).read_bytes(),filetype='svg');pdf=pymupdf.open('pdf',d.convert_to_pdf());px=pdf[0].get_pixmap(matrix=pymupdf.Matrix(.7,.7),alpha=False);im=Image.frombytes('RGB',(px.width,px.height),px.samples);can=Image.new('RGB',(620,300),'white');can.paste(im,(10,22));ImageDraw.Draw(can).text((10,3),e['id'],fill='black');ims.append(can)
for i in range(0,len(ims),6):
 sheet=Image.new('RGB',(1240,900),'#dee6eb')
 for n,im in enumerate(ims[i:i+6]):sheet.paste(im,(n%2*620,n//2*300))
 sheet.save(O/'review'/f'contact-{i//6+1:02d}.png')
print(json.dumps(summary))
