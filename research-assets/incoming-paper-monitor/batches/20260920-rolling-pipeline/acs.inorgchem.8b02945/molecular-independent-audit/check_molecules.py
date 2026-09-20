"""Independent read-only verification of the root-authored Friedfeld proposal.

Writes only this audit directory. Does not import or execute author builders.
"""
from pathlib import Path
import sys,json,hashlib,math,re
from collections import Counter
from datetime import datetime,timezone
sys.dont_write_bytecode=True
F=Path(__file__).resolve().parents[1]; O=Path(__file__).resolve().parent
M=F.parents[4]; P=F/'visuals/molecules'
sys.path[:0]=[str(M/'research-assets/rdkit-runtime'),str(M/'research-assets/corpus-20260917/runtime')]
from rdkit import Chem,rdBase
from rdkit.Chem import rdMolDescriptors,AllChem
from PIL import Image,ImageDraw,ImageFont
import pymupdf
J=lambda p:json.loads(Path(p).read_text('utf-8-sig'))
SHA=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[]; bound={}; details=[]
def ck(name,ok,detail=None):
 checks.append(dict(check=name,passed=bool(ok),**({'detail':detail} if detail is not None else {})))
def bind(p):
 p=Path(p);bound[str(p.resolve())]=SHA(p);return p
def graph(j):
 rw=Chem.RWMol()
 for a in j['atoms']:
  at=Chem.Atom(a['element']);at.SetFormalCharge(a.get('formalCharge',0));at.SetIsotope(a.get('isotope',0))
  if 'implicitHydrogenCount' in a:at.SetNoImplicit(True);at.SetNumExplicitHs(a['implicitHydrogenCount'])
  rw.AddAtom(at)
 for b in j['bonds']:
  rw.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,1.5:Chem.BondType.AROMATIC}[b['order']])
 m=rw.GetMol();Chem.SanitizeMol(m);return m
def smi(m):return Chem.MolToSmiles(Chem.RemoveHs(m),isomericSmiles=True)
def dist(a,b):return math.dist([a[x] for x in 'xyz'],[b[x] for x in 'xyz'])
expected={
 'indium-acetate':('[In+3].CC([O-])=O.CC([O-])=O.CC([O-])=O','C6H9InO6',4),
 'myristic-acid':('CCCCCCCCCCCCCC(O)=O','C14H28O2',1),
 'phenylacetic-acid':('O=C(O)Cc1ccccc1','C8H8O2',1),
 'bnmgcl':('[Mg+2].[Cl-].[CH2-]c1ccccc1','C7H7ClMg',3),
 'methyltetrahydrofuran':('O1C(C)CCC1','C5H10O',1),
 'labeled-co2':('O=[13C]=O','[13C]O2',1),
 'labeled-acid':('O=[13C](O)Cc1ccccc1','C7[13C]H8O2',1),
 'phosphine':('P([Si](C)(C)C)([Si](C)(C)C)[Si](C)(C)C','C9H27PSi3',1),
 'indium-myristate':('[In+3].'+'.'.join(['CCCCCCCCCCCCCC([O-])=O']*3),'C42H81InO6',4),
 'indium-labeled-phenylacetate':('[In+3].'+'.'.join(['O=[13C]([O-])Cc1ccccc1']*3),'C21[13C]3H21InO6',4),
 'ode':('CCCCCCCCCCCCCCCCC=C','C18H36',1),
 'toluene':('c1ccccc1C','C7H8',1),'pentane':('CCCCC','C5H12',1),
 'ethyl-acetate':('CCOC(C)=O','C4H8O2',1),'acetonitrile':('N#CC','C2H3N',1),
 'benzene-d6':('[2H]c1c([2H])c([2H])c([2H])c([2H])c1[2H]','C6D6',1),
 'toluene-d8':('[2H]C([2H])([2H])c1c([2H])c([2H])c([2H])c([2H])c1[2H]','C7D8',1),
 'chloroform-d':('[2H]C(Cl)(Cl)Cl','CDCl3',1),
 'calcium-hydride':('[H-].[Ca+2].[H-]','H2Ca',3),
 'nitrogen':('N#N','N2',1),'thf':('O1CCCC1','C4H8O',1),
 'liquid-nitrogen':('N#N','N2',1),'dry-ice':('O=C=O','CO2',1),
 'acetone':('CC(C)=O','C3H6O',1),'water':('O','H2O',1),'methanol':('CO','CH4O',1),
 'hcl':('[Cl-].[H+]','HCl',2),'diethyl-ether':('CCOCC','C4H10O',1),
 'sodium-sulfate':('[Na+].[Na+].[O-]S([O-])(=O)=O','Na2O4S',3),
 'dichloromethane':('ClCCl','CH2Cl2',1)}
patterns={
 'Carboxylic acid':'C(=O)[OH]','Carboxylate':'C(=O)[O-]',
 'Ester':'C(=O)OC','Alcohol':'[C][OH]','Ether':'C[O]C','Ketone':'CC(=O)C',
 'Terminal alkene':'[CH2]=[CH]','Nitrile':'C#N','Sulfate':'[O-]S(=O)(=O)[O-]',
 'Trimethylsilyl':'[Si]([CH3])([CH3])[CH3]'}
freeze=J(bind(P/'package-freeze.json'))
ck('Requested exact molecular freeze',SHA(P/'package-freeze.json')=='7c1a864dbdf6b3177d2aa907b4f3c5893232b0c7d213ab18312d12655d4f4c0f')
for rel,h in freeze['bound_files'].items():ck('Frozen file '+rel,SHA(bind(P/rel))==h)
src=J(bind(F/'source-extraction-revision-2/source-facts.json'))
source_materials={x['id']:x for x in src['materials']}
source_stocks={x['id']:x for x in src['stocks']}
source_audit=J(bind(F/'source-independent-audit/independent-audit-v2.json'))
reg=J(P/'registry-additions.json'); entries=reg['entries']; qualifying=J(P/'reference-qualification.json')['models']
ck('39 exact source identities',len(entries)==39 and {e['provenance']['sourceMaterialId'] for e in entries}==set(source_materials))
ck('30 graph identities',len(qualifying)==30)
ck('No canonical binding approval',freeze['canonical_bindings']=='pending' and all(e['binding_approved'] is False and e['eligible_training'] is False for e in entries))
all3d=[]
for e in entries:
 mid=e['provenance']['sourceMaterialId'];s=source_materials[mid]
 ck(mid+' source identity and source formula',e['name']==s['name'] and e['sourceFormula']==s['source_formula_or_abbreviation'])
 ck(mid+' exact source locators',e['provenance']['sourceLocators']==s['evidence'])
 ck(mid+' effective facts hash',e['provenance']['sourceFactsSha256']==SHA(F/'source-extraction-revision-2/source-facts.json'))
 for k,h in e['assetHashes'].items():ck(mid+' entry hash '+k,SHA(P/e[k])==h)
 if mid not in expected:
  ck(mid+' symbolic only',not e['model2dPath'] and not e['model3dPath'] and e['formula'] is None);continue
 exp,formula,nfrag=expected[mid]
 expected_mol=Chem.MolFromSmiles(exp)
 for mode in ['2d','3d']:
  rel=e.get('model'+mode+'Path')
  if not rel:continue
  j=J(P/rel);m=graph(j);aa=j['atoms'];bb=j['bonds'];key=mid+' '+mode
  ck(key+' connectivity and isotopes',smi(m)==smi(expected_mol),(smi(m),smi(expected_mol)))
  ck(key+' independent formula',rdMolDescriptors.CalcMolFormula(m,separateIsotopes=True)==formula,(rdMolDescriptors.CalcMolFormula(m,separateIsotopes=True),formula))
  ck(key+' serialized formula',j['formula']==formula)
  ck(key+' fragments',len(Chem.GetMolFrags(m))==nfrag)
  ck(key+' overall formal charge',sum(a.GetFormalCharge() for a in m.GetAtoms())==0)
  ck(key+' index units',j.get('indexConvention')=='zero-based' and j.get('coordinateUnits')==('angstrom' if mode=='3d' else 'arbitrary drawing units'))
  ck(key+' atom indices',[a['index'] for a in aa]==list(range(len(aa))))
  ck(key+' finite coordinates',all(math.isfinite(a[t]) for a in aa for t in 'xyz'))
  ck(key+' unique valid bonds',len({tuple(sorted((b['a'],b['b']))) for b in bb})==len(bb) and all(0<=b['a']<len(aa) and 0<=b['b']<len(aa) and b['a']!=b['b'] for b in bb))
  for gi,g in enumerate(j['functionalGroups']):
   ids=g['atomIndices'];bids=g['bondIndices'];label=g['label']
   ck(key+f' group {gi} indices',len(ids)==len(set(ids)) and all(0<=i<len(aa) for i in ids) and all(0<=i<len(bb) for i in bids))
   ck(key+f' group {gi} bond endpoints',all(bb[i]['a'] in ids and bb[i]['b'] in ids for i in bids))
   if label in patterns:ck(key+f' group {gi} chemical pattern',frozenset(ids) in {frozenset(x) for x in m.GetSubstructMatches(Chem.MolFromSmarts(patterns[label]))})
   else:ck(key+f' group {gi} isotope label',len(ids)==1 and label.startswith(str(aa[ids[0]].get('isotope'))+aa[ids[0]]['element']) and aa[ids[0]].get('isotope',0)>0)
  if mode=='2d':ck(key+' flat drawing',all(abs(a['z'])<1e-10 for a in aa))
  if mode!='3d':continue
  ck(key+' single connected species only',nfrag==1)
  all3d.append((mid,j))
  lengths=[]
  for bi,b in enumerate(bb):
   a,c=aa[b['a']],aa[b['b']];d=dist(a,c);els=sorted((a['element'],c['element']));order=b['order']
   lo,hi=(.85,1.2) if 'H' in els else (1.0,2.5)
   if els==['C','C']:lo,hi=(1.15,1.65)
   if els==['C','O']:lo,hi=(1.1,1.65)
   if els==['C','N']:lo,hi=(1.05,1.65)
   if els==['N','N'] and order==3:lo,hi=(1.05,1.15)
   if els==['C','Si']:lo,hi=(1.75,2.05)
   if els==['P','Si']:lo,hi=(2.05,2.45)
   if els==['C','Cl']:lo,hi=(1.6,1.95)
   ck(key+f' bond {bi} element/order range',lo<d<hi,dict(elements=els,order=order,length=d,screen=(lo,hi)))
   lengths.append(dict(elements=els,order=order,length=d))
  bonded={tuple(sorted((b['a'],b['b']))) for b in bb}
  for i in range(len(aa)):
   for z in range(i):
    if (z,i) not in bonded:ck(key+f' nonbonded overlap {z}/{i}',dist(aa[z],aa[i])>.7)
  prov=j.get('source') if isinstance(j.get('source'),dict) else None
  if prov and prov.get('embedding'):
   ck(key+' recorded reproducible compute method',prov.get('seed')==2019803 and prov['embedding']=='ETKDGv3' and prov.get('converged') is True and prov.get('unsupported_parameters') is False)
  if 'referenceQualification' in j:
   q=j['referenceQualification'];rid=q['retained_registry_id'];base=J(P/f'reference-snapshots/entry-{rid}.json');oldp=P/'reference-snapshots'/base['model3dPath'];old=J(oldp)
   ck(key+' exact cached geometry provenance',SHA(oldp)==q['retained_3d_sha256'] and old['atoms']==aa and old['bonds']==bb)
  details.append(dict(material=mid,formula=formula,model=rel,bond_lengths=lengths,provenance=j.get('referenceQualification',j.get('source')),method=j.get('method')))
ck('21 3D entries',len(all3d)==21)
stockprops=J(P/'source-stock-reference-proposal.json')['stocks']
ck('Five exact stock identities',{s['stock_id'] for s in stockprops}==set(source_stocks))
for s in stockprops:
 k=s['stock_id']; original=source_stocks[k]
 ck(k+' exact source stock payload',s['source_stock']==original)
 ck(k+' exact components',s['component_registry_ids']==['friedfeld2019-'+c['material_id']+'-reference' for c in original['components']])
 ck(k+' source stock SVG hash',s['sha256']==SHA(P/s['svg_path']))
ck('MSC representative not varied',next(s for s in stockprops if s['stock_id']=='msc-injection')['source_stock']['name'].startswith('Representative'))
ck('Ten source components',sum(len(s['source_stock']['components']) for s in stockprops)==10)

# Re-render frozen SVG bytes into memory to confirm the viewed PNG previews.
for d,pref in [('svg','previews'),('stock-svg','stock-previews')]:
 for svg in sorted((P/d).glob('*.svg')):
  doc=pymupdf.open(stream=svg.read_bytes(),filetype='svg');pix=doc[0].get_pixmap(alpha=False)
  actual=Image.open(P/pref/(svg.stem+'.png')).convert('RGB')
  ck(svg.stem+' exact frozen SVG raster',actual.size==(pix.width,pix.height) and actual.tobytes()==pix.samples);doc.close()

# Independent two orthogonal coordinate projections, not a new scientific asset.
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
colors={'C':'#455868','O':'#ce423c','N':'#3d66c1','H':'#a5b4bd','Cl':'#299849','P':'#dc8c21','Si':'#917046'}
for batch in range(0,len(all3d),6):
 canv=Image.new('RGB',(1800,1300),'white');dr=ImageDraw.Draw(canv)
 for offset,(mid,j) in enumerate(all3d[batch:batch+6]):
  x0=(offset%2)*900;y0=(offset//2)*425;dr.text((x0+15,y0+8),mid+' / '+j['formula'],font=font,fill='#143b4f')
  for col,axes in enumerate([('x','y'),('x','z')]):
   coords=[(a[axes[0]],a[axes[1]]) for a in j['atoms']];lo=[min(v[k] for v in coords) for k in [0,1]];hi=[max(v[k] for v in coords) for k in [0,1]]
   scale=min(370/max(hi[0]-lo[0],2),290/max(hi[1]-lo[1],2));center=[(a+b)/2 for a,b in zip(lo,hi)]
   pts=[(x0+225+col*450+(v[0]-center[0])*scale,y0+215-(v[1]-center[1])*scale) for v in coords]
   for b in j['bonds']:dr.line([pts[b['a']],pts[b['b']]],fill='#617584',width=3)
   for i,a in sorted(enumerate(j['atoms']),key=lambda t:t[1]['z']):
    x,y=pts[i];rad=5 if a['element']=='H' else 9;dr.ellipse((x-rad,y-rad,x+rad,y+rad),fill=colors.get(a['element'],'#777777'))
    if a['element']!='C' or a.get('isotope'):dr.text((x+8,y),str(a.get('isotope') or '')+a['element'],font=font,fill=colors.get(a['element'],'#333333'))
   dr.text((x0+190+col*450,y0+380),'/'.join(axes),font=font,fill='#526475')
 canv.save(O/f'coordinate-projections-{batch//6+1:02}.png')
output={'auditor':'/root/backlog_eta','author':'/root','at':datetime.now(timezone.utc).isoformat(),'runtime':rdBase.rdkitVersion,'checks':checks,'passed':sum(x['passed'] for x in checks),'failed':[x for x in checks if not x['passed']],'model_geometry_details':details,'bound_files':bound}
(O/'molecular-checks-v1.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'checks':len(checks),'passed':output['passed'],'failed':output['failed'],'bound_files':len(bound)},ensure_ascii=False))
