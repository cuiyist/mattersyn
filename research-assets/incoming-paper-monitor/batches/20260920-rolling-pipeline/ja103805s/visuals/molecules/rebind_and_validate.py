"""Final private author checks and exact binding to corrected canonical v3."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
from copy import deepcopy
import json,hashlib,math,sys,shutil,xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;B=O.parents[1];ROOT=B.parents[4];C=B/'canonical-proposal/v3';S=ROOT/'recipe-atlas'
sys.path.insert(0,str(ROOT/'research-assets/rdkit-runtime'))
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
from PIL import Image
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def ptr(x,p):
 for k in p.strip('/').split('/'):x=x[int(k)] if isinstance(x,list) else x[k]
 return x
assert not (O/'package-freeze.json').exists(),'Frozen package must not change.'
g=read(O/'generation-manifest.json');checks=0
for p,h in g['input_hashes'].items():assert sha(p)==h,p;checks+=1
assert sha(B/'proposal-freeze-v3.json')=='0e419d0d014740f7713debcd1baf3446b17a08ef2e4e1a67df394d2b45cc43dd'
for a in read(B/'proposal-freeze-v3.json')['bound_files']:assert sha(a['path'])==a['sha256'];checks+=1
cm=read(C/'record-manifest.json');records={r['record_id']:read(r['path']) for r in cm['records']}
for r in cm['records']:assert sha(r['path'])==r['sha256'];checks+=1
assets=[p for d in ['svg','models','previews','contacts'] for p in (O/d).glob('*') if p.is_file()];ah={str(p):sha(p) for p in assets}
archive=O/'binding-history/canonical-v2';archive.mkdir(parents=True,exist_ok=True)
files=['bindings-proposal.json','material-slot-map.json','stock-component-map.json'];changes=[]
for fn in files:
 p=O/fn;a=archive/fn
 if not a.exists():shutil.copyfile(p,a)
 current=read(p);before=read(a)
 rows=([b for bs in current['bindingNotes'].values() for b in bs.values()] if fn=='bindings-proposal.json' else current)
 for row in rows:
  rid=row['record_id'];old=read(B/'canonical-proposal/v2'/(rid+'.json'));new=records[rid]
  assert old['materials']==new['materials'] and old['stocks']==new['stocks'];checks+=2
  h=sha(C/(rid+'.json'))
  if row['canonical_record_sha256']!=h:changes.append({'file':fn,'record_id':rid,'json_pointer':row['json_pointer'],'before_sha256':row['canonical_record_sha256'],'after_sha256':h});row['canonical_record_sha256']=h
 save(p,current)
assert len(changes)==10 or len(changes)==0,len(changes)
if not (O/'canonical-v3-rebind.json').exists():
 save(O/'canonical-v3-rebind.json',{'status':'bounded_material_stock_hash_rebind','source':'canonical v2 to v3 residual-pot correction','prior_binding_files':[{'path':str(archive/f),'sha256':sha(archive/f)} for f in files],'canonical_manifest_sha256':sha(C/'record-manifest.json'),'proposal_freeze_v3_sha256':sha(B/'proposal-freeze-v3.json'),'hash_changes':changes,'all_slot_assignments_and_captions_unchanged':True,'all_assets_unchanged':ah})
registry=read(O/'registry-additions.json');entries={e['id']:e for e in registry['entries']};by_mid={e['provenance']['sourceMaterialId']:e for e in entries.values()}
assert len(entries)==50 and len(by_mid)==50;checks+=2
slotmap=read(O/'material-slot-map.json');stockmap=read(O/'stock-component-map.json');bindings=read(O/'bindings-proposal.json')
assert len(slotmap)==123 and len(stockmap)==13 and sum(len(s['components']) for s in stockmap)==41;checks+=3
for x in slotmap:
 r=records[x['record_id']];m=ptr(r,x['json_pointer']);e=entries[x['registry_id']]
 assert m['id']==x['material_id']==e['provenance']['sourceMaterialId'];checks+=1
 assert {k:m[k] for k in x['canonical_identity']}==x['canonical_identity'];checks+=1
 assert sha(C/(r['record_id']+'.json'))==x['canonical_record_sha256'];checks+=1
 assert bindings['recordBindings'][r['record_id']][m['id']]==e['id'];checks+=1
 assert bindings['bindingNotes'][r['record_id']][m['id']]==x;checks+=1
 assert x['entry_sha256']==hashlib.sha256(json.dumps(e,ensure_ascii=False,sort_keys=True).encode()).hexdigest();checks+=1
 assert x['binding_approved'] is False;checks+=1
for x in stockmap:
 r=records[x['record_id']];s=ptr(r,x['json_pointer']);assert s['id']==x['stock_id'];assert s['scope']==x['scope'];assert s['concentrations']==x['concentrations'];checks+=3
 assert sha(C/(r['record_id']+'.json'))==x['canonical_record_sha256'];checks+=1
 for q in x['components']:
  comp=ptr(r,q['json_pointer']);m=ptr(r,q['material_json_pointer']);assert comp['material_id']==m['id']==q['material_id'];assert comp['quantities']==q['source_quantities'];assert by_mid[m['id']]['id']==q['registry_id'];assert q['binding_approved'] is False;checks+=4
graphchecks=[]
for e in entries.values():
 assert e['binding_approved'] is False and not e['published'] and not e['eligible_training'];checks+=3
 assert e['provenance']['sourceDoi']=='10.1021/ja103805s';checks+=1
 root=ET.fromstring((O/e['svgPath']).read_text(encoding='utf-8'));assert root.tag.endswith('svg');checks+=1
 assert not root.findall('.//{http://www.w3.org/2000/svg}image');checks+=1
 for key in ['svgPath','model2dPath','model3dPath']:
  if e.get(key):assert sha(O/e[key])==e['assetHashes'][key];checks+=1
 if not e['model2dPath'] and not e['model3dPath']:assert e['depictionKind']!='molecule';checks+=1
 for key in ['model2dPath','model3dPath']:
  if not e.get(key):continue
  m=read(O/e[key]);assert m['id']==e['id'];checks+=1
  assert [a['index'] for a in m['atoms']]==list(range(len(m['atoms'])));checks+=1
  for a in m['atoms']:
   assert all(math.isfinite(a[k]) for k in 'xyz');checks+=1
  for bond in m['bonds']:assert 0<=bond['a']<len(m['atoms']) and 0<=bond['b']<len(m['atoms']) and bond['a']!=bond['b'];checks+=1
  for fg in m['functionalGroups']:
   assert all(0<=i<len(m['atoms']) for i in fg['atomIndices']);assert all(0<=i<len(m['bonds']) for i in fg['bondIndices']);checks+=2
  if key=='model2dPath':
   mol=Chem.MolFromSmiles(m['connectivitySmiles']);assert mol is not None;assert mol.GetNumAtoms()==len(m['atoms']);assert mol.GetNumBonds()==len(m['bonds']);checks+=3
   assert not m['has3D'] and not m['allowRotation'] and all(a['z']==0 for a in m['atoms']);checks+=1
   # Canonical SMILES may reorder atoms; compare reconstructed graph identity,
   # not its atom sequence, to the separately encoded connectivity string.
   rw=Chem.RWMol()
   for a in m['atoms']:
    atom=Chem.Atom(a['element']);atom.SetFormalCharge(a['formalCharge']);atom.SetIsotope(a['isotope']);atom.SetNumExplicitHs(a['implicitHydrogenCount']);atom.SetNoImplicit(True);rw.AddAtom(atom);checks+=1
   for bond in m['bonds']:
    kind={1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE,3:Chem.BondType.TRIPLE,1.5:Chem.BondType.AROMATIC}[bond['order']];rw.AddBond(bond['a'],bond['b'],kind)
    if bond['order']==1.5:rw.GetAtomWithIdx(bond['a']).SetIsAromatic(True);rw.GetAtomWithIdx(bond['b']).SetIsAromatic(True)
    checks+=1
   reconstructed=rw.GetMol();Chem.SanitizeMol(reconstructed)
   # The exported 2D coordinates carry stereo presentation. Connectivity is
   # compared without stereochemical order because graph atoms omit CIP flags.
   assert Chem.MolToSmiles(reconstructed,isomericSmiles=False)==Chem.MolToSmiles(mol,isomericSmiles=False),e['id'];checks+=1
   assert rdMolDescriptors.CalcMolFormula(reconstructed)==rdMolDescriptors.CalcMolFormula(mol);checks+=1
   mid=e['provenance']['sourceMaterialId'];ph=sum(a.GetTotalNumHs() for a in mol.GetAtoms() if a.GetAtomicNum()==15)
   if mid in ['dpp','compound-7','dppse','dop','dbp','dipp','dopo','dopse','compound-4']:assert ph==1;checks+=1
   if mid=='toluene-d8':assert sum(a.GetAtomicNum()==1 and a.GetIsotope()==2 for a in mol.GetAtoms())==8;checks+=1
   graphchecks.append({'id':e['id'],'formula':rdMolDescriptors.CalcMolFormula(mol),'P_H_count':ph,'formal_charge':sum(a.GetFormalCharge() for a in mol.GetAtoms()),'isotope_D_count':sum(a.GetAtomicNum()==1 and a.GetIsotope()==2 for a in mol.GetAtoms())})
assert sum(bool(e['model2dPath']) for e in entries.values())==32;assert sum(bool(e['model3dPath']) for e in entries.values())==1;checks+=2
assert all(not by_mid[mid]['model3dPath'] for mid in by_mid if mid!='species9');checks+=49
# Independent-of-builder equation replay from the retained typed CIF, using a metric tensor.
ci=read(B/'cif-source-inventory.json');sourcepath=Path(r'[local path redacted]');assert sha(sourcepath)==ci['source_sha256'];checks+=1
sc={x['tag']:x['token']['value'] for x in ci['scalars']};num=lambda x:float(str(x).split('(')[0]);length=[num(sc['_cell_length_'+k]) for k in 'abc'];angles=[math.radians(num(sc['_cell_angle_'+k])) for k in ['alpha','beta','gamma']]
metric=[[length[0]**2,length[0]*length[1]*math.cos(angles[2]),length[0]*length[2]*math.cos(angles[1])],[length[0]*length[1]*math.cos(angles[2]),length[1]**2,length[1]*length[2]*math.cos(angles[0])],[length[0]*length[2]*math.cos(angles[1]),length[1]*length[2]*math.cos(angles[0]),length[2]**2]]
model=read(O/by_mid['species9']['model3dPath']);sourceatoms=next(x['rows'] for x in ci['loops'] if '_atom_site_label' in x['tags']);assert len(sourceatoms)==len(model['atoms'])==51;checks+=1
for row,atom in zip(sourceatoms,model['atoms']):
 d={k:v['value'] for k,v in row.items()};assert atom['label']==d['_atom_site_label'];assert atom['element']==d['_atom_site_type_symbol'];assert atom['occupancy']==num(d['_atom_site_occupancy']);assert atom['source_calc_flag']==d['_atom_site_calc_flag'];assert atom['fractional_coordinates']==[num(d['_atom_site_fract_'+k]) for k in 'xyz'];checks+=5
for i,a in enumerate(model['atoms']):
 for b in model['atoms'][i+1:]:
  v=[a['fractional_coordinates'][k]-b['fractional_coordinates'][k] for k in range(3)];d2=sum(v[j]*metric[j][k]*v[k] for j in range(3) for k in range(3));cart2=sum((a[k]-b[k])**2 for k in 'xyz');assert abs(d2-cart2)<1e-9;checks+=1
assert Counter(a['element'] for a in model['atoms'])==Counter(C=24,H=20,P=2,Pb=1,Se=4);assert sum(a['source_calc_flag']=='calc' for a in model['atoms'])==20;checks+=2
transform=read(O/'species9-transform-validation.json');assert len(model['bonds'])==transform['retained_intra_asymmetric_unit_connections']==56;checks+=1
assert all(b['order']==1 and 'not a chemical bond-order' in b['rendered_line_semantics'] for b in model['bonds']);checks+=56
pm=read(O/'preview-manifest.json')
for q in pm['previews']+pm['contact_sheets']:
 assert sha(q['path'])==q['sha256'];im=Image.open(q['path']);im.verify();checks+=2
for p,h in ah.items():assert sha(p)==h;checks+=1
snapshot=O/'reference-snapshots/chemical-viewer.mjs';shutil.copyfile(S/'dist/chemical-viewer.mjs',snapshot)
visual={'author':'/root/norberg2004_extract','actual_visual_check':True,'scope':'All seven final contact sheets covering every one of the 50 previews were opened and visually inspected. Native DPPSe, deuterated toluene and species9 previews were additionally inspected at full size. This is author visual review, not a mounted browser test or independent audit.','contact_sheets':pm['contact_sheets'],'previews':pm['previews'],'source_basis':'Previously completed full-source extraction and passed independent source audit; identity diagrams and named compounds are reused without inventing solution speciation.','observations':['Every title, formula and footer is visible; molecular connectivity is displayed with distinct functional-group colors.','P–H functionality is preserved in secondary phosphines and their source-assigned oxides/selenides.','Commercial TOP entries and unknown phosphorus impurities remain symbolic; purity labels do not become measured composition.','Unisolated intermediates remain explicit mechanistic hypotheses with no atomic model.','Species9 shows the measured molecular unit and riding H with a rotatable model proposal; it is not a quantum dot.'],'pre_freeze_author_presentation_fixes':['Replaced nested SVG positioning with an explicit translated group to keep title/formula visible in the raster renderer.','Used PCA viewing axes for the species9 static preview only; original transformed 3D coordinates remained unchanged.'],'no_open_author_visual_findings':True,'independent_audit':'pending','mounted_browser_test':'not_performed'}
save(O/'author-visual-inspection.json',visual)
report={'status':'passed_author_source_binding_graph_coordinate_and_asset_checks','author':'/root/norberg2004_extract','created_at':datetime.now(timezone.utc).isoformat(),'checks':checks,'counts':g['counts'],'canonical_version':3,'canonical_manifest_sha256':sha(C/'record-manifest.json'),'source_audit_sha256':sha(B/'source-scientific-audit.json'),'chemical_graphs':graphchecks,'source9_metric_pair_checks':1275,'source9_atom_count':51,'source9_riding_hydrogen_count':20,'source9_connections':56,'model_scope':'Only molecular species9 has source crystallographic coordinates; no exact CdSe/PbSe QD structure pair.','asset_hashes_unchanged_by_rebind':True,'all_binding_approved':False,'independent_audit':'pending','browser_test':'not_performed','published':False,'training_eligible':False}
save(O/'author-validation.json',report)
print(json.dumps({'checks':checks,'registry':sha(O/'registry-additions.json'),'validation':sha(O/'author-validation.json'),'hash_rebindings':len(changes)}))
