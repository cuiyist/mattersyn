from pathlib import Path
from collections import Counter
import json,hashlib,math,sys
sys.path.insert(0,'[local path redacted]')
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
B=Path(__file__).resolve().parent;V=B/'visuals';S=B.parents[3]/'recipe-atlas/dist/assets/chemical-registry'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
C=[]
def ck(n,v):C.append({'check':n,'passed':bool(v)})
bind=read(V/'bindings-additions.json');prod=read(V/'product-reference-proposal.json');reuse=read(V/'reused-reference-audit-input.json')
new={e['id']:e for e in read(V/'registry-additions.json')['entries']};old={e['id']:e for e in read(S/'registry.json')['entries']}
R={p.stem:read(p)for p in (B/'canonical-drafts').glob('*.json')};audited=read(B/'canonical-records-audit.json')['record_hashes']
expected_smiles={'ethanol':'CCO','sulfuric-acid':'O=S(=O)(O)O','hydrochloric-acid-aqueous':'[H+].[Cl-]','water':'O','tetradecylphosphonic-acid':'CCCCCCCCCCCCCCP(=O)(O)O','topo':'CCCCCCCCP(=O)(CCCCCCCC)CCCCCCCC','top':'CCCCCCCCP(CCCCCCCC)CCCCCCCC','toluene':'Cc1ccccc1','methanol':'CO','dimethylformamide':'CN(C)C=O'}
expected_reuse=set(expected_smiles)|{'cadmium-oxide','argon'}
identity={'hydrochloric-acid':'hydrochloric-acid-aqueous','tdpa':'tetradecylphosphonic-acid'}
ck('All 14 record groups',set(bind['recordBindings'])==set(R));ck('41 material slots',sum(len(v)for v in bind['recordBindings'].values())==41)
for rid,r in R.items():
 ck(rid+'/audited bytes',sha(B/'canonical-drafts'/(rid+'.json'))==audited[rid]==bind['sourceRecordSha256'][rid]);row=bind['recordBindings'][rid];ck(rid+'/all slots',set(row)=={m['id']for m in r['materials']})
 for m in r['materials']:
  mid=m['id'];eid=row[mid];e=new.get(eid)or old[eid];expected=identity.get(mid,mid if mid in expected_reuse else 'identity-banerjee-'+mid)
  ck(rid+'/'+mid+'/identity',eid==expected);ck(rid+'/'+mid+'/formula',m['formula']==e['formula'])
  if mid in ['tellurium-source','te-top-stock','mwnt-oxidized','mwnt-mild']:ck(rid+'/'+mid+'/no invented formula or atomic model',e['formula'] is None and not e['model2dPath'] and not e['model3dPath'])
 ck(rid+'/scope note',bool(bind['bindingNotes'][rid]))
ck('Only reported growth product',prod['recordBindings']=={'banerjee-2003-growth':'identity-banerjee-composite-specimen'})
e=new['identity-banerjee-composite-specimen'];ck('Composite schematic excluded from training geometry',not e['model2dPath'] and not e['model3dPath'] and e['provenance']['eligible_training'] is False)
ck('Exactly 12 expected reused references',set(reuse['entries'])==expected_reuse)
asset_hashes={};graphs={}
for eid,row in reuse['entries'].items():
 e=row['entry'];ck(eid+'/metadata exact',e==old[eid]);asset_hashes[eid]={};graphs[eid]={}
 for k,h in row['assetHashes'].items():
  path=S/e[k];asset_hashes[eid][k]=sha(path);ck(eid+'/'+k+'/hash',asset_hashes[eid][k]==h==e['assetHashes'][k])
 if eid not in expected_smiles:
  ck(eid+'/formula-only',not e['model2dPath'] and not e['model3dPath']);continue
 expected=Chem.MolFromSmiles(expected_smiles[eid]);expected_graph=Chem.MolToSmiles(expected)
 for kind in ['2d','3d']:
  key='model'+kind+'Path'
  if not e.get(key):
   ck(eid+'/'+kind+'/intentional absent charged3D',eid=='hydrochloric-acid-aqueous' and kind=='3d');continue
  d=read(S/e[key]);atoms=d['atoms'];bonds=d['bonds'];m=Chem.RWMol()
  for atom in atoms:
   a=Chem.Atom(atom['element']);a.SetFormalCharge(atom.get('formalCharge',0));a.SetIsotope(atom.get('isotope',0));a.SetNoImplicit(True);a.SetNumExplicitHs(atom.get('implicitHydrogenCount',0));m.AddAtom(a)
  for bond in bonds:m.AddBond(bond['a'],bond['b'],{1:Chem.BondType.SINGLE,1.5:Chem.BondType.AROMATIC,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE}[bond['order']])
  mol=m.GetMol();Chem.SanitizeMol(mol);mol=Chem.RemoveHs(mol);graph=Chem.MolToSmiles(mol);graphs[eid][kind]={'canonical_smiles':graph,'formula':rdMolDescriptors.CalcMolFormula(mol),'atom_count':len(atoms),'bond_count':len(bonds)}
  ck(eid+'/'+kind+'/independent chemical graph',graph==expected_graph);ck(eid+'/'+kind+'/formula',rdMolDescriptors.CalcMolFormula(mol)==rdMolDescriptors.CalcMolFormula(expected))
  ck(eid+'/'+kind+'/finite coordinates',all(all(math.isfinite(a[k])for k in ['x','y','z'])for a in atoms))
  ck(eid+'/'+kind+'/atom index continuity',[a['index']for a in atoms]==list(range(len(atoms))))
  for gi,g in enumerate(d.get('functionalGroups',[])):
   ck(eid+'/'+kind+'/functional atoms '+str(gi),all(0<=i<len(atoms)for i in g['atomIndices']))
   ck(eid+'/'+kind+'/functional bonds '+str(gi),all(0<=i<len(bonds)for i in g['bondIndices']))
   els=Counter(atoms[i]['element']for i in g['atomIndices'])
   expected_groups={'ethanol':{'C':1,'O':1},'methanol':{'C':1,'O':1},'tetradecylphosphonic-acid':{'P':1,'O':3},'topo':{'P':1,'O':1},'top':{'P':1},'sulfuric-acid':{'S':1,'O':4},'dimethylformamide':{'C':1,'O':1}}
   if eid in expected_groups:ck(eid+'/'+kind+'/functional membership '+str(gi),els==expected_groups[eid])
  if kind=='3d':
   text=json.dumps(d).lower();ck(eid+'/computed geometry labeled',('computed' in text or 'rdkit' in text)and any(s in text for s in ['not measured','not a measured','not an experimental structure']))
   for bi,bond in enumerate(bonds):
    a=atoms[bond['a']];b=atoms[bond['b']];dist=math.sqrt(sum((a[k]-b[k])**2 for k in ['x','y','z']));ck(eid+'/3d/bond length '+str(bi),.65<dist<2.2)
ck('DMF shared caption has no old specimen role','qdoh' not in (old['dimethylformamide']['caption']+' '.join(old['dimethylformamide']['limitations'])).lower())
ck('HCl charged reference explicitly no 3D',old['hydrochloric-acid-aqueous']['model3dPath'] is None)
manual=[
'All 41 material bindings across the 14 audited records were independently matched to the source-named identities and actual material formula fields. The Te feed remains a chemically unresolved solution in TOP; no elemental allotrope or discrete TOPTe structure is invented. Oxidized MWNT surfaces have no molecular formula or refined atomic model.',
'The sole product reference belongs to the reported CdTe/MWNT growth route. Bound composite, free washings, no-tube comparison, mild oxidation and strongly oxidized precursor remain distinct contexts. The SI IR trace binds only the oxidized precursor. Analytical sample solvents are not synthesis precursors; the PTFE membrane remains equipment.',
'All 12 reused entries were read for source-neutral identity, caption and provenance. The actual SVG depictions were rasterized and visually inspected in reused-contact-1.png and reused-contact-2.png. Independent reconstruction of every supplied 2D/3D graph confirms ethanol, sulfuric acid, ionic HCl, water, 14-carbon TDPA, three C8-chain TOP/TOPO, toluene, methanol and DMF. Atom counts, valences, charges, functional-group members, finite coordinates and plausible covalent bond lengths were checked. Computed conformers are illustrative, not measured solution or surface structures.',
'HCl is an explicitly limited disconnected ionic 2D notation with no 3D geometry; sulfuric acid is a conventional free-molecule identity, not the acidic oxidation mixture speciation. CdO and Ar retain formula-only references. No common-reference source provenance was reinterpreted as evidence for current experimental conditions.',
'The 11 new entries already passed molecular-source-audit.json; this report binds those exact registry bytes, all current canonical bytes, the product proposal and all reused asset hashes. No Site, monitor or source-file mutation; no new downloads or browser claims.'
]
fail=[x for x in C if not x['passed']]
out={'status':'passed'if not fail else'failed','source_id':'banerjee2003','bindings_sha256':sha(V/'bindings-additions.json'),'product_reference_sha256':sha(V/'product-reference-proposal.json'),'reused_reference_input_sha256':sha(V/'reused-reference-audit-input.json'),'registry_sha256':sha(V/'registry-additions.json'),'record_hashes':audited,'reused_asset_hashes':asset_hashes,'graph_results':graphs,'record_count':14,'material_binding_count':41,'product_binding_count':1,'reused_reference_count':12,'check_count':len(C),'checks':C,'failures':fail,'manual_review':manual,'site_mutated':False}
(B/'bindings-source-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(B/'bindings-source-audit.md').write_text('# Banerjee2003 binding source audit\n\n'+out['status']+f'; {len(C)} checks, {len(fail)} failures.\n\n'+'\n\n'.join(manual)+'\n',encoding='utf8');print(json.dumps({'status':out['status'],'checks':len(C),'failures':fail}))
