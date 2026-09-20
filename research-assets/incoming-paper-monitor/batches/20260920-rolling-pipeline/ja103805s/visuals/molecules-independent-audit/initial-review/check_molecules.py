"""Independent molecular graph, source-coordinate, slot and public-path audit."""
import pathlib,json,hashlib,math,re,collections,sys
E=pathlib.Path(__file__).resolve().parents[2];B=E/'visuals/molecules';O=pathlib.Path(__file__).parent
sys.path.insert(0,r'[local path redacted]')
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
counts=collections.Counter();fail=[];bound={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):p=pathlib.Path(p);bound[str(p)]=sha(p);return json.loads(p.read_text(encoding='utf-8-sig'))
def ck(ok,cat,msg):
 counts[cat]+=1
 if not ok:fail.append({'category':cat,'detail':msg})
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def ptr(o,p):
 for k in p.lstrip('/').split('/') if p else []:o=o[int(k)] if isinstance(o,list) else o[k.replace('~1','/').replace('~0','~')]
 return o
freeze=read(B/'package-freeze.json')
for x in freeze['bound_files']:
 p=pathlib.Path(x['path']);ck(p.exists() and sha(p)==x['sha256'],'frozen_hash',str(p))
 if p.exists():bound[str(p)]=sha(p)
records={p.stem:read(p) for p in sorted((E/'canonical-proposal/v3').glob('evans-2010-*.json'))}
registry=read(B/'registry-additions.json');entries={x['id']:x for x in registry['entries']};slots=read(B/'material-slot-map.json');stocks=read(B/'stock-component-map.json');bindings=read(B/'bindings-proposal.json')
ck(freeze['canonical_version']==3 and freeze['canonical_manifest_sha256']==sha(E/'canonical-proposal/v3/record-manifest.json'),'canonical_boundary','v3')
expected_slots={(rid,m['id']) for rid,r in records.items() for m in r['materials']};actual_slots={(x['record_id'],x['material_id']) for x in slots}
ck(expected_slots==actual_slots and len(actual_slots)==len(slots)==123,'slot_complete','123')
for s in slots:
 rid=s['record_id'];r=records[rid];m=ptr(r,s['json_pointer']);e=entries[s['registry_id']]
 ck(m['id']==s['material_id'],'slot_pointer',rid+' '+m['id'])
 ck(s['canonical_record_sha256']==sha(E/'canonical-proposal/v3'/f'{rid}.json'),'slot_record_hash',rid)
 ck(s['entry_sha256']==digest(e),'entry_hash',s['registry_id'])
 ck(s['canonical_identity']=={k:m[k] for k in s['canonical_identity']},'slot_exact_identity',rid+' '+m['id'])
 ck(e['provenance']['sourceMaterialId']==m['id'],'slot_reference_identity',rid+' '+m['id'])
 ck(bindings['recordBindings'][rid][m['id']]==e['id'],'slot_runtime_mapping',rid+' '+m['id'])
 note=bindings['bindingNotes'][rid][m['id']]
 ck(note['viewOverrides']==s['viewOverrides'],'slot_override_exact',rid+' '+m['id'])
 ck(note['binding_approved'] is False and s['binding_approved'] is False,'pending_gate',rid+' '+m['id'])
 ck(set(s['viewOverrides'])<=set(['name','caption','limitations']),'override_whitelist',rid+' '+m['id'])
 ck(s['viewOverrides']['name']==m['name'],'override_name',rid+' '+m['id'])
expected_stock={(rid,x['id']) for rid,r in records.items() for x in r['stocks']}
ck(expected_stock=={(s['record_id'],s['stock_id']) for s in stocks} and len(stocks)==13,'stock_complete','13')
component_count=0
for s in stocks:
 r=records[s['record_id']];stock=ptr(r,s['json_pointer'])
 ck(stock['id']==s['stock_id'],'stock_pointer',s['stock_id'])
 ck(s['canonical_record_sha256']==sha(E/'canonical-proposal/v3'/f"{s['record_id']}.json"),'stock_record_hash',s['stock_id'])
 ck(s['concentrations']==stock['concentrations'],'stock_concentrations',s['stock_id'])
 ck(len(s['components'])==len(stock['components']),'stock_components_complete',s['stock_id'])
 for c in s['components']:
  component_count+=1;source=ptr(r,c['json_pointer']);material=ptr(r,c['material_json_pointer'])
  ck(source['material_id']==c['material_id']==material['id'],'component_pointer',s['stock_id']+' '+c['material_id'])
  ck(c['source_quantities']==source['quantities'],'component_quantity',s['stock_id']+' '+c['material_id'])
  ck(bindings['recordBindings'][s['record_id']][c['material_id']]==c['registry_id'],'component_binding',s['stock_id']+' '+c['material_id'])
ck(component_count==41,'component_count','41')
# Expected neutral named connectivities independently specified from the source names/diagrams.
expected={
 'oa':('CCCCCCCC/C=C\\CCCCCCCC(=O)O','C18H34O2'),
 'compound-2':('CCCCCCCC/C=C\\CCCCCCCC(=O)O','C18H34O2'),
 'ode':('C=CCCCCCCCCCCCCCCCC','C18H36'),
 'acetone':('CC(=O)C','C3H6O'),
 'toluene':('c1ccccc1C','C7H8'),'toluene-grade-unspecified':('c1ccccc1C','C7H8'),
 'topse':('P(=[Se])(CCCCCCCC)(CCCCCCCC)CCCCCCCC','C24H51PSe'),
 'tbp':('P(CCCC)(CCCC)CCCC','C12H27P'),
 'dpp':('[PH](c1ccccc1)c1ccccc1','C12H11P'),'compound-7':('[PH](c1ccccc1)c1ccccc1','C12H11P'),
 'dppse':('[PH](=[Se])(c1ccccc1)c1ccccc1','C12H11PSe'),
 'tep':('P(CC)(CC)CC','C6H15P'),'tipp':('P(C(C)C)(C(C)C)C(C)C','C9H21P'),
 'dipp':('[PH](C(C)C)C(C)C','C6H15P'),'tpp':('P(c1ccccc1)(c1ccccc1)c1ccccc1','C18H15P'),
 'tippse':('P(=[Se])(C(C)C)(C(C)C)C(C)C','C9H21PSe'),
 'tepse':('P(=[Se])(CC)(CC)CC','C6H15PSe'),'tppse':('P(=[Se])(c1ccccc1)(c1ccccc1)c1ccccc1','C18H15PSe'),
 'dop':('[PH](CCCCCCCC)CCCCCCCC','C16H35P'),'dbp':('[PH](CCCC)CCCC','C8H19P'),
 'dopo':('[PH](=O)(CCCCCCCC)CCCCCCCC','C16H35OP'),'dopse':('[PH](=[Se])(CCCCCCCC)CCCCCCCC','C16H35PSe'),
 'tms':('[Si](C)(C)(C)C','C4H12Si'),'h3po4':('P(=O)(O)(O)O','H3O4P'),
 'toluene-d8':('[2H]c1c([2H])c([2H])c(C([2H])([2H])[2H])c([2H])c1[2H]','C7H8'),
 'compound-3':('P(c1ccccc1)(c1ccccc1)OC(=O)*',None),
 'compound-4':('[PH](=O)(c1ccccc1)c1ccccc1','C12H11OP'),
 'compound-5':('*C(=O)OC(=O)*',None),'compound-8':('P(=[Se])(c1ccccc1)(c1ccccc1)OC(=O)*',None),
 'compound-12':('P(c1ccccc1)(c1ccccc1)P(c1ccccc1)c1ccccc1','C24H20P2'),
 'compound-13':('P(=O)(O)(c1ccccc1)c1ccccc1','C12H11O2P'),'n2':('N#N','N2')}
graph_results=[]
for e in entries.values():
 mid=e['provenance']['sourceMaterialId'];ck(not e['published'] and not e['eligible_training'] and not e['binding_approved'],'pending_gate',e['id'])
 for k in ['svgPath','model2dPath','model3dPath']:
  if e.get(k):ck(sha(B/e[k])==e['assetHashes'][k],'asset_hash',e['id']+' '+k)
 ck(not e['model3dPath'] or mid=='species9','no_QD_coordinate_inference',e['id'])
 if not e['model2dPath']:continue
 model=read(B/e['model2dPath']);atoms=model['atoms'];bb=model['bonds'];rw=Chem.RWMol()
 for ix,a in enumerate(atoms):
  ck(a['index']==ix and all(math.isfinite(a[k]) for k in 'xyz') and a['z']==0,'2d_coordinates',e['id']+' '+str(ix))
  x=Chem.Atom(a['element']);x.SetFormalCharge(a['formalCharge']);x.SetIsotope(a['isotope']);x.SetNumExplicitHs(a['implicitHydrogenCount']);x.SetNoImplicit(True);rw.AddAtom(x)
 for bond in bb:
  ck(0<=bond['a']<len(atoms) and 0<=bond['b']<len(atoms) and bond['a']!=bond['b'],'bond_indices',e['id'])
  bt={1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,1.5:Chem.BondType.AROMATIC}[bond['order']];rw.AddBond(bond['a'],bond['b'],bt)
  if bond['order']==1.5:rw.GetAtomWithIdx(bond['a']).SetIsAromatic(True);rw.GetAtomWithIdx(bond['b']).SetIsAromatic(True)
 mol=rw.GetMol();Chem.SanitizeMol(mol);wanted=Chem.MolFromSmiles(expected[mid][0]);formula=rdMolDescriptors.CalcMolFormula(mol)
 ck(Chem.MolToSmiles(mol,isomericSmiles=False)==Chem.MolToSmiles(wanted,isomericSmiles=False),'independent_named_graph',mid)
 if expected[mid][1]:ck(formula==expected[mid][1],'independent_formula',mid+' '+formula)
 ck(not model['has3D'] and not model['allowRotation'],'2d_not_geometry',mid)
 ck(model['functionalGroups']==e['functionalGroups'],'functional_group_contract',mid)
 for g in model['functionalGroups']:
  aa=g['atomIndices'];bi=g['bondIndices'];ck(all(0<=i<len(atoms) for i in aa) and all(0<=i<len(bb) for i in bi),'functional_group_indices',mid)
  ck(all(bb[i]['a'] in aa and bb[i]['b'] in aa for i in bi),'functional_group_internal_bonds',mid)
  if g['label']=='Phosphorus center':ck(all(atoms[i]['element']=='P' for i in aa),'functional_group_identity',mid)
  if g['label']=='Selenium functionality':ck(all(atoms[i]['element']=='Se' for i in aa),'functional_group_identity',mid)
  if 'Carbonyl' in g['label']:ck(any(bb[i]['order']==2 and {atoms[bb[i]['a']]['element'],atoms[bb[i]['b']]['element']}=={'C','O'} for i in bi),'functional_group_identity',mid)
 ph=sum(a.GetTotalNumHs() for a in mol.GetAtoms() if a.GetAtomicNum()==15)
 if mid in ['dpp','compound-7','dppse','dop','dbp','dipp','dopo','dopse','compound-4']:ck(ph==1,'P_H_retained',mid)
 if mid=='toluene-d8':ck(sum(a['element']=='H' and a['isotope']==2 for a in atoms)==8,'isotope_count',mid)
 if mid in ['compound-3','compound-5','compound-8']:ck(sum(a['element']=='*' for a in atoms)==(2 if mid=='compound-5' else 1) and 'R is the source abbreviation C17H33' in ' '.join(e['limitations']),'R_abbreviation_scope',mid)
 if mid in ['oa','compound-2']:ck(Chem.MolToSmiles(Chem.MolFromSmiles(model['connectivitySmiles']),isomericSmiles=True)==Chem.MolToSmiles(wanted,isomericSmiles=True),'named_oleic_reference_stereo',mid)
 graph_results.append({'material_id':mid,'formula':formula,'P_H_count':ph,'atom_count':len(atoms),'bond_count':len(bb)})
ck(len(graph_results)==32,'graph_count','32')
ci=read(E/'cif-source-inventory.json');sc={x['tag']:x['token']['value'] for x in ci['scalars']};num=lambda x:float(str(x).split('(')[0])
source=pathlib.Path(ci['source_path']);bound[str(source)]=sha(source);ck(sha(source)==ci['source_sha256'],'original_cif_hash','unchanged')
cell=[num(sc['_cell_length_'+k]) for k in 'abc'];alpha,beta,gamma=[math.radians(num(sc['_cell_angle_'+k])) for k in ['alpha','beta','gamma']]
# Independent explicit upper-triangular Cartesian basis from original scalar values.
a,b,c=cell;cy=c*(math.cos(alpha)-math.cos(beta)*math.cos(gamma))/math.sin(gamma);basis=[[a,0,0],[b*math.cos(gamma),b*math.sin(gamma),0],[c*math.cos(beta),cy,math.sqrt(c*c-(c*math.cos(beta))**2-cy*cy)]]
entry=next(e for e in entries.values() if e['provenance']['sourceMaterialId']=='species9');model=read(B/entry['model3dPath']);aa=model['atoms'];rows=next(l['rows'] for l in ci['loops'] if '_atom_site_label' in l['tags']);bylabel={x['label']:x for x in aa}
ck(len(aa)==len(rows)==51,'source_atoms_complete','51')
for row in rows:
 d={k:v['value'] for k,v in row.items()};atom=bylabel[d['_atom_site_label']];frac=[num(d['_atom_site_fract_'+k]) for k in 'xyz'];cart=[sum(frac[i]*basis[i][k] for i in range(3)) for k in range(3)]
 ck(atom['element']==d['_atom_site_type_symbol'] and atom['occupancy']==num(d['_atom_site_occupancy']) and atom['source_calc_flag']==d['_atom_site_calc_flag'],'source_atom_identity',atom['label'])
 ck(atom['fractional_coordinates']==frac,'source_fractional_exact',atom['label'])
 for k,val in zip('xyz',cart):ck(abs(atom[k]-val)<1e-11,'source_cartesian_transform',atom['label']+' '+k)
ck(collections.Counter(x['element'] for x in aa)==collections.Counter(C=24,H=20,P=2,Pb=1,Se=4),'species9_formula','C24H20P2PbSe4')
ck(sum(x['source_calc_flag']=='calc' for x in aa)==20,'riding_H_count','20')
bondrows=next(l['rows'] for l in ci['loops'] if '_geom_bond_distance' in l['tags']);intra=[];inter=[]
for row in bondrows:
 d={k:v['value'] for k,v in row.items()};(intra if d['_geom_bond_site_symmetry_2']=='.' else inter).append(d)
expected_connections={tuple(sorted((x['_geom_bond_atom_site_label_1'],x['_geom_bond_atom_site_label_2']))) for x in intra};actual_connections={tuple(sorted((aa[x['a']]['label'],aa[x['b']]['label']))) for x in model['bonds']}
ck(actual_connections==expected_connections and len(model['bonds'])==len(intra)==56,'source_connections_exact','56; no symmetry-expanded contact added')
for bond in model['bonds']:
 labels=tuple(sorted((aa[bond['a']]['label'],aa[bond['b']]['label'])));d=next(x for x in intra if tuple(sorted((x['_geom_bond_atom_site_label_1'],x['_geom_bond_atom_site_label_2'])))==labels)
 ck(bond['source_distance_raw']==d['_geom_bond_distance'],'source_distance_raw',labels)
 ck(bond['order']==1 and 'not a chemical bond-order' in bond['rendered_line_semantics'],'stick_not_bond_order',labels)
ck(len(inter)==3,'excluded_contacts','3 source symmetry-related rows')
for x in slots:
 if x['registry_id']==entry['id']:ck(x['material_id']=='species9' and x['record_id']=='evans-2010-reagents' and x['canonical_identity']['role']=='source_material' and 'Molecular species9 crystallization' in x['canonical_identity']['evidence'][0]['locator'],'species9_slot_scope',x['record_id'])
public=read(B/'public-asset-proposal.json');expected_assets={(e['id'],k,e[k]) for e in entries.values() for k in ['svgPath','model2dPath','model3dPath'] if e.get(k)}
ck({(x['registry_id'],x['kind'],x['registry_relative_path']) for x in public['assets']}==expected_assets and len(public['assets'])==83,'public_allowlist_exact','50 SVG and 33 JSON')
for x in public['assets']:
 path=pathlib.Path(x['private_path']);ck(path.resolve().is_relative_to(B.resolve()) and sha(path)==x['sha256'],'public_candidate_hash',x['registry_relative_path'])
 ck(path.suffix.lower() in ['.svg','.json'] and path.parent.name in ['svg','models'],'no_original_document_public',x['registry_relative_path'])
 text=path.read_text();ck(not re.search(r'(?i)((?<![A-Za-z])[A-Z]:[\\/]|file://|complete-source-payloads|firstPagePreviewPrivate)',text),'no_private_link_public',x['registry_relative_path'])
reuse=read(B/'reuse-qualification.json')
for x in reuse['snapshots']:
 p=B/x['snapshot_path'];ck(sha(p)==x['sha256'],'retained_snapshot_hash',x['snapshot_path'])
pm=read(B/'preview-manifest.json')
for x in pm['previews']+pm['contact_sheets']:ck(sha(pathlib.Path(x['path']))==x['sha256'],'preview_hash',x['path'])
report={'schema':'mattersyn-independent-molecular-checks/1','reviewer':'/root/peng1998_reader_assets','status':'passed' if not fail else 'findings','checks':sum(counts.values()),'categories':dict(counts),'failures':fail,'graphs':graph_results,'source_cell_basis':basis,'counts':freeze['counts'],'bound_files':bound,'scope':'Independent graph specifications, source-coordinate transform and complete slot/stock comparison. Contact sheets and source diagrams reviewed separately. No mounted browser or publication claim.'}
p=O/'mechanical-audit.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k not in ['graphs','bound_files']},ensure_ascii=False,indent=2))
