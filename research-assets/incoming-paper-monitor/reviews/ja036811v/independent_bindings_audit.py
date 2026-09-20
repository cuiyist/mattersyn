from pathlib import Path
from collections import Counter
import json,hashlib,math,sys,xml.etree.ElementTree as ET
sys.path.insert(0,'[local path redacted]')
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
B=Path(__file__).resolve().parent;V=B/'visuals';S=B.parents[3]/'recipe-atlas/dist/assets/chemical-registry';CR=S.parent/'crystal-references'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();C=[]
def ck(n,v):C.append({'check':n,'passed':bool(v)})
bind=read(V/'bindings-additions.json');prod=read(V/'product-reference-proposal.json');reuse=read(V/'reused-reference-audit-input.json');neutral=read(V/'registry-neutralizations.json');cr=read(V/'crystal-reference-proposal.json')
new={e['id']:e for e in read(V/'registry-additions.json')['entries']};old={e['id']:e for e in read(S/'registry.json')['entries']};proposed={**old,**{e['id']:e['after']for e in neutral['updates']}};nf={x['path']:x for x in neutral['files']}
R={p.stem:read(p)for p in(B/'canonical-drafts').glob('*.json')};audited=read(B/'canonical-records-audit.json')['record_hashes']
expected_smiles={'ethanol':'CCO','tetramethylammonium-hydroxide-pentahydrate':'C[N+](C)(C)C.[OH-].O.O.O.O.O','dimethyl-sulfoxide':'CS(C)=O','ethyl-acetate':'CCOC(C)=O','heptane':'CCCCCCC','toluene':'Cc1ccccc1','topo':'CCCCCCCCP(=O)(CCCCCCCC)CCCCCCCC'}
mapping={'dmso':'dimethyl-sulfoxide','topo-component':'topo'}
for k in ['ethanol','tetramethylammonium-hydroxide-pentahydrate','ethyl-acetate','heptane','toluene','helium','zinc-acetate-dihydrate','cobalt-acetate-tetrahydrate','nickel-perchlorate-hexahydrate','dodecylamine']:mapping[k]=k
equiv={'zinc-acetate-dihydrate':'Zn(C2H3O2)2·2H2O','cobalt-acetate-tetrahydrate':'Co(C2H3O2)2·4H2O','nickel-perchlorate-hexahydrate':'Ni(ClO4)2·6H2O','tetramethylammonium-hydroxide-pentahydrate':'C4H13NO·5H2O'}
ck('30groups',set(bind['recordBindings'])==set(R));ck('96slots',sum(len(v)for v in bind['recordBindings'].values())==96)
for rid,r in R.items():
 ck(rid+'/audited bytes',sha(B/'canonical-drafts'/(rid+'.json'))==audited[rid]==bind['sourceRecordSha256'][rid]);row=bind['recordBindings'][rid];ck(rid+'/all materials',set(row)=={m['id']for m in r['materials']})
 for m in r['materials']:
  mid=m['id'];eid=row[mid];e=new.get(eid)or proposed[eid];ck(rid+'/'+mid+'/identity',eid==mapping.get(mid,'identity-schwartz-'+mid))
  if mid=='zinc-acetate-additive':ck(rid+'/'+mid+'/unknown hydration card',e['formula']is None and'hydration unspecified'in m['name'].lower())
  else:ck(rid+'/'+mid+'/formula',m['formula']==equiv.get(eid,e['formula']))
  if mid=='topo-technical':ck(rid+'/mixture not pureTOPO',e['formula']is None and eid=='identity-schwartz-topo-technical')
 ck(rid+'/scope note',bool(bind['bindingNotes'][rid]))
expected_product={**{'schwartz-2003-'+i:'identity-schwartz-zno-specimen'for i in['zno-route','topo-zno','room-aging','thermal-ripening','clarity-restoration']},**{'schwartz-2003-'+i:'identity-schwartz-co-specimen'for i in['co-route','topo-co']},**{'schwartz-2003-'+i:'identity-schwartz-ni-specimen'for i in['ni-route','topo-ni']},**{'schwartz-2003-'+i:'identity-schwartz-co-aggregate-specimen'for i in['aggregation','magnetometry']},'schwartz-2003-surface-cleaning-control':'identity-schwartz-surface-co-specimen'}
ck('12 scoped productreferences',prod['recordBindings']==expected_product)
ck('No mixed/model generic productcard',all(not k.endswith(x)for k in prod['recordBindings']for x in ['mcd','optical-absorption','exchange-model','charge-transfer-model','microscopy']))
ck('Eight reused identities',set(reuse['entries'])==set(expected_smiles)|{'helium'})
assets={};graphs={}
for eid,row in reuse['entries'].items():
 e=row['entry'];ck(eid+'/proposed metadata',e==proposed[eid]);assets[eid]={};graphs[eid]={}
 for k,h in row['assetHashes'].items():
  path=Path(nf[e[k]]['private_path'])if e[k]in nf else S/e[k];assets[eid][k]=sha(path);ck(eid+'/'+k+'/hash',sha(path)==h==e['assetHashes'][k])
 if eid=='helium':ck('He single atom',e['formula']=='He'and e['model2dPath']is None and e['model3dPath']is None);continue
 expected=Chem.MolFromSmiles(expected_smiles[eid]);exp=Chem.MolToSmiles(expected)
 for dim in ['2d','3d']:
  key='model'+dim+'Path'
  if not e[key]:ck(eid+'/'+dim+'/intentionally no ionic3D',eid=='tetramethylammonium-hydroxide-pentahydrate'and dim=='3d');continue
  path=Path(nf[e[key]]['private_path'])if e[key]in nf else S/e[key];d=read(path);atoms=d['atoms'];bonds=d['bonds'];m=Chem.RWMol()
  for a in atoms:
   aa=Chem.Atom(a['element']);aa.SetFormalCharge(a.get('formalCharge',0));aa.SetIsotope(a.get('isotope',0));aa.SetNoImplicit(True);aa.SetNumExplicitHs(a.get('implicitHydrogenCount',0));m.AddAtom(aa)
  for b in bonds:m.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,1.5:Chem.BondType.AROMATIC,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE}[b['order']])
  mol=m.GetMol();Chem.SanitizeMol(mol);mol=Chem.RemoveHs(mol);sm=Chem.MolToSmiles(mol);graphs[eid][dim]={'canonical_smiles':sm,'formula':rdMolDescriptors.CalcMolFormula(mol),'atoms':len(atoms),'bonds':len(bonds)}
  ck(eid+'/'+dim+'/chemical graph',sm==exp);ck(eid+'/'+dim+'/formula',rdMolDescriptors.CalcMolFormula(mol)==rdMolDescriptors.CalcMolFormula(expected));ck(eid+'/'+dim+'/finite',all(math.isfinite(a[k])for a in atoms for k in['x','y','z']))
  for gi,g in enumerate(d.get('functionalGroups',[])):
   ck(eid+'/'+dim+'/group bounds'+str(gi),all(0<=i<len(atoms)for i in g['atomIndices'])and all(0<=i<len(bonds)for i in g['bondIndices']))
   expected_groups={'ethanol':{'C':1,'O':1},'ethyl-acetate':{'C':2,'O':2},'dimethyl-sulfoxide':{'S':1,'O':1},'topo':{'P':1,'O':1},'tetramethylammonium-hydroxide-pentahydrate':{'O':1}}
   if eid in expected_groups:ck(eid+'/'+dim+'/group membership'+str(gi),Counter(atoms[i]['element']for i in g['atomIndices'])==expected_groups[eid])
  if dim=='3d':
   text=json.dumps(d).lower();ck(eid+'/computed not sourcegeometry',any(x in text for x in['computed','rdkit'])and any(x in text for x in['not measured','not a measured','not an experimental structure']))
   for j,b in enumerate(bonds):dist=math.sqrt(sum((atoms[b['a']][k]-atoms[b['b']][k])**2 for k in['x','y','z']));ck(eid+'/bondlength'+str(j),.65<dist<2.2)
for e in neutral['updates']:
 ck(e['id']+'/before actual',e['before']==old[e['id']]);before=e['before'];after=e['after'];ck(e['id']+'/identity stable',all(before[k]==after[k]for k in ['id','formula','displayFormula','depictionKind','functionalGroups','model2dPath','model3dPath']))
 for k,v in before['provenance'].items():ck(e['id']+'/provenance retained/'+k,after['provenance'].get(k)==v)
for e in neutral['files']:
 ck('Neutral/'+e['path']+'/beforehash',sha(S/e['path'])==e['before_sha256']);ck('Neutral/'+e['path']+'/afterhash',sha(Path(e['private_path']))==e['sha256'])
 if e['path'].endswith('.json'):
  before=read(S/e['path']);after=read(Path(e['private_path']));ck('DMSO '+e['path']+'/exact graph coordinates',all(before[k]==after[k]for k in ['atoms','bonds','functionalGroups']))
 else:
  before=ET.fromstring((S/e['path']).read_text(encoding='utf8'));after=ET.fromstring(Path(e['private_path']).read_text(encoding='utf8'))
  def artwork(x):return[(z.tag,dict(z.attrib),z.text)for z in x.iter()if not z.tag.endswith('desc')and not z.tag.endswith('title')]
  ck('DMSO SVG actual artwork unchanged',artwork(before)==artwork(after))
ck('DMSO display source neutral',all(s not in (proposed['dimethyl-sulfoxide']['caption']+' '.join(proposed['dimethyl-sulfoxide']['limitations'])).lower()for s in ['qdoh','esterification','spectrophotometric','nmr']))
ck('Helium role neutral','carrier'not in ' '.join(proposed['helium']['limitations']).lower())
entry=next(x for x in read(CR/'registry.json')['entries']if x['id']==cr['entry_id']);ck('Bulk registry exactbefore',entry==cr['entry_before']);ck('Bulk registry hash',sha(CR/'registry.json')==cr['registry_before_sha256'])
for f,h in cr['asset_hashes'].items():ck('Bulk asset/'+f,sha(CR/f)==h)
cm=read(CR/entry['modelPath']);cif=(CR/entry['cifPath']).read_text(encoding='utf8')
ck('Undoped bulk atoms',Counter(a['element']for a in cm['atoms'])=={'Zn':2,'O':2});ck('No dopant occupancies',all(a['occupancy']==1 and not a['mixed_site']for a in cm['atoms']));ck('Prior independentlyidentifiedCOD',all(s in cif for s in['Kihara','Donnay','1985','9004178']));ck('Actualbulkcell separate',all(s in cif for s in ['3.2494','5.2038'])and'3.2495' in cr['scope']and'5.2067'in cr['scope']);ck('No sourcegeometrylabel',cr['reference_only']and cr['training_eligible']is False and cr['measured_sample_coordinates']is False);ck('Six contextualbulk links',set(cr['additional_record_ids'])=={'schwartz-2003-'+i for i in['zno-route','co-route','ni-route','topo-zno','topo-co','topo-ni']})
manual=['All 96 material slots across 30 independently audited records matched to correct chemical/specimen references. Hydrate expanded formulas agree with source condensed notation; unknown optional-additive hydration, surface control identity and technicalTOPO mixture remain unresolved, while pureTOPO is only its named component.','All eight reused entries read for identity and scope; each available 2D/3D molecular graph independently reconstructed. TMAOH pentahydrate is the correct quaternary-ammonium/hydroxide/fivewater formula unit, DMSO is sulfoxide, ethylacetate ester, n-heptane linearC7, ethanol/toluene and threeC8-chainTOPO correct. Computed coordinates are illustrative; no solutioncoordination or surfaceoccupancy inferred.','DMSO source-specific grade/QDOH/NMR metadata was found and corrected privately. Exact existing graph,bonds,coordinates,groupmembership and SVGartwork remain unchanged; previous provenance retained. Helium carrier-gas wording is neutralized because current use iscryostatcoolant.','Twelve product cards are source-scoped. Surface-CoS2 is not substitutionalCo,aggregate powder distinct fromisolateddots. Mixed analytical/modelrecords get no misleading singleproductreference.','Existing undoped bulkZnO COD9004178 is unchanged:2Zn+2O expandedunitcell,fulloccupancy,spacegroup186,a3.2494/c5.2038Å. It differs frompaper-cited3.2495/5.2067Å and isexplicitly independentreference,not synthesizedsample,dopantarrangement ortraininggroundtruth. No CIF or atompositions fabricated.','Molecularsourceaudit separately passed newest12entries. This report binds finalcanonicalhashes,allreferencebytes,neutralization andbulkproposal. No Site mutation or new downloads.']
fails=[x for x in C if not x['passed']];out={'status':'passed'if not fails else'failed','source_id':'schwartz2003','bindings_sha256':sha(V/'bindings-additions.json'),'product_reference_sha256':sha(V/'product-reference-proposal.json'),'crystal_reference_sha256':sha(V/'crystal-reference-proposal.json'),'neutralization_sha256':sha(V/'registry-neutralizations.json'),'reused_reference_input_sha256':sha(V/'reused-reference-audit-input.json'),'registry_sha256':sha(V/'registry-additions.json'),'record_hashes':audited,'reused_asset_hashes':assets,'graph_results':graphs,'record_count':30,'material_binding_count':96,'product_binding_count':12,'reused_reference_count':8,'check_count':len(C),'checks':C,'failures':fails,'manual_review':manual,'site_mutated':False}
(B/'bindings-source-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(B/'bindings-source-audit.md').write_text('# Schwartz 2003 bindings and reference audit\n\n'+out['status']+f'; {len(C)} supporting checks and {len(fails)} failures.\n\n'+'\n\n'.join(manual)+'\n',encoding='utf8');print(json.dumps({'status':out['status'],'checks':len(C),'failures':fails}))
