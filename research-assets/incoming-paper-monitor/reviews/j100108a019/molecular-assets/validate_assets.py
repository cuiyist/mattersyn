"""Independent JSON/connectivity/hash audit and render of the actual proposed SVGs."""
import sys,json,re,math,hashlib,collections,xml.etree.ElementTree as ET
from pathlib import Path
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent
REVIEW=OUT.parent
EXISTING=Path('[local path redacted]')
sys.path.insert(0,'[local path redacted]')
sys.path.insert(0,'[local path redacted]')
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
import pymupdf
from PIL import Image,ImageDraw,ImageFont
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def counts(s):
 out=collections.Counter()
 for e,n in re.findall(r'([A-Z][a-z]?)(\d*)',s):out[e]+=int(n or 1)
 return out
errors=[];checks=0
def check(test,msg):
 global checks
 checks+=1
 if not test:errors.append(msg)
def reconstructed(model):
 rw=Chem.RWMol()
 for a in model['atoms']:
  atom=Chem.Atom(a['element']);atom.SetFormalCharge(a['formalCharge']);atom.SetIsotope(a['isotope'])
  atom.SetNoImplicit(True);atom.SetNumExplicitHs(a['implicitHydrogenCount']);rw.AddAtom(atom)
 for b in model['bonds']:rw.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,1.5:Chem.BondType.AROMATIC,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE}[b['order']])
 mol=rw.GetMol();Chem.SanitizeMol(mol);return mol
registry=read(OUT/'registry-additions.json');new={e['id']:e for e in registry['entries']}
old={e['id']:e for e in read(EXISTING/'registry.json')['entries']}
bindings=read(OUT/'bindings-additions.json');catalog={e['id']:e for e in read(OUT/'source-catalog.json')}
check(len(new)==19,'19 unique new identities')
check(not (set(new)&set(old)),'No duplicate or overwritten existing registry identity')
for id,e in new.items():
 check(bool(e['sourceUrls']),id+' source URL present')
 for key in ['svgPath','model2dPath','model3dPath']:
  if not e.get(key):continue
  p=(OUT/e[key]).resolve();check(p.is_relative_to(OUT) and p.exists(),id+' local path '+key)
  check(sha(p)==e['assetHashes'][key],id+' hash '+key)
 svg=(OUT/e['svgPath']).read_text(encoding='utf-8');root=ET.fromstring(svg)
 check(not re.search(r'<script|onload=|javascript:|(?:href|src)="https?://',svg,re.I),id+' passive SVG')
 check(root.get('viewBox')=='0 0 840 360' or root.get('width')=='840px',id+' SVG dimensions')
 if e['depictionKind']!='molecule':check(not e['model3dPath'],id+' no nondiscrete 3D')
 if e['depictionKind'] in ['formula','support','single_atom']:check(not e['model2dPath'],id+' no guessed graph')
 for key in ['model2dPath','model3dPath']:
  if not e.get(key):continue
  model=read(OUT/e[key]);aa=model['atoms'];bb=model['bonds'];check(model['id']==id,id+' model ID '+key)
  check(bool(aa) and all(math.isfinite(a[c]) for a in aa for c in ['x','y','z']),id+' finite coordinates '+key)
  check([a['index'] for a in aa]==list(range(len(aa))),id+' contiguous atom indices '+key)
  check(all(0<=b['a']<len(aa) and 0<=b['b']<len(aa) and b['a']!=b['b'] and b['order'] in [1,1.5,2,3] for b in bb),id+' valid bonds '+key)
  check(len({tuple(sorted([b['a'],b['b']])) for b in bb})==len(bb),id+' no duplicate bonds '+key)
  mol=reconstructed(model);reference=Chem.MolFromMolFile(str(OUT/'raw'/(id+'-pubchem-2d.sdf')),removeHs=False,sanitize=True)
  check(counts(rdMolDescriptors.CalcMolFormula(mol))==counts(e['formula']),id+' reconstructed formula '+key)
  check(Chem.GetFormalCharge(mol)==catalog[id]['properties']['Charge']==0,id+' net charge '+key)
  check(Chem.MolToSmiles(Chem.RemoveHs(mol),isomericSmiles=True)==Chem.MolToSmiles(Chem.RemoveHs(reference),isomericSmiles=True),id+' source connectivity '+key)
  for group in model['functionalGroups']:
   check(all(0<=i<len(aa) for i in group['atomIndices']),id+' group atom indices '+key)
   check(all(0<=i<len(bb) and {bb[i]['a'],bb[i]['b']}<=set(group['atomIndices']) for i in group['bondIndices']),id+' group bond indices '+key)
  if key=='model3dPath':
   check(model.get('has3D') and model.get('allowRotation') and model.get('representation')=='3d',id+' correct 3D flags')
   check(model['coordinateSource']=='local-rdkit' and 'not a measured' in model['caption'],id+' illustrative provenance')
   for b in bb:
    d=math.dist([aa[b['a']][c] for c in ['x','y','z']],[aa[b['b']][c] for c in ['x','y','z']])
    check(.45<d<2.9,id+' plausible bond length')
   check(all(math.dist([aa[i][c] for c in ['x','y','z']],[aa[j][c] for c in ['x','y','z']])>.45 for i in range(len(aa)) for j in range(i)),id+' no gross overlaps')
   check(model['conformerGeneration']['minimizationReturnCode']==0,id+' force-field converged')
  else:check(not model['allowRotation'] and not model['has3D'] and all(a['z']==0 for a in aa),id+' 2D representation cannot claim 3D')
  if e['depictionKind']=='ionic_components':
   frags=Chem.GetMolFrags(mol)
   check(len(frags)==2 and sorted(sum(mol.GetAtomWithIdx(i).GetFormalCharge() for i in f) for f in frags)==[-1,1],id+' separate counterions')
for row in catalog.values():
 for key,file in [('lookupSha256',row['id']+'-lookup.json'),('propertiesSha256',row['id']+'-properties.json'),('sdfSha256',row['id']+'-pubchem-2d.sdf')]:
  check(sha(OUT/'raw'/file)==row[key],row['id']+' raw source hash '+key)
for e in read(OUT/'reused-references.json')['entries']:
 check(e['id'] in old,e['id']+' reuse resolves')
 for key,path in e['assetPaths'].items():
  check(sha(EXISTING/path)==e['assetHashes'][key],e['id']+' existing asset unchanged '+key)
  check(not (OUT/path).exists(),e['id']+' asset not duplicated '+key)
for rid,mm in bindings['recordBindings'].items():
 matches=[p for folder in ['canonical-drafts','procedure-drafts','context-drafts'] for p in (REVIEW/folder).glob(rid+'.json')]
 check(len(matches)==1,rid+' source record exists uniquely');r=read(matches[0])
 check(sha(matches[0])==bindings['sourceRecordSha256'][rid],rid+' record hash')
 check(set(mm)=={m['id'] for m in r['materials']},rid+' complete bindings')
 for mid,id in mm.items():check(id in new or id in old,rid+'/'+mid+' binding resolves')
check(bindings['recordBindings']['littau-1993-si-tem-characterization']['ethylene-chloride']=='identity-littau-ethylene-chloride-unresolved','Ambiguous ethylene chloride remains separate')
check(bindings['recordBindings']['littau-1993-si-powder-preparation']['ethylene-dichloride']=='ethylene-dichloride','Known ethylene dichloride resolves correctly')
check(new['tetrabutylammonium-bromide']['formula']=='C16H36BrN','TBAB not TOAB or TOPB')
for filename in ['registry-additions.json','bindings-additions.json','reused-references.json','molecules-3d-additions.json','missing-identities.json']:
 check(not re.search(r'(?<![A-Za-z])[A-Za-z]:[\\/]|file://',(OUT/filename).read_text(encoding='utf-8')),filename+' public metadata has no machine paths')

# Render actual SVG assets, not substitute drawings, and create contact sheets.
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
ids=list(new)
for id in ids:
 doc=pymupdf.open(stream=(OUT/new[id]['svgPath']).read_bytes(),filetype='svg')
 doc[0].get_pixmap(alpha=False).save(str(OUT/'review'/(id+'.png')))
for page in range(math.ceil(len(ids)/12)):
 canvas=Image.new('RGB',(1260,1056),'white');draw=ImageDraw.Draw(canvas)
 for i,id in enumerate(ids[page*12:(page+1)*12]):
  im=Image.open(OUT/'review'/(id+'.png')).convert('RGB');im.thumbnail((410,180));x=(i%3)*420;y=(i//3)*264
  canvas.paste(im,(x+5,y+46));draw.text((x+9,y+10),id[:42],font=font,fill='#112a3a')
 canvas.save(OUT/'review'/('contact-'+str(page+1)+'.png'))
report={'status':'passed' if not errors else 'failed','checks':checks,'errors':errors,'summary':registry['summary'],
 'registryAdditionsSha256':sha(OUT/'registry-additions.json'),'bindingsAdditionsSha256':sha(OUT/'bindings-additions.json'),
 'sourceCatalogSha256':sha(OUT/'source-catalog.json'),'visualReviewStatus':'pending manual inspection of the actual SVG contact sheets',
 'contactSheets':['review/contact-1.png','review/contact-2.png'],
 'limits':['3D coordinates are computed illustrative free-compound conformers.','Ionic fragments have no 3D model.','Eight unresolved or nondiscrete source identities have no inferred molecular graph.','Existing five reference assets are reused without copying.']}
(OUT/'validation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['status','checks','errors','summary']},indent=2));raise SystemExit(bool(errors))
