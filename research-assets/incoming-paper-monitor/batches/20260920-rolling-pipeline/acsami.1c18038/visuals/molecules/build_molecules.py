"""Private Lian identity and stock visuals; no network or Site mutations."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import json,hashlib,html,math,sys,re,textwrap
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;P=O.parents[1];M=P.parents[4];S=M/'recipe-atlas';REG=S/'dist/assets/chemical-registry';C=P/'canonical-proposal/v1'
sys.path.insert(0,str(M/'research-assets/rdkit-runtime'));sys.path.insert(0,str(M/'research-assets/corpus-20260917/runtime'))
from rdkit import Chem
from rdkit.Chem import rdDepictor,rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D
import pymupdf
from PIL import Image,ImageDraw
assert not(O/'package-freeze.json').exists(),'Frozen package must be revised separately.'
for d in ['svg','models','previews','contacts','reference-snapshots','stock-svg','stock-previews','conformer-previews']:(O/d).mkdir(parents=True,exist_ok=True)
inputs={};snapshots=[];entries=[];checks=[];qualifications=[]

def read(p): return json.loads(Path(p).read_bytes())

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def jsha(x): return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def save(n,x):
    p=O/n; p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def esc(x): return html.escape(str(x),quote=True)

def tx(x,y,s,n=18,color='#294558',anchor='middle'):
    return f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{n}" fill="{color}" text-anchor="{anchor}">{esc(s)}</text>'

def wrapped(s,x,y,width=83,size=18,line=25):
    return ''.join(tx(x,y+i*line,v,size,anchor='start') for i,v in enumerate(textwrap.wrap(s,width)))

def frame(e,body,footer):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="640" viewBox="0 0 1100 640"><title>{esc(e["name"])}</title><desc>{esc(e["caption"])}</desc><rect x="1" y="1" width="1098" height="638" rx="20" fill="white" stroke="#cbdde5"/>{tx(36,47,e["name"],26 if len(e["name"])<60 else 21,anchor="start")}<path d="M36 72H1064" stroke="#d5e3e8"/>{tx(550,107,e["displayFormula"] or "Composition not reported",22)}{body}<rect x="30" y="566" width="1040" height="53" rx="9" fill="#edf5f7"/>{wrapped(footer,50,589,102,16,20)}</svg>'

def raster(svg,png):
    doc=pymupdf.open(stream=svg.encode(),filetype='svg')
    doc[0].get_pixmap(matrix=pymupdf.Matrix(1,1),alpha=False).save(str(png));doc.close()

def render(e,svg):
    (O/e['svgPath']).write_text(svg,encoding='utf-8')
    raster(svg,O/'previews'/(e['id']+'.png'))
    e['assetHashes']={k:sha(O/e[k]) for k in ['svgPath','model2dPath','model3dPath'] if e.get(k)}
    entries.append(e)

def graph_from_model(raw):
    rw=Chem.RWMol()
    for a in raw['atoms']:
        atom=Chem.Atom(a['element']);atom.SetFormalCharge(a.get('formalCharge',0));atom.SetIsotope(a.get('isotope',0));rw.AddAtom(atom)
    for b in raw['bonds']:
        rw.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,1.5:Chem.BondType.AROMATIC}[b['order']])
    mol=rw.GetMol();Chem.SanitizeMol(mol);return mol

def canon(mol):return Chem.MolToSmiles(Chem.RemoveHs(mol))

def m2d(e,mol):
    rdDepictor.Compute2DCoords(mol); conf=mol.GetConformer();groups=fg(mol)
    atoms=[{'index':a.GetIdx(),'element':a.GetSymbol(),'x':conf.GetAtomPosition(a.GetIdx()).x,'y':conf.GetAtomPosition(a.GetIdx()).y,'z':0.0,'formalCharge':a.GetFormalCharge(),'isotope':a.GetIsotope(),'implicitHydrogenCount':a.GetTotalNumHs()} for a in mol.GetAtoms()]
    bonds=[{'a':b.GetBeginAtomIdx(),'b':b.GetEndAtomIdx(),'order':1.5 if b.GetIsAromatic() else b.GetBondTypeAsDouble()} for b in mol.GetBonds()]
    e['model2dPath']='models/'+e['id']+'-2d.json';e['functionalGroups']=groups
    save(e['model2dPath'],{'id':e['id'],'name':e['name'],'formula':e['formula'],'representation':'2d','has3D':False,'allowRotation':False,'indexConvention':'zero-based','coordinateUnits':'arbitrary drawing units','modelType':'Named connectivity reference; generated 2D drawing','caption':e['caption'],'connectivitySmiles':Chem.MolToSmiles(mol),'atoms':atoms,'bonds':bonds,'functionalGroups':groups,'source':{'urls':e['sourceUrls'],'retainedRegistryId':e['provenance'].get('retainedRegistryId'),'identityBasis':e['provenance'].get('identityBasis')},'notes':e['limitations']})
    drawer=rdMolDraw2D.MolDraw2DSVG(1000,405);opts=drawer.drawOptions();opts.padding=.11;opts.addStereoAnnotation=True
    palette=[(.85,.69,.33),(.62,.48,.77),(.29,.68,.65),(.84,.47,.53)];colors={}
    for i,g in enumerate(groups):
        for a in g['atomIndices']:colors[a]=palette[i%4]
    rdMolDraw2D.PrepareAndDrawMolecule(drawer,mol,highlightAtoms=list(colors),highlightAtomColors=colors);drawer.FinishDrawing()
    svg=drawer.GetDrawingText();start=svg.index('>',svg.index('<svg'))+1
    return '<g transform="translate(50,135)">'+svg[start:svg.rindex('</svg>')]+'</g>'

def bind(p):p=Path(p);inputs[str(p)]=sha(p)
def snap(p,rel):
 p=Path(p);out=O/'reference-snapshots'/rel;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(p.read_bytes());bind(p)
 snapshots.append({'original_path':str(p),'snapshot_path':str(out.relative_to(O)),'sha256':sha(p)});return out
def ck(n,ok):checks.append({'check':n,'passed':bool(ok)});assert ok,n
def fg(mol):
 out=[]
 for label,pat in [('Quaternary ammonium centre','[N+;X4]'),('Chloride counterion','[Cl-]'),('Formal antimony(III) ion','[Sb+3]'),('Amide group','[NX3][CX3]=[OX1]'),('Carboxylic acid','[CX3](=[OX1])[OX2H]'),('Cis alkene connectivity','[CX3]=[CX3]'),('Aromatic ring','c1ccccc1'),('Dinitrogen triple bond','N#N')]:
  ids=sorted({a for match in mol.GetSubstructMatches(Chem.MolFromSmarts(pat))for a in match})
  if ids:out.append({'label':label,'atomIndices':ids,'bondIndices':[b.GetIdx()for b in mol.GetBonds()if b.GetBeginAtomIdx()in ids and b.GetEndAtomIdx()in ids]})
 return out
for p in [C/'package-manifest.json',C/'record-manifest.json',P/'source-facts.json',P/'source-inventory.json',P/'package-freeze.json',P/'source-independent-audit/independent-audit-v2.json',S/'dist/chemical-viewer.mjs']:bind(p)
ck('Frozen canonical v1',sha(C/'package-manifest.json')=='d095fb8c95ada7a91831731ab86af875c9ed913ed33e5a498a338eb3e370b0e6')
ck('Passed source revision2',sha(P/'source-independent-audit/independent-audit-v2.json')=='794b3637c0d4d83952f83c5a694da41d9f6d0523cf9d6d0327388c1bcc897940')
bind(P/'canonical-reader-independent-audit/independent-audit-v1.json');ck('Distinct canonical reader audit passed',sha(P/'canonical-reader-independent-audit/independent-audit-v1.json')=='87e1a7f27e68bace9a6b162b1f1859f18b334391ceb8849ed53960f9988559fa')
records={};slots={}
for x in read(C/'record-manifest.json')['records']:
 ck(x['record_id']+' frozen bytes',sha(x['path'])==x['sha256']);bind(x['path']);records[x['record_id']]=read(x['path'])
for rid,r in records.items():
 for i,m in enumerate(r['materials']):slots.setdefault(m['id'],[]).append((rid,i,m))
ck('45 material slots / 15 source identities',len(slots)==15 and sum(map(len,slots.values()))==45)
base={e['id']:e for e in read(REG/'registry.json')['entries']};snap(REG/'registry.json','registry.json');source_url='https://doi.org/10.1021/acsami.1c18038'
GRAPH={
 'tpa-cl':('CCC[N+](CCC)(CCC)CCC.[Cl-]','C12H28ClN',None),
 'sbcl3':('[Sb+3].[Cl-].[Cl-].[Cl-]','Cl3Sb',None),
 'dmf':('CN(C)C=O','C3H7NO','dimethylformamide'),
 'toluene':('Cc1ccccc1','C7H8','toluene'),
 'oleic-acid':('CCCCCCCC/C=C\\CCCCCCCC(=O)O','C18H34O2','oleic-acid'),
 'nitrogen':('N#N','N2','norberg2004-nitrogen-reference'),
 'liquid-nitrogen':('N#N','N2','norberg2004-nitrogen-reference')}
SYMBOLS={
 'ps':('Polystyrene matrix','(C8H8)n',['Polystyrene matrix','Conventional repeat composition (C8H8)n','Chain length, tacticity and end groups unknown'],'Repeat composition only; no discrete polymer molecule or chain coordinates. The source reports approximate Mw 280000 without a printed unit.'),
 'blue-phosphor':('Blue phosphor component','BaMgAl10O17:Eu2+',['BaMgAl10O17 : Eu2+','Preformed blue phosphor','Dopant fraction and lattice model unavailable'],'No dopant coordinates, substitution fraction, particle size or upstream phosphor synthesis is inferred.'),
 'glass':('Glass support',None,['Glass substrate','Composition and surface unspecified','Removed after composite-film peeling'],'Glass remains the support of the separate spin-coated film; no silica composition or crystalline glass model is assigned.'),
 'bulk-a':('Bulk A material identity','(C12H28N)2SbCl5',['Bulk A · (C12H28N)2SbCl5','Source composition reference','Atomic-model qualification is separate'],'No bulk coordinate model or product sample binding is created here.'),
 'bulk-b':('Bulk B material identity','(C12H28N)SbCl4',['Bulk B · (C12H28N)SbCl4','Distinct source composition reference','No zero-PLQE value inferred'],'No bulk coordinate model, collapsed Sb environment or product sample binding is created here.'),
 'nc-a':('A nanocrystal material identity','(C12H28N)2SbCl5',['A nanocrystal component','Nominal source composition','Surface and ligand coverage unknown'],'No particle lattice, size-derived coordinates, bound oleate stoichiometry or exact aliquot join is supplied.'),
 'composite-film':('Nanocrystal / phosphor / PS material',None,['A nanocrystals + blue phosphor + PS','Five relative blue/yellow formulations','Exact beta-tested ratio unspecified'],'Symbolic component inventory only; no film microstructure or assignment of every formulation to the beta test.'),
 'spincoat-film':('Precursor-derived A film','(C12H28N)2SbCl5',['Precursor spin-coated A film','Distinct from nanocrystal / phosphor / PS','Glass support retained'],'No nanocrystal-composite composition, thickness, molecular geometry or product binding is assigned.')}
ck('Complete identity coverage',set(GRAPH)|set(SYMBOLS)==set(slots))
def identity(mid,formula,name=None,kind='molecule'):
 m=slots[mid][0][2];eid='lian2021-'+mid+'-reference'
 return {'id':eid,'name':name or m['name'],'aliases':[m['name']],'formula':formula,'displayFormula':formula,'depictionKind':kind,'pubchemCid':None,'svgPath':'svg/'+eid+'.svg','model2dPath':None,'model3dPath':None,'functionalGroups':[],'sourceUrls':[source_url],'caption':'Chemical identity reference; not a measured solution or bound-surface structure.','limitations':['Source grades, quantities and roles are attached separately to their exact canonical fields.'],'provenance':{'sourceDoi':'10.1021/acsami.1c18038','sourceMaterialId':mid,'sourceLocators':m['evidence'],'canonicalIdentityFormula':m['formula'],'measuredCoordinates':False,'sourceAuditSha256':sha(P/'source-independent-audit/independent-audit-v2.json')},'binding_approved':False,'independentScientificAudit':'pending','published':False,'eligible_training':False}
def model_mol(raw,with_geometry=False):
 mol=graph_from_model(raw)
 if with_geometry:
  c=Chem.Conformer(mol.GetNumAtoms());c.Set3D(True)
  for i,a in enumerate(raw['atoms']):c.SetAtomPosition(i,(a['x'],a['y'],a['z']))
  mol.AddConformer(c);Chem.AssignStereochemistryFrom3D(mol)
 return mol
for mid,(smiles,formula,cached)in GRAPH.items():
 mol=Chem.MolFromSmiles(smiles);ck(mid+' valid graph',mol is not None);ck(mid+' formula',rdMolDescriptors.CalcMolFormula(mol)==formula)
 e=identity(mid,formula);e['provenance']['identityBasis']='Conventional named-identity 2D reference, validated for formula, formal charge and connectivity; not source-measured geometry.'
 if mid=='tpa-cl':e['caption']='Tetrapropylammonium chloride connectivity: four n-propyl groups attached to N⁺, with a separate Cl⁻ counterion. No ion-pair geometry is inferred.';e['limitations']+=['The source explicitly names tetrapropylammonium; tetrabutylammonium and isopropyl variants are not substituted. No 3D conformer is generated.']
 if mid=='sbcl3':e['displayFormula']='SbCl3';e['caption']='Antimony trichloride formal stoichiometric reference: Sb³⁺ and three Cl⁻ symbols, with no Sb–Cl bonds. This is not a claim that SbCl3 exists as separated ions in DMF.';e['limitations']+=['Formal-ion bookkeeping only; molecular, polymeric, hydrated and dissolved coordination geometry are not assigned. No 3D model.']
 if mid=='oleic-acid':e['caption']='Reference (Z)-oleic-acid connectivity. The reported technical-grade reagent is not represented as a pure single-component sample.';e['limitations']+=['Reference cis identity does not quantify technical-grade impurities, establish bound oleate, ligand coverage, surface geometry or antimony–oleate speciation.']
 if mid=='nitrogen':e['caption']='Dinitrogen reference for the reported TGA atmosphere. It does not identify an inert synthesis atmosphere.';e['limitations']+=['Reference 14N2 ground-state distance 1.09768 Å; source isotope composition, gas flow and purity are not reported.']
 if mid=='liquid-nitrogen':e['caption']='Dinitrogen molecular reference for the liquid-nitrogen temperature-control utility. One reference molecule does not model the liquid phase or its temperature.';e['limitations']+=['Coolant role only; no addition to the specimen or synthesis atmosphere is implied. Reference 14N2 distance 1.09768 Å does not establish source isotopic composition.']
 if cached:
  old=base[cached];save('reference-snapshots/entry-'+cached+'.json',old)
  for k in ['svgPath','model2dPath','model3dPath']:
   if old.get(k):ck(cached+' '+k+' cache hash',sha(REG/old[k])==old['assetHashes'][k]);snap(REG/old[k],old[k])
  raw2=read(REG/old['model2dPath']);ck(mid+' cached connectivity',Chem.MolToSmiles(Chem.RemoveHs(graph_from_model(raw2)),isomericSmiles=False)==Chem.MolToSmiles(Chem.RemoveHs(mol),isomericSmiles=False))
  e['pubchemCid']=old.get('pubchemCid');e['sourceUrls']=list(dict.fromkeys([source_url]+old.get('sourceUrls',[])))
  e['provenance'].update(retainedRegistryId=cached,retainedEntrySha256=jsha(old),retainedModel2dSha256=sha(REG/old['model2dPath']),identityBasis='Exact cached named connectivity; source-specific role, grade and quantities are independently mapped.')
  q={'material_id':mid,'cached_id':cached,'cached_entry_sha256':jsha(old),'cached_entry_snapshot':'reference-snapshots/entry-'+cached+'.json','graph_identity_matches':True,'other_paper_display_metadata_removed':True}
  if old.get('model3dPath'):
   raw3=read(REG/old['model3dPath']);cm=model_mol(raw3,True);ck(mid+' retained 3D exact stereochemical identity',canon(cm)==canon(mol));new=deepcopy(raw3)
   new.update(id=e['id'],name=e['name'],caption='Retained illustrative reference geometry; not a measured Lian solution, surface or product structure.',notes=['Original atom/bond/coordinate arrays are unchanged. Reference provenance is distinct from current source conditions.'],functionalGroups=fg(graph_from_model(raw3)))
   if mid in ['nitrogen','liquid-nitrogen']:new['caption']='NIST 14N2 ground-state reference distance 1.09768 Å in arbitrary orientation; not measured gas or liquid geometry in this source.'
   new['source']={'referenceUrls':old['sourceUrls'],'retainedModelType':raw3.get('modelType'),'method':raw3.get('method',raw3.get('conformerGeneration',old.get('provenance',{}).get('computed3d')))}
   e['model3dPath']='models/'+e['id']+'-3d.json';save(e['model3dPath'],new)
   ck(mid+' exact retained atom/bond arrays',raw3['atoms']==new['atoms']and raw3['bonds']==new['bonds']);ck(mid+' Angstrom units',new['coordinateUnits'].lower()in['angstrom','angstroms','å'])
   lengths=[math.dist([new['atoms'][b['a']][k]for k in ['x','y','z']],[new['atoms'][b['b']][k]for k in ['x','y','z']])for b in new['bonds']]
   ck(mid+' finite/plausible reference coordinates',all(math.isfinite(a[k])for a in new['atoms']for k in ['x','y','z'])and all(.6<x<2.4 for x in lengths))
   if mid in ['nitrogen','liquid-nitrogen']:ck(mid+' NIST distance',abs(lengths[0]-1.09768)<1e-8)
   q.update(retainedModel3dSha256=sha(REG/old['model3dPath']),newModel3dSha256=sha(O/e['model3dPath']),atomic_arrays_unchanged=True,reference_stereochemistry_matches=True)
  qualifications.append(q)
 body=m2d(e,mol);footer='2D reference connectivity · highlighted functional groups · no measured solution geometry'
 if mid=='sbcl3':
  body=''
  for x,label,col in [(185,'Sb³⁺','#d6c2e5'),(430,'Cl⁻','#dfedcf'),(675,'Cl⁻','#dfedcf'),(920,'Cl⁻','#dfedcf')]:body+=f'<circle cx="{x}" cy="300" r="69" fill="{col}" stroke="#a7bdc8"/>'+tx(x,310,label,34)
  body+=tx(550,448,'Formal stoichiometric ions · no Sb–Cl bonds or dissolved-species claim',21);footer='SbCl3 composition reference · arbitrary 2D layout · no coordination geometry'
 render(e,frame(e,body,footer))
 ck(mid+' formal net charge',sum(a.GetFormalCharge()for a in mol.GetAtoms())==0)
 if mid=='tpa-cl':
  nitrogen=next(a for a in mol.GetAtoms()if a.GetSymbol()=='N');ck('Tetrapropylammonium has four carbon neighbours',nitrogen.GetDegree()==4 and all(a.GetSymbol()=='C'for a in nitrogen.GetNeighbors()))
  rw=Chem.RWMol(mol);rw.RemoveAtom(nitrogen.GetIdx());frags=Chem.GetMolFrags(rw.GetMol());ck('Four separate three-carbon propyl branches after N removal',sorted(len(f)for f in frags)==[1,3,3,3,3])
for mid,(name,formula,lines,limit)in SYMBOLS.items():
 e=identity(mid,formula,name,'symbolic_context');e['caption']='Symbolic source material identity. '+limit;e['limitations']=[limit,'No atomic coordinates, molecular polymer chain, ordered crystal or product/sample binding is supplied.']
 if mid=='composite-film':e['displayFormula']='Composite material · no single molecular formula'
 body='<rect x="75" y="160" width="950" height="350" rx="23" fill="#f2f8fa" stroke="#b4cbd7"/>'
 for j,line in enumerate(lines):body+=tx(550,242+j*81,line,28 if j==0 else 22)
 render(e,frame(e,body,'Symbolic material/component reference · exact specimens and crystal models are separate gates'))
by_mid={e['provenance']['sourceMaterialId']:e for e in entries}
raw=M/'research-assets/quality-20260918/molecules/raw';pilot=M/'research-assets/incoming-paper-monitor/batches/20260919-five-paper-pilot'
primary={
 'oleic-acid':[raw/'oleic-acid-properties.json',raw/'oleic-acid-pubchem-2d.sdf',M/'research-assets/oleic-acid-pubchem-445639-3d.sdf'],
 'toluene':[raw/'toluene-properties.json',raw/'toluene-pubchem-2d.sdf',M/'research-assets/toluene-pubchem-1140-3d.sdf'],
 'dmf':[M/'research-assets/incoming-paper-monitor/reviews/cm970189m/molecular-assets/sdf/dimethylformamide-computed-illustrative-3d.sdf'],
 'nitrogen':[pilot/'ja0496423/visuals/molecules/raw/nitrogen-nist-extracted-reference.json',pilot/'ja0496423/visuals/molecules/raw/nitrogen-nist-web-tool-excerpt.txt']}
primary_rows=[]
for mid,paths in primary.items():
 for p in paths:
  out=snap(p,'primary/'+mid+'/'+p.name);row={'material_id':mid,'snapshot_path':str(out.relative_to(O)),'sha256':sha(out),'new_retrieval':False}
  if p.suffix=='.sdf':
   mol=Chem.SDMolSupplier(str(out),removeHs=False)[0];ck(mid+' retained SDF identity '+p.name,canon(mol)==canon(Chem.MolFromSmiles(GRAPH[mid][0])));row['graph_and_stereochemistry_match']=True
  primary_rows.append(row)
def qfmt(q):
 def v(x):return str(int(x))if isinstance(x,(float,int))and x==int(x)else str(x)
 if q.get('value')is not None:s=v(q['value'])
 elif q.get('minimum')is not None and q.get('maximum')is not None:s=v(q['minimum'])+'–'+v(q['maximum'])
 elif q.get('minimum')is not None:s=('> 'if q.get('minimum_exclusive')else'≥ ')+v(q['minimum'])
 elif q.get('maximum')is not None:s=('< 'if q.get('maximum_exclusive')else'≤ ')+v(q['maximum'])
 else:return'Not reported'
 unit=q.get('unit');return('≈ 'if q.get('approximate')else'')+s+(' '+{'uL':'µL','degC':'°C'}.get(unit,unit)if unit else' (unit not printed)')
def qlink(rid,opid,key,meaning='component_charge'):
 i,op=next((i,o)for i,o in enumerate(records[rid]['operations'])if o['id']==opid);q=op['parameters'][key]
 return {'record_id':rid,'json_pointer':f'/operations/{i}/parameters/{key}','operation_id':opid,'field':key,'meaning':meaning,'quantity':deepcopy(q),'display_value':qfmt(q)}
FEEDS={'bulk-a-route':'a-dissolve-filter','bulk-b-route':'b-dissolve-filter','nc-a-route':'nc-dissolve-filter','spincoat-film-route':'spin-feed'}
QMAP={}
for short,op in FEEDS.items():
 for mid,k in [('tpa-cl','c12h28ncl_charge'),('sbcl3','sbcl3_charge'),('dmf','dmf_solvent_charge')]:QMAP[(short,mid)]=[(op,k)]
QMAP[('bulk-b-route','sbcl3')]=[('b-dissolve-filter','sbcl3_inherited_charge')]
QMAP[('bulk-b-route','dmf')]=[('b-dissolve-filter','dmf_inherited_solvent_charge')]
QMAP[('nc-a-route','toluene')]=[('nc-inject','toluene_antisolvent')];QMAP[('nc-a-route','oleic-acid')]=[('nc-inject','oleic_acid_ligand')]
GRADE_IDS={'dmf':1,'sbcl3':2,'tpa-cl':3,'toluene':4,'oleic-acid':5,'ps':6};GR={};rr=records['lian-2021-reagents-methods']
for mid,n in GRADE_IDS.items():
 i,m=next((i,m)for i,m in enumerate(rr['measurements'])if m['id']=='lian2021-chemicals-q'+str(n));q=m['value'];GR[mid]={'record_id':rr['record_id'],'json_pointer':f'/measurements/{i}/value','field':m['property'],'meaning':'source_material_grade'if mid!='ps'else'source_polymer_average_Mw','quantity':deepcopy(q),'display_value':qfmt(q)}
bindings={'schemaVersion':'1.0','source_id':'lian2021','status':'private_author_proposal_pending_independent_molecular_audit','recordBindings':{},'bindingNotes':{},'binding_approved':False,'published':False,'eligible_training':False};slot_rows=[]
for rid,r in records.items():
 if not r['materials']:continue
 bindings['recordBindings'][rid]={};bindings['bindingNotes'][rid]={}
 for i,m in enumerate(r['materials']):
  mid=m['id'];e=by_mid[mid];refs=[qlink(rid,op,k)for op,k in QMAP.get((rid.removeprefix('lian-2021-'),mid),[])];grades=[deepcopy(GR[mid])]if mid in GR else[]
  caption=m['name']+'; source role: '+m['role'].replace('_',' ')+'; stage: '+m['stage'].replace('_',' ')+'.'
  if grades:caption+=' Source grade/context: '+'; '.join(x['field'].replace('_',' ')+': '+x['display_value']for x in grades)+'.'
  if refs:caption+=' Reported charges: '+'; '.join(x['field'].replace('_',' ')+': '+x['display_value']for x in refs)+'.'
  else:caption+=' No separate material dose is assigned by this card.'
  if mid=='dmf':caption+=' This is solvent charged, not a calibrated final stock volume.'
  if mid=='oleic-acid':caption+=' Free reference identity only; bound ligand coverage and speciation are unknown.'
  if mid=='liquid-nitrogen':caption+=' Temperature-control utility; not a specimen input.'
  if mid=='nitrogen':caption+=' Reported only for TGA, not XPS or synthesis.'
  if mid=='glass':caption+=' Removed from the peeled composite film; retained in the distinct spin-coated-film route.'
  formulations=[]
  if rid=='lian-2021-composite-film-series'and mid in ['blue-phosphor','nc-a']:
   for j,measurement in enumerate(r['measurements']):
    if measurement['id']in ['lian2021-composite-mixing-q'+str(n)for n in range(1,6)]:formulations.append({'record_id':rid,'json_pointer':f'/measurements/{j}/value','field':'blue_phosphor/yellow_nanocrystal_mass_parts','meaning':'relative_formulation_parts_not_component_mass','quantity':deepcopy(measurement['value']),'display_value':measurement['value']['value']})
   caption+=' Blue-phosphor/yellow-nanocrystal mass parts: 1/0, 1/3, 1/2, 2/3, 0/1. These include zero-component controls; no absolute loading or beta-tested ratio is inferred.'
  note={'record_id':rid,'material_id':mid,'json_pointer':f'/materials/{i}','canonical_record_sha256':inputs[str(C/(rid+'.json'))],'registry_id':e['id'],'entry_sha256':jsha(e),'canonical_identity':deepcopy(m),'quantity_links':refs,'grade_context_links':grades,'formulation_context_links':formulations,'viewOverrides':{'name':m['name'],'caption':caption,'limitations':deepcopy(e['limitations'])},'binding_approved':False,'source_specific_join':'Exact material slot; source-wide reagent grade explicitly linked separately from record-specific charges.'}
  bindings['recordBindings'][rid][mid]=e['id'];bindings['bindingNotes'][rid][mid]=note;slot_rows.append(note)
stock_rows=[];contexts=[]
for rid,r in records.items():
 for si,st in enumerate(r['stocks']):
  short=rid.removeprefix('lian-2021-');comps=[]
  for ci,comp in enumerate(st['components']):
   mid=comp['material_id'];mi=next(i for i,m in enumerate(r['materials'])if m['id']==mid);refs=[qlink(rid,op,k)for op,k in QMAP.get((short,mid),[])];role='solvent'if mid in ['dmf','toluene']else'polymer_solute'if mid=='ps'else'solute'
   comps.append({'material_id':mid,'registry_id':by_mid[mid]['id'],'role':role,'json_pointer':f'/stocks/{si}/components/{ci}','material_json_pointer':f'/materials/{mi}','source_quantities':deepcopy(comp['quantities']),'quantity_links':refs,'binding_approved':False})
  aliquots=[qlink(rid,'nc-inject','precursor_solution_aliquot','stock_solution_aliquot')]if short=='nc-a-route'else[qlink(rid,'spin-deposit','precursor_solution_aliquot','stock_solution_aliquot')]if short=='spincoat-film-route'else[]
  summary=' + '.join((next(m['name']for m in r['materials']if m['id']==z['material_id'])+': '+('; '.join(x['display_value']for x in z['quantity_links'])or'amount not reported'))for z in comps)
  limit='Formulation already contained in the linked operation. Solvent charge is not a calibrated final solution volume; dissolved speciation and final concentration are unknown.'
  if aliquots:limit+=' The '+aliquots[0]['display_value']+' is a solution aliquot, not a second solvent charge; exact aliquot solute amounts are not inferred.'
  if short=='composite-film-series':limit='PS/toluene matrix solution: polymer mass, solvent amount and concentration are unreported. The separate blue/yellow mass parts do not define the PS concentration.'
  row={'record_id':rid,'stock_id':st['id'],'json_pointer':f'/stocks/{si}','canonical_record_sha256':inputs[str(C/(rid+'.json'))],'components':comps,'concentrations':deepcopy(st['concentrations']),'scope':st['scope'],'evidence':deepcopy(st['evidence']),'solution_quantity_links':aliquots,'display_summary':summary,'display_limit':limit,'binding_approved':False};stock_rows.append(row)
  label=st['name'].capitalize().replace('Nc feed','Nanocrystal feed').replace('Ps toluene','PS/toluene')
  ctx={'record_id':rid,'id':'lian2021-'+st['id'],'label':label,'scope':summary+'. '+limit,'components':[{'material_id':z['material_id'],'registry_id':z['registry_id'],'role':z['role'],'label':next(m['name']for m in r['materials']if m['id']==z['material_id']),'viewOverrides':{'caption':summary+'. '+limit,'limitations':[limit,'Component reference selector; no dissolved complex or ion-pair geometry.']}}for z in comps],'binding_approved':False};contexts.append(ctx)
  body='';width=1000/len(comps)
  for j,z in enumerate(comps):
   x=45+j*width;e=by_mid[z['material_id']];body+=f'<rect x="{x}" y="150" width="{width-15}" height="230" rx="15" fill="#eff7fa" stroke="#bfd3dc"/>'+tx(x+(width-15)/2,196,z['role'].replace('_',' ').capitalize(),20)+tx(x+(width-15)/2,245,e['displayFormula']or e['name'],22)
   body+=wrapped('; '.join(x['display_value']for x in z['quantity_links'])or'Amount not reported',x+15,302,28 if len(comps)==3 else 43,18,25)
  body+=wrapped(limit,45,433,102,17,23)
  e={'name':ctx['label'],'caption':ctx['scope'],'displayFormula':'Solute and solvent references · formulation, not speciation'};svg=frame(e,body,'Source-bound component selector · no additional charge or batch')
  (O/'stock-svg'/(st['id']+'.svg')).write_text(svg,encoding='utf-8');raster(svg,O/'stock-previews'/(st['id']+'.png'))
# Private projection of each retained 3D reference; no coordinates are generated.
for e in entries:
 if not e['model3dPath']:continue
 model=read(O/e['model3dPath']);atoms=model['atoms'];xy=[(a['x']+.32*a['z'],a['y']+.16*a['z'])for a in atoms];lo=[min(a[j]for a in xy)for j in [0,1]];hi=[max(a[j]for a in xy)for j in [0,1]];scale=min(800/max(hi[0]-lo[0],1),330/max(hi[1]-lo[1],1));pts=[(150+(a[0]-lo[0])*scale,160+(a[1]-lo[1])*scale)for a in xy];body=''
 for b in model['bonds']:
  a,z=pts[b['a']],pts[b['b']];body+=f'<path d="M{a[0]} {a[1]} L{z[0]} {z[1]}" stroke="#9badb8" stroke-width="6"/>'
 for a,(x,y)in zip(atoms,pts):body+=f'<circle cx="{x}" cy="{y}" r="16" fill="'+{'C':'#688398','H':'#edf2f5','O':'#e27375','N':'#728dce'}.get(a['element'],'#b494bd')+'" stroke="#78909e"/>'+tx(x,y+5,a['element'],13,'#153344')
 raster(frame(e,body,'Projection of retained reference coordinates · Å units · not source-measured molecular geometry'),O/'conformer-previews'/(e['id']+'.png'))
ck('15 entries /45 slots /5 stocks /14 components',len(entries)==15 and len(slot_rows)==45 and len(stock_rows)==5 and sum(len(x['components'])for x in stock_rows)==14)
for e in entries:
 for k in ['model2dPath','model3dPath']:
  if not e[k]:continue
  model=read(O/e[k]);n=len(model['atoms']);nb=len(model['bonds']);ck(e['id']+k+' zero-based atom indices',[a.get('index',i)for i,a in enumerate(model['atoms'])]==list(range(n)))
  for b in model['bonds']:ck(e['id']+k+' bond endpoints',0<=b['a']<n and 0<=b['b']<n and b['a']!=b['b'])
  for g in model['functionalGroups']:ck(e['id']+k+' group indices',all(0<=i<n for i in g['atomIndices'])and all(0<=i<nb for i in g.get('bondIndices',[])))
  if k=='model2dPath':ck(e['id']+' 2D only drawing units',model['coordinateUnits']=='arbitrary drawing units'and not model['has3D']and not model['allowRotation']and all(a['z']==0 for a in model['atoms']))
for p,h in inputs.items():ck('Input unchanged '+p,sha(p)==h)
save('registry-additions.json',{'schemaVersion':'1.0','source_id':'lian2021','status':'private_author_proposal','entries':entries,'binding_approved':False})
save('bindings-proposal.json',bindings);save('material-slot-map.json',{'schema':'mattersyn-molecular-slot-proposal/1','material_slot_count':45,'identity_count':15,'slots':slot_rows,'independent_audit':'pending'})
save('stock-component-map.json',{'schema':'mattersyn-stock-component-proposal/1','stock_count':5,'component_count':14,'stocks':stock_rows,'independent_audit':'pending'});save('solution-components-proposal.json',{'schemaVersion':'1.0','contexts':contexts,'binding_approved':False})
save('reference-qualification.json',{'status':'author_checks_only','qualifications':qualifications,'retained_primary_artifacts':primary_rows,'new_2d_identity_references':['tpa-cl','sbcl3'],'rejected':[{'id':'nitrogen','reason':'Old 1.460 Å registry conformer is not used; qualified NIST reference retained.'},{'id':'tetrabutylammonium reference','reason':'Wrong alkyl-chain identity for tetrapropylammonium.'},{'id':'polystyrene-sulfonate calibrant','reason':'Different polymer; not the reported PS matrix.'}],'normalization':'Reference geometry/provenance separated from source-specific grade, role and charge. No current product coordinates or source sample binding.'})
save('reference-snapshots/manifest.json',{'snapshots':snapshots,'note':'Private immutable reference snapshots; absolute original paths are audit metadata only.'});save('input-bindings.json',inputs)
counts={'entries':15,'material_slots':45,'stocks':5,'stock_components':14,'models_2d':7,'retained_illustrative_3d':5,'symbolic_materials':8,'new_2d_graphs':2,'cached_graph_bindings':5,'new_product_bindings':0,'new_atomic_coordinates':0}
save('author-validation.json',{'schema':'mattersyn-molecule-author-validation/1','author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'status':'automated_author_checks_passed_manual_visual_review_pending','counts':counts,'check_count':len(checks),'checks':checks,'independent_molecular_audit':'pending','canonical_independent_audit':'passed_v1_separate_from_molecular_audit','binding_approved':False,'browser_validation':'not_claimed','bound_files':inputs})
for folder,prefix in [('previews','identities'),('stock-previews','stocks'),('conformer-previews','conformers')]:
 imgs=sorted((O/folder).glob('*.png'))
 for start in range(0,len(imgs),6):
  canvas=Image.new('RGB',(1500,1410),'#dce7ed');draw=ImageDraw.Draw(canvas)
  for j,p in enumerate(imgs[start:start+6]):
   im=Image.open(p).convert('RGB');im.thumbnail((730,425));x=10+j%2*750;y=30+j//2*470;canvas.paste(im,(x,y));draw.text((x,y+430),p.stem,fill='#203a4b')
  canvas.save(O/'contacts'/f'{prefix}-{start//6+1:02}.png')
print(json.dumps({'counts':counts,'author_checks':len(checks),'status':'generated; persisted validation and manual views pending'}))
