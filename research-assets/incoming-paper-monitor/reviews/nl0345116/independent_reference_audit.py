from pathlib import Path
from collections import Counter
import json,hashlib,sys,math,itertools,shlex,xml.etree.ElementTree as ET
sys.path.insert(0,'[local path redacted]')
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
B=Path(__file__).resolve().parent;V=B/'visuals';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
C=[]
def ck(test,n):
 C.append({'check':n,'passed':bool(test)})
 if not test:raise AssertionError(n)
def report(path,data):
 data.update(status='passed_independent_source_and_artifact_audit',checks=C.copy(),check_count=len(C),site_mutated=False)
 (B/path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
reg=load(V/'registry-additions.json');entries=reg['entries'];ck(len(entries)==12,'Twelve source-scoped references')
asset_hashes={}
for e in entries:
 ck(e['provenance']['sourceDoi']=='10.1021/nl0345116',e['id']+' source DOI')
 ck(e['provenance']['measuredCoordinates'] is False and e['provenance']['eligible_training'] is False,e['id']+' excluded measured/training coordinates')
 for key,h in e['assetHashes'].items():
  p=V/e[key];ck(sha(p)==h,e['id']+' '+key+' exact hash');asset_hashes[e[key]]=h
  if key=='svgPath':ck(ET.parse(p).getroot().tag.endswith('svg'),e['id']+' valid SVG')
 if e['id']!='trimethylsilane':ck(e['model2dPath'] is None and e['model3dPath'] is None,e['id']+' identity/schematic only')
e=entries[0];mol=Chem.AddHs(Chem.MolFromSmiles('C[SiH](C)C'))
ck(rdMolDescriptors.CalcMolFormula(mol)=='C3H10Si','Trimethylsilane named free-molecule formula')
ck(Chem.GetFormalCharge(mol)==0,'Trimethylsilane neutral')
for key in ['model2dPath','model3dPath']:
 m=load(V/e[key]);a=m['atoms'];bs=m['bonds']
 ck(Counter(x['element']for x in a)=={'C':3,'H':10,'Si':1},key+' exact atom count')
 ck(len(bs)==13,key+' saturated acyclic bond count')
 ck(all(x['formalCharge']==0 for x in a),key+' formal charge neutral')
 expected={(min(b.GetBeginAtomIdx(),b.GetEndAtomIdx()),max(b.GetBeginAtomIdx(),b.GetEndAtomIdx()),b.GetBondTypeAsDouble())for b in mol.GetBonds()}
 ck({(min(b['a'],b['b']),max(b['a'],b['b']),b['order'])for b in bs}==expected,key+' exact independently specified graph')
 ck(all(all(math.isfinite(x[k])for k in ['x','y','z'])for x in a),key+' finite positions')
 g=m['functionalGroups'];ck(len(g)==1 and set(g[0]['atomIndices'])=={1,7} and g[0]['bondIndices']==[6],key+' Si-H highlight exact bond')
 if key=='model3dPath':
  for b in bs:
   d=math.dist([a[b['a']][k]for k in ['x','y','z']],[a[b['b']][k]for k in ['x','y','z']]);ck(.8<d<2.1,'Computed bond length plausible '+str(b))
  ck(m['has3D'] and m['allowRotation'] and m['eligible_training'] is False,'Computed molecular reference explicitly rotatable/not experimental')
em={e['id']:e for e in entries}
for i in ['lead-chxbu','topo-reagent','formvar-grid','pmma']:ck(em['identity-sashchiuk-'+i]['formula']is None,i+' unresolved/mixture formula not invented')
for i,f in [('pbse-individual','PbSe'),('pbse-spheres','PbSe'),('pbse-wires','PbSe'),('silicon-substrate','Si'),('silica-layer','SiO2'),('titanium','Ti'),('gold','Au')]:ck(em['identity-sashchiuk-'+i]['formula']==f,i+' composition scope')
ck('different chlorosilane' in entries[0]['caption'] and 'does not verify' in entries[0]['caption'],'Printed trimethylsilane versus bound trimethylsilyl caveat')
report('molecular-source-audit.json',{'source_id':'sashchiuk2004','registry_sha256':sha(V/'registry-additions.json'),'source_audit_sha256':sha(B/'source-audit.json'),'entry_count':12,'asset_hashes':asset_hashes,'visual_review':{'contacts_actually_viewed':[str(V/'review/molecular-contact-1.png'),str(V/'review/molecular-contact-2.png')],'all_twelve_cards_viewed':True},'scope':'Independent source identity/formula/connectivity/functional-group and computed conformer audit; all12 original cards actually visually inspected on two contacts. Unknown precursor and mixture/polymer identities remain unmodeled; device materials stay supports. No shared-reference binding yet certified.'})
(B/'molecular-source-audit.md').write_text('# Independent chemical reference audit\n\nPassed all '+str(len(C))+' checks for 12 entries and exact asset hashes. Both contact sheets actually viewed. Trimethylsilane has the correct neutral C3H10Si graph and Si–H highlight; its computed conformer is explicitly a free-molecule illustration, not proof of the printed surface treatment. Unknown Pb-cHxBu structure and TOPO mixture composition remain unassigned. Device supports and PbSe assembly cartoons do not imply measured coordinates.\n',encoding='utf8')
C=[];proposal=load(V/'crystal-reference-proposal.json');D=V/'crystal-reference';entry=proposal['entries'][0];unit=load(D/entry['modelPath']);finite=load(D/entry['finiteModelPath'])
for f in proposal['files']:ck(sha(D/f['path'])==f['sha256'],'Crystal artifact hash '+f['path'])
ck(entry['referenceOnly'] and not entry['trainingEligible'] and not entry['measuredSampleStructure'],'Reference entry excluded measured/training assignments')
ck(entry['spaceGroupNumber']==1 and entry['prototypeSpaceGroupNumber']==225,'Expanded P1 export distinct from ideal prototype Fm-3m')
# Independent restricted CIF reader: parse exact scalar/loop syntax used, then roundtrip every site into the viewer JSON.
tokens=[]
for ln in (D/entry['cifPath']).read_text(encoding='utf8').splitlines():
 if ln and not ln.startswith('#'):tokens.extend(shlex.split(ln))
scalars={};loops=[];i=1
while i<len(tokens):
 if tokens[i]=='loop_':
  i+=1;names=[]
  while i<len(tokens)and tokens[i].startswith('_'):names.append(tokens[i]);i+=1
  vals=[]
  while i<len(tokens)and tokens[i]!='loop_'and not tokens[i].startswith('_'):vals.append(tokens[i]);i+=1
  ck(len(vals)%len(names)==0,'CIF loop column count');loops.append([dict(zip(names,vals[j:j+len(names)]))for j in range(0,len(vals),len(names))])
 elif tokens[i].startswith('_'):scalars[tokens[i]]=tokens[i+1];i+=2
 else:raise ValueError(tokens[i])
ck(scalars['_chemical_formula_sum']=='Pb4 Se4','CIF conventional formula')
for k in ['a','b','c']:ck(float(scalars['_cell_length_'+k])==unit['cell'][k]==6.1,'Source rounded lattice '+k)
for k in ['alpha','beta','gamma']:ck(float(scalars['_cell_angle_'+k])==unit['cell'][k]==90,'Cell angle '+k)
ck(scalars['_space_group_name_H-M_alt']=='P 1' and scalars['_space_group_IT_number']=='1','CIF P1 declarations')
ck(loops[0]==[{'_space_group_symop_operation_xyz':'x,y,z'}],'CIF only identity symmetry')
sites=loops[1];ck(len(sites)==len(unit['atoms'])==8,'Eight expanded sites')
ck(Counter(x['_atom_site_type_symbol']for x in sites)=={'Pb':4,'Se':4},'Four Pb and four Se')
for s,a in zip(sites,unit['atoms']):
 xyz=[float(s['_atom_site_fract_'+k])for k in ['x','y','z']]
 ck(xyz==a['fractional'] and s['_atom_site_type_symbol']==a['element'] and s['_atom_site_label']==a['site'],'CIF to JSON site '+a['site'])
 ck(all(abs(a[k]-6.1*xyz[j])<1e-9 for j,k in enumerate(['x','y','z'])),'Fractional Cartesian roundtrip '+a['site'])
 neighbors=[]
 for b in unit['atoms']:
  for shift in itertools.product([-1,0,1],repeat=3):
   dist=math.sqrt(sum((b[k]+6.1*shift[j]-a[k])**2 for j,k in enumerate(['x','y','z'])))
   if abs(dist-3.05)<1e-8:neighbors.append(b['element'])
 ck(len(neighbors)==6 and all(x!=a['element']for x in neighbors),'Six opposite-species periodic neighbors '+a['site'])
ck(Counter(a['element']for a in finite['atoms'])=={'Pb':2048,'Se':2048},'Finite illustration counts')
xyz=(D/'downloads/pbse-illustrative-block.xyz').read_text(encoding='utf8').splitlines();ck(int(xyz[0])==4096 and len(xyz)==4098,'XYZ count and rows')
for a,line in zip(finite['atoms'],xyz[2:]):
 vals=line.split();ck(vals[0]==a['element'] and all(float(vals[j+1])==a[k]for j,k in enumerate(['x','y','z'])),'XYZ atom '+str(a['index']))
ck(len({tuple(a[k]for k in ['x','y','z'])for a in finite['atoms']})==4096,'No duplicate finite positions')
for k in ['x','y','z']:ck(abs(max(a[k]for a in finite['atoms'])-min(a[k]for a in finite['atoms'])-45.75)<1e-7,'Finite center-span '+k)
ck(finite['cell_envelope_nm']==4.88 and finite['atom_center_span_nm']==4.575,'Envelope and atom-center dimensions not confused')
ck(unit['periodic'] and finite['periodic']is False and finite['training_eligible']is False and finite['measured_sample_structure']is False,'Finite and unit periodicity/scope flags')
ck('not a fitted or measured particle' in finite['caption'] and 'not measured' in entry['description'],'No current specimen reconstruction claim')
ck(entry['record_ids']==['sashchiuk-2004-'+x for x in ['individual-low','sphere-intermediate','wire-intermediate','wire-high']],'Reference applies to four PbSe routes without asserting measured per-route coordinates')
report('crystal-source-audit.json',{'source_id':'sashchiuk2004','crystal_reference_sha256':sha(V/'crystal-reference-proposal.json'),'source_audit_sha256':sha(B/'source-audit.json'),'artifact_hashes':{f['path']:f['sha256']for f in proposal['files']},'scope':'Independently parsed the simple scalar/loop P1 CIF syntax, roundtripped all8sites to JSON and Cartesian coordinates, checked sixfold3.05Å opposite-species coordination and all4096XYZ/JSON rows. This is constructed ideal geometry using rounded reported a6.1Å, never measured sample coordinates. No external database, DFT relaxation or general-purpose CIF parser certification claimed.'})
(B/'crystal-source-audit.md').write_text('# Ideal PbSe reference audit\n\nPassed '+str(len(C))+' independent checks. Expanded P1 CIF has four Pb and four Se, correct 6.1 Å cubic cell and six opposite-species nearest neighbors per periodic site at 3.05 Å. All eight CIF sites roundtrip to JSON; all 4,096 finite XYZ rows match the nonperiodic model. The 4.88 nm cell envelope and 4.575 nm atom-center span are correctly distinguished.\n\nThe eight-site prototype and finite block are explicitly constructed illustrations, excluded from measured structures and training labels. No specimen-specific ligand, interface, defect or assembly coordinates are claimed. CIF checking uses an independent restricted parser for this file’s scalar/loop syntax, not a claim of general parser interoperability or DFT suitability.\n',encoding='utf8')
print('Independent molecular and crystal audits passed.')
