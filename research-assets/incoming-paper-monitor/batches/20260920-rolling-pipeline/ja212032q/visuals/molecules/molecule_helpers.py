"""Private Ghosh identity and stock visuals; no network or Site mutations."""
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
