from pathlib import Path
import sys,json,hashlib,math,xml.etree.ElementTree as ET
from collections import Counter
sys.path.insert(0,'[local path redacted]')
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
B=Path(__file__).resolve().parent;V=B/'visuals';read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();C=[];assets={}
def ck(n,v):C.append({'check':n,'passed':bool(v)})
E=read(V/'registry-additions.json')['entries'];D={e['id']:e for e in E}
forms={'zinc-acetate-dihydrate':('C4H10O6Zn',5),'cobalt-acetate-tetrahydrate':('C4H14CoO8',7),'nickel-perchlorate-hexahydrate':('H12Cl2NiO14',9),'dodecylamine':('C12H27N',1)}
cards={'zinc-acetate-additive':None,'topo-technical':None,'zno-specimen':'ZnO','co-specimen':'ZnO:Co','ni-specimen':'ZnO:Ni','surface-co-specimen':None,'co-aggregate-specimen':'ZnO:Co','quartz':'SiO2'}
ck('12 exact references',set(D)==set(forms)|{'identity-schwartz-'+i for i in cards})
for e in E:
 i=e['id'];ck(i+'/source',e['provenance']['sourceDoi']=='10.1021/ja036811v'and e['provenance']['sourceSha256']=='48bb96493905290ae44c58f2346c6313677041e68ec5a9d50bdc428011c2be9f');ck(i+'/not measured geometry',e['provenance']['measuredCoordinates']is False);ck(i+'/not training geometry',e['provenance']['eligible_training']is False);ck(i+'/no database lookup',e['pubchemCid']is None)
 for k in ['svgPath','model2dPath','model3dPath']:
  if e[k]:p=V/e[k];assets[e[k]]=sha(p);ck(i+'/'+k+'/hash',sha(p)==e['assetHashes'][k])
 ET.fromstring((V/e['svgPath']).read_text(encoding='utf8'))
 if i in forms:
  m=Chem.AddHs(Chem.MolFromSmiles(e['provenance']['smiles']));f,nfr= forms[i]
  ck(i+'/formula',rdMolDescriptors.CalcMolFormula(m)==f==e['formula']);ck(i+'/neutral formula unit',sum(a.GetFormalCharge()for a in m.GetAtoms())==0);ck(i+'/disconnected components',len(Chem.GetMolFrags(m))==nfr)
  for dim in ['2d','3d']:
   key='model'+dim+'Path'
   if not e[key]:continue
   md=read(V/e[key]);atoms=md['atoms'];bonds=md['bonds']
   ck(i+'/'+dim+'/atom counts',Counter(a['element']for a in atoms)==Counter(a.GetSymbol()for a in m.GetAtoms()))
   ck(i+'/'+dim+'/charges',[a['formalCharge']for a in atoms]==[a.GetFormalCharge()for a in m.GetAtoms()]);ck(i+'/'+dim+'/bonds',[(b['a'],b['b'],b['order'])for b in bonds]==[(b.GetBeginAtomIdx(),b.GetEndAtomIdx(),b.GetBondTypeAsDouble())for b in m.GetBonds()]);ck(i+'/'+dim+'/finite',all(math.isfinite(a[k])for a in atoms for k in ['x','y','z']));ck(i+'/'+dim+'/not labels',md['eligible_training']is False);ck(i+'/'+dim+'/groups',md['functionalGroups']==e['functionalGroups'])
   if dim=='3d':
    lengths=[math.sqrt(sum((atoms[b['a']][k]-atoms[b['b']][k])**2 for k in ['x','y','z']))for b in bonds]
    ck(i+'/plausible free-molecule bond lengths',all(.85<d<1.7 for d in lengths));ck(i+'/3d declared computed','computed conformer'in md['caption']);ck(i+'/3d rotation',md['allowRotation']and md['has3D']);ck(i+'/angstrom',md['coordinateUnits']=='angstrom')
  if i!='dodecylamine':ck(i+'/no ionic3D',e['model3dPath']is None)
  if 'acetate'in i:
   g=e['functionalGroups'];ck(i+'/two carboxylate groups highlighted',len(g)==1 and g[0]['label']=='Carboxylate group'and len(g[0]['atomIndices'])==6 and len(g[0]['bondIndices'])==4)
  if i=='dodecylamine':
   ck('Dodecylamine 12-carbon linear primary amine',sum(a.GetSymbol()=='C'for a in m.GetAtoms())==12 and len(m.GetSubstructMatches(Chem.MolFromSmarts('[NX3;H2][CH2]')))==1);ck('Primary amine highlight',len(e['functionalGroups'])==1 and e['functionalGroups'][0]['label']=='Primary amine');ck('Dodecylamine conformer converged',e['provenance']['conformerConverged']is True)
 else:
  k=i.replace('identity-schwartz-','');ck(i+'/source formula',e['formula']==cards[k]);ck(i+'/no atomic construction',e['model2dPath']is None and e['model3dPath']is None and e['functionalGroups']==[])
for row in read(V/'asset-manifest.json')['files']:ck('Manifest/'+row['path'],sha(V/row['path'])==row['sha256'])
ck('Additive hydration unresolved','hydration is not silently transferred'in D['identity-schwartz-zinc-acetate-additive']['caption']);ck('TechnicalTOPO impurity limit','unidentified phosphonic-acid impurities'in D['identity-schwartz-topo-technical']['caption']);ck('Surfacecontrol not substitutional','separate from substitutionally doped'in D['identity-schwartz-surface-co-specimen']['caption']);ck('Aggregate size conflict retained','4.9 and5.0nm'in D['identity-schwartz-co-aggregate-specimen']['caption']);ck('Quartz support not precursor','not a synthesis ingredient'in D['identity-schwartz-quartz']['caption'])
manual=['All twelve actual registry entries, captions, model graphs and SVG contents independently inspected; both current contact sheets actually viewed. No clipped formula or confusing ligand overlap observed.','Zn acetate dihydrate C4H10O6Zn has oneZn2+,twoacetates,two waters; Co acetate tetrahydrate C4H14CoO8 has oneCo2+,twoacetates,four waters. Disconnected graphs do not imply measured metalcoordination.','Nickel perchlorate hexahydrate has oneNi2+,twoClO4−,sixwaters: H12Cl2NiO14. RDKit charge-separated perchlorate resonance drawing is valid; no Ni–O coordination or hydrated lattice claimed.','Dodecylamine is a linear twelvecarbon primaryamine C12H27N. Explicit-H free-molecule2D/3D graphs agree; ETKDG/UFF coordinates are illustrative, finite and bond lengths plausible, not surface geometry or measuredconformer.','TechnicalTOPO has unknown phosphonicacid composition; separate pureTOPO component can be referenced without equating it to actualreagent/ligandshell. OptionalZnacetate additive retains unspecified hydration.','Pure/co-/ni-doped specimen cards do not impose universal dopantfraction or measured atomicsite map. S2surface-boundCo andaggregate3.6%Co are separatecontexts. Quartz isanalyticalsupport. No source atomisticmodel fabricated.','Final reusedreferences,recordbindings and anybulkCIF are separateaudit; noSitechange.']
fails=[c for c in C if not c['passed']];out={'status':'passed_source_and_asset_audit_bindings_separate'if not fails else'failed','source_id':'schwartz2003','source_audit_sha256':sha(B/'source-audit.json'),'registry_sha256':sha(V/'registry-additions.json'),'asset_manifest_sha256':sha(V/'asset-manifest.json'),'entry_count':len(E),'asset_hashes':assets,'visual_coverage':[{'path':str(V/'review'/f'molecular-contact-{i}.png'),'sha256':sha(V/'review'/f'molecular-contact-{i}.png'),'actually_viewed':True}for i in [1,2]],'check_count':len(C),'checks':C,'failures':fails,'manual_review':manual,'site_mutated':False}
(B/'molecular-source-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(B/'molecular-source-audit.md').write_text('# Schwartz 2003 molecular source audit\n\n'+out['status']+f'; {len(C)} checks and {len(fails)} failures.\n\n'+'\n\n'.join(manual)+'\n\nRegistry SHA256 `'+out['registry_sha256']+'`.\n',encoding='utf8');print(json.dumps({'status':out['status'],'checks':len(C),'failures':fails,'registry_sha256':out['registry_sha256']}))
