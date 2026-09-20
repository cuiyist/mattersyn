"""Private local-only Matuhina chemical-reference authoring, never Site writes."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import hashlib,html,json,math,sys,textwrap,re
O=Path(__file__).resolve().parent;P=O.parents[1];M=P.parents[4];S=M/'recipe-atlas';R=S/'dist/assets/chemical-registry'
sys.dont_write_bytecode=True;sys.path.insert(0,str(M/'research-assets/rdkit-runtime'));sys.path.insert(0,str(M/'research-assets/corpus-20260917/runtime'))
from rdkit import Chem,rdBase
from rdkit.Chem import rdDepictor,rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D
import pymupdf
from PIL import Image,ImageDraw
assert not(O/'package-freeze.json').exists(),'Preserve frozen packages.'
for n in['models','svg','previews','contacts','stock-svg','stock-previews','conformer-previews','reference-snapshots']:(O/n).mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def esc(x):return html.escape(str(x),quote=True)
def prose(x):
 x=str(x).replace('FigureS','Figure S').replace('Figure1','Figure 1').replace(';2%','; 2%').replace('20×20mm','20 × 20 mm').replace('2×2cm2','2 × 2 cm²').replace('~2×0.15cm','~2 × 0.15 cm')
 return re.sub(r'(?<=\d)(mg|mL|mm|cm)\b',r' \1',x)
def tx(x,y,s,size=19,anchor='start',fill='#294558'):return f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{size}" text-anchor="{anchor}" fill="{fill}">{esc(s)}</text>'
def wrap(s,x,y,width=93,size=18,line=25):return ''.join(tx(x,y+i*line,t,size)for i,t in enumerate(textwrap.wrap(s,width)))
def raster(svg,path):
 d=pymupdf.open(stream=svg.encode(),filetype='svg');d[0].get_pixmap(alpha=False).save(str(path));d.close()
checks=[];inputs={};snapshots=[]
def ck(label,ok):checks.append({'check':label,'passed':bool(ok)});assert ok,label
def snap(p,rel):
 p=Path(p);dst=O/'reference-snapshots'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():assert sha(dst)==sha(p),str(dst)
 else:dst.write_bytes(p.read_bytes())
 inputs[str(p)]=sha(p);snapshots.append({'original_path':str(p),'snapshot':str(dst.relative_to(O)),'sha256':sha(p)});return dst
source=read(P/'source-facts.json');materials={m['id']:m for m in source['materials']}
ck('Source identity',source['source_id']=='matuhina2023'and len(materials)==28)
for n in['source-facts.json','source-inventory.json','package-freeze.json','source-independent-audit/independent-audit.json']:inputs[str(P/n)]=sha(P/n)
snap(R/'registry.json','registry-base.json');base={e['id']:e for e in read(R/'registry.json')['entries']}
# Missing isomer/mixture identity is shown symbolically; no terminal-alkene or
# normal-hexane geometry is assigned to an unspecified source distribution.
spec={
'cs-carbonate':('O=C([O-])[O-].[Cs+].[Cs+]','CCs2O3','cesium-carbonate'),
'oa':('CCCCCCCC/C=C\\CCCCCCCC(=O)O','C18H34O2','oleic-acid'),
'olam':('CCCCCCCC/C=C\\CCCCCCCCN','C18H37N','oleylamine'),
'mncl2':('[Mn+2].[Cl-].[Cl-]','Cl2Mn',None),
'meoac':('COC(C)=O','C3H6O2',None),
'ipa':('CC(O)C','C3H8O','2-propanol'),
'etoac':('CCOC(C)=O','C4H8O2','ethyl-acetate'),
'water':('O','H2O','water'),
'hno3':('O=[N+]([O-])O','HNO3','reference-nitric-acid'),
'heavy-water':('[2H]O[2H]','H2O',None)}
limits={
'cs-carbonate':'Disconnected 2 Cs+ and CO3(2-) formula components. Their drawing positions are arbitrary; no carbonate crystal packing or solution coordination is supplied.',
'oa':'One cis-oleic-acid reference. The source 90% reagent has no batch-specific isomer assay; this free molecule is not a surface ligand or metal-oleate complex.',
'olam':'One cis-oleylamine reference constituent. The source technical 70% reagent is a mixture of unspecified composition; no ligand shell, protonation or bound configuration is inferred.',
'mncl2':'Disconnected Mn2+ and two Cl- formula components of the explicitly anhydrous salt. No Mn-Cl coordination bonds, hydration, lattice or dissolved complex are reconstructed.',
'meoac':'Methyl-acetate reference connectivity from the unambiguous source name. This 2D graph is not a measured conformation, distillation outcome or solution complex.',
'ipa':'Free 2-propanol reference. This is the isopropanol alternative purification trial, separate from ethyl acetate; no mixed-antisolvent formulation is inferred.',
'etoac':'Free ethyl-acetate reference. This is a separate alternative purification trial, not methyl acetate and not an isopropanol mixture.',
'water':'One free-water reference. Source-specific thermal-bath and Milli-Q analytical roles remain separate; no shared grade, hydration shell or liquid structure is inferred.',
'hno3':'Undissociated nitric-acid reference in one resonance representation. The concentrated digest and 2% aqueous matrix have unknown acid/solvent speciation; percentage basis is unreported.',
'heavy-water':'Isotopically labeled D2O connectivity, with two deuterium atoms. This is the TA white-light continuum generator medium, not the NC dispersion solvent; no isotope purity or physical geometry is inferred.'}
symbols={
'ode':['Octadecene · source calls it ODE','90%; used dry in precursor preparation','Positional/isomer distribution is not specified'],
'argon':['Ar · inert handling atmosphere','Grade and flow rate are not reported','No solution species or reaction ingredient model'],
'hexane':['Hexane · C6H14 source identity','At least 95%; primary redispersion volume unknown','Source-specific isomer distribution not assigned'],
'cs-standard':['Cs ionic analytical standard','Concentration series in 2% HNO3','Counterion, oxidation state and speciation not specified'],
'mn-standard':['Mn ionic analytical standard','Concentration series in 2% HNO3','Counterion, oxidation state and speciation not specified'],
'cover-glass':['Microscopy cover glass · XRD support','Precleaned 20 × 20 mm substrate','Glass composition, thickness and cleaning recipe unknown'],
'cu-grid':['Carbon-coated Cu microscopy grid','TEM and SAED specimen support','Mesh and carbon-surface coordinates not supplied'],
'quartz-cuvette':['Quartz cuvette · TA support','Reported optical thickness: 2 mm','No quartz lattice or exact vessel geometry assigned'],
'silica-substrate':['Silica substrate · low-temperature PL','Deposited NC film is a distinct specimen','Thickness, surface structure and deposition recipe unknown'],
'lsc-glass':['Glass plate · LSC proof of concept','Unencapsulated NC film; edge about 2 × 0.15 cm','Not a demonstrated polymer-embedded material'],
'si-photodiode':['Silicon pn-junction photodiode','Reported area: 2 × 2 cm²','Doping profile and contacts are not supplied'],
'nc-series':['CsMnCl3 · source sample family','Five preparation conditions; films and dispersions separate','No exact atomic coordinates, surface coverage or shape model'],
'cs-oleate-identity':['Cs-oleate solution · reported stock identity','Stored under vacuum; reactivated before injection','Final concentration and dissolved speciation unknown'],
'manganese-oleate-context':['Mn(oleate)2 · idealized reaction label','Figure 1 schematic context only','No isolated compound, coordination graph or analysis'],
'cscl-aged':['CsCl · aged cubic refinement assignment','Reported degradation phase, not purchased reagent','No independent atomic structure or new synthesis route'],
'cs3mncl5-aged':['Cs3MnCl5 · aged refinement assignment','Reported degradation phase','No independent atomic structure or new synthesis route'],
'csmn4cl9-aged':['CsMn4Cl9 · aged refinement assignment','Reported degradation phase','No independent atomic structure or new synthesis route']}
ck('All28 identities planned',set(symbols)|{'quench-water','milliq'}|(set(spec)-{'water'})==set(materials))
def modelmol(raw,coords=False):
 rw=Chem.RWMol()
 for a in raw['atoms']:
  atom=Chem.Atom(a['element']);atom.SetFormalCharge(a.get('formalCharge',0));atom.SetIsotope(a.get('isotope',0));
  if 'implicitHydrogenCount'in a:atom.SetNoImplicit(True);atom.SetNumExplicitHs(a['implicitHydrogenCount'])
  rw.AddAtom(atom)
 for b in raw['bonds']:rw.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,1.5:Chem.BondType.AROMATIC}[b['order']])
 m=rw.GetMol();Chem.SanitizeMol(m)
 if coords:
  c=Chem.Conformer(len(raw['atoms']));c.Set3D(True)
  for a in raw['atoms']:c.SetAtomPosition(a['index'],(a['x'],a['y'],a['z']))
  m.AddConformer(c);Chem.AssignStereochemistryFrom3D(m)
 return m
def canon(m,stereo=False):return Chem.MolToSmiles(Chem.RemoveHs(m),isomericSmiles=stereo)
def groups(m):
 out=[]
 for name,pattern in [('Carboxylic acid','[CX3](=[OX1])[OX2H]'),('Primary amine','[NX3;H2][CX4]'),('Alkene','[CX3]=[CX3]'),('Ester','[CX3](=[OX1])[OX2][CX4]'),('Alcohol group','[CX4][OX2H]'),('Carbonate resonance group','[CX3](=[OX1])([O-])[O-]'),('Nitric-acid resonance group','[N+](=O)([O-])O'),('Cesium ion','[Cs+]'),('Manganese(II) ion','[Mn+2]'),('Chloride ion','[Cl-]')]:
  for ids in m.GetSubstructMatches(Chem.MolFromSmarts(pattern)):
   ids=sorted(ids);out.append({'label':name,'atomIndices':ids,'bondIndices':[b.GetIdx()for b in m.GetBonds()if b.GetBeginAtomIdx()in ids and b.GetEndAtomIdx()in ids]})
 if not out and all(a.GetSymbol()in['H','O']for a in m.GetAtoms()):out=[{'label':'Heavy-water reference'if any(a.GetIsotope()==2 for a in m.GetAtoms())else'Water reference','atomIndices':list(range(m.GetNumAtoms())),'bondIndices':list(range(m.GetNumBonds()))}]
 return out
models={};qualified=[]
rawdir=M/'research-assets/quality-20260918/molecules/raw'
for key,(smiles,formula,cached)in spec.items():
 mol=Chem.MolFromSmiles(smiles);ck(key+' source formula',rdMolDescriptors.CalcMolFormula(mol)==formula);prov={'identity_basis':'Unambiguous source chemical identity represented with conventional connectivity or formal ions; no measured geometry.','source_url':'https://doi.org/10.1021/acsanm.2c04342'}
 if cached:
  entry=base[cached];save('reference-snapshots/entry-'+cached+'.json',entry)
  for field in['svgPath','model2dPath','model3dPath']:
   if entry.get(field):ck(cached+' cached hash '+field,sha(R/entry[field])==entry['assetHashes'][field]);snap(R/entry[field],entry[field])
  raw=read(R/entry['model2dPath']);ck(key+' cached graph',canon(modelmol(raw))==canon(mol));prov.update(retained_registry_id=cached,retained_model2d_sha256=sha(R/entry['model2dPath']),primary_reference='https://pubchem.ncbi.nlm.nih.gov/compound/'+str(entry['pubchemCid']))
  for n in [cached+'-pubchem-2d.sdf',cached+'-properties.json']:
   if(rawdir/n).exists():dest=snap(rawdir/n,'raw/'+n)
 elif key=='ipa':raise AssertionError('isopropanol must use cache')
 if key=='ipa':snap(M/'research-assets/2-propanol-pubchem-3776-3d.sdf','raw/2-propanol-pubchem-3776-3d.sdf')
 if key in['oa','olam']:
  n=('oleic-acid-pubchem-445639-3d.sdf'if key=='oa'else'oleylamine-pubchem-5356789-3d.sdf');snap(M/'research-assets'/n,'raw/'+n)
 if key=='hno3':
  q=M/'research-assets/incoming-paper-monitor/batches/20260919-five-paper-pilot/jp0473669/visuals/molecules'
  for n in['nitric-acid-pubchem-2d.sdf','nitric-acid-properties.json']:
   candidates=list(q.rglob(n))
   if candidates:snap(candidates[0],'raw/'+n)
 rdDepictor.Compute2DCoords(mol);conf=mol.GetConformer();gg=groups(mol)
 atoms=[{'index':a.GetIdx(),'element':a.GetSymbol(),'x':conf.GetAtomPosition(a.GetIdx()).x,'y':conf.GetAtomPosition(a.GetIdx()).y,'z':0.0,'formalCharge':a.GetFormalCharge(),'isotope':a.GetIsotope(),'implicitHydrogenCount':a.GetTotalNumHs()}for a in mol.GetAtoms()]
 bonds=[{'a':b.GetBeginAtomIdx(),'b':b.GetEndAtomIdx(),'order':b.GetBondTypeAsDouble()}for b in mol.GetBonds()]
 mp='models/matuhina2023-'+key+'-2d.json';model={'id':'matuhina2023-'+key+'-reference','name':key+' reference','formula':'D2O'if key=='heavy-water'else formula,'representation':'2d','has3D':False,'allowRotation':False,'indexConvention':'zero-based','coordinateUnits':'arbitrary drawing units','atoms':atoms,'bonds':bonds,'functionalGroups':gg,'caption':limits[key],'modelType':'Reference connectivity or disconnected formula components','computedBy':'RDKit '+rdBase.rdkitVersion,'sourceType':'Reference graph; not measured sample coordinates','source':prov,'connectivitySmiles':smiles,'stereochemistryScope':'Explicit reference SMILES; no source-batch isomer assay. Stereo retained in 2D drawing and reference SMILES.'if key in['oa','olam']else'No stereocenter assigned beyond the named reference.','notes':[limits[key]],'eligible_training':False};save(mp,model);models[key]={'mol':mol,'model2dPath':mp,'model3dPath':None,'groups':gg,'formula':model['formula'],'provenance':prov}
 if cached and base[cached].get('model3dPath'):
  raw=read(R/base[cached]['model3dPath']);new=deepcopy(raw);m3=modelmol(raw,True);ck(key+' retained3D graph',canon(m3)==canon(mol))
  if key in['oa','olam']:ck(key+' retained cis geometry',canon(m3,True)==canon(mol,True))
  new.update(id='matuhina2023-'+key+'-reference',name=key+' reference',caption='Retained illustrative reference conformer; not measured sample coordinates. '+limits[key],sourceType='Locally cached reference geometry, not observed sample coordinates',source={'primary_reference':prov['primary_reference'],'retained_model_sha256':sha(R/base[cached]['model3dPath']),'coordinate_provenance':deepcopy(raw.get('source'))},notes=[limits[key]],functionalGroups=groups(m3),connectivitySmiles=smiles,eligible_training=False)
  ck(key+' arrays unchanged',new['atoms']==raw['atoms']and new['bonds']==raw['bonds']);path='models/matuhina2023-'+key+'-3d.json';save(path,new);models[key]['model3dPath']=path
 qualified.append({'reference_key':key,'graph_smiles':smiles,'formula':model['formula'],'fragment_count':len(Chem.GetMolFrags(mol)),'formal_charge':sum(a.GetFormalCharge()for a in mol.GetAtoms()),'model2dPath':mp,'model3dPath':models[key]['model3dPath'],'cached_identity':cached,'qualification':limits[key]})
entries=[]
for mid,m in materials.items():
 key='water'if mid in['quench-water','milliq']else mid;g=models.get(key);eid='matuhina2023-'+mid+'-reference';formula=m['source_formula_or_abbreviation'];scope=prose(m['scope_note'].replace('Source90%','Source 90%').replace('Technical70%','Technical 70%').replace('Sigma-Aldrich99.9%','Sigma-Aldrich 99.9%').replace('in2%','in 2%').replace('Precleaned20','Precleaned 20').replace('2mm','2 mm').replace('edge~2','edge ~2'))
 if g:
  kind='ionic_components'if key in['cs-carbonate','mncl2']else'molecule';caption=scope+' '+limits[key];drawer=rdMolDraw2D.MolDraw2DSVG(990,330);drawer.drawOptions().padding=.12;drawer.drawOptions().includeRadicals=False
  colors={i:(.65,.82,.84)for group in g['groups']for i in group['atomIndices']};rdMolDraw2D.PrepareAndDrawMolecule(drawer,g['mol'],highlightAtoms=list(colors),highlightAtomColors=colors);drawer.FinishDrawing();ss=drawer.GetDrawingText();ss=ss[ss.index('>',ss.index('<svg'))+1:ss.rindex('</svg>')];body='<g transform="translate(55,150)">'+ss+'</g>';m2=g['model2dPath'];m3=g['model3dPath'];gg=g['groups'];prov=g['provenance']
 else:
  kind='symbolic_context';caption=scope+' Symbolic identity/context only; no chemical, crystal, surface or solution geometry is assigned.';m2=m3=None;gg=[];prov={'identity_basis':'Source identity or context; unresolved structure kept symbolic.'};body='<rect x="60" y="155" width="980" height="330" rx="18" fill="#f1f7fa" stroke="#b9d0db"/>'
  for j,line in enumerate(symbols[mid]):body+=tx(550,240+j*80,line,23 if j==0 else 20,'middle')
 if key in['oa','olam']:body+=tx(550,501,'Cis reference constituent; source batch isomer composition is not assigned.',17,'middle')
 if key in['cs-carbonate','mncl2']:body+=tx(550,501,'Disconnected formula components; no metal coordination or lattice geometry.',17,'middle')
 display=formula or'Exact composition / species not specified';svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="700" viewBox="0 0 1100 700"><title>{esc(m["name"])}</title><desc>{esc(caption)}</desc><rect x="1" y="1" width="1098" height="698" rx="20" fill="white" stroke="#cbdde5"/>{tx(36,48,m["name"],24)}<path d="M36 75H1064" stroke="#d5e3e8"/>{tx(550,115,display,23,"middle")}{body}<rect x="30" y="520" width="1040" height="148" rx="10" fill="#eef5f8"/>{wrap(scope,50,550,104,17,23)}{wrap("Reference identity only. No exact solution species, ligand shell or source atomic model is reconstructed.",50,628,107,16,21)}</svg>'
 path='svg/'+eid+'.svg';(O/path).write_text(svg,encoding='utf8');raster(svg,O/'previews'/(eid+'.png'))
 entry={'id':eid,'name':m['name'],'aliases':[m['name']],'formula':formula,'displayFormula':formula,'depictionKind':kind,'pubchemCid':base[spec[key][2]]['pubchemCid']if g and spec[key][2]else None,'sourceUrls':['https://doi.org/10.1021/acsanm.2c04342']+([prov['primary_reference']]if prov.get('primary_reference')else[]),'svgPath':path,'model2dPath':m2,'model3dPath':m3,'functionalGroups':gg,'caption':caption,'limitations':[scope,limits[key]if g else'Symbolic source identity only; no molecule, source coordinates or exact specimen reconstruction.'],'provenance':{'sourceDoi':'10.1021/acsanm.2c04342','sourceMaterialId':mid,'sourceLocators':m['evidence'],'sourceFactsSha256':sha(P/'source-facts.json'),'sourceGeneration':2,'referenceQualification':prov,'measuredCoordinates':False},'binding_approved':False,'independentScientificAudit':'pending','published':False,'eligible_training':False};entry['assetHashes']={k:sha(O/entry[k])for k in['svgPath','model2dPath','model3dPath']if entry.get(k)};entries.append(entry)
save('registry-additions.json',{'schemaVersion':'1.0','source_id':'matuhina2023','status':'private_author_proposal','binding_approved':False,'entries':entries})
stocks=[]
for st in source['stocks']:
 lines=[prose(st['notes']),'Scope: '+st['sample_scope']]+[q['meaning']+': '+q['raw_text']+(' '+q['unit']if q['unit']else'')for q in st['quantities']];y=170;body=''
 for line in lines:body+=wrap(line,55,y,100,18,25);y+=len(textwrap.wrap(line,100))*25+17
 h=max(590,y+100);comp=' + '.join(materials[x]['name']for x in st['components']);svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{h}" viewBox="0 0 1100 {h}"><title>{esc(st["name"])}</title><rect width="1100" height="{h}" fill="white"/>{tx(35,45,st["name"],25)}{wrap(comp,40,88,110,17,23)}{body}{tx(40,h-35,"Component references do not establish dissolved speciation or an extra stock charge.",16)}</svg>';path='stock-svg/matuhina2023-'+st['id']+'.svg';(O/path).write_text(svg,encoding='utf8');raster(svg,O/'stock-previews'/('matuhina2023-'+st['id']+'.png'));stocks.append({'stock_id':st['id'],'source_stock':st,'svg_path':path,'sha256':sha(O/path),'binding_approved':False})
for key,g in models.items():
 if not g['model3dPath']:continue
 model=read(O/g['model3dPath']);xy=[(a['x']+.31*a['z'],a['y']+.17*a['z'])for a in model['atoms']];lo=[min(p[k]for p in xy)for k in(0,1)];hi=[max(p[k]for p in xy)for k in(0,1)];sc=min(800/max(hi[0]-lo[0],1),310/max(hi[1]-lo[1],1));pts=[(140+(p[0]-lo[0])*sc,150+(p[1]-lo[1])*sc)for p in xy];body=''
 for b in model['bonds']:
  a,z=pts[b['a']],pts[b['b']];body+=f'<path d="M{a[0]} {a[1]}L{z[0]} {z[1]}" stroke="#8da3b2" stroke-width="4"/>'
 for a,(x,y)in zip(model['atoms'],pts):
  radius=8 if a['element']=='H'else 14;color={'O':'#e69193','H':'#e6eef3','C':'#99b3c4','N':'#8b9cdd'}[a['element']];body+=f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{color}" stroke="#466273"/>'
  if a['element']!='H':body+=tx(x,y+5,a['element'],12,'middle')
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="700"><rect width="1100" height="700" fill="white"/>{tx(40,50,key+" · retained illustrative reference conformer",25)}{body}{wrap(limits[key],45,555,104,18,27)}</svg>';raster(svg,O/'conformer-previews'/(key+'.png'))
files=list(sorted((O/'previews').glob('*.png')))+list(sorted((O/'stock-previews').glob('*.png')))+list(sorted((O/'conformer-previews').glob('*.png')))
for start in range(0,len(files),6):
 canvas=Image.new('RGB',(1500,((min(6,len(files)-start)+1)//2)*560),'#e8eef1');draw=ImageDraw.Draw(canvas)
 for j,p in enumerate(files[start:start+6]):
  im=Image.open(p);im.thumbnail((730,505));x=(j%2)*750+(750-im.width)//2;y=(j//2)*560+30;canvas.paste(im,(x,y));draw.text(((j%2)*750+10,(j//2)*560+7),p.stem,fill='#294558')
 canvas.save(O/'contacts'/f'contact-{start//6+1:02}.png')
save('source-stock-reference-proposal.json',{'stocks':stocks,'binding_approved':False});save('reference-qualification.json',{'author':'/root/backlog_eta','source_scope':'Complete supplied main/SI source revision2; distinct source audit passed','models':qualified,'snapshots':snapshots,'new_downloads':0,'new_3d_generated':False,'atomic_product_models':False,'source_assay_inferred':False});save('input-bindings.json',{'inputs':inputs,'source_freeze_sha256':sha(P/'package-freeze.json'),'source_facts_sha256':sha(P/'source-facts.json')});save('generation-checks.json',{'checks':checks,'check_count':len(checks),'counts':{'identities':len(entries),'models2d':len(models),'models3d':sum(bool(g['model3dPath'])for g in models.values()),'symbolic':len(symbols),'previews':len(files)},'independent_approval':False});print(json.dumps({'identities':len(entries),'models2d':len(models),'models3d':sum(bool(g['model3dPath'])for g in models.values()),'previews':len(files),'checks':len(checks)}))
