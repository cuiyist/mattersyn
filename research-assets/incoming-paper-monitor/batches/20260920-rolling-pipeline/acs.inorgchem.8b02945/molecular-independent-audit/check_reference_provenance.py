from pathlib import Path
import sys,json,hashlib,math
sys.dont_write_bytecode=True
F=Path(__file__).resolve().parents[1];O=Path(__file__).resolve().parent;P=F/'visuals/molecules';M=F.parents[4]
sys.path[:0]=[str(M/'research-assets/rdkit-runtime'),str(M/'research-assets/corpus-20260917/runtime')]
from rdkit import Chem
from rdkit.Chem import AllChem,rdMolDescriptors
J=lambda p:json.loads(Path(p).read_text('utf-8-sig'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[];bound={};notes=[]
def ck(n,v,d=None):checks.append(dict(check=n,passed=bool(v),detail=d))
def bind(p):p=Path(p);bound[str(p)]=sha(p);return p
primary=J(P/'reference-snapshots/primary/pubchem-identities.json')['PropertyTable']['Properties']
for a in primary:
 mol=Chem.MolFromSmiles(a['SMILES']);ck(str(a['CID'])+' primary graph formula',rdMolDescriptors.CalcMolFormula(mol)==a['MolecularFormula'])
 ck(str(a['CID'])+' primary InChI',Chem.MolToInchi(mol)==a['InChI'])
ck('CID 241 parent is unlabeled benzene',next(a for a in primary if a['CID']==241)['MolecularFormula']=='C6H6')
for p in sorted((P/'models').glob('*-3d.json')):
 j=J(p);mid=p.stem;src=j.get('source');aa=j['atoms']
 if j.get('assetFile'):
  path=bind(M/'research-assets'/j['assetFile']);mol=next(x for x in Chem.SDMolSupplier(str(path),removeHs=False) if x)
  ck(mid+' raw SDF atom order',[a.GetSymbol() for a in mol.GetAtoms()]==[a['element'] for a in aa])
  ck(mid+' raw SDF bond count',mol.GetNumBonds()==len(j['bonds']))
  for i,a in enumerate(aa):ck(mid+f' raw coordinate {i}',max(abs(mol.GetConformer().GetAtomPosition(i)[k]-a[t]) for k,t in enumerate('xyz'))<1e-6)
  ck(mid+' raw SDF isotope graph formula',rdMolDescriptors.CalcMolFormula(mol,separateIsotopes=True)==j['formula'])
 if isinstance(src,dict) and src.get('embedding'):
  m=Chem.AddHs(Chem.MolFromSmiles(src['reference_smiles']));opts=AllChem.ETKDGv3();opts.randomSeed=src['seed'];emb=AllChem.EmbedMolecule(m,opts)
  result=AllChem.MMFFOptimizeMolecule(m,maxIters=2000) if src['minimization']=='MMFF94' else AllChem.UFFOptimizeMolecule(m,maxIters=2000)
  ck(mid+' independently reproduced convergence',emb==0 and result==src['minimization_result'])
  for i,a in enumerate(aa):ck(mid+f' reproduced coordinate {i}',max(abs(m.GetConformer().GetAtomPosition(i)[k]-a[t]) for k,t in enumerate('xyz'))<1e-7)
 if 'conformerGeneration' in j:
  q=j['conformerGeneration'];ck(mid+' cached recorded convergence',q['embeddingStatus']==0 and q['minimizationReturnCode']==0)
  ck(mid+' cached recorded method',j['method']=='ETKDGv3 + '+q['forceField'] and q['randomSeed'] in (20260918,20260919))
 # Cached computed arrays are bound exactly in check_molecules.py. Prior generation
 # methods remain supporting historical provenance, never current source measurements.
for rel in ['quality-20260918/molecules/build_registry.py','incoming-paper-monitor/reviews/jp011815c/build_molecular_assets.py','incoming-paper-monitor/reviews/jp011815c/visuals/molecular-generation-check.json']:
 bind(M/'research-assets'/rel)
gu=M/'research-assets/incoming-paper-monitor/batches/20260919-five-paper-pilot/ja0496423/visuals/molecules/raw'
for name in ['nitrogen-nist-web-tool-excerpt.txt','nitrogen-nist-extracted-reference.json']:bind(gu/name)
excerpt=(gu/'nitrogen-nist-web-tool-excerpt.txt').read_text('utf-8-sig');ck('Retained NIST reference row', '1.09768' in excerpt and '^{14}N_{2}' in excerpt and 'internuclear distance' in excerpt)
bind(P/'reference-snapshots/primary/pubchem-identities.json');bind(P/'reference-snapshots/primary/retrieval.json')
out=dict(author='/root',auditor='/root/backlog_eta',checks=checks,passed=sum(x['passed'] for x in checks),failed=[x for x in checks if not x['passed']],bound_files=bound,auditor_checker_corrections=['Initial helper wrongly assumed every cached model seed was 20260918; three documented older models use 20260919. Corrected without author changes.','Initial literal NIST isotope test expected plain 14N2, while the retained exact tool output uses superscript/subscript markup. Corrected the parser only.'])
(O/'reference-provenance-checks-v1.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'checks':len(checks),'passed':out['passed'],'failed':out['failed'],'raw_files':len(bound)}))
